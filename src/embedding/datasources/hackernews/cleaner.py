from typing import List

from bs4 import BeautifulSoup
from tqdm import tqdm

from embedding.datasources.hackernews.document import HackerNewsDocument
from embedding.datasources.core.cleaner import BaseCleaner


class HackerNewsCleaner(BaseCleaner):
    """
    The `HackerNewsCleaner` class is a concrete implementation of `BaseCleaner` for cleaning HackerNews documents.
    """

    def clean(
        self, documents: List[HackerNewsDocument]
    ) -> List[HackerNewsDocument]:
        """
        Clean the list of HackerNews documents. If the content is empty it is not added to the cleaned documents.

        :param documents: List of HackerNewsDocument objects
        :return: List of cleaned HackerNewsDocument objects
        """
        cleaned_documents = []

        for document in HackerNewsCleaner._get_documents_with_tqdm(documents):
            if not HackerNewsCleaner._has_empty_content(document):
                cleaned_documents.append(self._clean_document(document))

        return cleaned_documents

    def _clean_document(self, document: HackerNewsDocument) -> HackerNewsDocument:
        if document.text and any(c in document.text for c in ["<", ">"]):
            document.text = self._clean_html(document.text)

        # Remove special markers
        if document.text in ["[deleted]", "[dead]"]:
            document.text = ""

        return document

    def _clean_html(self, text: str) -> str:
        soup = BeautifulSoup(text, "html.parser")
        return soup.get_text(separator="\n", strip=True)

    @staticmethod
    def _get_documents_with_tqdm(documents: List[HackerNewsDocument]):
        return tqdm(documents, desc="[HackerNews] Cleaning documents")

    @staticmethod
    def _has_empty_content(document: HackerNewsDocument) -> bool:
        return not document.text