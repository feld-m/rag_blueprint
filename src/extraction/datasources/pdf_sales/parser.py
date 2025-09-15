import os
import re
from typing import Callable, List, Type

from llama_index.core.readers.file.base import default_file_metadata_func
from markitdown import MarkItDown

from core.base_factory import Factory
from extraction.datasources.core.parser import BaseParser
from extraction.datasources.pdf_sales.configuration import (
    PDFSalesDatasourceConfiguration,
)
from extraction.datasources.pdf_sales.document import PDFSalesDocument


class PDFSalesDatasourceParser(BaseParser[PDFSalesDocument]):
    """
    Parser for PDF sales documents that converts them to structured PDFSalesDocument objects.
    On top of standard PDF parsing, it extracts specific fields like client name,
    offer name, project lead, and validity date from the document text.
    """

    FIELDS_TO_EXTRACT = [
        {
            "name": "valid_until",
            "search_patterns": r"(?:Gültig bis|Valid until)\s*[:\s]*([\d/]+)",
        },
        {
            "name": "client_name",
            "search_patterns": r"(?:Client|Kunde)\s*[:\s]*([\S ]+?)(?=\s*\b(?:Quote No\.|Quote|Angebotsnummer|Date|Contact|Conta ct|Contents|Project Lead|Projektnummer)\b)",
        },
        {
            "name": "offer_name",
            "search_patterns": r"(?:Angebot|Quote)\s*[:\s]*([\S ]+?)(?=\s*\b(?:Datum|Date|Valid until|Contact|Project Lead|Projektleiter|Projektnummer)\b)",
        },
        {
            "name": "project_lead",
            "search_patterns": r"(?:Project\s*Lead|Projektleiter)\s*[:\s]*([\w\s.]+?)(?=\s*(Contact|Kontakt|Project Number|Quote Number|Valid until|$))",
        },
    ]

    def __init__(
        self,
        parser: MarkItDown = MarkItDown(),
        metadata_extractor: Callable = default_file_metadata_func,
    ):
        """
        Initialize the PDF Sales datasource parser.

        Attributes:
            parser: MarkItDown parser instance for PDF to markdown conversion
            metadata_extractor: Function to extract metadata from the PDF file
        """
        self.parser = parser
        self.metadata_extractor = metadata_extractor

    def parse(self, file_path: str) -> PDFSalesDocument:
        """
        Parses the given PDF Sales file into a structured document.

        Args:
            file_path: Path to the PDF file

        Returns:
            PDFSalesDocument object containing the parsed content and metadata
        """
        markdown = self.parser.convert(
            file_path, file_extension=".pdf"
        ).text_content
        markdown = self._preprocess_text(markdown)

        metadata = self._extract_metadata(file_path)
        metadata = self._extract_fields(
            markdown, metadata, self.FIELDS_TO_EXTRACT
        )

        return PDFSalesDocument(text=markdown, metadata=metadata)

    def _preprocess_text(self, markdown: str) -> str:
        """
        Preprocess text to clean split labels and values while preserving structure.

        Args:
            text (str): Raw extracted text.

        Returns:
            str: Cleaned and normalized text.
        """
        # Normalize known splits or errors
        markdown = re.sub(r"Conta\s*ct", "Contact", markdown)
        markdown = re.sub(r"Projektl\s*eiter", "Projektleiter", markdown)
        markdown = re.sub(r"Proje\s*ct\s*Lead", "Project Lead", markdown)
        # Join lines where a label is split from its value (without look-behind)
        markdown = re.sub(
            r"(Client|Kunde|Projektleiter|Project Lead|Gültig bis|Valid until)\s*\n\s*",
            r"\1 ",
            markdown,
        )
        # Remove excessive spaces
        markdown = re.sub(r"\s{2,}", " ", markdown)

        return markdown

    def _extract_metadata(self, file_path: str) -> dict:
        """
        Extract and process PDF metadata from the file.

        Args:
            file_path: Path to the PDF Sales file

        Returns:
            Processed metadata dictionary with standardized fields
        """
        metadata = self.metadata_extractor(file_path)
        metadata.update(
            {
                "datasource": "pdf_sales",
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

    def _extract_fields(
        self, markdown: str, metadata: dict, fields_to_extract: List[dict]
    ) -> dict:
        """
        Extract specific fields from the markdown text using regex patterns.

        Args:
            markdown (str): The markdown text to search.
            metadata (dict): The metadata dictionary to update.
            fields_to_extract (List[dict]): List of dictionaries containing field names and regex patterns.

        Returns:
            dict: Updated metadata dictionary with extracted fields.
        """
        for field in fields_to_extract:
            match = re.search(field["search_patterns"], markdown, re.IGNORECASE)
            if match:
                metadata[field["name"]] = match.group(1).strip()

        # Fallback/default values
        metadata.setdefault("valid_until", "01/01/2024")
        metadata.setdefault("client_name", "Unknown Client")
        metadata.setdefault("offer_name", "Generic Offer")
        metadata.setdefault("project_lead", "Not Assigned")

        return metadata


class PDFSalesDatasourceParserFactory(Factory):
    """
    Factory for creating PDF Sales parser instances.

    Creates and configures PDFSalesDatasourceParser objects according to
    the provided configuration.
    """

    _configuration_class: Type = PDFSalesDatasourceConfiguration

    @classmethod
    def _create_instance(
        cls, _: PDFSalesDatasourceConfiguration
    ) -> PDFSalesDatasourceParser:
        """
        Creates a new instance of the PDF Sales parser.

        Args:
            _: Configuration object for the parser (not used in this implementation)

        Returns:
            PDFSalesDatasourceParser: Configured parser instance
        """
        return PDFSalesDatasourceParser()
