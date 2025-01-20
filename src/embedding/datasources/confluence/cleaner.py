from typing import List

from tqdm import tqdm

from embedding.datasources.confluence.document import ConfluenceDocument
from embedding.datasources.core.cleaner import BaseCleaner


class ConfluenceCleaner(BaseCleaner):
    """
    The `ConfluenceCleaner` class is a concrete implementation of `BaseCleaner` for cleaning Confluence documents.
    """

    def clean(
        self, documents: List[ConfluenceDocument]
    ) -> List[ConfluenceDocument]:
        """
        Clean the list of Confluence documents. If the content is empty it is not added to the cleaned documents.

        :param documents: List of ConfluenceDocument objects
        :return: List of cleaned ConfluenceDocument objects
        """
        cleaned_documents = []

        for document in ConfluenceCleaner._get_documents_with_tqdm(documents):
            if not ConfluenceCleaner._has_empty_content(document):
                cleaned_documents.append(document)

        return cleaned_documents

    @staticmethod
    def _get_documents_with_tqdm(documents: List[ConfluenceDocument]):
        """
        Return the documents with tqdm progress bar if GlobalSettings.SHOW_PROGRESS is True, else return the documents as is.

        :param documents: List of Notion document objects
        """
        return tqdm(documents, desc="[Confluence] Cleaning documents")
