from typing import TYPE_CHECKING

from injector import inject
from llama_index.llms.openai import OpenAI
from llama_index.llms.openai_like import OpenAILike

if TYPE_CHECKING:
    from common.bootstrap.configuration.pipeline.augmentation.query_engine.llm_configuration import (
        OpenAILikeLLMConfiguration,
        OpenAILLMConfiguration,
    )


class OpenAIBuilder:
    """Builder for creating OpenAI language model instances.

    Provides factory method to create configured OpenAI objects.
    """

    @staticmethod
    @inject
    def build(configuration: "OpenAILLMConfiguration") -> OpenAI:
        """Creates a configured OpenAI language model.

        Args:
            configuration: Model settings including API key and parameters.

        Returns:
            OpenAI: Configured language model instance.
        """
        return OpenAI(
            api_key=configuration.secrets.api_key.get_secret_value(),
            model=configuration.name,
            max_tokens=configuration.max_tokens,
            max_retries=configuration.max_retries,
        )


class OpenAILikeBuilder:
    """Builder for creating OpenAI-compatible language model instances.

    Provides factory method to create configured OpenAILike objects.
    """

    @staticmethod
    @inject
    def build(configuration: "OpenAILikeLLMConfiguration") -> OpenAILike:
        """Creates a configured OpenAI-compatible language model.

        Args:
            configuration: Model settings including API endpoints and parameters.

        Returns:
            OpenAILike: Configured language model instance.
        """
        return OpenAILike(
            api_base=configuration.secrets.api_base.get_secret_value(),
            api_key=configuration.secrets.api_key.get_secret_value(),
            model=configuration.name.value,
            max_tokens=configuration.max_tokens,
            max_retries=configuration.max_retries,
            context_window=configuration.context_window,
            logprobs=None,
            api_version="",
        )
