import logging
import os
import re
from typing import Any, Dict, List

from llama_index.core.readers.file.base import default_file_metadata_func
from markitdown import MarkItDown
from tqdm import tqdm

from common.bootstrap.configuration.pipeline.embedding.datasources.datasources_configuration import (
    PdfDatasourceConfiguration,
    PDFParser,
)
from embedding.datasources.core.reader import BaseReader
from embedding.datasources.pdf.document import PdfDocument


class DefaultPDFParser:

    def __init__(self):
        """
        Attributes:
            parser: MarkItDown parser instance
        """
        self.parser = MarkItDown()

    def parse(self, file_path: str) -> PdfDocument:
        """
        Parses the given PDF file.

        Args:
            file_path (str): Path to the PDF file.

        Returns:
            PdfDocument: PdfDocument objects.
        """
        markdown = self.parser.convert(
            file_path, file_extension=".pdf"
        ).text_content
        metadata = self._extract_metadata(file_path)
        return PdfDocument(markdown=markdown, metadata=metadata)

    def _extract_metadata(self, file_path: str) -> dict:
        """Extract and process PDF metadata.

        Args:
            reader: PDF reader instance

        Returns:
            dict: Processed metadata dictionary
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


class ContractPDFParser(DefaultPDFParser):
    # Field patterns as class constant
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

    def parse(self, file_path: str) -> PdfDocument:
        """
        Parses the given PDF file and enriches its metadata with additional fields.

        Args:
            file_path (str): Path to the PDF file.

        Returns:
            PdfDocument: Enriched PdfDocument objects.
        """
        markdown = self.parser.convert(
            file_path, file_extension="pdf"
        ).text_content
        markdown = self._preprocess_text(markdown)
        metadata = self._extract_metadata(file_path, text=markdown)
        return PdfDocument(markdown=markdown, metadata=metadata)

    def _extract_metadata(self, file_path: str, text: str) -> dict:
        """Extract and process PDF metadata.

        Args:
            reader: PDF reader instance

        Returns:
            dict: Processed metadata dictionary

        Note:
            Converts date strings to ISO format where possible
        """
        metadata = super()._extract_metadata(file_path)
        metadata.update(self._extract_fields(text, self.FIELDS_TO_EXTRACT))
        return metadata

    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text to clean split labels and values while preserving structure.

        Args:
            text (str): Raw extracted text.

        Returns:
            str: Cleaned and normalized text.
        """
        # Normalize known splits or errors
        text = re.sub(r"Conta\s*ct", "Contact", text)
        text = re.sub(r"Projektl\s*eiter", "Projektleiter", text)
        text = re.sub(r"Proje\s*ct\s*Lead", "Project Lead", text)
        # Join lines where a label is split from its value (without look-behind)
        text = re.sub(
            r"(Client|Kunde|Projektleiter|Project Lead|Gültig bis|Valid until)\s*\n\s*",
            r"\1 ",
            text,
        )
        # Remove excessive spaces
        text = re.sub(r"\s{2,}", " ", text)

        return text

    def _extract_fields(self, text: str, fields_to_extract: List[dict]) -> dict:
        extracted_fields = {}

        for field in fields_to_extract:
            match = re.search(field["search_patterns"], text, re.IGNORECASE)
            if match:
                extracted_fields[field["name"]] = match.group(1).strip()

        # Fallback/default values
        extracted_fields.setdefault("valid_until", "01/01/2024")
        extracted_fields.setdefault("client_name", "Unknown Client")
        extracted_fields.setdefault("offer_name", "Generic Offer")
        extracted_fields.setdefault("project_lead", "Not Assigned")

        return extracted_fields


class PdfReader(BaseReader[PdfDocument]):
    """Reader for extracting content from PDF files.

    Implements document extraction from PDF files with support for
    text and metadata extraction.

    Attributes:
        export_limit: Maximum number of documents to process
        base_path: Root directory containing PDF files
    """

    parsers_mapping: Dict[PDFParser, Any] = {
        PDFParser.DEFAULT: DefaultPDFParser,
        PDFParser.CONTRACT: ContractPDFParser,
    }

    def __init__(self, configuration: PdfDatasourceConfiguration):
        """Initialize PDF reader.

        Args:
            configuration: Settings for PDF processing
        """
        super().__init__()
        self.export_limit = configuration.export_limit
        self.base_path = configuration.base_path
        self.parser = self.parsers_mapping[configuration.parser]()

    def get_all_documents(self) -> List[PdfDocument]:
        documents = []
        pdf_files = [
            f for f in os.listdir(self.base_path) if f.endswith(".pdf")
        ]
        files_to_load = (
            pdf_files
            if self.export_limit is None
            else pdf_files[: self.export_limit]
        )

        for file_name in tqdm(files_to_load, desc="Loading PDFs"):
            file_path = os.path.join(self.base_path, file_name)
            if os.path.isfile(file_path):
                try:
                    parsed_doc = self.parser.parse(file_path)
                    documents.append(parsed_doc)
                except Exception as e:
                    logging.error(f"Failed to load PDF {file_name}: {str(e)}")

        return documents

    async def get_all_documents_async(self) -> List[PdfDocument]:
        """Load documents asynchronously from configured path.

        Returns:
            List[PdfDocument]: Collection of processed documents

        Note:
            Currently calls synchronous implementation
        """
        return self.get_all_documents()
