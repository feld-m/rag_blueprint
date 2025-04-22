from typing import Dict, List, Optional, TypeVar

from llama_index.core import Document
from pydantic import Field

DocType = TypeVar("DocType", bound=Document)


class BaseDocument(Document):
    """Base document class for structured content storage.

    Extends LlamaIndex Document to add support for attachments and
    metadata filtering for embedding and LLM contexts.

    Attributes:
        attachments: Dictionary mapping placeholder keys to attachment content
        included_embed_metadata_keys: Metadata fields to include in embeddings
        included_llm_metadata_keys: Metadata fields to include in LLM context

    Note:
        DocType TypeVar ensures type safety when implementing document types.
        Default metadata includes title and timestamp information.
    """

    attachments: Optional[Dict[str, str]] = Field(
        description="Document attachments with placeholders as keys and content as values",
        default=None,
    )

    included_embed_metadata_keys: List[str] = [
        "title",
        "created_time",
        "last_edited_time",
    ]

    included_llm_metadata_keys: List[str] = [
        "title",
        "created_time",
        "last_edited_time",
    ]

    def __init__(self, text: str, metadata: dict, attachments: dict = None):
        """Initialize a document with text, metadata, and optional attachments.

        Sets up excluded metadata keys for embedding and LLM contexts.
        """
        super().__init__(text=text, metadata=metadata)
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
        """Identify metadata keys to exclude from processing.

        Returns all keys from metadata that aren't in the included_keys list.
        """
        return [key for key in metadata.keys() if key not in included_keys]
