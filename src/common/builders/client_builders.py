from chromadb import HttpClient as ChromaHttpClient
from chromadb.api import ClientAPI as ChromaClient
from injector import inject
from qdrant_client import QdrantClient

from common.bootstrap.configuration.pipeline.embedding.vector_store.vector_store_configuration import (
    ChromaConfiguration,
    QDrantConfiguration,
)


class QdrantClientBuilder:
    """Builder for creating configured Qdrant client instances.

    Provides factory method to create QdrantClient with vector store settings.
    """

    @staticmethod
    @inject
    def build(configuration: QDrantConfiguration) -> QdrantClient:
        """Creates a configured Qdrant client instance.

        Args:
            configuration: Qdrant connection settings.

        Returns:
            QdrantClient: Configured client instance for qdrant.
        """
        return QdrantClient(
            url=configuration.url,
        )


class ChromaClientBuilder:
    """Builder for creating configured Chroma client instances.

    Provides factory method to create ChromaClient with vector store settings.
    """

    @staticmethod
    @inject
    def build(configuration: ChromaConfiguration) -> ChromaClient:
        """Creates a configured Chroma client instance.

        Args:
            configuration: Chroma connection settings.

        Returns:
            HttpClient: Configured http client instance for Chroma.
        """
        return ChromaHttpClient(
            host=configuration.host,
            port=configuration.ports.rest,
        )
