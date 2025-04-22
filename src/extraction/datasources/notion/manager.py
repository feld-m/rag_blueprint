from typing import AsyncIterator

from core.base_factory import Factory
from extraction.datasources.core.base.manager import BaseDatasourceManager
from extraction.datasources.notion.cleaner import (
    NotionDatasourceCleaner,
    NotionDatasourceCleanerFactory,
)
from extraction.datasources.notion.configuration import (
    NotionDatasourceConfiguration,
)
from extraction.datasources.notion.document import NotionDocument
from extraction.datasources.notion.parser import (
    NotionDatasourceParser,
    NotionDatasourceParserFactory,
)
from extraction.datasources.notion.reader import (
    NotionDatasourceReader,
    NotionDatasourceReaderFactory,
)


class NotionDatasourceManager(BaseDatasourceManager[NotionDocument]):
    """Manager for handling Notion datasource extraction and processing.

    This class coordinates the reading, parsing, and cleaning of Notion content
    to produce structured NotionDocument objects ready for further processing.
    """

    def __init__(
        self,
        configuration: NotionDatasourceConfiguration,
        reader: NotionDatasourceReader,
        parser: NotionDatasourceParser,
        cleaner: NotionDatasourceCleaner,
    ):
        """Initialize the Notion datasource manager.

        Args:
            configuration: Configuration for the Notion datasource
            reader: Component responsible for fetching data from Notion
            parser: Component responsible for parsing Notion data
            cleaner: Component responsible for cleaning parsed Notion documents
        """
        self.configuration = configuration
        self.reader = reader
        self.parser = parser
        self.cleaner = cleaner

    def incremental_sync(self):
        """
        Not implemented.
        """
        raise NotImplementedError("Currently unsupported feature.")

    async def full_refresh_sync(
        self,
    ) -> AsyncIterator[NotionDocument]:
        """Perform a full refresh of all documents from the Notion datasource.

        This method reads all objects from the Notion datasource, parses them
        into documents, cleans them, and yields the cleaned documents.

        Returns:
            An async iterator of cleaned NotionDocument objects
        """
        objects = await self.reader.read_all_async()
        for object in objects:
            document = self.parser.parse(object)
            cleaned_document = self.cleaner.clean(document)
            if cleaned_document:
                yield cleaned_document


class NotionDatasourceManagerFactory(Factory):
    """Factory for creating NotionDatasourceManager instances.

    This factory is responsible for creating instances of the
    NotionDatasourceManager class, which manages the extraction and
    processing of content from Notion databases and pages.

    Attributes:
        _configuration_class: Type of configuration object for Notion datasource
    """

    _configuration_class = NotionDatasourceConfiguration

    @classmethod
    def _create_instance(
        cls,
        configuration: NotionDatasourceConfiguration,
    ) -> NotionDatasourceManager:
        """Create a new instance of NotionDatasourceManager.

        This method creates all necessary components (reader, parser, cleaner)
        and assembles them into a NotionDatasourceManager instance.

        Args:
            configuration: Configuration object for the Notion datasource

        Returns:
            A fully configured NotionDatasourceManager instance
        """
        reader = NotionDatasourceReaderFactory.create(configuration)
        parser = NotionDatasourceParserFactory.create(configuration)
        cleaner = NotionDatasourceCleanerFactory.create(configuration)
        return NotionDatasourceManager(
            configuration=configuration,
            reader=reader,
            parser=parser,
            cleaner=cleaner,
        )
