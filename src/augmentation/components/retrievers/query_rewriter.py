"""Query rewriter for improving retrieval quality on specific query patterns."""

import logging
from typing import Optional

from core.logger import LoggerConfiguration


class QueryRewriter:
    """Rewrites queries to improve semantic search retrieval.

    Uses pattern-based detection to selectively expand queries with
    domain-specific terminology that appears in target documents.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the query rewriter.

        Args:
            logger: Logger instance for logging rewrite operations.
        """
        self._logger = logger or LoggerConfiguration.get_logger(__name__)

    def rewrite(self, query: str) -> str:
        """Rewrite query if it matches known patterns.

        Args:
            query: Original user query

        Returns:
            Rewritten query with expansion terms, or original query if no pattern matches
        """
        if not query or not query.strip():
            return query

        query_lower = query.lower()

        # Pattern 1: Party/Fraction composition queries
        # Triggers: Questions about parties, fractions, parliamentary groups
        # Goal: Add German parliamentary terminology that appears in procedural documents
        party_keywords = [
            "party",
            "parties",  # English
            "partei",
            "parteien",  # German: party/parties
            "fraktion",
            "fraktionen",  # German: fraction/fractions
        ]

        if any(keyword in query_lower for keyword in party_keywords):
            return self._expand_party_query(query, query_lower)

        # Pattern 2: Temporal queries (current/recent information)
        # Triggers: Questions with "current", "latest", "recent", etc.
        # Goal: Boost period 21 documents in semantic search
        temporal_keywords = [
            "current",
            "recent",
            "latest",
            "today",
            "now",
            "this year",
            "aktuell",
            "jetzt",
            "neueste",
            "derzeitig",
            "gegenwärtig",
            "dieses jahr",
            "momentan",
        ]

        if any(keyword in query_lower for keyword in temporal_keywords):
            return self._expand_temporal_query(query, query_lower)

        # No pattern matched - return original query
        self._logger.debug(
            "[QueryRewriter] No pattern matched, returning original query"
        )
        return query

    def _expand_party_query(self, query: str, query_lower: str) -> str:
        """Expand party/fraction queries with parliamentary terminology.

        Adds generic parliamentary terms that appear in documents listing fractions,
        without hardcoding specific party names to avoid temporal bias.

        Args:
            query: Original query
            query_lower: Lowercase version for language detection

        Returns:
            Expanded query
        """
        # Detect language based on German-specific words
        german_indicators = ["welche", "alle", "partei", "im", "gibt", "sind"]
        is_german = any(
            indicator in query_lower for indicator in german_indicators
        )

        if is_german:
            # German parliamentary terms that appear in procedural documents
            # These are generic terms, not specific party names
            expansion = "Fraktionen Bundestag Bundestagsfraktionen parlamentarische Gruppen Wahlperiode"
        else:
            # English + key German terms (documents are in German)
            expansion = "Fraktionen Bundestag parliamentary fractions parliamentary groups Wahlperiode"

        rewritten = f"{query} {expansion}"

        self._logger.info(
            f"[QueryRewriter] Expanded party query\n"
            f"  Original: {query[:80]}...\n"
            f"  Rewritten: {rewritten[:120]}..."
        )

        return rewritten

    def _expand_temporal_query(self, query: str, query_lower: str) -> str:
        """Expand temporal queries to boost period 21 documents.

        Adds terms that appear in recent period 21 documents to improve
        semantic matching for "current" information queries.

        Args:
            query: Original query
            query_lower: Lowercase version for language detection

        Returns:
            Expanded query
        """
        # Detect language based on German-specific words
        german_indicators = [
            "wer",
            "was",
            "welche",
            "der",
            "die",
            "das",
            "ist",
            "sind",
        ]
        is_german = any(
            indicator in query_lower for indicator in german_indicators
        )

        if is_german:
            # German terms that boost period 21 (2025 parliament)
            # Include period identifier and recent year
            expansion = "21. Wahlperiode 2025 aktuelle Bundesregierung neueste"
        else:
            # English + German terms (documents are in German)
            expansion = "21st legislature 2025 21. Wahlperiode current government latest"

        rewritten = f"{query} {expansion}"

        self._logger.info(
            f"[QueryRewriter] Expanded temporal query\n"
            f"  Original: {query[:80]}...\n"
            f"  Rewritten: {rewritten[:120]}..."
        )

        return rewritten

    def should_rewrite(self, query: str) -> bool:
        """Check if query would be rewritten.

        Useful for testing and debugging.

        Args:
            query: Query to check

        Returns:
            True if query matches a rewrite pattern
        """
        if not query:
            return False

        query_lower = query.lower()

        # Check party pattern
        party_keywords = [
            "party",
            "parties",
            "partei",
            "parteien",
            "fraktion",
            "fraktionen",
        ]
        if any(keyword in query_lower for keyword in party_keywords):
            return True

        # Check temporal pattern
        temporal_keywords = [
            "current",
            "recent",
            "latest",
            "today",
            "now",
            "this year",
            "aktuell",
            "jetzt",
            "neueste",
            "derzeitig",
            "gegenwärtig",
            "dieses jahr",
            "momentan",
        ]
        if any(keyword in query_lower for keyword in temporal_keywords):
            return True

        return False
