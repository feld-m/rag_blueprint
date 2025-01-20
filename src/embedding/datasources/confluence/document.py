from markdownify import markdownify as md

from embedding.datasources.core.document import BaseDocument


class ConfluenceDocument(BaseDocument):
    """Document representation for Confluence page content.

    Extends BaseDocument to handle Confluence-specific document processing including
    content extraction, metadata handling, and exclusion configuration.

    Attributes:
        text: Markdown-formatted page content
        attachments: Dictionary of page attachments (placeholder for future)
        metadata: Extracted page metadata including dates, IDs, and URLs
        excluded_embed_metadata_keys: Metadata keys to exclude from embeddings
        excluded_llm_metadata_keys: Metadata keys to exclude from LLM context

    Note:
        Handles conversion of HTML content to markdown and manages metadata
        filtering for both embedding and LLM contexts.
    """

    @classmethod
    def from_page(cls, page: dict, base_url: str) -> "ConfluenceDocument":
        """Create ConfluenceDocument instance from page data.

        Args:
            page: Dictionary containing Confluence page details
            base_url: Base URL of the Confluence instance

        Returns:
            ConfluenceDocument: Configured document instance
        """
        document = cls(
            text=md(page["body"]["view"]["value"]),
            attachments={},  # TBD
            metadata=ConfluenceDocument._get_metadata(page, base_url),
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
    def _get_metadata(page: dict, base_url: str) -> dict:
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
