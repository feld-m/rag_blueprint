from injector import inject
from notion_client import Client

from common.bootstrap.configuration.pipeline.embedding.datasources.datasources_configuration import (
    NotionDatasourceConfiguration,
)
from common.bootstrap.configuration.pipeline.embedding.embedding_model.embedding_model_binding_keys import (
    BoundEmbeddingModelMarkdownSplitter,
)
from embedding.datasources.notion.cleaner import NotionCleaner
from embedding.datasources.notion.exporter import NotionExporter
from embedding.datasources.notion.manager import NotionDatasourceManager
from embedding.datasources.notion.reader import NotionReader
from embedding.datasources.notion.splitter import NotionSplitter


class NotionDatasourceManagerBuilder:
    """Builder for creating Notion datasource manager instances.

    Provides factory method to create configured NotionDatasourceManager
    with required components for content processing.
    """

    @staticmethod
    @inject
    def build(
        configuration: NotionDatasourceConfiguration,
        reader: NotionReader,
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


class NotionReaderBuilder:
    """Builder for creating Notion reader instances.

    Provides factory method to create configured NotionReader objects.
    """

    @staticmethod
    @inject
    def build(
        configuration: NotionDatasourceConfiguration,
        notion_client: Client,
        exporter: NotionExporter,
    ) -> NotionReader:
        """Creates a configured Notion reader.

        Args:
            configuration: Notion access settings
            notion_client: Client for Notion API interaction
            exporter: Component for content export

        Returns:
            NotionReader: Configured reader instance
        """
        return NotionReader(
            configuration=configuration,
            notion_client=notion_client,
            exporter=exporter,
        )


class NotionClientBuilder:
    """Builder for creating Notion API client instances.

    Provides factory method to create configured Notion API clients.
    """

    @staticmethod
    @inject
    def build(configuration: NotionDatasourceConfiguration) -> Client:
        """Creates a configured Notion API client.

        Args:
            configuration: Notion authentication settings

        Returns:
            Client: Configured API client instance
        """
        return Client(auth=configuration.secrets.api_token.get_secret_value())


class NotionExporterBuilder:
    """Builder for creating Notion content exporter instances.

    Provides factory method to create configured NotionExporter objects.
    """

    @staticmethod
    @inject
    def build(configuration: NotionDatasourceConfiguration) -> NotionExporter:
        """Creates a configured Notion content exporter.

        Args:
            configuration: Notion authentication settings

        Returns:
            NotionExporter: Configured exporter instance
        """
        return NotionExporter(
            api_token=configuration.secrets.api_token.get_secret_value()
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
