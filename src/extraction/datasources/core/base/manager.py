from abc import ABC, abstractmethod
from typing import AsyncIterator, Generic

from extraction.bootstrap.configuration.configuration import (
    ExtractionConfiguration,
)
from extraction.datasources.core.base.cleaner import (
    BaseCleaner,
    BasicMarkdownCleaner,
)
from extraction.datasources.core.base.document import DocType
from extraction.datasources.core.base.parser import (
    BaseParser,
    BasicMarkdownParser,
)
from extraction.datasources.core.base.reader import BaseReader
from extraction.datasources.core.base.splitter import (
    BaseSplitter,
    BasicMarkdownSplitter,
)


class BaseDatasourceManager(ABC, Generic[DocType]):
    """Abstract base class for datasource management.

    Defines the interface for managing the extraction, parsing,
    cleaning, and splitting of documents from a data source.
    This class serves as a template for implementing specific
    datasource managers, ensuring a consistent interface and
    behavior across different implementations.
    """

    def __init__(
        self,
        configuration: ExtractionConfiguration,
        reader: BaseReader,
        parser: BaseParser = BasicMarkdownParser(),
        cleaner: BaseCleaner = BasicMarkdownCleaner(),
        splitter: BaseSplitter = BasicMarkdownSplitter(),
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
        self.parser = parser
        self.cleaner = cleaner
        self.splitter = splitter

    @abstractmethod
    async def full_refresh_sync(
        self,
    ) -> AsyncIterator[DocType]:
        """Extract and process all content from the datasource.

        Returns:
            An async iterator yielding processed document chunks of type DocType
        """
        pass

    @abstractmethod
    def incremental_sync(self):
        """Process only new or changed content from the datasource.

        This method should handle differential updates to avoid
        reprocessing all content when only portions have changed.
        Implementations should update the vector storage accordingly.
        """
        pass


class BasicDatasourceManager(BaseDatasourceManager, Generic[DocType]):
    """Standard implementation of datasource content processing pipeline.

    Handles the extraction, parsing, cleaning, and splitting of documents
    from a data source. Processes documents using the provided components
    in a sequential pipeline to prepare them for embedding and storage.
    """

    async def full_refresh_sync(
        self,
    ) -> AsyncIterator[DocType]:
        """Process all content from the datasource from scratch.

        Executes the complete pipeline:
        1. Reads source objects asynchronously
        2. Parses each object into a document
        3. Cleans the content
        4. Splits into appropriate chunks

        Returns:
            An async iterator yielding processed document chunks of type DocType
        """
        objects = self.reader.read_all_async()
        async for object in objects:
            md_document = self.parser.parse(object)
            cleaned_document = self.cleaner.clean(md_document)
            if cleaned_document:
                for split_document in self.splitter.split(cleaned_document):
                    yield split_document

    def incremental_sync(self):
        """Process only new or changed content since the last sync.

        Should be implemented by subclasses to provide efficient
        updates when only a portion of the datasource has changed.

        Raises:
            NotImplementedError: This feature is not yet implemented
        """
        raise NotImplementedError("Currently unsupported feature.")
