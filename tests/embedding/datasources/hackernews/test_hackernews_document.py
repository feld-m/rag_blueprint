import unittest
from datetime import datetime
from embedding.datasources.hackernews.document import HackerNewsDocument

class TestHackerNewsDocument(unittest.TestCase):

    def test_initialization(self):
        metadata = {"extra": "data"}
        document = HackerNewsDocument(
            text="Sample text",
            metadata=metadata,
            id="123",
            type="story",
            title="Sample Title",
            author="Author",
            time=datetime(2023, 1, 1),
            url="http://example.com",
            score=100,
            parent=1,
            kids=[2, 3]
        )
        self.assertEqual(document.text, "Sample text")
        self.assertEqual(document.metadata["id"], "123")
        self.assertEqual(document.metadata["type"], "story")
        self.assertEqual(document.metadata["title"], "Sample Title")
        self.assertEqual(document.metadata["author"], "Author")
        self.assertEqual(document.metadata["time"], "2023-01-01T00:00:00")
        self.assertEqual(document.metadata["url"], "http://example.com")
        self.assertEqual(document.metadata["score"], 100)
        self.assertEqual(document.metadata["parent"], 1)
        self.assertEqual(document.metadata["kids"], [2, 3])
        self.assertEqual(document.metadata["extra"], "data")

    def test_get_content(self):
        document = HackerNewsDocument(
            text="Sample text",
            metadata={},
            id="123",
            type="story"
        )
        self.assertEqual(document.get_content(), "Sample text")

    def test_excluded_metadata(self):
        document = HackerNewsDocument(
            text="Sample text",
            metadata={"extra": "data"},
            id="123",
            type="story"
        )
        self.assertIn("extra", document.excluded_embed_metadata_keys)
        self.assertIn("extra", document.excluded_llm_metadata_keys)
