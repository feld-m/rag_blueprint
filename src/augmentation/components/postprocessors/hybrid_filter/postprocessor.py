from typing import Any, List, Optional

import numpy as np
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore, QueryBundle
from pydantic import Field, PrivateAttr

from augmentation.bootstrap.configuration.temporal_domain_config import (
    TemporalDomainConfiguration,
)
from augmentation.components.llms.registry import LLMRegistry
from augmentation.components.postprocessors.hybrid_filter.configuration import (
    HybridFilterConfiguration,
)
from core.logger import LoggerConfiguration


class HybridFilterPostprocessor(BaseNodePostprocessor):
    """
    Multi-stage filtering postprocessor for intelligent document filtering.

    Applies five stages of filtering to retrieved documents:
    1. Score threshold - fast removal of low-similarity documents
    2. Temporal filtering - removes old documents when query mentions current/recent
    3. Semantic deduplication - removes near-duplicate content
    4. LLM relevance check (optional) - verifies semantic relevance to query
    5. Max documents limit - caps final document count

    This approach balances quality and performance by applying cheap filters first,
    then expensive LLM checks only on remaining high-quality candidates.
    """

    score_threshold: float = Field(
        default=0.65, description="Minimum similarity score to keep a document"
    )
    similarity_threshold: float = Field(
        default=0.90,
        description="Threshold for considering documents as duplicates",
    )
    max_documents: int = Field(
        default=8, description="Maximum number of documents to return"
    )
    enable_llm_filter: bool = Field(
        default=False,
        description="Whether to use LLM for final relevance checking",
    )

    _llm: Any = PrivateAttr(default=None)
    _logger: Any = PrivateAttr(default=None)
    _temporal_domain_config: Optional[TemporalDomainConfiguration] = (
        PrivateAttr(default=None)
    )
    _current_keywords: List[str] = PrivateAttr(default_factory=list)
    _historical_keywords: List[str] = PrivateAttr(default_factory=list)

    def __init__(
        self,
        configuration: HybridFilterConfiguration,
        temporal_domain_config: Optional[TemporalDomainConfiguration] = None,
        **kwargs,
    ):
        """
        Initialize the hybrid filter postprocessor.

        Args:
            configuration: Configuration containing filter thresholds and LLM settings
            temporal_domain_config: Optional temporal domain configuration.
                If None, runs without temporal filtering.
        """
        super().__init__(
            score_threshold=configuration.score_threshold,
            similarity_threshold=configuration.similarity_threshold,
            max_documents=configuration.max_documents,
            enable_llm_filter=configuration.enable_llm_filter,
            **kwargs,
        )
        self._logger = LoggerConfiguration.get_logger(__name__)
        self._temporal_domain_config = temporal_domain_config

        # Build keyword lists from config (empty if no config provided)
        # Lowercase keywords for case-insensitive substring matching
        if temporal_domain_config:
            self._current_keywords = [
                kw.lower()
                for kw in temporal_domain_config.get_all_current_keywords()
            ]
            self._historical_keywords = [
                kw.lower()
                for kw in temporal_domain_config.get_all_historical_keywords()
            ]
            self._logger.info(
                f"[HybridFilter] Initialized with temporal domain: {temporal_domain_config.name}"
            )
        else:
            self._current_keywords = []
            self._historical_keywords = []
            self._logger.info(
                "[HybridFilter] Running without temporal filtering (no temporal_domain config)"
            )

        # Initialize LLM if relevance filtering is enabled
        if configuration.enable_llm_filter and configuration.llm:
            self._llm = LLMRegistry.get(configuration.llm.provider).create(
                configuration.llm
            )
            self._logger.info(
                f"LLM relevance filtering enabled with {configuration.llm.provider}/{configuration.llm.name}"
            )

    def _postprocess_nodes(
        self,
        nodes: List[NodeWithScore],
        query_bundle: Optional[QueryBundle] = None,
    ) -> List[NodeWithScore]:
        """
        Apply multi-stage filtering to retrieved nodes.

        Args:
            nodes: List of retrieved nodes with similarity scores
            query_bundle: Optional query information for LLM relevance checking

        Returns:
            List of filtered nodes, max length = max_documents
        """
        if not nodes:
            return nodes

        initial_count = len(nodes)
        self._logger.info(
            f"[HybridFilter] Starting with {initial_count} retrieved documents"
        )

        # Stage 1: Score threshold filtering
        nodes = self._filter_by_score(nodes)

        # Stage 2: Temporal filtering (if query mentions current/recent)
        # Track if we applied historical filtering (WP20-only)
        applied_historical_filter = False
        if query_bundle:
            nodes, applied_historical_filter = (
                self._filter_by_temporal_relevance(
                    nodes, query_bundle.query_str
                )
            )

        # Stage 3: Semantic deduplication
        nodes = self._deduplicate_semantically(nodes)

        # Stage 4: LLM relevance check (optional, expensive)
        # Skip LLM filtering if we already applied strict WP20 metadata filtering
        # since all documents are already from the correct period
        if (
            self.enable_llm_filter
            and self._llm
            and query_bundle
            and not applied_historical_filter
        ):
            nodes = self._filter_by_llm_relevance(nodes, query_bundle.query_str)
        elif applied_historical_filter:
            self._logger.info(
                "[HybridFilter] Skipping LLM filtering - documents already strictly filtered to WP20"
            )

        # Stage 5: Limit to max_documents
        nodes = nodes[: self.max_documents]

        self._logger.info(
            f"[HybridFilter] Final: {len(nodes)}/{initial_count} documents retained"
        )

        return nodes

    def _filter_by_temporal_relevance(
        self, nodes: List[NodeWithScore], query: str
    ) -> tuple[List[NodeWithScore], bool]:
        """
        Stage 2: Filter documents by temporal relevance based on query keywords.

        Uses configured temporal domain to detect temporal intent and filter accordingly.
        If no temporal_domain_config is provided, returns all nodes unchanged.

        Args:
            nodes: List of nodes to filter
            query: User query string

        Returns:
            Tuple of (filtered nodes, bool indicating if historical filter was applied)
        """
        # If no temporal domain config, skip temporal filtering
        if not self._temporal_domain_config:
            self._logger.debug(
                "[HybridFilter] Temporal filtering SKIPPED - no temporal_domain config"
            )
            return nodes, False

        query_lower = query.lower()

        # First check for historical keywords - these trigger historical period filtering
        has_historical_keyword = any(
            keyword in query_lower for keyword in self._historical_keywords
        )

        if has_historical_keyword:
            field_name = self._temporal_domain_config.temporal_field_name
            target_period = str(
                self._temporal_domain_config.historical_period_value
            )

            self._logger.info(
                f"[HybridFilter] Historical filtering ACTIVATED - filtering to {field_name}={target_period} for query: '{query[:80]}'"
            )

            filtered = []
            for node in nodes:
                period = node.node.metadata.get(field_name, "")
                document_number = node.node.metadata.get("document_number", "")

                # Fallback: Try to extract period from document_number if not in metadata field
                if not period and "/" in document_number:
                    period = document_number.split("/")[0]

                # Convert period to string for comparison
                period = str(period) if period else ""

                # Keep only historical period documents
                if period == target_period:
                    filtered.append(node)
                    self._logger.debug(
                        f"[HybridFilter] ✓ KEPT {field_name}={period} doc: {node.node.metadata.get('title', 'Untitled')[:60]}"
                    )
                else:
                    self._logger.debug(
                        f"[HybridFilter] ✗ FILTERED OUT {field_name}={period} doc (keeping {target_period} only)"
                    )

            removed_count = len(nodes) - len(filtered)
            if removed_count > 0:
                self._logger.info(
                    f"[HybridFilter] Historical filtering: removed {removed_count} non-{target_period} documents → {len(filtered)} remaining"
                )

            # If filtering removed everything, fall back to all nodes
            if not filtered:
                self._logger.warning(
                    "[HybridFilter] Historical filtering would remove all documents. Keeping all to avoid empty results."
                )
                return nodes, False

            return (
                filtered,
                True,
            )  # True indicates historical filtering was applied

        # Then check for current/temporal keywords - these trigger current period filtering
        has_temporal_keyword = any(
            keyword in query_lower for keyword in self._current_keywords
        )

        if not has_temporal_keyword:
            self._logger.info(
                f"[HybridFilter] Temporal filtering SKIPPED - no temporal keywords found in query: '{query[:80]}'"
            )
            return nodes, False

        field_name = self._temporal_domain_config.temporal_field_name
        current_period = str(self._temporal_domain_config.current_period_value)

        self._logger.info(
            f"[HybridFilter] Temporal filtering ACTIVATED - filtering to {field_name}={current_period} for query: '{query[:80]}'"
        )

        filtered = []
        for node in nodes:
            period = node.node.metadata.get(field_name, "")
            document_number = node.node.metadata.get("document_number", "")
            title = node.node.metadata.get("title", "Untitled")[:60]

            # Fallback: Try to extract period from document_number if not in metadata field
            if not period and "/" in document_number:
                period = document_number.split("/")[0]

            # Convert period to string for comparison
            period = str(period) if period else ""

            # Log what we found
            self._logger.info(
                f"[HybridFilter]   Doc: '{title}' | {field_name}='{node.node.metadata.get(field_name, '')}' | document_number='{document_number}' | extracted_period='{period}'"
            )

            # Keep if from current period or if period is unknown (empty)
            if period == current_period or period == "":
                filtered.append(node)
                self._logger.info(
                    f"[HybridFilter]     ✓ KEPT (period={period or 'unknown'})"
                )
            else:
                self._logger.info(
                    f"[HybridFilter]     ✗ FILTERED OUT (old period={period})"
                )

        removed_count = len(nodes) - len(filtered)
        if removed_count > 0:
            self._logger.info(
                f"[HybridFilter] Temporal filtering: removed {removed_count} old documents "
                f"(kept {field_name}={current_period} only) → {len(filtered)} remaining"
            )

        # If filtering removed everything, fall back to all nodes
        if not filtered:
            self._logger.warning(
                "[HybridFilter] Temporal filtering would remove all documents. Keeping all to avoid empty results."
            )
            return nodes, False

        return (
            filtered,
            False,
        )  # False - current period filtering, not historical

    def _filter_by_score(
        self, nodes: List[NodeWithScore]
    ) -> List[NodeWithScore]:
        """
        Stage 1: Remove documents below similarity threshold.

        Fast and cheap - eliminates clearly irrelevant docs based on vector similarity.

        Args:
            nodes: List of nodes with scores

        Returns:
            Filtered list of nodes above threshold
        """
        filtered = [n for n in nodes if n.score >= self.score_threshold]

        removed_count = len(nodes) - len(filtered)
        self._logger.info(
            f"[HybridFilter] Score filtering: removed {removed_count} docs "
            f"(threshold: {self.score_threshold:.2f}) → {len(filtered)} remaining"
        )

        if removed_count > 0 and self._logger.isEnabledFor(10):  # DEBUG level
            for node in nodes:
                if node.score < self.score_threshold:
                    title = node.node.metadata.get("title", "Untitled")[:60]
                    self._logger.debug(
                        f"  Filtered out (score={node.score:.3f}): {title}"
                    )

        return filtered

    def _deduplicate_semantically(
        self, nodes: List[NodeWithScore]
    ) -> List[NodeWithScore]:
        """
        Stage 2: Remove near-duplicate documents using embedding similarity.

        Common in Bundestag where multiple speeches discuss the same topic.
        Keeps highest-scoring doc from each semantic cluster.

        Args:
            nodes: List of nodes to deduplicate

        Returns:
            Deduplicated list of nodes
        """
        if len(nodes) <= 1:
            return nodes

        kept_nodes = []
        skip_indices = set()

        for i, node_i in enumerate(nodes):
            if i in skip_indices:
                continue

            # Check if similar to any already kept node
            is_duplicate = False
            for kept_node in kept_nodes:
                if self._are_nodes_similar(node_i, kept_node):
                    is_duplicate = True
                    if self._logger.isEnabledFor(10):  # DEBUG level
                        title_i = node_i.node.metadata.get("title", "Untitled")[
                            :60
                        ]
                        title_kept = kept_node.node.metadata.get(
                            "title", "Untitled"
                        )[:60]
                        self._logger.debug(
                            f"  Duplicate detected: '{title_i}' similar to '{title_kept}'"
                        )
                    break

            if not is_duplicate:
                kept_nodes.append(node_i)

                # Mark similar subsequent docs as duplicates
                for j in range(i + 1, len(nodes)):
                    if j not in skip_indices:
                        node_j = nodes[j]
                        if self._are_nodes_similar(node_i, node_j):
                            skip_indices.add(j)

        removed_count = len(nodes) - len(kept_nodes)
        self._logger.info(
            f"[HybridFilter] Deduplication: removed {removed_count} duplicates "
            f"(threshold: {self.similarity_threshold:.2f}) → {len(kept_nodes)} remaining"
        )

        return kept_nodes

    def _are_nodes_similar(
        self, node1: NodeWithScore, node2: NodeWithScore
    ) -> bool:
        """
        Check if two nodes are semantically similar based on embeddings.

        Args:
            node1: First node
            node2: Second node

        Returns:
            True if similarity >= similarity_threshold, False otherwise
        """
        # Use embeddings if available
        if (
            hasattr(node1.node, "embedding")
            and hasattr(node2.node, "embedding")
            and node1.node.embedding is not None
            and node2.node.embedding is not None
        ):
            similarity = self._cosine_similarity(
                node1.node.embedding, node2.node.embedding
            )
            return similarity >= self.similarity_threshold

        return False

    def _filter_by_llm_relevance(
        self, nodes: List[NodeWithScore], query: str
    ) -> List[NodeWithScore]:
        """
        Stage 3: Use LLM to check if each document actually helps answer the query.

        Most accurate but expensive - only use after cheaper filters.
        Only checks remaining documents (typically 3-6 after deduplication).

        Args:
            nodes: List of nodes to check
            query: User query string

        Returns:
            List of nodes deemed relevant by LLM
        """
        if not self._llm:
            return nodes

        relevant_nodes = []
        checked_count = 0

        for node in nodes:
            checked_count += 1

            # Extract metadata for context
            title = node.node.metadata.get("title", "N/A")
            date = node.node.metadata.get("created_time", "N/A")
            speaker = node.node.metadata.get("speaker", "N/A")
            doc_type = node.node.metadata.get("document_type", "N/A")

            # Use more text for better relevance judgment (1500 chars instead of 500)
            text_excerpt = node.node.text[:1500]

            prompt = f"""You are a lenient relevance filter for a German Bundestag document retrieval system.
Your job is to filter out ONLY clearly irrelevant documents. When in doubt, keep the document.

User Query: {query}

Document Information:
- Title: {title}
- Date: {date}
- Speaker: {speaker}
- Type: {doc_type}
- Similarity Score: {node.score:.3f} (already pre-filtered by semantic search)

Document Excerpt (first 1500 characters):
{text_excerpt}

Task: This document was already retrieved by semantic search with score {node.score:.3f}.
Only reject it if it's CLEARLY and OBVIOUSLY irrelevant to the query.
If the document might contain ANY useful information for answering the query, keep it.

Reply with ONLY "YES" (keep) or "NO" (reject) followed by a brief reason (max 10 words).

Format: YES/NO - <reason>
"""

            try:
                response = self._llm.complete(prompt)
                response_text = response.text.strip().upper()

                is_relevant = response_text.startswith("YES")

                if is_relevant:
                    relevant_nodes.append(node)
                    self._logger.info(
                        f"[HybridFilter] LLM kept ({checked_count}/{len(nodes)}): {title[:60]}"
                    )
                else:
                    self._logger.info(
                        f"[HybridFilter] LLM rejected ({checked_count}/{len(nodes)}): {title[:60]} - {response_text[:80]}"
                    )

            except Exception as e:
                self._logger.warning(
                    f"[HybridFilter] LLM check failed for document: {e}. Keeping document."
                )
                relevant_nodes.append(node)  # Keep on error to avoid data loss

        removed_count = len(nodes) - len(relevant_nodes)
        self._logger.info(
            f"[HybridFilter] LLM filtering: removed {removed_count} irrelevant docs → {len(relevant_nodes)} remaining"
        )

        return relevant_nodes

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First embedding vector
            vec2: Second embedding vector

        Returns:
            Cosine similarity score (0-1)
        """
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)

        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))
