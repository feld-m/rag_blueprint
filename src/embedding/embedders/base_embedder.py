from abc import ABC, abstractmethod
from typing import List

from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.schema import TextNode
from llama_index.core.vector_stores.types import VectorStore

from embedding.bootstrap.configuration.configuration import (
    EmbeddingConfiguration,
)


class BaseEmbedder(ABC):
    """Abstract base class for text node embedding operations.

    Defines interface for embedding generation and storage operations
    on text nodes.

    Attributes:
        embedding_model: Model for generating embeddings
        vector_store: Storage for embedding vectors
    """

    def __init__(
        self,
        configuration: EmbeddingConfiguration,
        embedding_model: BaseEmbedding,
        vector_store: VectorStore,
    ):
        """Initialize embedder with model and storage.

        Args:
            embedding_model: Model to generate embeddings
            vector_store: Storage for embedding vectors
        """
        super().__init__()
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.batch_size = configuration.embedding.embedding_model.batch_size
        self.current_nodes_batch = []

    @abstractmethod
    def embed(self, nodes: List[TextNode]) -> None:
        """Generate embeddings for text nodes in batches.

        Args:
            nodes: Collection of text nodes to embed

        Note:
            Modifies nodes in-place by adding embeddings
        """
        pass

    @abstractmethod
    def embed_flush(self) -> None:
        """Generate embeddings for remaining nodes.

        Args:
            nodes: Collection of text nodes to embed

        Note:
            Modifies nodes in-place by adding embeddings
        """
        pass
