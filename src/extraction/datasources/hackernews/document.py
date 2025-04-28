#create document class for HackerNews
from extraction.datasources.core.document import BaseDocument
class HackerNewsDocument(BaseDocument):
    """Document representation for Hacker News content.

    Extends BaseDocument to handle Hacker News-specific document processing including
    metadata handling and filtering for embeddings and LLM contexts.
    """

    pass