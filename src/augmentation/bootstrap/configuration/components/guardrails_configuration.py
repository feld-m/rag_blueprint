from enum import Enum
from typing import Any, Type

from pydantic import Field, ValidationInfo, field_validator

from augmentation.bootstrap.configuration.components.llm_configuration import (
    LLMConfigurationRegistry,
)
from core.base_configuration import BaseConfiguration
from core.base_factory import ConfigurationRegistry


class GuardrailsName(str, Enum):
    """
    Enumeration of supported guardrails.
    """

    BASIC = "basic"


class GuardrailsConfiguration(BaseConfiguration):
    """
    Configuration settings for guardrails.

    This class defines the necessary parameters for configuring
    and interacting with guardrails used in the system.
    """

    llm: Any = Field(
        ..., description="The llm configuration for the guardrails."
    )
    input_prompt_name: str = Field(
        "default_input_guardrail_prompt",
        description=(
            "The name of the input guardrail prompt to use available in Langfuse prompts.",
            "The prompt is used to determine if the input is valid to be passed to the chat engine.",
            "The LLM should respond with 'yes' or 'true' if the input should be blocked.",
        ),
    )
    output_prompt_name: str = Field(
        "default_output_guardrail_prompt",
        description=(
            "The name of the output guardrail prompt to use available in Langfuse prompts.",
            "The prompt is used to determine if the output of the chat engine is valid to be returned to the user.",
            "The LLM should respond with 'yes' or 'true' if the output should be blocked.",
        ),
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


class GurdrailsConfigurationRegistry(ConfigurationRegistry):
    """
    Registry for guardrails configurations.

    This registry maintains a mapping between guardrails names and
    their corresponding configuration classes, allowing the system to
    dynamically select and instantiate the appropriate configuration
    based on the provider name.

    Attributes:
        _key_class: The enumeration class for guardrails names.
    """

    _key_class: Type = GuardrailsName
