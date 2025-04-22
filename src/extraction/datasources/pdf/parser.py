import os
from typing import Type

from llama_index.core.readers.file.base import default_file_metadata_func
from markitdown import MarkItDown

from core import Factory
from extraction.datasources.core.base.parser import BaseParser
from extraction.datasources.pdf.configuration import PDFDatasourceConfiguration
from extraction.datasources.pdf.document import PDFDocument


class PDFDatasourceParser(BaseParser[PDFDocument]):
    """
    Parser for PDF documents that converts them to structured PDFDocument objects.

    Uses MarkItDown to convert PDF files to markdown format for easier processing.
    """

    def __init__(self, parser: MarkItDown = MarkItDown()):
        """
        Initialize the PDF parser.

        Attributes:
            parser: MarkItDown parser instance for PDF to markdown conversion
        """
        self.parser = parser

    def parse(self, file_path: str) -> PDFDocument:
        """
        Parses the given PDF file into a structured document.

        Args:
            file_path: Path to the PDF file

        Returns:
            PDFDocument object containing the parsed content and metadata
        """
        markdown = self.parser.convert(
            file_path, file_extension=".pdf"
        ).text_content
        metadata = self._extract_metadata(file_path)
        return PDFDocument(text=markdown, metadata=metadata)

    def _extract_metadata(self, file_path: str) -> dict:
        """
        Extract and process PDF metadata from the file.

        Args:
            file_path: Path to the PDF file

        Returns:
            Processed metadata dictionary with standardized fields
        """
        metadata = default_file_metadata_func(file_path)
        metadata.update(
            {
                "datasource": "pdf",
                "format": "pdf",
                "url": None,
                "title": os.path.basename(file_path),
                "last_edited_date": metadata["last_modified_date"],
                "created_date": metadata["creation_date"],
            }
        )
        del metadata["last_modified_date"]
        del metadata["creation_date"]
        return metadata


class PDFDatasourceParserFactory(Factory):
    """
    Factory for creating PDF parser instances.

    Creates and configures PDFDatasourceParser objects according to
    the provided configuration.
    """

    _configuration_class: Type = PDFDatasourceConfiguration

    @classmethod
    def _create_instance(
        cls, _: PDFDatasourceConfiguration
    ) -> PDFDatasourceParser:
        """
        Creates a new instance of the PDF parser.

        Args:
            _: Configuration object for the parser (not used in this implementation)

        Returns:
            PDFDatasourceParser: Configured parser instance
        """
        return PDFDatasourceParser()
