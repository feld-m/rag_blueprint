import logging
from typing import List, Tuple

from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.retrievers import VectorIndexAutoRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.core.vector_stores.types import VectorStoreQuerySpec


class CustomVectorIndexAutoRetriever(VectorIndexAutoRetriever):
    """Extended auto-retriever with Notion metadata fallback handling.

    Extends VectorIndexAutoRetriever to handle missing metadata in Notion documents.
    When no documents are found using creation_date filter, falls back to
    last_update_date to maximize retrieval coverage.

    Attributes:
        retriever: Internal retriever instance for filter manipulation
    """

    def _build_retriever_from_spec(
        self, spec: VectorStoreQuerySpec
    ) -> Tuple[BaseRetriever, QueryBundle]:
        """Builds retriever from vector store query specification.

        Args:
            spec: Query specification including filters and parameters

        Returns:
            Tuple containing:
                - Configured retriever instance
                - Modified query bundle
        """
        retriever, new_query_bundle = super()._build_retriever_from_spec(spec)
        self.retriever = retriever
        return retriever, new_query_bundle

    def _retrieve(
        self,
        query_bundle: QueryBundle,
    ) -> List[NodeWithScore]:
        """Retrieves relevant nodes with metadata fallback strategy.

        Attempts retrieval with creation_date filter first. If no results found,
        falls back to last_update_date filter.

        Args:
            query_bundle: Bundle containing query and additional info

        Returns:
            List[NodeWithScore]: Retrieved nodes with relevance scores
        """
        nodes = super()._retrieve(query_bundle)

        if len(nodes) == 0:
            first_filter = next(iter(self.retriever._filters.filters), None)
            if first_filter and first_filter.key == "creation_date":
                logging.info(
                    f"No nodes found for the given creation date - {first_filter.value}. "
                    "Replacing creation date filter with last update date filter."
                )
                first_filter.key = "last_update_date"
                nodes = self.retriever._retrieve(query_bundle)

        return nodes
