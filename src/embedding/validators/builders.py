from chromadb.api import ClientAPI as ChromaClient
from injector import inject
from qdrant_client import QdrantClient

from common.bootstrap.configuration.pipeline.embedding.vector_store.vector_store_configuration import (
    ChromaConfiguration,
    QDrantConfiguration,
)
from embedding.validators.vector_store_validators import (
    ChromaVectorStoreValidator,
    QdrantVectorStoreValidator,
)


class QdrantVectorStoreValidatorBuilder:
    """Builder for creating Qdrant vector store validator instances.

    Provides factory method to create configured QdrantVectorStoreValidator
    objects with required components.
    """

    @staticmethod
    @inject
    def build(
        configuration: QDrantConfiguration, qdrant_client: QdrantClient
    ) -> QdrantVectorStoreValidator:
        """Create configured Qdrant validator instance.

        Args:
            configuration: Settings for vector store
            qdrant_client: Client for Qdrant interactions

        Returns:
            QdrantVectorStoreValidator: Configured validator instance
        """
        return QdrantVectorStoreValidator(
            configuration=configuration, qdrant_client=qdrant_client
        )


class ChromaVectorStoreValidatorBuilder:
    """Builder for creating Chroma vector store validator instances.

    Provides factory method to create configured ChromaVectorStoreValidator
    objects with required components.
    """

    @staticmethod
    @inject
    def build(
        configuration: ChromaConfiguration, chroma_client: ChromaClient
    ) -> ChromaVectorStoreValidator:
        """Create configured Chroma validator instance.

        Args:
            configuration: Settings for vector store
            chroma_client: Client for Chroma interactions

        Returns:
            ChromaVectorStoreValidator: Configured validator instance
        """
        return ChromaVectorStoreValidator(
            configuration=configuration, chroma_client=chroma_client
        )
