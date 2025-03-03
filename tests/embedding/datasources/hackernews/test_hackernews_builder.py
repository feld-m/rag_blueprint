import unittest
from unittest.mock import MagicMock
from embedding.datasources.hackernews.builders import HackerNewsDatasourceManagerBuilder
from common.bootstrap.configuration.pipeline.embedding.datasources.datasources_configuration import HackerNewsDatasourceConfiguration
from embedding.datasources.hackernews.manager import HackerNewsDatasourceManager
from embedding.datasources.hackernews.reader import HackerNewsReader
from embedding.datasources.hackernews.splitter import HackerNewsSplitter
from embedding.datasources.core.cleaner import Cleaner

class TestHackerNewsDatasourceManagerBuilder(unittest.TestCase):

    def setUp(self):
        self.configuration = MagicMock(spec=HackerNewsDatasourceConfiguration)
        self.reader = MagicMock(spec=HackerNewsReader)
        self.cleaner = MagicMock(spec=Cleaner)
        self.splitter = MagicMock(spec=HackerNewsSplitter)

    def test_build(self):
        manager = HackerNewsDatasourceManagerBuilder.build(
            configuration=self.configuration,
            reader=self.reader,
            cleaner=self.cleaner,
            splitter=self.splitter
        )
        self.assertIsInstance(manager, HackerNewsDatasourceManager)
        self.assertEqual(manager.configuration, self.configuration)
        self.assertEqual(manager.reader, self.reader)
        self.assertEqual(manager.cleaner, self.cleaner)
        self.assertEqual(manager.splitter, self.splitter)
