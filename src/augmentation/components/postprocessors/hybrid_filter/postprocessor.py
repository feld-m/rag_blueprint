from typing import Any, List, Optional

import numpy as np
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore, QueryBundle
from pydantic import Field, PrivateAttr

from augmentation.components.llms.registry import LLMRegistry
from augmentation.components.postprocessors.hybrid_filter.configuration import (
    HybridFilterConfiguration,
)
from core.logger import LoggerConfiguration


class HybridFilterPostprocessor(BaseNodePostprocessor):
    """
    Multi-stage filtering postprocessor for intelligent document filtering.

    Applies three stages of filtering to retrieved documents:
    1. Score threshold - fast removal of low-similarity documents
    2. Semantic deduplication - removes near-duplicate content
    3. LLM relevance check (optional) - verifies semantic relevance to query

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

    def __init__(self, configuration: HybridFilterConfiguration, **kwargs):
        """
        Initialize the hybrid filter postprocessor.

        Args:
            configuration: Configuration containing filter thresholds and LLM settings
        """
        super().__init__(
            score_threshold=configuration.score_threshold,
            similarity_threshold=configuration.similarity_threshold,
            max_documents=configuration.max_documents,
            enable_llm_filter=configuration.enable_llm_filter,
            **kwargs,
        )
        self._logger = LoggerConfiguration.get_logger(__name__)

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

        # Stage 2: Semantic deduplication
        nodes = self._deduplicate_semantically(nodes)

        # Stage 3: LLM relevance check (optional, expensive)
        if self.enable_llm_filter and self._llm and query_bundle:
            nodes = self._filter_by_llm_relevance(nodes, query_bundle.query_str)

        # Stage 4: Limit to max_documents
        nodes = nodes[: self.max_documents]

        self._logger.info(
            f"[HybridFilter] Final: {len(nodes)}/{initial_count} documents retained"
        )

        return nodes

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
