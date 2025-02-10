from atlassian import Confluence
from injector import inject

from common.bootstrap.configuration.pipeline.embedding.datasources.datasources_configuration import (
    ConfluenceDatasourceConfiguration,
)
from common.bootstrap.configuration.pipeline.embedding.embedding_model.embedding_model_binding_keys import (
    BoundEmbeddingModelMarkdownSplitter,
)
from embedding.datasources.confluence.cleaner import ConfluenceCleaner
from embedding.datasources.confluence.manager import ConfluenceDatasourceManager
from embedding.datasources.confluence.reader import ConfluenceReader
from embedding.datasources.confluence.splitter import ConfluenceSplitter
from embedding.datasources.core.cleaner import Cleaner


class ConfluenceDatasourceManagerBuilder:
    """Builder for creating Confluence datasource manager instances.

    Provides factory method to create configured ConfluenceDatasourceManager
    with required components for content processing.
    """

    @staticmethod
    @inject
    def build(
        configuration: ConfluenceDatasourceConfiguration,
        reader: ConfluenceReader,
        cleaner: Cleaner,
        splitter: ConfluenceSplitter,
    ) -> ConfluenceDatasourceManager:
        """Creates a configured Confluence datasource manager.

        Args:
            configuration: Confluence access and processing settings
            reader: Component for reading Confluence content
            cleaner: Component for cleaning raw content
            splitter: Component for splitting content into chunks

        Returns:
            ConfluenceDatasourceManager: Configured manager instance
        """
        return ConfluenceDatasourceManager(
            configuration=configuration,
            reader=reader,
            cleaner=cleaner,
            splitter=splitter,
        )


class ConfluenceReaderBuilder:
    """Builder for creating Confluence reader instances.

    Provides factory method to create configured ConfluenceReader objects.
    """

    @staticmethod
    @inject
    def build(
        configuration: ConfluenceDatasourceConfiguration,
        confluence_client: Confluence,
    ) -> ConfluenceReader:
        """Creates a configured Confluence reader.

        Args:
            configuration: Confluence access settings
            confluence_client: Client for Confluence API interaction

        Returns:
            ConfluenceReader: Configured reader instance
        """
        return ConfluenceReader(
            configuration=configuration,
            confluence_client=confluence_client,
        )


class ConfluenceClientBuilder:
    """Builder for creating Confluence API client instances.

    Provides factory method to create configured Confluence API clients.
    """

    @staticmethod
    @inject
    def build(configuration: ConfluenceDatasourceConfiguration) -> Confluence:
        """Creates a configured Confluence API client.

        Args:
            configuration: Confluence connection settings

        Returns:
            Confluence: Configured API client instance
        """
        return Confluence(
            url=configuration.base_url,
            username=configuration.secrets.username.get_secret_value(),
            password=configuration.secrets.password.get_secret_value(),
        )


class ConfluenceCleanerBuilder:
    """Builder for creating Confluence content cleaner instances.

    Provides factory method to create Cleaner objects for Confluence content.
    """

    @staticmethod
    @inject
    def build() -> ConfluenceCleaner:
        """Creates a content cleaner for Confluence.

        Returns:
            Cleaner: Configured cleaner instance
        """
        return ConfluenceCleaner()


class ConfluenceSplitterBuilder:

    @staticmethod
    @inject
    def build(
        markdown_splitter: BoundEmbeddingModelMarkdownSplitter,
    ) -> ConfluenceSplitter:
        """
        Builds a `ConfluenceSplitter` instance using `MarkdownSplitter`.

        :param markdown_splitter: MarkdownSplitter object
        :return: ConfluenceSplitter object
        """
        return ConfluenceSplitter(markdown_splitter)
