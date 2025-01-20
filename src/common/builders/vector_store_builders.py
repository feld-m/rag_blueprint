from injector import inject
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from common.bootstrap.configuration.pipeline.embedding.vector_store.vector_store_configuration import (
    QDrantConfiguration,
)


class QdrantStoreBuilder:
    """Builder for creating configured Qdrant vector store instances.

    Provides factory method to create QdrantVectorStore with client and collection settings.
    """

    @staticmethod
    @inject
    def build(
        qdrant_client: QdrantClient,
        configuration: QDrantConfiguration,
    ) -> QdrantVectorStore:
        """Creates a configured Qdrant vector store instance.

        Args:
            qdrant_client: Client for Qdrant vector database interaction.
            configuration: Qdrant settings including collection name.

        Returns:
            QdrantVectorStore: Configured Qdrant instance.
        """
        return QdrantVectorStore(
            client=qdrant_client,
            collection_name=configuration.collection_name,
        )
