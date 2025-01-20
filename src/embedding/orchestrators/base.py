from abc import ABC, abstractmethod


class BaseDatasourceOrchestrator(ABC):
    """Abstract base class for datasource orchestration.

    Defines interface for managing content extraction, embedding generation,
    and vector storage operations across datasources.

    Note:
        All implementing classes must provide concrete implementations
        of extract, embed, save and update methods.
    """

    @abstractmethod
    async def extract(self) -> None:
        """Extract content from configured datasources.

        Performs asynchronous content extraction from all configured
        datasource implementations.
        """
        pass

    @abstractmethod
    def embed(self) -> None:
        """Generate embeddings for extracted content.

        Processes extracted content through embedding model to
        generate vector representations.
        """
        pass

    @abstractmethod
    def save_to_vector_storage(self) -> None:
        """Persist embedded content to vector store.

        Saves generated embeddings and associated content to
        configured vector storage backend.
        """
        pass

    @abstractmethod
    def update_vector_storage(self) -> None:
        """Update existing vector store content.

        Updates or replaces existing embeddings in vector storage
        with newly generated ones.
        """
        pass
