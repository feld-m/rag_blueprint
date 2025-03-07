from typing import List, Dict, Optional
from datetime import datetime
from llama_index.core.schema import MetadataMode
from embedding.datasources.core.document import BaseDocument


class HackerNewsDocument(BaseDocument):
    """Document representation for Hacker News content."""

    included_embed_metadata_keys: List[str] = [
        "title", "author", "time", "url", "score", "type", "parent", "kids"
    ]
    included_llm_metadata_keys: List[str] = [
        "title", "author", "time", "url", "score", "type", "parent", "kids"
    ]

    def __init__(
            self,
            text: str,
            metadata: Dict,
            id: str,
            type: str,
            title: Optional[str] = None,
            author: Optional[str] = None,
            time: Optional[datetime] = None,
            url: Optional[str] = None,
            score: Optional[int] = None,
            parent: Optional[int] = None,
            kids: Optional[List[int]] = None,
    ):
        super().__init__()
        # Store kids as instance property


        # Add to metadata for embedding/LLM context
        metadata.update({
            "kids": kids,
            "parent": parent
        })

        self.text = text
        self.metadata = {
            "id": id,
            "type": type,
            "title": title,
            "author": author,
            "time": time.isoformat() if time else None,
            "url": url,
            "score": score,
            **metadata
        }
        self._set_excluded_metadata()

    def _set_excluded_metadata(self):
        """Configure metadata filtering based on class settings"""
        self.excluded_embed_metadata_keys = [
            key for key in self.metadata.keys()
            if key not in self.included_embed_metadata_keys
        ]
        self.excluded_llm_metadata_keys = [
            key for key in self.metadata.keys()
            if key not in self.included_llm_metadata_keys
        ]

    def get_content(self, metadata_mode: MetadataMode = MetadataMode.NONE) -> str:
        return self.text or ""

    def get_kids(self) -> Optional[List[int]]:
        return self.metadata.get("kids")