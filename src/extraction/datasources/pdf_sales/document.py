from typing import List

from extraction.datasources.core.document import BaseDocument


class PDFSalesDocument(BaseDocument):
    """
    Represents a PDF sales document with text and metadata.
    This class extends the BaseDocument class and includes additional metadata
    specific to PDF sales documents.
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
