from abc import ABC, abstractmethod
from typing import Any, Generic, List

from llama_index.core.schema import TextNode
from tqdm import tqdm

from embedding.datasources.core.document import DocType


class BaseCleaner(ABC, Generic[DocType]):
    """Abstract base class defining document cleaning interface.

    Provides interface for cleaning document collections with type safety
    through generic typing.

    Attributes:
        None
    """

    @abstractmethod
    def clean(self, documents: List[DocType]) -> List[DocType]:
        """Clean a list of documents.

        Args:
            documents: List of documents to clean

        Returns:
            List[DocType]: List of cleaned documents
        """
        pass

    @staticmethod
    def _has_empty_content(document: TextNode) -> bool:
        """Check if document content is empty.

        Args:
            document: Document to check for content

        Returns:
            bool: True if document text is empty after stripping whitespace
        """
        return not document.text.strip()


class Cleaner(BaseCleaner):
    """Generic document cleaner implementation.

    Removes empty documents from collections while tracking progress.
    Supports any document type with a text attribute.
    """

    def clean(self, documents: List[Any]) -> List[Any]:
        """Remove empty documents from collection.

        Args:
            documents: List of documents to clean

        Returns:
            List[Any]: Filtered list containing only non-empty documents

        Note:
            Document type is inferred from first document in collection.
        """
        if not documents:
            return []

        # Infer document type from the first document
        document_type_name = type(documents[0]).__name__

        cleaned_documents = []
        for document in self._get_documents_with_tqdm(
            documents, document_type_name
        ):
            if not self._has_empty_content(document):
                cleaned_documents.append(document)

        return cleaned_documents

    def _get_documents_with_tqdm(
        self, documents: List[Any], document_type_name: str
    ):
        """Wrap document iteration with optional progress bar.

        Args:
            documents: List of documents to process
            document_type_name: Name of document type for progress display

        Returns:
            Iterator over documents, optionally wrapped with progress bar
        """
        return tqdm(
            documents, desc=f"[{document_type_name}] Cleaning documents"
        )

    @staticmethod
    def _has_empty_content(document: Any) -> bool:
        """Check if document has empty content.

        Args:
            document: Document to check (must have text attribute)

        Returns:
            bool: True if document text is empty after stripping whitespace
        """
        return not document.text.strip()
