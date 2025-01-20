from abc import ABC, abstractmethod
from typing import Generic, List, Tuple

from llama_index.core.schema import Document, TextNode

from common.bootstrap.configuration.configuration import Configuration
from embedding.datasources.core.cleaner import BaseCleaner
from embedding.datasources.core.document import DocType
from embedding.datasources.core.reader import BaseReader
from embedding.datasources.core.splitter import BaseSplitter


class BaseDatasourceManager(ABC, Generic[DocType]):
    """Abstract base class for datasource management.

    Provides interface for content extraction and vector storage updates.

    Attributes:
        configuration: Settings for embedding and processing
        reader: Component for reading source content
        cleaner: Component for cleaning extracted content
        splitter: Component for splitting content into chunks
    """

    def __init__(
        self,
        configuration: Configuration,
        reader: BaseReader,
        cleaner: BaseCleaner,
        splitter: BaseSplitter,
    ):
        """Initialize datasource manager.

        Args:
            configuration: Embedding and processing settings
            reader: Content extraction component
            cleaner: Content cleaning component
            splitter: Content splitting component
        """
        self.configuration = configuration
        self.reader = reader
        self.cleaner = cleaner
        self.splitter = splitter

    @abstractmethod
    async def extract(
        self,
    ) -> Tuple[List[DocType], List[DocType], List[TextNode]]:
        """Extract and process content from datasource.

        Returns:
            Tuple containing:
                - List of raw documents
                - List of cleaned documents
                - List of text nodes for embedding
        """
        pass

    @abstractmethod
    def update_vector_storage(self):
        """Update vector storage with current embeddings."""
        pass


class DatasourceManager(BaseDatasourceManager):
    """Manager for datasource content processing and embedding.

    Implements content extraction pipeline using configurable components
    for reading, cleaning, splitting and embedding content.
    """

    async def extract(
        self,
    ) -> Tuple[List[Document], List[Document], List[TextNode]]:
        """Extract and process content from datasource.

        Returns:
            Tuple containing:
                - List of raw documents
                - List of cleaned documents
                - List of text nodes for embedding
        """
        documents = await self.reader.get_all_documents_async()
        cleaned_documents = self.cleaner.clean(documents)
        nodes = self.splitter.split(cleaned_documents)
        return documents, cleaned_documents, nodes

    def update_vector_storage(self):
        """Update vector storage with current embeddings.

        Raises:
            NotImplementedError: Method must be implemented by subclasses
        """
        raise NotImplementedError
