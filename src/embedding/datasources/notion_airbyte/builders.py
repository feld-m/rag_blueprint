from injector import inject
from sqlalchemy import create_engine

from common.bootstrap.configuration.pipeline.embedding.datasources.datasources_configuration import (
    NotionAirbyteDatasourceConfiguration,
)
from common.bootstrap.configuration.pipeline.embedding.embedding_model.embedding_model_binding_keys import (
    BoundEmbeddingModelMarkdownSplitter,
)
from embedding.datasources.notion_airbyte.cleaner import NotionCleaner
from embedding.datasources.notion_airbyte.manager import NotionDatasourceManager
from embedding.datasources.notion_airbyte.parser import NotionParser
from embedding.datasources.notion_airbyte.reader import NotionAirbyteReader
from embedding.datasources.notion_airbyte.splitter import NotionSplitter


class NotionAirbyteDatasourceManagerBuilder:
    """Builder for creating Notion datasource manager instances.

    Provides factory method to create configured NotionDatasourceManager
    with required components for content processing.
    """

    @staticmethod
    @inject
    def build(
        configuration: NotionAirbyteDatasourceConfiguration,
        reader: NotionAirbyteReader,
        cleaner: NotionCleaner,
        splitter: NotionSplitter,
    ) -> NotionDatasourceManager:
        """Creates a configured Notion datasource manager.

        Args:
            configuration: Notion access and processing settings
            reader: Component for reading Notion content
            cleaner: Component for cleaning raw content
            splitter: Component for splitting content into chunks

        Returns:
            NotionDatasourceManager: Configured manager instance
        """
        return NotionDatasourceManager(
            configuration=configuration,
            reader=reader,
            cleaner=cleaner,
            splitter=splitter,
        )


class NotionAirbyteReaderBuilder:
    """Builder for creating Notion reader instances.

    Provides factory method to create configured NotionReader objects.
    """

    @staticmethod
    @inject
    def build(
        configuration: NotionAirbyteDatasourceConfiguration,
    ) -> NotionAirbyteReader:
        """Creates a configured Notion reader.

        Args:
            configuration: Notion airbyte datasource configuration
            engine: SQLAlchemy engine for airbyte destination database
            parser: Notion parser for processing raw content from destination

        Returns:
            NotionReader: Configured reader instance
        """
        return NotionAirbyteReader(
            configuration=configuration,
            engine=create_engine(configuration.destination.connection_url),
            parser=NotionParser(),
        )


class NotionCleanerBuilder:
    """Builder for creating Notion content cleaner instances.

    Provides factory method to create NotionCleaner objects.
    """

    @staticmethod
    @inject
    def build() -> NotionCleaner:
        """Creates a content cleaner for Notion.

        Returns:
            NotionCleaner: Configured cleaner instance
        """
        return NotionCleaner()


class NotionSplitterBuilder:
    """Builder for creating Notion content splitter instances.

    Provides factory method to create configured NotionSplitter objects
    with separate splitters for databases and pages.
    """

    @staticmethod
    @inject
    def build(
        database_splitter: BoundEmbeddingModelMarkdownSplitter,
        page_splitter: BoundEmbeddingModelMarkdownSplitter,
    ) -> NotionSplitter:
        """Creates a configured Notion content splitter.

        Args:
            database_splitter: Splitter for database content
            page_splitter: Splitter for page content

        Returns:
            NotionSplitter: Configured splitter instance
        """
        return NotionSplitter(
            database_splitter=database_splitter, page_splitter=page_splitter
        )
