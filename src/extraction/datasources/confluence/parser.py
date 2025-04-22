import tempfile
from typing import Type

from markitdown import MarkItDown

from core import Factory
from extraction.datasources.confluence.configuration import (
    ConfluenceDatasourceConfiguration,
)
from extraction.datasources.confluence.document import ConfluenceDocument
from extraction.datasources.core.base.parser import BaseParser


class ConfluenceDatasourceParser(BaseParser[ConfluenceDocument]):
    def __init__(
        self,
        configuration: ConfluenceDatasourceConfiguration,
        parser: MarkItDown = MarkItDown(),
    ):
        """Initialize the Confluence parser with the provided configuration.

        Args:
            configuration: Configuration object containing Confluence connection details
        """
        self.configuration = configuration
        self.parser = parser

    def parse(self, page: str) -> ConfluenceDocument:
        """Parse a Confluence page into a document.

        Args:
            page: Dictionary containing Confluence page information

        Returns:
            ConfluenceDocument: Parsed document with extracted text and metadata
        """
        markdown = self._get_page_markdown(page)
        metadata = self._extract_metadata(page, self.configuration.base_url)
        return ConfluenceDocument(text=markdown, metadata=metadata)

    def _get_page_markdown(self, page: dict) -> str:
        """Extract markdown content from a Confluence page. Because of MarkItDown,
        we need to write the HTML content to a temporary file and then convert it to markdown.

        Args:
            page: Dictionary containing Confluence page details

        Returns:
            str: Markdown content of the page
        """
        html_content = page["body"]["view"]["value"]
        if not html_content:
            return ""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html") as temp_file:
            temp_file.write(html_content)
            temp_file.flush()
            return self.parser.convert(
                temp_file.name, file_extension=".html"
            ).text_content

    @staticmethod
    def _extract_metadata(page: dict, base_url: str) -> dict:
        """Extract and format page metadata.

        Args:
            page: Dictionary containing Confluence page details
            base_url: Base URL of the Confluence instance

        Returns:
            dict: Structured metadata including dates, IDs, and URLs
        """
        return {
            "created_time": page["history"]["createdDate"],
            "created_date": page["history"]["createdDate"].split("T")[0],
            "datasource": "confluence",
            "format": "md",
            "last_edited_date": page["history"]["lastUpdated"]["when"],
            "last_edited_time": page["history"]["lastUpdated"]["when"].split(
                "T"
            )[0],
            "page_id": page["id"],
            "space": page["_expandable"]["space"].split("/")[-1],
            "title": page["title"],
            "type": "page",
            "url": base_url + page["_links"]["webui"],
        }


class ConfluenceDatasourceParserFactory(Factory):
    _configuration_class: Type = ConfluenceDatasourceConfiguration

    @classmethod
    def _create_instance(
        cls, configuration: ConfluenceDatasourceConfiguration
    ) -> ConfluenceDatasourceParser:
        """Creates a Confluence parser instance.

        Args:
            configuration: Configuration object containing Confluence connection details

        Returns:
            ConfluenceDatasourceParser: Configured Confluence parser instance
        """
        return ConfluenceDatasourceParser(configuration)
