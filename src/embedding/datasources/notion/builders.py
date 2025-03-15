from injector import inject

from common.bootstrap.configuration.pipeline.embedding.embedding_model.embedding_model_binding_keys import (
    BoundEmbeddingModelMarkdownSplitter,
)
from embedding.datasources.notion.cleaner import NotionCleaner
from embedding.datasources.notion.splitter import NotionSplitter


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
