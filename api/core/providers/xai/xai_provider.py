import json
from json import JSONDecodeError
from typing import Any, override

from httpx import Response
from pydantic import BaseModel, ValidationError

from core.domain.errors import (
    ContentModerationError,
    FailedGenerationError,
    MaxTokensExceededError,
    ModelDoesNotSupportMode,
    StructuredGenerationError,
)
from core.domain.llm_usage import LLMUsage
from core.domain.message import Message
from core.domain.models import Model, Provider
from core.domain.models.model_data import ModelData
from core.domain.models.utils import get_model_data
from core.domain.tool_call import ToolCallRequestWithID
from core.providers.base.httpx_provider import HTTPXProvider, ParsedResponse
from core.providers.base.models import RawCompletion, StandardMessage
from core.providers.base.provider_options import ProviderOptions
from core.providers.base.streaming_context import ToolCallRequestBuffer
from core.providers.base.utils import get_provider_config_env, get_unique_schema_name, should_use_structured_output
from core.providers.google.google_provider_domain import (
    internal_tool_name_to_native_tool_call,
    native_tool_name_to_internal,
)
from core.providers.openai.openai_domain import parse_tool_call_or_raise
from core.providers.xai.xai_config import THINKING_MODEL_MAP, XAIConfig
from core.providers.xai.xai_domain import (
    CompletionRequest,
    CompletionResponse,
    JSONResponseFormat,
    JSONSchemaResponseFormat,
    StreamedResponse,
    StreamOptions,
    Tool,
    ToolFunction,
    XAIError,
    XAIMessage,
    XAISchema,
    XAIToolMessage,
)
from core.runners.workflowai.utils import FileWithKeyPath


class XAIProvider(HTTPXProvider[XAIConfig, CompletionResponse]):
    def _response_format(self, options: ProviderOptions, model_data: ModelData):
        if not should_use_structured_output(options, model_data) or not options.output_schema:
            return JSONResponseFormat()

        return JSONSchemaResponseFormat(
            json_schema=XAISchema(
                name=get_unique_schema_name(options.task_name, options.output_schema),
                json_schema=options.output_schema,
            ),
        )

    @override
    def _build_request(self, messages: list[Message], options: ProviderOptions, stream: bool) -> BaseModel:
        message: list[XAIMessage | XAIToolMessage] = []
        for m in messages:
            if m.tool_call_results:
                message.extend(XAIToolMessage.from_domain(m))
            else:
                message.append(XAIMessage.from_domain(m))

        model_data = get_model_data(options.model)

        model_value, reasoning_effort = THINKING_MODEL_MAP.get(options.model, (options.model.value, None))

        completion_request = CompletionRequest(
            messages=message,
            model=model_value,
            temperature=options.temperature,
            max_tokens=options.max_tokens,
            stream=stream,
            stream_options=StreamOptions(include_usage=True) if stream else None,
            response_format=self._response_format(options, model_data),
            reasoning_effort=reasoning_effort,
        )

        if options.enabled_tools is not None and options.enabled_tools != []:
            completion_request.tools = [
                Tool(
                    type="function",
                    function=ToolFunction(
                        name=internal_tool_name_to_native_tool_call(tool.name),
                        description=tool.description,
                        parameters=tool.input_schema,
                    ),
                )
                for tool in options.enabled_tools
            ]

        return completion_request

    @override
    def _response_model_cls(self) -> type[CompletionResponse]:
        return CompletionResponse

    @classmethod
    def xai_message_or_tool_message(cls, messag_dict: dict[str, Any]) -> XAIMessage | XAIToolMessage:
        try:
            return XAIToolMessage.model_validate(messag_dict)
        except ValidationError:
            return XAIMessage.model_validate(messag_dict)

    @classmethod
    def standardize_messages(cls, messages: list[dict[str, Any]]) -> list[StandardMessage]:
        result: list[StandardMessage] = []
        current_tool_messages: list[XAIToolMessage] = []

        for message in (cls.xai_message_or_tool_message(m) for m in messages):
            if isinstance(message, XAIToolMessage):
                current_tool_messages.append(message)
            else:
                # Process any accumulated tool messages before adding the non-tool message
                if current_tool_messages:
                    if tool_message := XAIToolMessage.to_standard(current_tool_messages):
                        result.append(tool_message)
                    current_tool_messages = []

                # Add the non-tool message
                result.append(message.to_standard())

        # Handle any remaining tool messages at the end
        if current_tool_messages:
            if tool_message := XAIToolMessage.to_standard(current_tool_messages):
                result.append(tool_message)

        return result

    @override
    async def _request_headers(self, request: dict[str, Any], url: str, model: Model) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._config.api_key}",
        }

    @override
    def _request_url(self, model: Model, stream: bool) -> str:
        return self._config.url

    # TODO:
    # @override
    # def _extract_reasoning_steps(self, response: CompletionResponse) -> list[InternalReasoningStep] | None:
    #     return None

    @override
    def _extract_content_str(self, response: CompletionResponse) -> str:
        for choice in response.choices:
            if choice.finish_reason == "length":
                raise MaxTokensExceededError(
                    msg="Model returned a response with a length finish reason, meaning the maximum number of tokens was exceeded.",
                    raw_completion=response,
                )
        message = response.choices[0].message
        content = message.content
        if content is None:
            if message.refusal:
                raise ContentModerationError(
                    msg=f"Model refused to generate a response: {message.refusal}",
                )
            if not message.tool_calls:
                raise FailedGenerationError(
                    msg="Model did not generate a response content",
                    capture=True,
                )
            return ""
        if isinstance(content, str):
            return content
        if len(content) > 1:
            self.logger.warning("Multiple content items found in response", extra={"response": response.model_dump()})
        # TODO: we should check if it is possible to have multiple text content items
        for item in content:
            if item.type == "text":
                return item.text
        self.logger.warning("No content found in response", extra={"response": response.model_dump()})
        return ""

    @override
    def _invalid_json_error(self, response: Response, exception: Exception, content_str: str):
        # TODO: check if this is needed
        if "sorry" in content_str.lower():
            return FailedGenerationError(
                msg=f"Model refused to generate a response: {content_str}",
                response=response,
            )
        return super()._invalid_json_error(response, exception, content_str)

    @override
    def _extract_usage(self, response: CompletionResponse) -> LLMUsage | None:
        return response.usage.to_domain() if response.usage else None

    def _invalid_request_error(self, payload: XAIError, response: Response):
        if payload.error.param == "response_format":
            if "Invalid schema" in payload.error.message:
                return StructuredGenerationError(
                    msg=payload.error.message,
                    response=response,
                )
        # Azure started returning an error with very little information about
        # a model not supporting structured generation
        if "response_format" in payload.error.message and "json_schema" in payload.error.message:
            return StructuredGenerationError(
                msg=payload.error.message,
                response=response,
            )
        if "tools is not supported in this model" in payload.error.message:
            return ModelDoesNotSupportMode(
                msg=payload.error.message,
                response=response,
                capture=True,
            )

        return None

    @override
    def _unknown_error_message(self, response: Response):
        try:
            payload = XAIError.model_validate_json(response.text)
            return payload.error.message or "Unknown error"
        except Exception:
            self.logger.exception("failed to parse Fireworks AI error response", extra={"response": response.text})
            return super()._unknown_error_message(response)

    @override
    @classmethod
    def requires_downloading_file(cls, file: FileWithKeyPath, model: Model) -> bool:
        return False

    @override
    @classmethod
    def required_env_vars(cls) -> list[str]:
        return ["XAI_API_KEY"]

    @override
    @classmethod
    def name(cls) -> Provider:
        return Provider.X_AI

    @override
    @classmethod
    def _default_config(cls, index: int) -> XAIConfig:
        return XAIConfig(api_key=get_provider_config_env("XAI_API_KEY", index))

    @override
    def default_model(self) -> Model:
        return Model.LLAMA_3_3_70B

    @property
    def is_structured_generation_supported(self) -> bool:
        return True

    def _extract_stream_delta(  # noqa: C901
        self,
        sse_event: bytes,
        raw_completion: RawCompletion,
        tool_call_request_buffer: dict[int, ToolCallRequestBuffer],
    ):
        if sse_event == b"[DONE]":
            return ParsedResponse("")
        raw = StreamedResponse.model_validate_json(sse_event)
        for choice in raw.choices:
            if choice.finish_reason == "length":
                raise MaxTokensExceededError(
                    msg="Model returned a response with a length finish reason, meaning the maximum number of tokens was exceeded.",
                    raw_completion=raw,
                )
        if raw.usage:
            raw_completion.usage = raw.usage.to_domain()

        if raw.choices:
            tools_calls: list[ToolCallRequestWithID] = []
            if raw.choices[0].delta.tool_calls:
                for tool_call in raw.choices[0].delta.tool_calls:
                    # Check if a tool call at that index is already in the buffer
                    if tool_call.index not in tool_call_request_buffer:
                        tool_call_request_buffer[tool_call.index] = ToolCallRequestBuffer()

                    buffered_tool_call = tool_call_request_buffer[tool_call.index]

                    if tool_call.id and not buffered_tool_call.id:
                        buffered_tool_call.id = tool_call.id

                    if tool_call.function.name and not buffered_tool_call.tool_name:
                        buffered_tool_call.tool_name = tool_call.function.name

                    if tool_call.function.arguments:
                        buffered_tool_call.tool_input += tool_call.function.arguments

                    if buffered_tool_call.id and buffered_tool_call.tool_name and buffered_tool_call.tool_input:
                        try:
                            tool_input_dict = json.loads(buffered_tool_call.tool_input)
                        except JSONDecodeError:
                            # That means the tool call is not full streamed yet
                            continue

                        tools_calls.append(
                            ToolCallRequestWithID(
                                id=buffered_tool_call.id,
                                tool_name=native_tool_name_to_internal(buffered_tool_call.tool_name),
                                tool_input_dict=tool_input_dict,
                            ),
                        )

            return ParsedResponse(
                raw.choices[0].delta.content or "",
                tool_calls=tools_calls,
            )

        return ParsedResponse("")

    def _compute_prompt_token_count(
        self,
        messages: list[dict[str, Any]],
        model: Model,
    ) -> float:
        raise NotImplementedError("Token counting is not implemented for XAI")

    def _compute_prompt_image_count(
        self,
        messages: list[dict[str, Any]],
    ) -> int:
        # OpenAI includes image usage in the prompt token count, so we do not need to add those separately
        return 0

    async def _compute_prompt_audio_token_count(
        self,
        messages: list[dict[str, Any]],
    ):
        return 0, None

    @classmethod
    def _extract_native_tool_calls(cls, response: CompletionResponse) -> list[ToolCallRequestWithID]:
        choice = response.choices[0]

        tool_calls: list[ToolCallRequestWithID] = [
            ToolCallRequestWithID(
                id=tool_call.id,
                tool_name=native_tool_name_to_internal(tool_call.function.name),
                # OpenAI returns the tool call arguments as a string, so we need to parse it
                tool_input_dict=parse_tool_call_or_raise(tool_call.function.arguments) or {},
            )
            for tool_call in choice.message.tool_calls or []
        ]
        return tool_calls

    @override
    async def _extract_and_log_rate_limits(self, response: Response, options: ProviderOptions):
        await self._log_rate_limit_remaining(
            "requests",
            remaining=response.headers.get("x-ratelimit-remaining-requests"),
            total=response.headers.get("x-ratelimit-limit-requests"),
            options=options,
        )
        await self._log_rate_limit_remaining(
            "tokens",
            remaining=response.headers.get("x-ratelimit-remaining-tokens"),
            total=response.headers.get("x-ratelimit-limit-tokens"),
            options=options,
        )
