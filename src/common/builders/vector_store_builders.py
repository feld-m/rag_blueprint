from injector import inject
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from common.bootstrap.configuration.pipeline.embedding.vector_store.vector_store_configuration import (
    ChromaConfiguration,
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


class ChromaStoreBuilder:
    """Builder for creating configured Chroma vector store instances.

    Provides factory method to create ChromaVectorStore with client and collection settings.
    """

    @staticmethod
    @inject
    def build(
        configuration: ChromaConfiguration,
    ) -> ChromaVectorStore:
        """Creates a configured Chroma vector store instance.

        Args:
            chroma_client: Client for Chroma vector database interaction.
            configuration: Chroma settings including collection name.

        Returns:
            ChromaVectorStore: Configured Chroma instance.
        """
        return ChromaVectorStore(
            host=configuration.host,
            port=str(configuration.ports.rest),
            collection_name=configuration.collection_name,
        )
