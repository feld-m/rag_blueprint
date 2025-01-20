from typing import List

from llama_index_client import TextNode

from common.bootstrap.configuration.pipeline.embedding.embedding_model.embedding_model_binding_keys import (
    BoundEmbeddingModelMarkdownSplitter,
)
from embedding.datasources.confluence.document import ConfluenceDocument
from embedding.datasources.core.splitter import BaseSplitter


class ConfluenceSplitter(BaseSplitter):

    def __init__(
        self,
        markdown_splitter: BoundEmbeddingModelMarkdownSplitter,
    ):
        """
        The `ConfluenceSplitter` class is a concrete class that defines the interface for splitting documents into text nodes.

        :param markdown_splitter: MarkdownSplitter object for splitting documents
        """
        self.markdown_splitter = markdown_splitter

    def split(self, documents: List[ConfluenceDocument]) -> List[TextNode]:
        """
        Split the given list of documents into text nodes using `markdown_splitter`. Documents should be in markdown format.

        :param documents: List of Document objects
        :return: List of TextNode objects
        """
        return self.markdown_splitter.split(documents)
