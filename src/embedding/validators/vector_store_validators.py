from abc import ABC, abstractmethod

from qdrant_client import QdrantClient

from common.bootstrap.configuration.pipeline.embedding.vector_store.vector_store_configuration import (
    QDrantConfiguration,
)
from common.exceptions import QdrantCollectionExistsException


class VectorStoreValidator(ABC):

    @abstractmethod
    def validate(self) -> None:
        """
        Validate the vector store settings.
        """
        pass


class QdrantVectorStoreValidator(VectorStoreValidator):
    """Validator for Qdrant vector store configuration.

    Validates collection settings and existence for Qdrant
    vector store backend.

    Attributes:
        configuration: Settings for vector store
        qdrant_client: Client for Qdrant interactions
    """

    def __init__(
        self,
        configuration: QDrantConfiguration,
        qdrant_client: QdrantClient,
    ):
        """Initialize validator with configuration and client.

        Args:
            configuration: Qdrant vector store settings
            qdrant_client: Client for Qdrant operations
        """
        self.configuration = configuration
        self.qdrant_client = qdrant_client

    def validate(self) -> None:
        """
        Valiuate the Qdrant vector store settings.
        """
        self.validate_qdrant_collection()

    def validate_qdrant_collection(self) -> None:
        """Validate Qdrant collection existence.

        Raises:
            QdrantCollectionExistsException: If collection already exists
        """
        collection_name = self.configuration.collection_name
        if self.qdrant_client.collection_exists(collection_name):
            raise QdrantCollectionExistsException(collection_name)
