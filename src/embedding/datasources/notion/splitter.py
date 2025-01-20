from typing import List

from llama_index.core.schema import TextNode

from embedding.datasources.core.splitter import BaseSplitter, MarkdownSplitter
from embedding.datasources.notion.document import NotionDocument
from embedding.datasources.notion.reader import NotionObjectType


class NotionSplitter(BaseSplitter):
    """Splitter for Notion content with separate database and page handling.

    Implements content splitting for Notion documents by routing databases
    and pages to specialized splitters.

    Attributes:
        database_splitter: Splitter configured for database content
        page_splitter: Splitter configured for page content
    """

    def __init__(
        self,
        database_splitter: MarkdownSplitter,
        page_splitter: MarkdownSplitter,
    ):
        """Initialize Notion content splitter.

        Args:
            database_splitter: MarkdownSplitter instance for databases
            page_splitter: MarkdownSplitter instance for pages
        """
        self.database_splitter = database_splitter
        self.page_splitter = page_splitter

    def split(self, documents: List[NotionDocument]) -> List[TextNode]:
        """Split Notion documents into text nodes.

        Separates documents by type and processes them with appropriate
        splitter.

        Args:
            documents: Collection of Notion documents to split

        Returns:
            List[TextNode]: Combined collection of text nodes from all documents
        """
        database_documents = [
            doc
            for doc in documents
            if doc.extra_info["type"] == NotionObjectType.DATABASE.value
        ]
        page_documents = [
            doc
            for doc in documents
            if doc.extra_info["type"] == NotionObjectType.PAGE.value
        ]

        nodes = self.database_splitter.split(database_documents)
        nodes.extend(self.page_splitter.split(page_documents))

        return nodes
