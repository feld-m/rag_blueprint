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

    @classmethod
    def from_page(cls, metadata: dict, text: str) -> "NotionDocument":
        """Create NotionDocument instance from page data.

        Args:
            metadata: Dictionary containing page metadata
            text: Extracted page content

        Returns:
            NotionDocument: Configured document instance
        """
        document = cls(
            attachments={},
            text=text,
            metadata=NotionDocument._get_metadata(metadata),
        )
        document._set_excluded_embed_metadata_keys()
        document._set_excluded_llm_metadata_keys()
        return document

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

    @staticmethod
    def _get_metadata(metadata: dict) -> dict:
        """Process and enhance page metadata.

        Args:
            metadata: Raw page metadata dictionary

        Returns:
            dict: Enhanced metadata including source and formatted dates
        """
        metadata["datasource"] = "notion"
        metadata["created_date"] = metadata["created_time"].split("T")[0]
        metadata["last_edited_date"] = metadata["last_edited_time"].split("T")[
            0
        ]
        return metadata
