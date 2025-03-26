from typing import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from api.dependencies.analytics import UserPropertiesDep
from api.dependencies.event_router import EventRouterDep
from api.dependencies.path_params import TaskSchemaID
from api.dependencies.services import ModelsServiceDep, RunsServiceDep, StorageDep
from api.dependencies.task_info import TaskTupleDep
from api.services.internal_tasks.meta_agent_service import (
    MetaAgentChatMessage,
    MetaAgentService,
    PlaygroundState,
)
from core.utils.stream_response_utils import safe_streaming_response

router = APIRouter(prefix="/agents/{task_id}/prompt-engineer-agent")


class MetaAgentChatRequest(BaseModel):
    # Schema id is passed here instead of as a path parameters in order to have the endpoint schema-agnostic since
    # the schema id might change in the middle of the conversation based on the agent's actions.
    schema_id: TaskSchemaID

    playground_state: PlaygroundState = Field(
        description="The state of the playground",
    )

    messages: list[MetaAgentChatMessage] = Field(
        description="The list of messages in the conversation, the last message being the most recent one",
    )


class MetaAgentChatResponse(BaseModel):
    messages: list[MetaAgentChatMessage] = Field(
        description="The list of messages that compose the response of the meta-agent",
    )


@router.post(
    "/messages",
    description="To chat with WorkflowAI's meta agent",
    responses={
        200: {
            "content": {
                "text/event-stream": {
                    "schema": MetaAgentChatResponse.model_json_schema(),
                },
            },
        },
    },
)
async def get_meta_agent_chat(
    task_tuple: TaskTupleDep,
    request: MetaAgentChatRequest,
    user_properties: UserPropertiesDep,
    runs_service: RunsServiceDep,
    storage: StorageDep,
    event_router: EventRouterDep,
    models_service: ModelsServiceDep,
) -> StreamingResponse:
    async def _stream() -> AsyncIterator[BaseModel]:
        meta_agent_service = MetaAgentService(
            storage=storage,
            event_router=event_router,
            runs_service=runs_service,
            models_service=models_service,
        )

        async for messages in meta_agent_service.stream_meta_agent_response(
            task_tuple=task_tuple,
            agent_schema_id=request.schema_id,
            user_email=user_properties.user_email,
            messages=request.messages,
            playground_state=request.playground_state,
        ):
            yield MetaAgentChatResponse(messages=messages)

    return safe_streaming_response(_stream)
