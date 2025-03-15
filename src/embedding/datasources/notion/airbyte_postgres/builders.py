from injector import inject
from sqlalchemy import create_engine

from common.bootstrap.configuration.pipeline.embedding.datasources.datasources_configuration import (
    NotionPostgresAirbyteDatasourceConfiguration,
)
from embedding.datasources.notion.airbyte_postgres.reader import (
    NotionPostgresAirbyteReader,
)
from embedding.datasources.notion.cleaner import NotionCleaner
from embedding.datasources.notion.manager import NotionDatasourceManager
from embedding.datasources.notion.parser import NotionParser
from embedding.datasources.notion.splitter import NotionSplitter


class NotionPostgresAirbyteDatasourceManagerBuilder:
    """Builder for creating Notion datasource manager instances.

    Provides factory method to create configured NotionDatasourceManager
    with required components for content processing.
    """

    @staticmethod
    @inject
    def build(
        configuration: NotionPostgresAirbyteDatasourceConfiguration,
        reader: NotionPostgresAirbyteReader,
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


class NotionPostgresAirbyteReaderBuilder:
    """Builder for creating Notion reader instances.

    Provides factory method to create configured NotionReader objects.
    """

    @staticmethod
    @inject
    def build(
        configuration: NotionPostgresAirbyteDatasourceConfiguration,
    ) -> NotionPostgresAirbyteReader:
        """Creates a configured Notion reader.

        Args:
            configuration: Notion airbyte datasource configuration
            engine: SQLAlchemy engine for airbyte destination database
            parser: Notion parser for processing raw content from destination

        Returns:
            NotionReader: Configured reader instance
        """
        return NotionPostgresAirbyteReader(
            configuration=configuration,
            engine=create_engine(configuration.destination.connection_url),
            parser=NotionParser(),
        )
