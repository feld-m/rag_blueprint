from typing import Type

from llama_index.core.base.llms.types import LLMMetadata
from llama_index.llms.litellm import LiteLLM

from augmentation.components.llms.lite_llm.configuration import (
    LiteLLMConfiguration,
)
from core import SingletonFactory


class ConfigurableLiteLLM(LiteLLM):
    """
    Extended LiteLLM that allows context_window and num_output override.

    This subclass overrides the metadata property to allow configuration-based
    context_window and num_output values, rather than relying solely on LiteLLM's
    model registry defaults.
    """

    def __init__(
        self,
        *args,
        context_window: int | None = None,
        num_output: int | None = None,
        **kwargs,
    ):
        """Initialize with optional context_window and num_output overrides."""
        super().__init__(*args, **kwargs)
        self._context_window_override = context_window
        self._num_output_override = num_output

    @property
    def metadata(self) -> LLMMetadata:
        """
        Get LLM metadata with configuration overrides applied.

        Returns:
            LLMMetadata with context_window and num_output from configuration
            if specified, otherwise uses parent class defaults.
        """
        # Get default metadata from parent
        default_metadata = super().metadata

        # Apply overrides if configured
        context_window = (
            self._context_window_override
            if self._context_window_override is not None
            else default_metadata.context_window
        )

        num_output = (
            self._num_output_override
            if self._num_output_override is not None
            else default_metadata.num_output
        )

        return LLMMetadata(
            context_window=context_window,
            num_output=num_output,
            is_chat_model=default_metadata.is_chat_model,
            is_function_calling_model=default_metadata.is_function_calling_model,
            model_name=default_metadata.model_name,
            system_role=default_metadata.system_role,
        )


class LiteLLMFactory(SingletonFactory):
    """
    Factory class for creating LiteLLM language model instances.

    This class implements the Singleton pattern to ensure only one instance
    of an LiteLLM model with a specific configuration exists in the application.
    It uses LiteLLMConfiguration to configure the model parameters.

    Attributes:
        _configuration_class: Type of the configuration class used for
            creating LiteLLM model instances.
    """

    _configuration_class: Type = LiteLLMConfiguration

    @classmethod
    def _create_instance(cls, configuration: LiteLLMConfiguration) -> LiteLLM:
        """
        Creates a new instance of the LiteLLM language model.

        Args:
            configuration (LiteLLMConfiguration): Configuration object containing
                settings for the LiteLLM model, including API key, model name,
                maximum tokens, retry settings, context_window, and num output.

        Returns:
            ConfigurableLiteLLM: An instance of the LiteLLM language model configured
                with the provided settings, including optional context_window and
                num_output overrides.
        """
        return ConfigurableLiteLLM(
            api_key=configuration.secrets.api_key.get_secret_value(),
            api_base=configuration.api_base,
            model=configuration.name,
            max_tokens=configuration.max_tokens,
            max_retries=configuration.max_retries,
            context_window=configuration.context_window,
            num_output=configuration.num_output,
        )
