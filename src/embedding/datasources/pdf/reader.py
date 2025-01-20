import logging
import os
import re
from datetime import datetime
from typing import List

import pypdf
from llama_index.core.readers.file.base import default_file_metadata_func
from llmsherpa.readers import LayoutPDFReader
from tqdm import tqdm

from common.bootstrap.configuration.pipeline.embedding.datasources.datasources_configuration import (
    PdfDatasourceConfiguration,
)
from embedding.datasources.core.reader import BaseReader
from embedding.datasources.pdf.document import PdfDocument


class DefaultPDFParser:
    def parse(self, file_path: str) -> List[PdfDocument]:
        with open(file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            text = "\n\n".join(
                page.extract_text() or "" for page in reader.pages
            )
            metadata = self._extract_metadata(reader)
            return [PdfDocument(text=text, metadata=metadata)]

    def _extract_metadata(self, reader: pypdf.PdfReader) -> dict:
        """Extract and process PDF metadata.

        Args:
            reader: PDF reader instance

        Returns:
            dict: Processed metadata dictionary

        Note:
            Converts date strings to ISO format where possible
        """
        pdf_metadata = reader.metadata
        metadata = {}
        if pdf_metadata is not None:
            for key, value in pdf_metadata.items():
                clean_key = key.strip("/")
                if clean_key in ["CreationDate", "ModDate"]:
                    date_str = value.strip("D:")
                    try:
                        parsed_date = datetime.strptime(
                            date_str[:14], "%Y%m%d%H%M%S"
                        )
                        metadata[clean_key] = parsed_date.isoformat()
                    except ValueError:
                        metadata[clean_key] = value
                else:
                    metadata[clean_key] = value
        return metadata


def preprocess_text(text: str) -> str:
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


class NLMPDFParser:
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

    def __init__(self, api_base: str):
        self.reader = LayoutPDFReader(api_base)

    def parse(self, file_path: str) -> List[PdfDocument]:
        """
        Parses the given PDF file and enriches its metadata with additional fields.

        Args:
            file_path (str): Path to the PDF file.

        Returns:
            List[PdfDocument]: List of enriched PdfDocument objects.
        """
        doc = self.reader.read_pdf(file_path)
        metadata = default_file_metadata_func(file_path)
        additional_metadata = self._extract_page_metadata(file_path)
        documents = []

        for chunk in doc.chunks():
            chunk_metadata = metadata.copy()
            chunk_metadata["page_label"] = chunk.page_idx
            enriched_metadata = {**chunk_metadata, **additional_metadata}
            documents.append(
                PdfDocument(
                    text=chunk.to_context_text(),
                    metadata=enriched_metadata,
                )
            )

        return documents

    def _extract_page_metadata(self, file_path: str) -> dict:
        """Extract metadata from first pages of PDF.

        Args:
            file_path: Path to PDF file

        Returns:
            dict: Extracted metadata fields
        """
        reader = pypdf.PdfReader(file_path)
        text = "".join(page.extract_text() or "" for page in reader.pages[:2])
        text = preprocess_text(text)
        return self._extract_fields(text, self.FIELDS_TO_EXTRACT)

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

    def __init__(self, configuration: PdfDatasourceConfiguration):
        """Initialize PDF reader.

        Args:
            configuration: Settings for PDF processing
        """
        super().__init__()
        self.export_limit = configuration.export_limit
        self.base_path = configuration.base_path

        if configuration.nlm_parser_enabled:
            self.parser = NLMPDFParser(configuration.nlm_parser_api_base)
        else:
            self.parser = DefaultPDFParser()

    def get_all_documents(self) -> List[PdfDocument]:
        documents = []
        files = os.listdir(self.base_path)
        files_to_load = (
            files if self.export_limit is None else files[: self.export_limit]
        )

        for file_name in tqdm(files_to_load, desc="Loading PDFs"):
            file_path = os.path.join(self.base_path, file_name)
            if os.path.isfile(file_path) and file_name.endswith(".pdf"):
                try:
                    parsed_docs = self.parser.parse(file_path)
                    documents.extend(parsed_docs)
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
