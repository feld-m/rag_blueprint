from abc import ABC, abstractmethod
from typing import Generic, List

from extraction.datasources.core.base.document import DocType


class BaseSplitter(ABC, Generic[DocType]):
    """Abstract base class for document splitters.

    This class defines the interface for splitting documents into smaller chunks.
    All splitter implementations should inherit from this class.
    """

    @abstractmethod
    def split(self, document: DocType) -> List[DocType]:
        """Split a document into multiple smaller documents.

        Args:
            document: The document to be split.

        Returns:
            A list of document chunks.
        """
        pass


class BasicMarkdownSplitter(BaseSplitter, Generic[DocType]):
    """A simple splitter implementation that returns the document as-is.

    This splitter does not perform any actual splitting and is primarily
    used as a pass-through when splitting is not required.
    """

    def split(self, document: DocType) -> List[DocType]:
        """Return the document as a single-item list without splitting.

        Args:
            document: The document to be processed.

        Returns:
            A list containing the original document as the only element.
        """
        return [document]
