import unittest
from embedding.datasources.hackernews.cleaner import HackerNewsCleaner
from embedding.datasources.hackernews.document import HackerNewsDocument

class TestHackerNewsCleaner(unittest.TestCase):

    def setUp(self):
        self.cleaner = HackerNewsCleaner()

    def test_clean_empty_content(self):
        documents = [HackerNewsDocument(text="", metadata={}, id=1, type="story")]
        cleaned_documents = self.cleaner.clean(documents)
        self.assertEqual(len(cleaned_documents), 0)

    def test_clean_html_content(self):
        documents = [HackerNewsDocument(text="<p>Hello World</p>", metadata={}, id=2, type="story")]
        cleaned_documents = self.cleaner.clean(documents)
        self.assertEqual(cleaned_documents[0].text, "Hello World")


