from injector import inject

from common.bootstrap.configuration.pipeline.embedding.datasources.datasources_configuration import (
    HackerNewsDatasourceConfiguration,
)
from common.bootstrap.configuration.pipeline.embedding.embedding_model.embedding_model_binding_keys import (
    BoundEmbeddingModelMarkdownSplitter,
)
from embedding.datasources.hackernews.cleaner import HackerNewsCleaner
from embedding.datasources.hackernews.manager import HackerNewsDatasourceManager
from embedding.datasources.hackernews.reader import HackerNewsReader
from embedding.datasources.hackernews.splitter import HackerNewsSplitter
from embedding.datasources.core.cleaner import Cleaner


class HackerNewsDatasourceManagerBuilder:
    """Builder for creating HackerNews datasource manager instances.

    Provides factory method to create configured HackerNewsDatasourceManager
    with required components for content processing.
    """

    @staticmethod
    @inject
    def build(
        configuration: HackerNewsDatasourceConfiguration,
        reader: HackerNewsReader,
        cleaner: Cleaner,
        splitter: HackerNewsSplitter,
    ) -> HackerNewsDatasourceManager:
        """Creates a configured HackerNews datasource manager.

        Args:
            configuration: HackerNews access and processing settings
            reader: Component for reading HackerNews content
            cleaner: Component for cleaning raw content
            splitter: Component for splitting content into chunks

        Returns:
            HackerNewsDatasourceManager: Configured manager instance
        """
        return HackerNewsDatasourceManager(
            configuration=configuration,
            reader=reader,
            cleaner=cleaner,
            splitter=splitter,
        )


class HackerNewsReaderBuilder:
    """Builder for creating HackerNews reader instances.

    Provides factory method to create configured HackerNewsReader objects.
    """

    @staticmethod
    @inject
    def build(
        configuration: HackerNewsDatasourceConfiguration,
    ) -> HackerNewsReader:
        """Creates a configured HackerNews reader.

        Args:
            configuration: HackerNews access settings

        Returns:
            HackerNewsReader: Configured reader instance
        """
        return HackerNewsReader(
            configuration=configuration
        )


class HackerNewsCleanerBuilder:
    """Builder for creating HackerNews content cleaner instances.

    Provides factory method to create Cleaner objects for HackerNews content.
    """

    @staticmethod
    @inject
    def build() -> HackerNewsCleaner:
        """Creates a content cleaner for HackerNews.

        Returns:
            Cleaner: Configured cleaner instance
        """
        return HackerNewsCleaner()


class HackerNewsSplitterBuilder:

    @staticmethod
    @inject
    def build(
            markdown_splitter: BoundEmbeddingModelMarkdownSplitter,
    ) -> HackerNewsSplitter:
        """
        Builds a `HackerNewsSplitter` instance using `MarkdownSplitter`.

        :param markdown_splitter: MarkdownSplitter object
        :return: HackerNewsSplitter object
        """
        return HackerNewsSplitter(markdown_splitter)
