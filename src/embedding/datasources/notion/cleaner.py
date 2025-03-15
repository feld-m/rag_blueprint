import re
from typing import List

from bs4 import BeautifulSoup
from markdownify import markdownify as md
from tqdm import tqdm

from embedding.datasources.core.cleaner import BaseCleaner
from embedding.datasources.notion.document import NotionDocument


class NotionCleaner(BaseCleaner):
    """Cleaner for Notion document content.

    Implements cleaning logic for Notion databases and pages, removing HTML
    tags and comments while preserving meaningful content.

    Note:
        Expects documents to be in markdown format.
    """

    def clean(self, documents: List[NotionDocument]) -> List[NotionDocument]:
        """Clean a collection of Notion documents.

        Processes both databases and pages, removing HTML artifacts and empty content.

        Args:
            documents: Collection of Notion documents to clean

        Returns:
            List[NotionDocument]: Filtered and cleaned documents
        """
        cleaned_documents = []

        for document in NotionCleaner._get_documents_with_tqdm(documents):
            if document.extra_info["type"] == "database":
                document.text = self._clean_database(document)
            if document.extra_info["type"] == "page":
                document.text = self._clean_page(document)

            if not NotionCleaner._has_empty_content(document):
                cleaned_documents.append(document)

        return cleaned_documents

    def _clean_database(self, document: NotionDocument) -> str:
        """Clean Notion database content.

        Args:
            document: Database document to clean

        Returns:
            str: Cleaned database content
        """
        return NotionCleaner._parse_html_in_markdown(document.text)

    def _clean_page(self, document: NotionDocument) -> str:
        """Clean Notion page content.

        Args:
            document: Page document to clean

        Returns:
            str: Cleaned page content
        """
        return NotionCleaner._parse_html_in_markdown(document.text)

    @staticmethod
    def _parse_html_in_markdown(md_text: str) -> str:
        """Process HTML elements within markdown content.

        Converts HTML to markdown and removes content without alphanumeric characters.

        Args:
            md_text: Text containing markdown and HTML

        Returns:
            str: Cleaned markdown text

        Note:
            Uses BeautifulSoup for HTML parsing
        """

        def replace_html(match):
            html_content = match.group(0)
            soup = BeautifulSoup(html_content, "html.parser")
            markdown = md(str(soup))

            if not re.search(r"[a-zA-Z0-9]", markdown):
                return ""
            return markdown

        md_text = re.sub(r"<!--.*?-->", "", md_text, flags=re.DOTALL)
        html_block_re = re.compile(r"<.*?>", re.DOTALL)
        return re.sub(html_block_re, replace_html, md_text)

    @staticmethod
    def _get_documents_with_tqdm(documents: List[NotionDocument]):
        """Wrap document iteration with optional progress bar.

        Args:
            documents: Collection of documents to process

        Returns:
            Iterator over documents, optionally with progress bar
        """
        return tqdm(documents, desc="[Notion] Cleaning documents")
