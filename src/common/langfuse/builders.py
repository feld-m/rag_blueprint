from injector import inject
from langfuse import Langfuse
from langfuse.llama_index import LlamaIndexCallbackHandler

from common.bootstrap.configuration.pipeline.augmentation.langfuse.langfuse_configuration import (
    LangfuseConfiguration,
)
from common.langfuse.dataset import LangfuseDatasetService


class LangfuseDatasetServiceBuilder:
    """Builder for creating Langfuse dataset service instances.

    Provides factory method to create configured LangfuseDatasetService objects.
    """

    @staticmethod
    @inject
    def build(langfuse_client: Langfuse) -> LangfuseDatasetService:
        """Creates a configured Langfuse dataset service.

        Args:
            langfuse_client: Client for Langfuse API interaction.

        Returns:
            LangfuseDatasetService: Configured dataset service instance.
        """
        return LangfuseDatasetService(langfuse_client=langfuse_client)


class LangfuseClientBuilder:
    """Builder for creating Langfuse client instances.

    Provides factory method to create configured Langfuse API clients.
    """

    @staticmethod
    @inject
    def build(configuration: LangfuseConfiguration) -> Langfuse:
        """Creates a configured Langfuse client.

        Args:
            configuration: Langfuse connection and authentication settings.

        Returns:
            Langfuse: Configured client instance.
        """
        return Langfuse(
            secret_key=configuration.secrets.secret_key.get_secret_value(),
            public_key=configuration.secrets.public_key.get_secret_value(),
            host=configuration.url,
        )


class LangfuseCallbackHandlerBuilder:
    """Builder for creating Langfuse callback handler instances.

    Provides factory method to create LlamaIndex callback handlers for Langfuse
    integration, enabling tracing and monitoring of LLM interactions.
    """

    @staticmethod
    @inject
    def build(
        configuration: LangfuseConfiguration, session_id: str = ""
    ) -> LlamaIndexCallbackHandler:
        """Creates a configured Langfuse callback handler.

        Args:
            configuration: Langfuse connection and authentication settings.
            session_id: Optional user session identifier for tracking.

        Returns:
            LlamaIndexCallbackHandler: Configured callback handler instance.
        """
        return LlamaIndexCallbackHandler(
            secret_key=configuration.secrets.secret_key.get_secret_value(),
            public_key=configuration.secrets.public_key.get_secret_value(),
            host=configuration.url,
            session_id=session_id,
        )
