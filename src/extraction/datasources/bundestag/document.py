from typing import List

from extraction.datasources.core.document import BaseDocument


class BundestagMineDocument(BaseDocument):
    """
    Represents a document from the Bundestag datasource.

    Supports multiple data sources:
    - BundestagMine: Individual speeches with speaker information
    - DIP API: Comprehensive parliamentary documents (protocols, drucksachen, proceedings)

    Inherits from BaseDocument and includes additional metadata specific to Bundestag documents.
    """

    included_embed_metadata_keys: List[str] = [
        "title",
        "created_time",
        "last_edited_time",
        "speaker_party",
        "speaker",
        "protocol_number",
        "legislature_period",
        "document_type",
        "document_number",
        "document_subtype",
        "agenda_item_number",
        "source_client",
        "publisher",
        "document_art",
        "document_id",
    ]

    included_llm_metadata_keys: List[str] = [
        "title",
        "created_time",
        "last_edited_time",
        "speaker_party",
        "speaker",
        "protocol_number",
        "legislature_period",
        "document_type",
        "document_number",
        "document_subtype",
        "agenda_item_number",
        "source_client",
        "publisher",
        "document_art",
        "document_id",
        "distribution_date",
        "xml_url",
        "related_proceedings_count",
    ]
