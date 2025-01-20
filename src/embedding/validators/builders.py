from injector import inject
from qdrant_client import QdrantClient

from common.bootstrap.configuration.pipeline.embedding.vector_store.vector_store_configuration import (
    QDrantConfiguration,
)
from embedding.validators.vector_store_validators import (
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
