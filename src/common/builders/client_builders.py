from injector import inject
from qdrant_client import QdrantClient

from common.bootstrap.configuration.pipeline.embedding.vector_store.vector_store_configuration import (
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
