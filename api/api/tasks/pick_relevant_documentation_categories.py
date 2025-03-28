import workflowai
from pydantic import BaseModel, Field

from api.tasks.meta_agent import MetaAgentChatMessage
from core.domain.documentation_section import DocumentationSection


class PickRelevantDocumentationSectionsInput(BaseModel):
    chat_messages: list[MetaAgentChatMessage] | None = Field(
        default=None,
        description="The chat messages between the user and the assistant.",
    )
    agent_instructions: str | None = Field(
        default=None,
        description="The agent's internal instructions.",
    )
    available_doc_sections: list[DocumentationSection] | None = Field(
        default=None,
        description="The available documentation sections.",
    )


class PickRelevantDocumentationSectionsOutput(BaseModel):
    reason: str = Field(description="The reason for the choice of documentation sections.")
    relevant_doc_sections: list[str] = Field(description="The relevant documentation sections for the agent.")


@workflowai.agent(model=workflowai.Model.GEMINI_2_0_FLASH_001)
async def pick_relevant_documentation_sections(
    input: PickRelevantDocumentationSectionsInput,
) -> PickRelevantDocumentationSectionsOutput:
    """
    You are an expert at picking relevant docucmentation sections for other agents.

    Your goal is to analyze the chat history and the agent's instructions, and pick the needed documentation sections required to answer the user's question, if any.
    You must avoid picking unnecessary sections, because processing them will cost money and time.
    Unnecessary sections are, for example:
    - things that the agent already knows about based on the 'agent_instructions'
    - things that are not directly related to the matters discussed in the 'chat_messages'
    - things that we already answer in older messages of the 'chat_messages'. You must focus on the latest messages in 'chat_messages'.

    Type of request that do not require any documentation section:
    - instructions improvement
    - schema updates
    - picking models
    - generating agent input
    Those cases are very well covered in the "agent_instructions".
    """
    ...
