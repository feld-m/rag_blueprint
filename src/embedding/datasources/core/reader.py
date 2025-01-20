from abc import ABC, abstractmethod
from typing import Generic, List

from embedding.datasources.core.document import DocType


class BaseReader(ABC, Generic[DocType]):
    """Abstract base class for document source readers.

    Defines interface for document extraction from various sources.
    Supports both synchronous and asynchronous implementations through
    generic typing for document types.

    Attributes:
        None
    """

    @abstractmethod
    def get_all_documents(self) -> List[DocType]:
        """Synchronously retrieve all documents from source.

        Returns:
            List[DocType]: Collection of extracted documents

        Raises:
            NotImplementedError: Must be implemented by concrete classes
        """
        pass

    @abstractmethod
    async def get_all_documents_async(self) -> List[DocType]:
        """Asynchronously retrieve all documents from source.

        Returns:
            List[DocType]: Collection of extracted documents

        Raises:
            NotImplementedError: Must be implemented by concrete classes
        """
        pass
