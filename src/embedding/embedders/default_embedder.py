import logging
from typing import List

from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.schema import MetadataMode, TextNode

from embedding.embedders.base import BaseEmbedder


class Embedder(BaseEmbedder):
    """Implementation of text node embedding operations.

    Handles batch embedding generation and vector store persistence
    for text nodes.
    """

    def save(self, nodes: List[TextNode]) -> None:
        """Save embedded nodes to vector store.

        Args:
            nodes: Collection of text nodes with embeddings

        Note:
            Creates new storage context and vector store index
        """
        logging.info("Saving nodes...")
        storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )
        VectorStoreIndex(
            nodes,
            storage_context=storage_context,
            embed_model=self.embedding_model,
        )

    def embed(self, nodes: List[TextNode]) -> None:
        """Generate embeddings for text nodes in batch.

        Args:
            nodes: Collection of text nodes to embed

        Note:
            Modifies nodes in-place by setting embedding attribute
        """
        logging.info(f"Embedding {len(nodes)} nodes...")
        nodes_contents = [
            node.get_content(metadata_mode=MetadataMode.EMBED) for node in nodes
        ]
        nodes_embeddings = self.embedding_model.get_text_embedding_batch(
            nodes_contents,
            show_progress=True,
        )
        for node, node_embedding in zip(nodes, nodes_embeddings):
            node.embedding = node_embedding
