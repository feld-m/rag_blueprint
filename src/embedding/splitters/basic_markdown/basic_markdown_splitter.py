import uuid
from typing import Callable, Generic, List, Type

from llama_index.core.node_parser import MarkdownNodeParser, SentenceSplitter
from llama_index.core.schema import TextNode

from core import Factory
from embedding.bootstrap.configuration.embedding_model_configuration import (
    EmbeddingModelConfiguration,
)
from embedding.embedding_models.registry import EmbeddingModelTokenizerRegistry
from embedding.splitters.base_splitter import BaseSplitter
from embedding.splitters.basic_markdown.configuration import (
    BasicMarkdownSplitterConfiguration,
)
from extraction.datasources.core.base.document import DocType


class BasicMarkdownSplitter(BaseSplitter, Generic[DocType]):
    """Splitter for markdown documents with token-based chunking.

    Splits markdown content into nodes based on document structure and
    token limits. Supports node merging and splitting to maintain
    consistent chunk sizes.
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
            tokenize_func: Function to tokenize text for token counting
        """
        self.chunk_size_in_tokens = chunk_size_in_tokens
        self.tokenize_func = tokenize_func

        self.markdown_node_parser = MarkdownNodeParser()
        self.sentence_splitter = SentenceSplitter(
            chunk_size=chunk_size_in_tokens,
            chunk_overlap=chunk_overlap_in_tokens,
            tokenizer=tokenize_func,
        )

    def split(self, document: DocType) -> TextNode:
        """Split markdown documents into text nodes.

        Split markdown document by markdown tags, then adjusts node sizes
        through splitting large nodes and merging small nodes to optimize
        for the target chunk size.

        Args:
            document: Markdown document to be processed

        Returns:
            List[TextNode]: Collection of processed text nodes with optimized sizes
        """
        document_nodes = self.markdown_node_parser.get_nodes_from_documents([document])
        document_nodes = self._split_big_nodes(document_nodes)
        document_nodes = self._merge_small_nodes(document_nodes)

        return document_nodes

    def _split_big_nodes(self, document_nodes: List[TextNode]) -> List[TextNode]:
        """Split oversized nodes into smaller chunks.

        Identifies nodes exceeding the token limit and processes them
        through the sentence splitter to create smaller, semantically
        coherent chunks.

        Args:
            document_nodes: Collection of nodes to process

        Returns:
            List[TextNode]: Processed nodes within token size limits
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

        Uses sentence boundary detection to create semantically meaningful
        smaller chunks from a large node, preserving metadata from the
        original node.

        Args:
            document_node: Node exceeding token size limit

        Returns:
            List[TextNode]: Collection of smaller nodes derived from original
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

    def _merge_small_nodes(self, document_nodes: List[TextNode]) -> List[TextNode]:
        """Merge adjacent small nodes into larger chunks.

        Combines consecutive nodes when their combined token count remains
        under the maximum limit, optimizing for fewer, larger chunks
        while respecting token boundaries.

        Args:
            document_nodes: Collection of nodes to potentially merge

        Returns:
            List[TextNode]: Optimized collection with merged nodes
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


class BasicMarkdownSplitterFactory(Factory):
    """Factory for creating BasicMarkdownSplitter instances.

    Creates splitter instances configured according to the provided
    embedding model configuration.
    """

    _configuration_class: Type = EmbeddingModelConfiguration

    @classmethod
    def _create_instance(
        cls, configuration: EmbeddingModelConfiguration
    ) -> BasicMarkdownSplitter:
        """Create a BasicMarkdownSplitter instance from configuration.

        Validates the configuration, retrieves the appropriate tokenizer,
        and instantiates a properly configured splitter.

        Args:
            configuration: Embedding model configuration containing splitter settings

        Returns:
            BasicMarkdownSplitter: Configured splitter instance

        Raises:
            ValueError: If the configuration lacks proper splitter settings
        """
        if not configuration.splitter or not isinstance(
            configuration.splitter, BasicMarkdownSplitterConfiguration
        ):
            raise ValueError(
                "`BasicMarkdownSplitterConfiguration` configuration is required for `BasicMarkdownSplitter`."
            )

        tokenizer_func = EmbeddingModelTokenizerRegistry.get(
            configuration.provider
        ).create(configuration)

        return BasicMarkdownSplitter(
            chunk_size_in_tokens=configuration.splitter.chunk_size_in_tokens,
            chunk_overlap_in_tokens=configuration.splitter.chunk_overlap_in_tokens,
            tokenize_func=tokenizer_func,
        )
