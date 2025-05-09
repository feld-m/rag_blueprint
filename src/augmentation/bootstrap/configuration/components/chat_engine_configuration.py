from enum import Enum
from typing import Any, List, Type

from pydantic import Field, ValidationInfo, field_validator

from augmentation.bootstrap.configuration.components.llm_configuration import (
    LLMConfigurationRegistry,
)
from augmentation.bootstrap.configuration.components.postprocessors_configuration import (
    PostProcessorConfigurationRegistry,
)
from augmentation.bootstrap.configuration.components.retriever_configuration import (
    RetrieverConfigurationRegistry,
)
from core.base_configuration import BaseConfiguration
from core.base_factory import ConfigurationRegistry


class ChatEngineName(str, Enum):
    """Enum defining available chat engine types."""

    LANGFUSE = "langfuse"


class ChatEnginePromptTemplates(BaseConfiguration):
    condense_prompt_name: str = Field(
        "default_condense_prompt",
        description="The name of the condense prompt to use available in Langfuse prompts. "
        "The prompt is used to reformulate the user query based on chat history and query.",
    )
    context_prompt_name: str = Field(
        "default_context_prompt",
        description=(
            "The name of the context prompt to use available in Langfuse prompts.",
            "The prompt is used together with retrieved context.",
        ),
    )
    context_refine_prompt_name: str = Field(
        "default_context_refine_prompt",
        description=(
            "The name of the context refine prompt to use available in Langfuse prompts.",
            "The prompt is used to refine the answer based on retrieved context.",
        ),
    )
    system_prompt_name: str = Field(
        "default_system_prompt",
        description=(
            "The name of the system prompt to use available in Langfuse prompts.",
            "The prompt is used to set the system context for the chat engine.",
        ),
    )
    input_guardrail_prompt_name: str = Field(
        "default_input_guardrail_prompt",
        description=(
            "The name of the input guardrail prompt to use available in Langfuse prompts.",
            "The prompt is used to determine if the input is valid to be passed to the chat engine.",
            "The LLM should respond with 'yes' or 'true' if the input should be blocked.",
        ),
    )
    output_guardrail_prompt_name: str = Field(
        "default_output_guardrail_prompt",
        description=(
            "The name of the output guardrail prompt to use available in Langfuse prompts.",
            "The prompt is used to determine if the output of the chat engine is valid to be returned to the user.",
            "The LLM should respond with 'yes' or 'true' if the output should be blocked.",
        ),
    )


class BaseChatEngineConfiguration(BaseConfiguration):
    """Base configuration class for chat engines.

    This class defines the standard configuration structure for all chat engines,
    including retriever, llm, and postprocessor components.
    """

    retriever: Any = Field(
        ...,
        description="The retriever configuration for the augmentation pipeline.",
    )
    llm: Any = Field(
        ..., description="The llm configuration for the chat engine."
    )
    postprocessors: List[Any] = Field(
        ..., description="The list of postprocessors for the chat engine."
    )
    prompt_templates: ChatEnginePromptTemplates = Field(
        ...,
        description="The prompt templates configuration for the chat engine.",
        default_factory=ChatEnginePromptTemplates,
    )

    @field_validator("retriever")
    @classmethod
    def _validate_retriever(cls, value: Any, info: ValidationInfo) -> Any:
        """Validate retriever configuration against registered retriever types.

        Args:
            value: The retriever configuration to validate
            info: Validation context information

        Returns:
            Validated retriever configuration
        """
        return super()._validate(
            value,
            info=info,
            registry=RetrieverConfigurationRegistry,
        )

    @field_validator("llm")
    @classmethod
    def _validate_llm(cls, value: Any, info: ValidationInfo) -> Any:
        """Validate llm configuration against registered llm types.

        Args:
            value: The llm configuration to validate
            info: Validation context information

        Returns:
            Validated llm configuration
        """
        return super()._validate(
            value,
            info=info,
            registry=LLMConfigurationRegistry,
        )

    @field_validator("postprocessors")
    @classmethod
    def _validate_postprocessors(
        cls, value: Any, info: ValidationInfo
    ) -> List[Any]:
        """Validate postprocessors configuration against registered postprocessor types.

        Args:
            value: The postprocessor configurations to validate
            info: Validation context information

        Returns:
            List of validated postprocessor configurations
        """
        return super()._validate(
            value,
            info=info,
            registry=PostProcessorConfigurationRegistry,
        )


class ChatEngineConfigurationRegistry(ConfigurationRegistry):
    """Registry for chat engine configurations.

    Maps chat engine names to their corresponding configuration classes
    to facilitate configuration validation and factory creation.

    Attributes:
        _key_class: The enumeration class for chat engine names.
    """

    _key_class: Type = ChatEngineName
