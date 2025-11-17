"""Query rewriter for improving retrieval quality on specific query patterns."""

import logging
from typing import Optional

from augmentation.bootstrap.configuration.temporal_domain_config import (
    TemporalDomainConfiguration,
)
from core.logger import LoggerConfiguration


class QueryRewriter:
    """Rewrites queries to improve semantic search retrieval.

    Uses pattern-based detection to selectively expand queries with
    domain-specific terminology. If temporal_domain_config is provided,
    uses configured keywords and expansion terms. Otherwise, performs
    no query rewriting (generic mode).
    """

    def __init__(
        self,
        temporal_domain_config: Optional[TemporalDomainConfiguration] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize the query rewriter.

        Args:
            temporal_domain_config: Optional temporal domain configuration.
                If None, runs in generic mode (no query rewriting).
            logger: Logger instance for logging rewrite operations.
        """
        self._temporal_domain_config = temporal_domain_config
        self._logger = logger or LoggerConfiguration.get_logger(__name__)

        # Build keyword lists from config
        # Lowercase keywords for case-insensitive substring matching
        if temporal_domain_config:
            self._historical_keywords = [
                kw.lower()
                for kw in temporal_domain_config.get_all_historical_keywords()
            ]
            self._current_keywords = [
                kw.lower()
                for kw in temporal_domain_config.get_all_current_keywords()
            ]
            self._logger.info(
                f"[QueryRewriter] Initialized with temporal domain: {temporal_domain_config.name}"
            )
        else:
            self._historical_keywords = []
            self._current_keywords = []
            self._logger.info(
                "[QueryRewriter] Running in generic mode (no query rewriting)"
            )

    def rewrite(self, query: str) -> str:
        """Rewrite query if it matches known patterns.

        Args:
            query: Original user query

        Returns:
            Rewritten query with expansion terms, or original query if no pattern matches
        """
        if not query or not query.strip():
            return query

        # If no temporal domain config, return query unchanged
        if not self._temporal_domain_config:
            return query

        query_lower = query.lower()

        # Pattern 1: Historical queries (previous/past information)
        # Check this FIRST so "parties in previous parliament" gets historical expansion
        if any(keyword in query_lower for keyword in self._historical_keywords):
            return self._expand_historical_query(query, query_lower)

        # Pattern 2: Temporal queries (current/recent information)
        # Check this SECOND so "parties in current parliament" gets temporal expansion
        if any(keyword in query_lower for keyword in self._current_keywords):
            return self._expand_temporal_query(query, query_lower)

        # Pattern 3: Entity queries (if entity_terms expansion is configured)
        # Check for entity-specific expansion terms
        entity_expansion = self._temporal_domain_config.query_expansion.get(
            "entity_terms"
        )
        if entity_expansion:
            # Extract entity keywords from expansion config to use as triggers
            # For Bundestag: checks for "party", "parties", "partei", "fraktion", etc.
            entity_keywords = self._extract_entity_keywords_from_config()
            if any(keyword in query_lower for keyword in entity_keywords):
                return self._expand_entity_query(query, query_lower)

        # No pattern matched - return original query
        self._logger.debug(
            "[QueryRewriter] No pattern matched, returning original query"
        )
        return query

    def _extract_entity_keywords_from_config(self) -> list:
        """Extract entity keywords from config to use as triggers.

        Returns basic entity-related keywords that might trigger entity expansion.

        Returns:
            List of entity trigger keywords
        """
        # Return common parliamentary/entity keywords
        # These are generic enough to work across domains
        return [
            "party",
            "parties",
            "partei",
            "parteien",
            "fraktion",
            "fraktionen",
            "group",
            "groups",
            "faction",
            "factions",
        ]

    def _expand_entity_query(self, query: str, query_lower: str) -> str:
        """Expand entity queries with domain-specific terminology.

        Uses configured entity_terms expansion if available.

        Args:
            query: Original query
            query_lower: Lowercase version for language detection

        Returns:
            Expanded query
        """
        if not self._temporal_domain_config:
            return query

        # Detect language
        language = self._temporal_domain_config.detect_language(query_lower)

        # Get expansion terms
        expansion = self._temporal_domain_config.get_expansion_terms(
            "entity_terms", language
        )

        if not expansion:
            # Fallback to other language if primary not available
            fallback_lang = "de" if language != "de" else "en"
            expansion = self._temporal_domain_config.get_expansion_terms(
                "entity_terms", fallback_lang
            )

        if expansion:
            rewritten = f"{query} {expansion}"
            self._logger.info(
                f"[QueryRewriter] Expanded entity query\n"
                f"  Original: {query[:80]}...\n"
                f"  Rewritten: {rewritten[:120]}..."
            )
            return rewritten

        return query

    def _expand_historical_query(self, query: str, query_lower: str) -> str:
        """Expand historical queries to boost historical period documents.

        Uses configured temporal_historical expansion terms.

        Args:
            query: Original query
            query_lower: Lowercase version for language detection

        Returns:
            Expanded query
        """
        if not self._temporal_domain_config:
            return query

        # Detect language
        language = self._temporal_domain_config.detect_language(query_lower)

        # Get expansion terms
        expansion = self._temporal_domain_config.get_expansion_terms(
            "temporal_historical", language
        )

        if not expansion:
            # Fallback to other language if primary not available
            fallback_lang = "de" if language != "de" else "en"
            expansion = self._temporal_domain_config.get_expansion_terms(
                "temporal_historical", fallback_lang
            )

        # Check if query also mentions entities (for additional entity terms)
        entity_keywords = self._extract_entity_keywords_from_config()
        entity_terms_present = any(
            keyword in query_lower for keyword in entity_keywords
        )

        if entity_terms_present:
            entity_expansion = self._temporal_domain_config.get_expansion_terms(
                "entity_terms", language
            )
            if entity_expansion:
                expansion = f"{expansion} {entity_expansion}"

        if expansion:
            rewritten = f"{query} {expansion}"
            self._logger.info(
                f"[QueryRewriter] Expanded historical query\n"
                f"  Original: {query[:80]}...\n"
                f"  Rewritten: {rewritten[:120]}..."
            )
            return rewritten

        return query

    def _expand_temporal_query(self, query: str, query_lower: str) -> str:
        """Expand temporal queries to boost current period documents.

        Uses configured temporal_current expansion terms.

        Args:
            query: Original query
            query_lower: Lowercase version for language detection

        Returns:
            Expanded query
        """
        if not self._temporal_domain_config:
            return query

        # Detect language
        language = self._temporal_domain_config.detect_language(query_lower)

        # Get expansion terms
        expansion = self._temporal_domain_config.get_expansion_terms(
            "temporal_current", language
        )

        if not expansion:
            # Fallback to other language if primary not available
            fallback_lang = "de" if language != "de" else "en"
            expansion = self._temporal_domain_config.get_expansion_terms(
                "temporal_current", fallback_lang
            )

        if expansion:
            rewritten = f"{query} {expansion}"
            self._logger.info(
                f"[QueryRewriter] Expanded temporal query\n"
                f"  Original: {query[:80]}...\n"
                f"  Rewritten: {rewritten[:120]}..."
            )
            return rewritten

        return query

    def should_rewrite(self, query: str) -> bool:
        """Check if query would be rewritten.

        Useful for testing and debugging.

        Args:
            query: Query to check

        Returns:
            True if query matches a rewrite pattern
        """
        if not query or not self._temporal_domain_config:
            return False

        query_lower = query.lower()

        # Check historical pattern
        if any(keyword in query_lower for keyword in self._historical_keywords):
            return True

        # Check temporal/current pattern
        if any(keyword in query_lower for keyword in self._current_keywords):
            return True

        # Check entity pattern
        entity_keywords = self._extract_entity_keywords_from_config()
        if any(keyword in query_lower for keyword in entity_keywords):
            return True

        return False
