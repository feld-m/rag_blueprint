from typing import List

from embedding.datasources.core.document import BaseDocument


class PdfDocument(BaseDocument):
    """Document representation for PDF file content.

    Extends BaseDocument to handle PDF-specific document processing including
    metadata filtering for embeddings and LLM contexts.

    Attributes:
        included_embed_metadata_keys: Metadata keys to include in embeddings
        included_llm_metadata_keys: Metadata keys to include in LLM context
        text: Document content in text format
        metadata: Extracted PDF metadata
        attachments: Dictionary of document attachments
        excluded_embed_metadata_keys: Metadata keys to exclude from embeddings
        excluded_llm_metadata_keys: Metadata keys to exclude from LLM context
    """

    included_embed_metadata_keys: List[str] = [
        "Title",
        "CreationDate",
        "ModDate",
        "creation_date",
        "client_name",
        "offer_name",
        "project_lead",
    ]
    included_llm_metadata_keys: List[str] = [
        "Title",
        "CreationDate",
        "ModDate",
        "creation_date",
        "client_name",
        "offer_name",
        "project_lead",
    ]

    def __init__(self, text: str, metadata: dict, attachments: dict = None):
        """Initialize PDF document.

        Args:
            text: Extracted text content
            metadata: PDF metadata dictionary
            attachments: Optional dictionary of attachments
        """
        super().__init__()
        self.text = text
        self.metadata = metadata
        self.attachments = attachments or {}
        self.excluded_embed_metadata_keys = self._set_excluded_metadata_keys(
            self.metadata, self.included_embed_metadata_keys
        )
        self.excluded_llm_metadata_keys = self._set_excluded_metadata_keys(
            self.metadata, self.included_llm_metadata_keys
        )

    @staticmethod
    def _set_excluded_metadata_keys(
        metadata: dict, included_keys: List[str]
    ) -> List[str]:
        """Determine metadata keys to exclude from processing.

        Args:
            metadata: Complete metadata dictionary
            included_keys: Keys to include in processing

        Returns:
            List[str]: Keys that should be excluded

        Note:
            Returns any key from metadata that isn't in included_keys
        """
        return [key for key in metadata.keys() if key not in included_keys]
