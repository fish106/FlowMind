from datetime import date

from pydantic import BaseModel, Field

from core.domain.errors import ProviderDoesNotSupportModelError
from core.domain.models import Model, Provider
from core.domain.task_typology import TaskTypology

from ._sourced_base_model import SourcedBaseModel
from .model_data_supports import ModelDataSupports
from .model_provider_data import ModelProviderData

# --- Max tokens data models --- #


class MaxTokensData(SourcedBaseModel):
    max_tokens: int = Field(
        description="The maximum number of tokens (input + output) that can be handled by the model.",
        gt=0,
    )
    max_output_tokens: int | None = Field(
        default=None,
        description="The maximum number of tokens that can be generated by the model.",
        gt=0,
    )


class ModelData(ModelDataSupports):
    display_name: str = Field(description="The display name of the model, that will be used in the UIs, etc.")
    icon_url: str = Field(description="The icon url of the model")

    max_tokens_data: MaxTokensData

    provider_for_pricing: Provider

    latest_model: Model | None = Field(
        default=None,
        description="The latest model for the family",
    )

    is_default: bool = Field(
        default=False,
        description="If true, the model will be used as default model.",
    )

    release_date: date = Field(description="The date the model was released")

    quality_index: int = Field(
        description="The quality index of the model. None if not available",
    )

    provider_name: str = Field(
        description="The name of the provider for the model",
    )

    supports_tool_calling: bool = Field(
        description="Whether the model supports tool calling",
    )

    @property
    def modes(self) -> list[str]:
        out: list[str] = []
        if self.supports_json_mode:
            out.append("text")

        if self.supports_input_image:
            out.append("images")

        if self.supports_input_audio:
            out.append("audio")
        return out


class FinalModelData(ModelData):
    model: Model

    # TODO: this should be a dict since it's ordered
    providers: list[tuple[Provider, ModelProviderData]] = Field(
        description="The provider data for the model. Extracted from the model provider data list",
    )

    def provider_data(self, provider: Provider) -> ModelProviderData:
        for p, provider_data in self.providers:
            if p == provider:
                return provider_data
        raise ProviderDoesNotSupportModelError(self.model, provider)

    def provider_data_for_pricing(self) -> ModelProviderData:
        """Returns the provider data for the model for pricing purposes"""
        # The for loop is not the best solution, but we will at most have 2 providers
        # and usually the provider that is used is the first one in the array since they are
        # ordered by priority
        for provider, provider_data in self.providers:
            if provider == self.provider_for_pricing:
                return provider_data
        # This should never happen, we have tests for that
        raise ValueError(f"Provider {self.provider_for_pricing} not found for model {self.display_name}")

    def is_not_supported_reason(
        self,
        task_typology: TaskTypology,
    ) -> str | None:
        """Returns the reason why the model is not supported for the given task typology or
        None if the task typology is supported"""

        # Fireworks supports document inlining which makes models without vision "support" vision
        # TODO[models]: Having this explicit exception is not great. Instead we should
        # make the model data represent what WorkflowAI support instead of the model card
        supports_inlining = any(provider == Provider.FIREWORKS for provider, _ in self.providers)

        if self.supports_audio_only and not task_typology.has_audio_in_input:
            return f"{self.display_name} does not support non-audio inputs"
        if task_typology.has_image_in_input and not self.supports_input_image:
            if supports_inlining:
                return None
            return f"{self.display_name} does not support input images"
        if task_typology.has_multiple_images_in_input and not self.supports_multiple_images_in_input:
            if supports_inlining:
                return None
            return f"{self.display_name} does not support multiple images in input"
        if task_typology.has_audio_in_input and not self.supports_input_audio:
            return f"{self.display_name} does not support input audio"
        if task_typology.has_pdf_in_input and (not self.supports_input_pdf and not self.supports_input_image):
            if supports_inlining:
                return None
            return f"{self.display_name} does not support input pdf"
        return None


class LatestModel(BaseModel):
    # Used to map a latest model to a specific model
    model: Model
    display_name: str
    # By default all latest models can be used as default model
    is_default: bool = True
    icon_url: str = ""  # Fixed at build time


class DeprecatedModel(BaseModel):
    replacement_model: Model
