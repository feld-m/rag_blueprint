import re

from bs4 import BeautifulSoup
from markdownify import markdownify as md

from core.base_factory import Factory
from extraction.datasources.core.base.cleaner import BasicMarkdownCleaner
from extraction.datasources.notion.configuration import (
    NotionDatasourceConfiguration,
)
from extraction.datasources.notion.document import NotionDocument


class NotionDatasourceCleaner(BasicMarkdownCleaner[NotionDocument]):
    """Cleaner for Notion document content.

    Implements cleaning logic for Notion databases and pages, removing HTML
    tags and comments while preserving meaningful content.

    Note:
        Expects documents to be in markdown format.
    """

    def clean(self, document: NotionDocument) -> NotionDocument:
        """Clean a single Notion document.

        Processes the document based on its type (database or page),
        removing HTML artifacts and cleaning the content.

        Args:
            document: Notion document to clean

        Returns:
            NotionDocument: Cleaned document, or None if content is empty after cleaning
        """
        if document.metadata["type"] == "database":
            cleaned_text = self._clean_database(document)
            document.set_content(cleaned_text)
        if document.metadata["type"] == "page":
            cleaned_text = self._clean_page(document)
            document.set_content(cleaned_text)

        if self._has_empty_content(document):
            return None

        return document

    def _clean_database(self, document: NotionDocument) -> str:
        """Clean Notion database content.

        Extracts and cleans the text content from a Notion database document,
        processing any embedded HTML elements.

        Args:
            document: Database document to clean

        Returns:
            str: Cleaned database content as markdown text
        """
        return NotionDatasourceCleaner._parse_html_in_markdown(document.text)

    def _clean_page(self, document: NotionDocument) -> str:
        """Clean Notion page content.

        Extracts and cleans the text content from a Notion page document,
        processing any embedded HTML elements.

        Args:
            document: Page document to clean

        Returns:
            str: Cleaned page content as markdown text
        """
        return NotionDatasourceCleaner._parse_html_in_markdown(document.text)

    @staticmethod
    def _parse_html_in_markdown(md_text: str) -> str:
        """Process HTML elements within markdown content.

        Performs two main cleaning operations:
        1. Removes HTML comments completely
        2. Converts HTML tags to markdown format
        3. Removes elements that don't contain alphanumeric characters

        Args:
            md_text: Text containing markdown and HTML

        Returns:
            str: Cleaned markdown text with HTML properly converted or removed

        Note:
            Uses BeautifulSoup for HTML parsing and markdownify for HTML-to-markdown conversion
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


class NotionDatasourceCleanerFactory(Factory):
    """Factory for creating NotionDatasourceCleaner instances.

    This factory is responsible for creating instances of NotionDatasourceCleaner
    with the appropriate configuration.
    """

    _configuration_class = NotionDatasourceConfiguration

    @classmethod
    def _create_instance(
        cls, _: NotionDatasourceConfiguration
    ) -> NotionDatasourceCleaner:
        """Create a new instance of NotionDatasourceCleaner.

        Args:
            configuration: Configuration for the cleaner

        Returns:
            NotionDatasourceCleaner: Instance of NotionDatasourceCleaner
        """
        return NotionDatasourceCleaner()
