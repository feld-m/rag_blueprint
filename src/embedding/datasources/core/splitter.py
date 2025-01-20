import uuid
from abc import ABC, abstractmethod
from typing import Callable, Generic, List

from llama_index.core import Document
from llama_index.core.node_parser import MarkdownNodeParser, SentenceSplitter
from llama_index.core.schema import TextNode

from embedding.datasources.core.document import DocType


class BaseSplitter(ABC, Generic[DocType]):
    """Abstract base class for document splitting.

    Defines interface for splitting documents into text nodes with
    generic typing support for document types.
    """

    @abstractmethod
    def split(self, documents: List[DocType]) -> List[TextNode]:
        """Split documents into text nodes.

        Args:
            documents: Collection of documents to split

        Returns:
            List[TextNode]: Collection of text nodes
        """
        pass


class MarkdownSplitter(BaseSplitter):
    """Splitter for markdown documents with token-based chunking.

    Splits markdown content into nodes based on document structure and
    token limits. Supports node merging and splitting to maintain
    consistent chunk sizes.

    Attributes:
        chunk_size_in_tokens: Maximum tokens per chunk
        tokenize_func: Function to convert text to tokens
        markdown_node_parser: Parser for markdown structure
        sentence_splitter: Splitter for text chunks
    """

    def __init__(
        self,
        chunk_size_in_tokens: int,
        chunk_overlap_in_tokens: int,
        tokenize_func: Callable,
    ):
        """Initialize markdown splitter.

        Args:
            chunk_size_in_tokens: Maximum tokens per chunk
            chunk_overlap_in_tokens: Token overlap between chunks
            tokenize_func: Function to tokenize text
        """
        self.chunk_size_in_tokens = chunk_size_in_tokens
        self.tokenize_func = tokenize_func

        self.markdown_node_parser = MarkdownNodeParser()
        self.sentence_splitter = SentenceSplitter(
            chunk_size=chunk_size_in_tokens,
            chunk_overlap=chunk_overlap_in_tokens,
            tokenizer=tokenize_func,
        )

    def split(self, documents: List[Document]) -> List[TextNode]:
        """Split markdown documents into text nodes.

        Processes documents through markdown parsing, then adjusts node sizes
        through splitting and merging to match chunk size requirements.

        Args:
            documents: Collection of markdown documents

        Returns:
            List[TextNode]: Collection of processed text nodes
        """
        nodes = []

        for document in documents:
            document_nodes = self.markdown_node_parser.get_nodes_from_documents(
                [document]
            )
            document_nodes = self._split_big_nodes(document_nodes)
            document_nodes = self._merge_small_nodes(document_nodes)
            nodes.extend(document_nodes)

        return nodes

    def _split_big_nodes(
        self, document_nodes: List[TextNode]
    ) -> List[TextNode]:
        """Split oversized nodes into smaller chunks.

        Args:
            document_nodes: Collection of nodes to process

        Returns:
            List[TextNode]: Processed nodes within size limits
        """
        new_document_nodes = []

        for document_node in document_nodes:
            text = document_node.text
            document_node_size = len(self.tokenize_func(text))

            if document_node_size > self.chunk_size_in_tokens:
                document_sub_nodes = self._split_big_node(document_node)
                new_document_nodes.extend(document_sub_nodes)
            else:
                new_document_nodes.append(document_node)

        return new_document_nodes

    def _split_big_node(self, document_node: TextNode) -> List[TextNode]:
        """Split single oversized node into smaller nodes.

        Args:
            document_node: Node to split

        Returns:
            List[TextNode]: Collection of smaller nodes
        """
        text = document_node.text
        sub_texts = self.sentence_splitter.split_text(text)
        sub_nodes = []

        for sub_text in sub_texts:
            sub_node = document_node.model_copy()
            sub_node.id_ = str(uuid.uuid4())
            sub_node.text = sub_text
            sub_nodes.append(sub_node)

        return sub_nodes

    def _merge_small_nodes(
        self, document_nodes: List[TextNode]
    ) -> List[TextNode]:
        """Merge adjacent small nodes into larger chunks.

        Args:
            document_nodes: Collection of nodes to process

        Returns:
            List[TextNode]: Collection of merged nodes
        """
        new_document_nodes = []
        current_node = document_nodes[0]

        for node in document_nodes[1:]:
            current_text = current_node.text
            current_node_size = len(self.tokenize_func(current_text))
            node_text = node.text
            node_size = len(self.tokenize_func(node_text))

            if current_node_size + node_size <= self.chunk_size_in_tokens:
                current_node.text += node.text
            else:
                new_document_nodes.append(current_node)
                current_node = node

        new_document_nodes.append(current_node)
        return new_document_nodes
