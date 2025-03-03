import unittest
from unittest.mock import MagicMock
from typing import List
from src.embedding.datasources.hackernews.splitter import HackerNewsSplitter
from common.bootstrap.configuration.pipeline.embedding.embedding_model.embedding_model_binding_keys import BoundEmbeddingModelMarkdownSplitter
from embedding.datasources.hackernews.document import HackerNewsDocument


class TestHackerNewsSplitter(unittest.TestCase):

    def setUp(self):
        self.mock_markdown_splitter = MagicMock(spec=BoundEmbeddingModelMarkdownSplitter)
        self.mock_markdown_splitter.split = MagicMock()
        self.splitter = HackerNewsSplitter(markdown_splitter=self.mock_markdown_splitter)

    def test_split_empty_documents(self):
        documents: List[HackerNewsDocument] = []
        self.mock_markdown_splitter.split.return_value = []
        result = self.splitter.split(documents)
        self.assertEqual(result, [])
        self.mock_markdown_splitter.split.assert_called_once_with(documents)
