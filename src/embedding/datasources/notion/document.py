from enum import Enum

from embedding.datasources.core.document import BaseDocument


class NotionDocument(BaseDocument):
    """Document representation for Notion page content.

    Extends BaseDocument to handle Notion-specific document processing including
    metadata handling and filtering for embeddings and LLM contexts.

    Attributes:
        attachments: Dictionary of document attachments
        text: Document content in markdown format
        metadata: Extracted page metadata including dates and source info
        excluded_embed_metadata_keys: Metadata keys to exclude from embeddings
        excluded_llm_metadata_keys: Metadata keys to exclude from LLM context
    """

    class Type(str, Enum):
        PAGE = "page"
        DATABASE = "database"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._set_excluded_embed_metadata_keys()
        self._set_excluded_llm_metadata_keys()

    def _set_excluded_embed_metadata_keys(self) -> None:
        """Configure metadata keys to exclude from embeddings.

        Identifies metadata keys not explicitly included in embedding
        processing and marks them for exclusion.
        """
        metadata_keys = self.metadata.keys()
        self.excluded_embed_metadata_keys = [
            key
            for key in metadata_keys
            if key not in self.included_embed_metadata_keys
        ]

    def _set_excluded_llm_metadata_keys(self) -> None:
        """Configure metadata keys to exclude from LLM context.

        Identifies metadata keys not explicitly included in LLM
        processing and marks them for exclusion.
        """
        metadata_keys = self.metadata.keys()
        self.excluded_llm_metadata_keys = [
            key
            for key in metadata_keys
            if key not in self.included_llm_metadata_keys
        ]
