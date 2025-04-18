from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field

from core.domain.errors import InternalError
from core.domain.fields.file import File
from core.domain.llm_usage import LLMUsage
from core.domain.message import Message
from core.providers.base.models import (
    DocumentContentDict,
    DocumentURLDict,
    ImageContentDict,
    ImageURLDict,
    StandardMessage,
    TextContentDict,
    ToolCallRequestDict,
    ToolCallResultDict,
)
from core.providers.google.google_provider_domain import (
    internal_tool_name_to_native_tool_call,
    native_tool_name_to_internal,
)

_role_to_map: dict[Message.Role, Literal["user", "assistant"]] = {
    Message.Role.SYSTEM: "assistant",
    Message.Role.USER: "user",
    Message.Role.ASSISTANT: "assistant",
}


class TextContent(BaseModel):
    type: Literal["text"]
    text: str

    def to_standard(self) -> TextContentDict:
        return {"type": "text", "text": self.text}


class FileSource(BaseModel):
    type: Literal["base64"]
    media_type: str
    data: str

    def to_standard(self) -> DocumentURLDict | ImageURLDict:
        return {"url": f"data:{self.media_type};base64,{self.data}"}


class DocumentContent(BaseModel):
    type: Literal["document"]
    source: FileSource

    def to_standard(self) -> DocumentContentDict:
        return {"type": "document_url", "source": self.source.to_standard()}


class ImageContent(BaseModel):
    type: Literal["image"]
    source: FileSource

    def to_standard(self) -> ImageContentDict:
        return {"type": "image_url", "image_url": self.source.to_standard()}


class ToolUseContent(BaseModel):
    type: Literal["tool_use"]
    id: str
    name: str
    input: dict[str, Any]

    def to_standard(self) -> ToolCallRequestDict:
        return {
            "type": "tool_call_request",
            "id": self.id,
            "tool_name": native_tool_name_to_internal(self.name),
            "tool_input_dict": self.input,
        }


class ToolResultContent(BaseModel):
    type: Literal["tool_result"]
    tool_use_id: str
    content: str

    def to_standard(self) -> ToolCallResultDict:
        return {
            "type": "tool_call_result",
            "id": self.tool_use_id,
            "tool_name": None,
            "result": self.content,
            "error": None,
            "tool_input_dict": None,
        }


class AnthropicMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: list[TextContent | DocumentContent | ImageContent | ToolUseContent | ToolResultContent]

    @classmethod
    def content_from_domain(cls, file: File):
        if file.data is None:
            raise InternalError("Data is always required for Anthropic", extras={"file": file.model_dump()})
        if file.is_pdf:
            return DocumentContent(
                type="document",
                source=FileSource(type="base64", media_type="application/pdf", data=file.data),
            )
        if file.is_image:
            if not file.content_type:
                raise InternalError("Content type is required for Anthropic", extras={"file": file.model_dump()})
            return ImageContent(
                type="image",
                source=FileSource(type="base64", media_type=file.content_type, data=file.data),
            )

        raise InternalError("Unsupported file type", extras={"file": file.model_dump()})

    @classmethod
    def from_domain(cls, message: Message):
        role = _role_to_map[message.role]

        content: list[TextContent | DocumentContent | ImageContent | ToolUseContent | ToolResultContent] = []
        if message.content:
            content.append(TextContent(type="text", text=message.content))

        content.extend([cls.content_from_domain(file) for file in message.files or []])

        content.extend(
            [
                ToolUseContent(
                    type="tool_use",
                    id=tool.id,
                    name=internal_tool_name_to_native_tool_call(tool.tool_name),
                    input=tool.tool_input_dict,
                )
                for tool in message.tool_call_requests or []
            ],
        )

        content.extend(
            [
                ToolResultContent(
                    type="tool_result",
                    tool_use_id=tool.id,
                    content=str(tool.result) if tool.result else f"Error: {tool.error}",
                )
                for tool in message.tool_call_results or []
            ],
        )
        return cls(content=content, role=role)

    def to_standard(self) -> StandardMessage:
        return {"role": self.role, "content": [item.to_standard() for item in self.content]}


class CompletionRequest(BaseModel):
    messages: List[AnthropicMessage]
    model: str
    max_tokens: int
    temperature: float
    stream: bool

    class Tool(BaseModel):
        name: str
        description: str | None = None
        input_schema: dict[str, Any]

    tools: list[Tool] | None = None


class Usage(BaseModel):
    input_tokens: int | None = None
    output_tokens: int | None = None

    def to_domain(self) -> LLMUsage:
        return LLMUsage(
            prompt_token_count=self.input_tokens,
            completion_token_count=self.output_tokens,
        )


class ContentBlock(BaseModel):
    type: Literal["text"]
    text: str


class CompletionResponse(BaseModel):
    content: list[ContentBlock | ToolUseContent]
    usage: Usage
    stop_reason: str | None = None


class TextDelta(BaseModel):
    type: Literal["text_delta"]
    text: str


class DeltaMessage(BaseModel):
    type: Literal["text_delta"]
    text: str


class ContentBlockDelta(BaseModel):
    type: Literal["content_block_delta"]
    index: int
    delta: TextDelta


class ContentBlockStart(BaseModel):
    type: Literal["content_block_start"]
    index: int
    content_block: ContentBlock


class ContentBlockStop(BaseModel):
    type: Literal["content_block_stop"]
    index: int


class MessageStart(BaseModel):
    type: Literal["message_start"]
    message: dict[str, Any]


class MessageDelta(BaseModel):
    type: Literal["message_delta"]
    delta: dict[str, Any]
    usage: Optional[Usage]


class MessageStop(BaseModel):
    type: Literal["message_stop"]


class StopReasonDelta(BaseModel):
    type: Literal["stop_reason_delta"] = "stop_reason_delta"
    stop_reason: str | None = None
    stop_sequence: str | None = None


class ToolUse(BaseModel):
    type: Literal["tool_use"]
    id: str
    name: str
    input: dict[str, Any] | None = None


class InputJsonDelta(BaseModel):
    type: Literal["input_json_delta"]
    partial_json: str


class CompletionChunk(BaseModel):
    """Represents a streaming chunk response from Anthropic"""

    type: Literal[
        "message_start",
        "content_block_start",
        "content_block_delta",
        "content_block_stop",
        "message_delta",
        "message_stop",
        "ping",
    ]
    # For message_start
    message: Optional[dict[str, Any]] = None
    # For content_block_start
    content_block: Optional[ContentBlock | ToolUse] = None
    # For content_block_delta
    delta: Optional[TextDelta | StopReasonDelta | InputJsonDelta] = None
    # For message_delta
    usage: Optional[Usage] = None
    index: Optional[int] = None

    def extract_delta(self) -> str:
        """Extract the text delta from the chunk"""
        if self.type == "content_block_delta" and isinstance(self.delta, TextDelta):
            return self.delta.text
        if self.type == "message_delta" and isinstance(self.delta, StopReasonDelta):
            return self.delta.stop_reason or self.delta.stop_sequence or ""
        return ""


class AnthropicErrorResponse(BaseModel):
    type: Literal["error"]

    class ErrorDetails(BaseModel):
        message: str | None = None
        code: str | None = None
        type: str | None = None

    error: ErrorDetails = Field(default_factory=ErrorDetails)
