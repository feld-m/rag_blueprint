"""Dynamic temporal retriever that applies filters based on query content."""

import re
from typing import List, Optional, Type

from llama_index.core import VectorStoreIndex
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.core.vector_stores.types import (
    FilterOperator,
    MetadataFilter,
    MetadataFilters,
)

from augmentation.bootstrap.configuration.configuration import (
    AugmentationConfiguration,
)
from augmentation.bootstrap.configuration.temporal_domain_config import (
    TemporalDomainConfiguration,
)
from augmentation.components.retrievers.query_rewriter import QueryRewriter
from core.base_factory import Factory
from core.logger import LoggerConfiguration
from embedding.embedding_models.registry import EmbeddingModelRegistry
from embedding.vector_stores.registry import VectorStoreRegistry


class DynamicTemporalRetriever(BaseRetriever):
    """Retriever that dynamically applies temporal filters based on query.

    Detects temporal keywords in queries and applies appropriate metadata
    filters based on configured temporal domain. If no temporal_domain_config
    is provided, runs in generic mode without temporal filtering.
    """

    def __init__(
        self,
        index: VectorStoreIndex,
        similarity_top_k: int,
        query_rewriter: Optional[QueryRewriter] = None,
        temporal_domain_config: Optional[TemporalDomainConfiguration] = None,
    ):
        """Initialize dynamic temporal retriever.

        Args:
            index: Vector store index
            similarity_top_k: Number of top results to retrieve
            query_rewriter: Optional query rewriter for semantic improvements
            temporal_domain_config: Optional temporal domain configuration.
                If None, runs in generic mode (no temporal filtering).
        """
        super().__init__()
        self._index = index
        self._similarity_top_k = similarity_top_k
        self._temporal_domain_config = temporal_domain_config
        self._query_rewriter = query_rewriter or QueryRewriter(
            temporal_domain_config
        )
        self._logger = LoggerConfiguration.get_logger(__name__)

        # Build keyword lists from config (empty if no config provided)
        if temporal_domain_config:
            self._current_keywords = (
                temporal_domain_config.get_all_current_keywords()
            )
            self._historical_keywords = (
                temporal_domain_config.get_all_historical_keywords()
            )
            self._logger.info(
                f"[DynamicTemporal] Initialized with temporal domain: {temporal_domain_config.name}"
            )
        else:
            self._current_keywords = []
            self._historical_keywords = []
            self._logger.info(
                "[DynamicTemporal] Running in generic mode (no temporal filtering)"
            )

    def _get_temporal_filter_mode(self, query: str) -> str:
        """Determine which temporal filter to apply based on query keywords.

        Uses configured temporal keywords to detect temporal intent.
        If no temporal domain config is provided, always returns "none".

        Args:
            query: User query string

        Returns:
            One of: "historical", "current", "none"
        """
        # If no temporal domain config, no filtering
        if not self._temporal_domain_config:
            return "none"

        query_lower = query.lower()

        # First check for historical keywords - higher priority
        for keyword in self._historical_keywords:
            # Use word boundary matching for keyword detection
            if re.search(
                rf"\b{re.escape(keyword)}\b", query_lower, re.IGNORECASE
            ):
                self._logger.info(
                    f"[DynamicTemporal] Detected historical keyword: '{keyword}' "
                    f"- will filter to period {self._temporal_domain_config.historical_period_value}"
                )
                return "historical"

        # Then check for current/temporal keywords
        for keyword in self._current_keywords:
            if re.search(
                rf"\b{re.escape(keyword)}\b", query_lower, re.IGNORECASE
            ):
                self._logger.info(
                    f"[DynamicTemporal] Detected current keyword: '{keyword}' "
                    f"- will filter to period {self._temporal_domain_config.current_period_value}"
                )
                return "current"

        return "none"

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """Retrieve with dynamic temporal filtering.

        Applies metadata filtering based on configured temporal domain and query keywords.
        If no temporal_domain_config is provided, retrieves without filtering.

        Args:
            query_bundle: Query bundle

        Returns:
            List of nodes with scores
        """
        original_query = query_bundle.query_str

        # Apply query rewriting
        rewritten_query = self._query_rewriter.rewrite(original_query)
        if rewritten_query != original_query:
            query_bundle = QueryBundle(query_str=rewritten_query)

        # Determine which temporal filter to apply
        filter_mode = self._get_temporal_filter_mode(original_query)

        if filter_mode == "current" and self._temporal_domain_config:
            field_name = self._temporal_domain_config.temporal_field_name
            period_value = self._temporal_domain_config.current_period_value

            self._logger.info(
                f"[DynamicTemporal] Applying {field_name}={period_value} filter for current/recent query"
            )
            # Create filter for current period
            temporal_filter = MetadataFilters(
                filters=[
                    MetadataFilter(
                        key=field_name,
                        value=period_value,
                        operator=FilterOperator.EQ,
                    )
                ]
            )
            retriever = self._index.as_retriever(
                similarity_top_k=self._similarity_top_k,
                filters=temporal_filter,
            )

        elif filter_mode == "historical" and self._temporal_domain_config:
            field_name = self._temporal_domain_config.temporal_field_name
            period_value = self._temporal_domain_config.historical_period_value

            self._logger.info(
                f"[DynamicTemporal] Applying {field_name}={period_value} filter for historical/previous query"
            )
            # Create filter for historical period
            temporal_filter = MetadataFilters(
                filters=[
                    MetadataFilter(
                        key=field_name,
                        value=period_value,
                        operator=FilterOperator.EQ,
                    )
                ]
            )
            retriever = self._index.as_retriever(
                similarity_top_k=self._similarity_top_k,
                filters=temporal_filter,
            )

        else:  # filter_mode == "none"
            self._logger.info(
                "[DynamicTemporal] No temporal filtering - searching all documents"
            )
            # No temporal filter - search all documents
            retriever = self._index.as_retriever(
                similarity_top_k=self._similarity_top_k,
            )

        # Retrieve using the configured retriever
        return retriever.retrieve(query_bundle.query_str)

    async def _aretrieve(
        self, query_bundle: QueryBundle
    ) -> List[NodeWithScore]:
        """Async retrieve (delegates to sync)."""
        return self._retrieve(query_bundle)


class DynamicTemporalRetrieverFactory(Factory):
    """Factory for creating dynamic temporal retriever."""

    _configuration_class: Type = AugmentationConfiguration

    @classmethod
    def _create_instance(
        cls, configuration: AugmentationConfiguration
    ) -> BaseRetriever:
        """Create dynamic temporal retriever.

        Args:
            configuration: AugmentationConfiguration

        Returns:
            DynamicTemporalRetriever instance
        """
        vector_store_configuration = configuration.embedding.vector_store
        vector_store = VectorStoreRegistry.get(
            vector_store_configuration.name
        ).create(vector_store_configuration)

        embedding_model_config = configuration.embedding.embedding_model
        embedding_model = EmbeddingModelRegistry.get(
            embedding_model_config.provider
        ).create(embedding_model_config)

        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            embed_model=embedding_model,
        )

        retriever_configuration = (
            configuration.augmentation.chat_engine.retriever
        )

        # Get temporal domain config (may be None for generic mode)
        temporal_domain_config = configuration.augmentation.temporal_domain

        query_rewriter = QueryRewriter(
            temporal_domain_config=temporal_domain_config
        )

        return DynamicTemporalRetriever(
            index=index,
            similarity_top_k=retriever_configuration.similarity_top_k,
            query_rewriter=query_rewriter,
            temporal_domain_config=temporal_domain_config,
        )
