from abc import ABC, abstractmethod

from chromadb.api import ClientAPI as ChromaClient
from qdrant_client import QdrantClient

from common.bootstrap.configuration.pipeline.embedding.vector_store.vector_store_configuration import (
    ChromaConfiguration,
    QDrantConfiguration,
)
from common.exceptions import CollectionExistsException


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
        self.validate_collection()

    def validate_collection(self) -> None:
        """Validate Qdrant collection existence.

        Raises:
            CollectionExistsException: If collection already exists
        """
        collection_name = self.configuration.collection_name
        if self.qdrant_client.collection_exists(collection_name):
            raise CollectionExistsException(collection_name)


class ChromaVectorStoreValidator(VectorStoreValidator):
    """Validator for Chroma vector store configuration.

    Validates collection settings and existence for Chroma
    vector store backend.

    Attributes:
        configuration: Settings for vector store
        chroma_client: Client for Chroma interactions
    """

    def __init__(
        self,
        configuration: ChromaConfiguration,
        chroma_client: ChromaClient,
    ):
        """Initialize validator with configuration and client.

        Args:
            configuration: Chroma vector store settings
            chroma_client: Client for Chroma operations
        """
        self.configuration = configuration
        self.chroma_client = chroma_client

    def validate(self) -> None:
        """
        Valiuate the Chroma vector store settings.
        """
        self.validate_collection()

    def validate_collection(self) -> None:
        """Validate Chroma collection existence.

        Raises:
            CollectionExistsException: If collection already exists
        """
        collection_name = self.configuration.collection_name
        if collection_name in self.chroma_client.list_collections():
            raise CollectionExistsException(collection_name)
