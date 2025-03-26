import asyncio
from abc import abstractmethod
from json import JSONDecodeError
from typing import Any, AsyncIterator, Generic, Protocol, TypeVar

import httpx
from pydantic import BaseModel
from typing_extensions import override

from core.domain.errors import (
    ContentModerationError,
    FailedGenerationError,
    InternalError,
    MaxTokensExceededError,
    MissingModelError,
    ModelDoesNotSupportMode,
    ProviderBadRequestError,
    ProviderError,
    ProviderInvalidFileError,
    ProviderRateLimitError,
    UnknownProviderError,
)
from core.domain.fields.internal_reasoning_steps import InternalReasoningStep
from core.domain.llm_usage import LLMCompletionUsage, LLMUsage
from core.domain.message import Message
from core.domain.models import Model
from core.domain.models.utils import get_model_data
from core.domain.tool_call import ToolCallRequestWithID
from core.providers.base.abstract_provider import ProviderConfigInterface
from core.providers.base.httpx_provider import HTTPXProvider, ParsedResponse
from core.providers.base.models import RawCompletion, StandardMessage
from core.providers.base.provider_options import ProviderOptions
from core.providers.base.streaming_context import ToolCallRequestBuffer
from core.providers.google.google_provider_domain import (
    BLOCK_THRESHOLD,
    CompletionRequest,
    CompletionResponse,
    GoogleMessage,
    GoogleSystemMessage,
    HarmCategory,
    StreamedResponse,
    message_or_system_message,
    native_tool_name_to_internal,
)
from core.runners.workflowai.utils import FileWithKeyPath
from core.services.message import merge_messages
from core.tools import ToolKind
from core.utils.models.dumps import safe_dump_pydantic_model

MODELS_THAT_REQUIRE_DOWNLOADING_FILES = {
    Model.GEMINI_2_0_FLASH_THINKING_EXP_1219,
    Model.GEMINI_2_0_FLASH_EXP,
    Model.GEMINI_EXP_1206,
    Model.GEMINI_2_0_FLASH_THINKING_EXP_0121,
}


class GoogleProviderBaseConfig(ProviderConfigInterface, Protocol):
    @property
    def default_block_threshold(self) -> BLOCK_THRESHOLD | None: ...


_GoogleConfigVar = TypeVar("_GoogleConfigVar", bound=GoogleProviderBaseConfig)

THINKING_MODE_MODELS = (
    Model.GEMINI_2_0_FLASH_THINKING_EXP_1219,
    Model.GEMINI_2_0_FLASH_THINKING_EXP_0121,
)


class GoogleProviderBase(HTTPXProvider[_GoogleConfigVar, CompletionResponse], Generic[_GoogleConfigVar]):
    def _safety_settings(self) -> list[CompletionRequest.SafetySettings] | None:
        if self.config.default_block_threshold is None:
            return None

        return [
            CompletionRequest.SafetySettings(
                category=cat,
                threshold=self.config.default_block_threshold,
            )
            for cat in HarmCategory
        ]

    @classmethod
    def sanitize_agent_instructions(cls, instructions: str) -> str:
        # Remove the "@" prefix from tool names, since Google API does not support it for native tool calls
        for tool_name in ToolKind.__members__.values():
            if tool_name.startswith("@"):
                instructions = instructions.replace(tool_name, tool_name[1:])
        return instructions

    def _add_native_tools(self, options: ProviderOptions, completion_request: CompletionRequest):
        if options.enabled_tools not in (None, []):
            tools: CompletionRequest.Tool | None = None
            tool_config: CompletionRequest.ToolConfig | None = None

            tools = CompletionRequest.Tool(
                functionDeclarations=[],
            )

            tool_config = CompletionRequest.ToolConfig(
                functionCallingConfig=CompletionRequest.ToolConfig.FunctionCallingConfig(
                    mode="AUTO",
                ),
            )

            for tool in options.enabled_tools:
                tools.functionDeclarations.append(
                    CompletionRequest.Tool.FunctionDeclaration.from_tool(tool),
                )

            completion_request.tools = tools
            completion_request.toolConfig = tool_config

    @override
    def _build_request(self, messages: list[Message], options: ProviderOptions, stream: bool) -> BaseModel:
        system_message: GoogleSystemMessage | None = None
        user_messages: list[GoogleMessage] = []

        model_data = get_model_data(model=options.model)

        if not model_data.support_system_messages:
            # For models that do not system messages, we merge all messages into a 'USER' single message
            merged_message = merge_messages(messages, role=Message.Role.USER)
            user_messages = [GoogleMessage.from_domain(merged_message)]
        else:
            for message in messages:
                if message.role == Message.Role.USER:
                    user_messages.append(GoogleMessage.from_domain(message))
                if message.role == Message.Role.ASSISTANT:
                    user_messages.append(GoogleMessage.from_domain(message))
                if message.role == Message.Role.SYSTEM:
                    if system_message is not None:
                        raise InternalError("Multiple system messages not supported")
                    system_message = GoogleSystemMessage.from_domain(message)

        completion_request = CompletionRequest(
            systemInstruction=system_message,
            contents=user_messages,
            generationConfig=CompletionRequest.GenerationConfig(
                temperature=options.temperature,
                # TODO[max-tokens]: Set the max token from the context data
                maxOutputTokens=options.max_tokens,
                responseMimeType="application/json"
                if (model_data.supports_json_mode and not options.enabled_tools)
                # Google does not allow setting the response mime type at all when using tools.
                else "text/plain",
                thinking_config=CompletionRequest.GenerationConfig.ThinkingConfig(
                    include_thoughts=True,
                )
                if options.model in THINKING_MODE_MODELS
                else None,
            ),
            safetySettings=self._safety_settings(),
        )

        self._add_native_tools(options, completion_request)

        return completion_request

    def _raw_prompt(self, request_json: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract the raw prompt from the request JSON"""

        raw_messages: list[dict[str, Any]] = []

        if request_json.get("systemInstruction"):
            raw_messages.append(request_json["systemInstruction"])

        for message in request_json["contents"]:
            # TODO: fix noqa
            raw_messages.append(message)  # noqa: PERF402

        return raw_messages

    async def wrap_sse(self, raw: AsyncIterator[bytes], termination_chars: bytes = b"\r\n\r\n"):
        async for data in super().wrap_sse(raw, termination_chars):
            yield data

    @abstractmethod
    def _request_url(self, model: Model, stream: bool) -> str:
        pass

    @override
    def _response_model_cls(self) -> type[CompletionResponse]:
        return CompletionResponse

    @override
    def _extract_reasoning_steps(self, response: CompletionResponse):
        reasoning_step: str = ""
        if not response.candidates:
            return None
        if response.candidates[0].content and len(response.candidates[0].content.parts) > 1:
            # More than one part means the model has returned a reasoning step
            index = 0 if response.candidates[0].content.parts[0].thought else 1
            reasoning_step = response.candidates[0].content.parts[index].text or ""
            return [
                InternalReasoningStep(
                    title="Gemini Thinking Mode Thoughts",
                    explaination=reasoning_step,
                ),
            ]
        return None

    @override
    def _extract_content_str(self, response: CompletionResponse) -> str:
        # No need to check for errors, it will be handled upstream in httpx provider
        if not response.candidates:
            if response.promptFeedback and response.promptFeedback.blockReason:
                raise ContentModerationError(
                    f"The model blocked the generation with reason '{response.promptFeedback.blockReason}'",
                    capture=False,
                )
            # Otherwise not sure what's going on
            self.logger.warning(
                "No candidates found in response",
                extra={"response": safe_dump_pydantic_model(response)},
            )
            raise UnknownProviderError("No candidates found in response")

        # Check if we have a finish
        if any(c.finishReason == "MAX_TOKENS" for c in response.candidates):
            raise MaxTokensExceededError(
                msg="Model returned a MAX_TOKENS finish reason. The max number of tokens as specified in the request was reached.",
            )

        try:
            content = response.candidates[0].content
            if not content:
                self.logger.warning("No content found in first candidate", extra={"response": response.model_dump()})
                return ""

            parts = content.parts
            if not parts:
                self.logger.warning("No parts found in first candidate", extra={"response": response.model_dump()})
                return ""

            txt = parts[0].text
            if len(parts) > 1:
                # More than one part means the model has returned a reasoning step
                index = 1 if parts[0].thought else 0
                txt = parts[index].text

        except IndexError as e:
            self.logger.warning("Empty content found in response", extra={"response": response.model_dump()})
            raise e
        if not txt:
            if not parts[0].functionCall:
                self.logger.warning("Empty content found in response", extra={"response": response.model_dump()})
            return ""
        return txt

    @override
    def _extract_usage(self, response: CompletionResponse) -> LLMUsage | None:
        return response.usageMetadata.to_domain() if response.usageMetadata else None

    @classmethod
    def _extract_native_tool_calls(cls, response: CompletionResponse) -> list[ToolCallRequestWithID]:
        if not response.candidates:
            return []
        candidate = response.candidates[0]
        if candidate.content and len(candidate.content.parts) > 0:
            return [
                ToolCallRequestWithID(
                    tool_name=native_tool_name_to_internal(part.functionCall.name)
                    or "missing tool name",  # Will raise an error to pass back to the model models in the runner
                    tool_input_dict=part.functionCall.args or {},
                )
                for part in candidate.content.parts
                if part.functionCall
            ]
        return []

    @override
    def _provider_rate_limit_error(self, response: httpx.Response):
        return ProviderRateLimitError(
            retry=True,
            max_attempt_count=3,
            msg="Rate limit exceeded in region",
            response=response,
        )

    def _failed_generation_error(self, response: httpx.Response):
        return FailedGenerationError(
            msg=response.text,
            raw_completion=response.text,
            usage=LLMCompletionUsage(),
        )

    @override
    def default_model(self) -> Model:
        return Model.GEMINI_1_5_FLASH_002

    @override
    @classmethod
    def requires_downloading_file(cls, file: FileWithKeyPath, model: Model) -> bool:
        if model in MODELS_THAT_REQUIRE_DOWNLOADING_FILES:
            # Experimental models only support files passed by GCP URLs or base64 encoded strings
            return True
        # We download audio files for now
        # Since we will need it for pricing anyway
        if file.is_audio is True:
            return True
        # Google requires a content type to be set for files
        # We can guess the content type when not provided by downloading the file
        # Guessing the content type based on the URL should have happened upstream
        return not file.content_type

    @override
    def _unknown_error_message(self, response: httpx.Response):
        return response.text

    # If the error message contains these, we raise an invalid file error and pass the message as is
    _INVALID_FILE_SEARCH_STRINGS = [
        "the document has no pages",
        "unable to process input image",
    ]

    @classmethod
    def _handle_invalid_argument(cls, message: str, response: httpx.Response):
        error_cls: type[ProviderError] = ProviderBadRequestError
        error_msg = message
        capture = False
        match message.lower():
            case lower_msg if any(
                m in lower_msg
                for m in [
                    "educe the input token count and try again",
                    "exceeds the maximum number of tokens allowed",
                ]
            ):
                error_cls = MaxTokensExceededError
            case lower_msg if any(
                m in lower_msg
                for m in [
                    "number of function response parts should be equal to number of function call parts",
                    "request payload size exceeds the limit",
                ]
            ):
                pass
            case lower_msg if "non-leading vision input which the model does not support" in lower_msg:
                # Capturing since we should have the data in the model data
                capture = True
                error_cls = ModelDoesNotSupportMode
            case lower_msg if "url_error-error_not_found" in lower_msg:
                error_msg = "Provider could not retrieve file: URL returned a 404 error"
                error_cls = ProviderInvalidFileError
            case lower_msg if "url_timeout-timeout_fetchproxy" in lower_msg:
                error_msg = "Provider could not retrieve file: URL timed out"
                error_cls = ProviderInvalidFileError
            case lower_msg if "url_unreachable-unreachable_no_response" in lower_msg:
                error_msg = "Provider could not retrieve file: No response"
                error_cls = ProviderInvalidFileError
            case lower_msg if "url_rejected-rejected_rpc_app_error" in lower_msg:
                error_msg = "Provider could not retrieve file: Rejected"
                error_cls = ProviderInvalidFileError
            case lower_msg if any(m in lower_msg for m in cls._INVALID_FILE_SEARCH_STRINGS):
                error_cls = ProviderInvalidFileError
            case _:
                return
        raise error_cls(error_msg, response=response, capture=capture)

    def _handle_not_found(self, message: str, response: httpx.Response):
        if "models" in message:
            raise MissingModelError(message, capture=not self._is_custom_config, response=response)

    def _handle_unknown_error(self, payload: dict[str, Any], response: httpx.Response):
        error = payload.get("error")
        if error is None:
            return
        message = error.get("message")
        if not message:
            return

        match error.get("status"):
            case "INVALID_ARGUMENT":
                self._handle_invalid_argument(message, response)
            case "NOT_FOUND":
                self._handle_not_found(message, response)
            case _:
                return

    @override
    def _handle_error_status_code(self, response: httpx.Response):
        try:
            response_json = response.json()
        except JSONDecodeError:
            super()._handle_error_status_code(response)
            return

        # Will raise an error if the error is known
        self._handle_unknown_error(response_json, response)
        # Call upstream to handle the error
        super()._handle_error_status_code(response)

    @override
    @classmethod
    def standardize_messages(cls, messages: list[dict[str, Any]]) -> list[StandardMessage]:
        return [message_or_system_message(message).to_standard() for message in messages]

    async def _compute_prompt_audio_seconds(
        self,
        messages: list[dict[str, Any]],
    ) -> float:
        coroutines = [message_or_system_message(message).audio_duration_seconds() for message in messages]
        durations = await asyncio.gather(*coroutines)
        return sum(durations)

    @override
    async def _compute_prompt_audio_token_count(
        self,
        messages: list[dict[str, Any]],
    ):
        # 32 tokens per second https://ai.google.dev/gemini-api/docs/tokens?lang=python#multimodal-tokens
        duration = await self._compute_prompt_audio_seconds(messages)
        return int(duration * 32), duration

    @override
    def _get_prompt_text_token_count(self, llm_usage: LLMUsage):
        # audio tokens are included in the prompt token count
        if not llm_usage.prompt_audio_token_count or not llm_usage.prompt_token_count:
            return llm_usage.prompt_token_count
        return llm_usage.prompt_token_count - llm_usage.prompt_audio_token_count

    @override
    def _extract_stream_delta(
        self,
        sse_event: bytes,
        raw_completion: RawCompletion,
        tool_call_request_buffer: dict[int, ToolCallRequestBuffer],
    ):
        raw = StreamedResponse.model_validate_json(sse_event)

        if (
            raw.usageMetadata is not None
            and raw.usageMetadata.promptTokenCount is not None
            and raw.usageMetadata.candidatesTokenCount is not None
        ):
            raw_completion.usage = raw.usageMetadata.to_domain()

        if not raw.candidates:
            # No candidates so we can just skip
            return ParsedResponse("")

        if raw.candidates[0].finishReason == "RECITATION":
            raise FailedGenerationError(
                msg="Gemini API returned a RECITATION finish reason, see https://issuetracker.google.com/issues/331677495",
            )

        for candidate in raw.candidates:
            if candidate.finishReason == "MAX_TOKENS":
                raise MaxTokensExceededError(
                    msg="Model returned a MAX_TOKENS finish reason. The maximum number of tokens as specified in the request was reached.",
                )

        if not raw.candidates or not raw.candidates[0] or not raw.candidates[0].content:
            return ParsedResponse("")

        thoughts = ""
        response = ""

        native_tool_calls: list[ToolCallRequestWithID] = []
        for part in raw.candidates[0].content.parts:
            if part.thought:
                thoughts += part.text or ""
            else:
                response += part.text or ""

            if part.functionCall:
                native_tool_calls.append(
                    ToolCallRequestWithID(
                        id="",
                        tool_name=native_tool_name_to_internal(part.functionCall.name),
                        tool_input_dict=part.functionCall.args or {},
                    ),
                )

        return ParsedResponse(
            response,
            thoughts,
            native_tool_calls,
        )
