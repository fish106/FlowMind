from typing import Annotated

from taskiq import Context, TaskiqDepends

from api.services import storage as storage_service
from api.services.analytics import AnalyticsService
from api.services.background_run import BackgroundRunService
from api.services.groups import GroupService
from api.services.internal_tasks.internal_tasks_service import InternalTasksService
from api.services.internal_tasks.meta_agent_service import MetaAgentService
from api.services.payments import PaymentService
from api.services.reviews import ReviewsService
from api.services.run import RunService
from api.services.runs import RunsService
from api.services.versions import VersionsService
from core.deprecated.workflowai import WorkflowAI
from core.domain.analytics_events.analytics_events import UserProperties
from core.domain.events import Event, EventRouter
from core.domain.users import UserIdentifier
from core.providers.factory.local_provider_factory import shared_provider_factory
from core.storage.azure.azure_blob_file_storage import FileStorage
from core.storage.backend_storage import BackendStorage
from core.utils.encryption import Encryption


def encryption_dep() -> Encryption:
    return storage_service.shared_encryption()


EncryptionDep = Annotated[Encryption, TaskiqDepends(encryption_dep)]


def event_dep(context: Annotated[Context, TaskiqDepends()]) -> Event:
    event = context.message.args[0]
    if not isinstance(event, Event):
        raise ValueError("Event dependency must be an Event")
    return event


EventDep = Annotated[Event, TaskiqDepends(event_dep)]


def user_properties_dep(event: EventDep) -> UserProperties | None:
    return event.user_properties


UserPropertiesDep = Annotated[UserProperties, TaskiqDepends(user_properties_dep)]


def event_router_dep(event: EventDep) -> EventRouter:
    from api.services.event_handler import tenant_event_router

    return tenant_event_router(
        event.tenant,
        event.tenant_uid,
        event.user_properties,
        event.organization_properties,
        event.task_properties,
    )


EventRouterDep = Annotated[EventRouter, TaskiqDepends(event_router_dep)]


def analytics_service_dep(event: EventDep, event_router: EventRouterDep) -> AnalyticsService:
    from api.services.analytics import analytics_service

    return analytics_service(
        user_properties=event.user_properties,
        organization_properties=event.organization_properties,
        event_router=event_router,
        task_properties=event.task_properties,
    )


AnalyticsServiceDep = Annotated[AnalyticsService, TaskiqDepends(analytics_service_dep)]


def storage_dep(event: EventDep, event_router: EventRouterDep) -> BackendStorage:
    from api.services import storage as storage_service

    return storage_service.storage_for_tenant(event.tenant, event.tenant_uid, event_router=event_router)


StorageDep = Annotated[BackendStorage, TaskiqDepends(storage_dep)]


def file_storage_dep() -> FileStorage:
    return storage_service.file_storage_for_tenant()


FileStorageDep = Annotated[FileStorage, TaskiqDepends(file_storage_dep)]


def group_service_dep(
    event_router: EventRouterDep,
    storage: StorageDep,
    analytics_service: AnalyticsServiceDep,
    enc: EncryptionDep,
    event: EventDep,
):
    from api.services.groups import GroupService

    return GroupService(
        storage=storage,
        encryption=enc,
        event_router=event_router,
        analytics_service=analytics_service,
        user=UserIdentifier(
            user_id=str(event.user_properties.user_id if event.user_properties else None),
            user_email=str(event.user_properties.user_email if event.user_properties else None),
        ),
    )


GroupServiceDep = Annotated[GroupService, TaskiqDepends(group_service_dep)]


def run_service_dep(
    event: EventDep,
    event_router: EventRouterDep,
    analytics_service: AnalyticsServiceDep,
    storage: StorageDep,
    group_service: GroupServiceDep,
):
    user = event.user_properties.to_user_identifier() if event.user_properties else None

    return RunService(
        storage=storage,
        event_router=event_router,
        group_service=group_service,
        analytics_service=analytics_service,
        user=user,
    )


RunServiceDep = Annotated[RunService, TaskiqDepends(run_service_dep)]


def wai_dep(
    storage: StorageDep,
    file_storage: FileStorageDep,
    run_service: RunServiceDep,
) -> WorkflowAI:
    return WorkflowAI(
        run_service=run_service,
        storage=storage,
        file_storage=file_storage,
    )


WaiDep = Annotated[WorkflowAI, TaskiqDepends(wai_dep)]


def runs_service_for_event_dep(
    storage: StorageDep,
    event_router: EventRouterDep,
    analytics_service: AnalyticsServiceDep,
    file_storage: FileStorageDep,
):
    return RunsService(
        storage=storage,
        provider_factory=shared_provider_factory(),
        event_router=event_router,
        analytics_service=analytics_service,
        file_storage=file_storage,
    )


RunsServiceDep = Annotated[RunsService, TaskiqDepends(runs_service_for_event_dep)]


def internal_tasks_service_dep(wai: WaiDep, storage: StorageDep, event_router: EventRouterDep) -> InternalTasksService:
    return InternalTasksService(
        wai=wai,
        storage=storage,
        event_router=event_router,
    )


InternalTasksServiceDep = Annotated[InternalTasksService, TaskiqDepends(internal_tasks_service_dep)]


def review_service_dep(
    storage: StorageDep,
    event_router: EventRouterDep,
    internal_tasks: InternalTasksServiceDep,
):
    return ReviewsService(
        backend_storage=storage,
        event_router=event_router,
        internal_tasks=internal_tasks,
    )


ReviewsServiceDep = Annotated[ReviewsService, TaskiqDepends(review_service_dep)]


def meta_agent_service_dep(storage: StorageDep, event_router: EventRouterDep) -> MetaAgentService:
    return MetaAgentService(storage=storage, event_router=event_router)


MetaAgentServiceDep = Annotated[MetaAgentService, TaskiqDepends(meta_agent_service_dep)]


def versions_service_dep(storage: StorageDep, event_router: EventRouterDep) -> VersionsService:
    return VersionsService(storage=storage, event_router=event_router)


VersionsServiceDep = Annotated[VersionsService, TaskiqDepends(versions_service_dep)]


def payment_service_dep(
    storage: StorageDep,
    event_router: EventRouterDep,
    analytics_service: AnalyticsServiceDep,
) -> PaymentService:
    from api.services.payments import PaymentService

    return PaymentService(
        storage=storage,
        event_router=event_router,
        analytics_service=analytics_service,
    )


PaymentServiceDep = Annotated[PaymentService, TaskiqDepends(payment_service_dep)]


def background_run_service_dep(
    storage: StorageDep,
    event_router: EventRouterDep,
    group_service: GroupServiceDep,
    run_service: RunServiceDep,
):
    return BackgroundRunService(
        run_service=run_service,
        storage=storage,
        event_router=event_router,
        group_service=group_service,
        user=run_service.user,
    )


BackgroundRunServiceDep = Annotated[BackgroundRunService, TaskiqDepends(background_run_service_dep)]
