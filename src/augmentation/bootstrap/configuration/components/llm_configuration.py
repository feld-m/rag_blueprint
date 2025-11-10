from enum import Enum
from typing import Optional, Type

from pydantic import Field

from core.base_configuration import BaseConfigurationWithSecrets
from core.base_factory import ConfigurationRegistry


class LLMProviderName(str, Enum):
    """
    Enumeration of supported language model providers.
    """

    LITE_LLM = "lite_llm"


class LLMConfiguration(BaseConfigurationWithSecrets):
    """
    Configuration settings for language models.

    This class defines the necessary parameters for configuring
    and interacting with language models (LLMs) used in the system.
    """

    name: str = Field(..., description="The name of the language model.")
    max_tokens: int = Field(
        ..., description="The maximum number of tokens for the language model."
    )
    max_retries: int = Field(
        ..., description="The maximum number of retries for the language model."
    )
    context_window: Optional[int] = Field(
        None,
        description="The maximum context window size for the language model. "
        "If not specified, uses the model's default from LiteLLM metadata.",
    )
    num_output: Optional[int] = Field(
        None,
        description="The maximum number of output tokens for the language model. "
        "If not specified, uses the model's default from LiteLLM metadata.",
    )


class LLMConfigurationRegistry(ConfigurationRegistry):
    """
    Registry for language model configurations.

    This registry maintains a mapping between LLM provider names and
    their corresponding configuration classes, allowing the system to
    dynamically select and instantiate the appropriate configuration
    based on the provider name.

    Attributes:
        _key_class: The enumeration class for LLM provider names.
    """

    _key_class: Type = LLMProviderName
