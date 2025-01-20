from injector import inject
from llama_index.core.vector_stores.types import VectorStore

from common.bootstrap.configuration.pipeline.embedding.embedding_model.embedding_model_binding_keys import (
    BoundEmbeddingModel,
)
from embedding.embedders.default_embedder import Embedder


class EmbedderBuilder:
    """Builder for creating Embedder instances.

    Provides factory method to create configured Embedder objects
    with injection of required components.
    """

    @staticmethod
    @inject
    def build(
        embedding_model: BoundEmbeddingModel, vector_store: VectorStore
    ) -> Embedder:
        """Create configured Embedder instance.

        Args:
            embedding_model: Model for generating embeddings
            vector_store: Storage for embedding vectors

        Returns:
            Embedder: Configured embedder instance
        """
        return Embedder(
            embedding_model=embedding_model, vector_store=vector_store
        )
