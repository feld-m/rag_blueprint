from abc import ABC, abstractmethod
from typing import Any, AsyncIterator


class BaseReader(ABC):
    """Abstract base class for document source readers.

    This class defines a standard interface for extracting documents from various
    data sources. Concrete implementations should inherit from this class and
    implement the required methods to handle specific data source types.

    The generic typing allows for flexibility in the document types returned
    by different implementations.
    """

    @abstractmethod
    async def read_all_async(self) -> AsyncIterator[Any]:
        """Asynchronously retrieve documents from the source.

        Implementations should use async iteration to efficiently stream documents
        from the source without loading all content into memory at once.

        Returns:
            AsyncIterator[Any]: An async iterator that yields documents as they're
                               extracted from the source.

        Raises:
            NotImplementedError: This abstract method must be implemented by subclasses.
        """
        pass
