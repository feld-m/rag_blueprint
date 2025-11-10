"""Query rewriting retriever wrapper that enhances retrieval with query expansion."""

import logging
from typing import List, Optional

from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle

from augmentation.components.retrievers.query_rewriter import QueryRewriter
from core.logger import LoggerConfiguration


class QueryRewritingRetriever(BaseRetriever):
    """Retriever wrapper that applies query rewriting before retrieval.

    This wrapper intercepts queries, applies domain-specific expansions
    to improve semantic search, then delegates to the underlying retriever.
    """

    def __init__(
        self,
        base_retriever: BaseRetriever,
        query_rewriter: Optional[QueryRewriter] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize the query rewriting retriever.

        Args:
            base_retriever: The underlying retriever to delegate to
            query_rewriter: Query rewriter instance (creates default if None)
            logger: Logger instance
        """
        super().__init__()
        self._base_retriever = base_retriever
        self._query_rewriter = query_rewriter or QueryRewriter()
        self._logger = logger or LoggerConfiguration.get_logger(__name__)

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """Retrieve nodes with query rewriting.

        Args:
            query_bundle: Query bundle containing the user query

        Returns:
            List of nodes with scores from the underlying retriever
        """
        original_query = query_bundle.query_str

        # Rewrite query if it matches a pattern
        rewritten_query = self._query_rewriter.rewrite(original_query)

        # If query was rewritten, create new query bundle
        if rewritten_query != original_query:
            self._logger.info(
                f"[QueryRewritingRetriever] Query rewritten\n"
                f"  Original: {original_query[:100]}...\n"
                f"  Rewritten: {rewritten_query[:150]}..."
            )
            query_bundle = QueryBundle(
                query_str=rewritten_query,
                custom_embedding_strs=[rewritten_query],
            )
        else:
            self._logger.debug("[QueryRewritingRetriever] No rewriting applied")

        # Delegate to base retriever
        return self._base_retriever._retrieve(query_bundle)

    async def _aretrieve(
        self, query_bundle: QueryBundle
    ) -> List[NodeWithScore]:
        """Async retrieve (delegates to sync for now)."""
        return self._retrieve(query_bundle)
