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
        description="Attachments of the document. Key is the attachment placeholder in raw_content and value is the Attachment object",
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
