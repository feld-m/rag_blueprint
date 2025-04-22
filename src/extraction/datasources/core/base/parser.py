from abc import ABC, abstractmethod
from typing import Generic

from llama_index.core import Document

from extraction.datasources.core.document import DocType


class BaseParser(ABC, Generic[DocType]):
    """
    Abstract base class for document parsers.

    Defines the interface for parsing content into documents
    of specified type (DocType).
    """

    @abstractmethod
    def parse(self, content: str) -> DocType:
        """
        Parse content into a document of type DocType.

        Args:
            content: Raw content string to be parsed

        Returns:
            Parsed document of type DocType
        """
        pass


class BasicMarkdownParser(BaseParser[Document]):
    """
    Markdown parser that converts markdown text into Document objects.

    Implements the BaseParser interface for basic markdown content.
    """

    def parse(self, markdown: str) -> Document:
        """
        Parse markdown content into a Document object.

        Args:
            markdown: Markdown content to be parsed

        Returns:
            Document object containing the markdown text
        """
        return Document(text=markdown, metadata={})
