import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Awaitable, Callable

import stripe
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.logging import ignore_logger

from api.errors import configure_scope_for_error
from api.services.storage import storage_for_tenant
from api.tags import RouteTags
from api.utils import (
    close_metrics,
    convert_error_response,
    error_json_response,
    log_end,
    log_start,
    log_start_with_body,
    set_start_time,
    setup_metrics,
)
from core.domain.errors import (
    DefaultError,
    ProviderError,
)
from core.domain.models import Model
from core.storage import ObjectNotFoundException
from core.storage.mongo.migrations.migrate import check_migrations, migrate
from core.utils import no_op
from core.utils.background import wait_for_background_tasks
from core.utils.uuid import uuid7

from .common import setup
from .routers import (
    probes,
    run,
)
from .services.request_id_ctx import request_id_var

setup()

logger = logging.getLogger(__name__)
ignore_logger(__name__)


async def _prepare_storage():
    storage = storage_for_tenant(
        tenant="__system__",
        tenant_uid=-1,
        event_router=no_op.event_router,
        encryption=no_op.NoopEncryption(),
    )
    # If the environment variable is set to true, we migrate the database
    if os.environ.get("WORKFLOWAI_MONGO_MIGRATIONS_ON_START") == "true":
        await migrate(storage)
        return

    # By default, We check migrations and log an exception if they are not in sync
    # Crashing if the migrations are not good here would be problematic in
    # a multi replica environment
    try:
        # check_migrations raises an error if the migrations are not in sync
        await check_migrations(storage)
    except Exception as e:
        logger.exception(e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    metrics_service = await setup_metrics()

    logger.info("Checking migrations")

    # TODO: purge connection pool for httpx_provider

    await _prepare_storage()

    logger.info("Preparing providers")

    from api.services.providers_service import shared_provider_factory

    factory = shared_provider_factory()
    logger.info(f"Prepared providers {', '.join(list(factory.available_providers()))}")  # noqa: G004

    logger.info("Starting services")
    yield

    # Closing the metrics service to send whatever is left in the buffer
    await close_metrics(metrics_service)
    await wait_for_background_tasks()


_ONLY_RUN_ROUTES = os.getenv("ONLY_RUN_ROUTES") == "true"

app = FastAPI(
    title="FlowMind",
    description="Structured AI workflows",
    version="0.1.0",
    openapi_tags=[
        {"name": RouteTags.AGENTS},
        {"name": RouteTags.AGENT_SCHEMAS},
        {"name": RouteTags.RUNS},
        {"name": RouteTags.EXAMPLES},
        {"name": RouteTags.AGENT_GROUPS},
        {"name": RouteTags.ORGANIZATIONS},
        {"name": RouteTags.MODELS},
        {"name": RouteTags.MONITORING},
        {"name": RouteTags.TRANSCRIPTIONS},
        {"name": RouteTags.API_KEYS},
        {"name": RouteTags.PAYMENTS},
        {"name": RouteTags.NEW_TOOL_AGENT},
    ]
    if not _ONLY_RUN_ROUTES
    else [],
    lifespan=lifespan,
)


WORKFLOWAI_ALLOWED_ORIGINS = os.environ.get("WORKFLOWAI_ALLOWED_ORIGINS", os.environ.get("WORKFLOWAI_APP_URL"))
if WORKFLOWAI_ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=WORKFLOWAI_ALLOWED_ORIGINS.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(probes.router)
app.include_router(run.router)

if not _ONLY_RUN_ROUTES:
    from .main_router import main_router

    app.include_router(main_router)


# Because the run and api containers are deployed at different times,
# the run container must be the source of truth for available models, otherwise
# the API might believe that some models are available when they are not.
@app.get("/v1/models", description="List all available models", include_in_schema=False)
async def list_all_available_models() -> list[Model]:
    # No need to filter anything here as the raw models will not be exposed
    # The api container will filter the models based on the task schema
    return list(Model)


@app.exception_handler(ObjectNotFoundException)
async def object_not_found_exception_handler(request: Request, exc: ObjectNotFoundException):
    return error_json_response(
        status_code=404,
        msg=str(exc),
        code=exc.code,
    )


@app.exception_handler(stripe.CardError)
async def stripe_card_exception_handler(request: Request, exc: stripe.CardError):
    return error_json_response(
        status_code=402,
        msg=str(exc),
        code="card_validation_error",
    )


@app.exception_handler(ProviderError)
async def provider_error_handler(request: Request, exc: ProviderError):
    exc.capture_if_needed()
    retry_after = exc.retry_after_str()
    if retry_after:
        headers = {"Retry-After": retry_after}
    else:
        headers = None
    return convert_error_response(exc.error_response(), headers=headers)


@app.exception_handler(DefaultError)
async def default_error_handler(request: Request, exc: DefaultError):
    return convert_error_response(exc.error_response())


print_body = logger.getEffectiveLevel() <= logging.DEBUG

_log_start = log_start_with_body if print_body else log_start


@app.middleware("http")
async def logger_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    start_time = time.time()
    set_start_time(request, start_time)

    rid = request.headers.get("X-Request-Id", str(uuid7()))
    request_id_var.set(rid)

    await _log_start(request, request_id_var, logger)

    try:
        response = await call_next(request)
    except Exception as e:
        log_end(
            request,
            start_time=start_time,
            status_code=500,
            logger=logger,
            error=e,
        )

        # Re raising for normal sentry processing
        with configure_scope_for_error(e):
            raise e

    log_end(
        request,
        start_time=start_time,
        status_code=response.status_code,
        logger=logger,
    )

    return response
