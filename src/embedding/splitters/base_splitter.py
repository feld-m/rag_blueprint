from abc import ABC, abstractmethod
from typing import Generic

from llama_index.core.schema import TextNode

from extraction.datasources.core.base.document import DocType


class BaseSplitter(ABC, Generic[DocType]):
    """Abstract base class for document splitter.

    This class defines a common interface for document splitters that transform
    various document types into text nodes for further processing. It leverages
    generic typing to support different document formats while maintaining type safety.

    Implementations should handle the specific logic required to parse and split
    different document types into meaningful text chunks.
    """

    @abstractmethod
    def split(self, document: DocType) -> TextNode:
        """Split a document into a text node.

        This method processes a single document and converts it into a TextNode
        representation suitable for embedding or other processing. Implementing
        classes should define the specific logic for parsing different document types.

        Args:
            document: The document to split or process

        Returns:
            TextNode: The processed text node generated from the document
        """
        pass
