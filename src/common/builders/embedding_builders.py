from typing import TYPE_CHECKING

from injector import inject
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.embeddings.voyageai import VoyageEmbedding

if TYPE_CHECKING:
    from common.bootstrap.configuration.pipeline.embedding.embedding_model.embedding_model_configuration import (
        BGEConfiguration,
        OpenAIEmbeddingModelConfiguration,
        VoyageConfiguration,
    )


class HuggingFaceEmbeddingModelBuilder:
    """Builder for creating HuggingFace embedding model instances.

    Provides factory method to create configured HuggingFaceEmbedding objects.
    """

    @staticmethod
    @inject
    def build(
        configuration: "BGEConfiguration",
    ) -> HuggingFaceEmbedding:
        """Creates a configured HuggingFace embedding model.

        Args:
            configuration: Model settings including name and batch size.

        Returns:
            HuggingFaceEmbedding: Configured embedding model instance.
        """
        return HuggingFaceEmbedding(
            model_name=configuration.name.value,
            embed_batch_size=configuration.batch_size,
        )


class VoyageEmbeddingModelBuilder:
    """Builder for creating Voyage AI embedding model instances.

    Provides factory method to create configured VoyageEmbedding objects.
    """

    @staticmethod
    @inject
    def build(
        configuration: "VoyageConfiguration",
    ) -> VoyageEmbedding:
        """Creates a configured Voyage AI embedding model.

        Args:
            configuration: Model settings including API key, name and batch size.

        Returns:
            VoyageEmbedding: Configured embedding model instance.
        """
        return VoyageEmbedding(
            voyage_api_key=configuration.secrets.api_key.get_secret_value(),
            model_name=configuration.name,
            embed_batch_size=configuration.batch_size,
        )


class OpenAIEmbeddingModelBuilder:
    """Builder for creating OpenAI embedding model instances.

    Provides factory method to create configured OpenAIEmbedding objects.
    """

    @staticmethod
    @inject
    def build(
        configuration: "OpenAIEmbeddingModelConfiguration",
    ) -> OpenAIEmbedding:
        """Creates a configured OpenAI embedding model.

        Args:
            configuration: Model settings including API key, name and batch size.

        Returns:
            OpenAIEmbedding: Configured embedding model instance.
        """
        return OpenAIEmbedding(
            api_key=configuration.secrets.api_key.get_secret_value(),
            model_name=configuration.name,
            embed_batch_size=configuration.batch_size,
        )
