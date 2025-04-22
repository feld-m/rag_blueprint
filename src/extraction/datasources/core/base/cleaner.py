from abc import ABC, abstractmethod
from typing import Generic

from extraction.datasources.core.document import DocType


class BaseCleaner(ABC, Generic[DocType]):
    """Abstract base class for document cleaning operations.

    Defines the interface for document cleaners with generic type support
    to ensure type safety across different document implementations.
    """

    @abstractmethod
    def clean(self, document: DocType) -> DocType:
        """Clean a single document.

        Args:
            document: The document to be cleaned

        Returns:
            The cleaned document or None if document should be filtered out
        """
        pass


class BasicMarkdownCleaner(BaseCleaner, Generic[DocType]):
    """Document cleaner for basic content validation.

    Checks for empty content in documents and filters them out.
    Works with any document type that has a text attribute.
    """

    def clean(self, document: DocType) -> DocType:
        """Remove document if it contains empty content.

        Args:
            document: The document to validate

        Returns:
            The original document if content is not empty, None otherwise
        """
        if not self._has_empty_content(document):
            return document

        return None

    @staticmethod
    def _has_empty_content(document: DocType) -> bool:
        """Check if document content is empty.

        Args:
            document: Document to check (must have a text attribute)

        Returns:
            True if document's text is empty or contains only whitespace
        """
        return not document.text.strip()
