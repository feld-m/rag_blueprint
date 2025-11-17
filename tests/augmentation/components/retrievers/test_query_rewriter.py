import sys

import pytest

sys.path.append("./src")

from augmentation.bootstrap.configuration.temporal_domain_config import (
    TemporalDomainConfiguration,
)
from augmentation.components.retrievers.query_rewriter import QueryRewriter


class TestQueryRewriterGenericMode:
    """Test suite for QueryRewriter in generic mode (no temporal_domain config)"""

    @pytest.fixture
    def rewriter(self):
        """Create a QueryRewriter without temporal_domain config"""
        return QueryRewriter(temporal_domain_config=None)

    def test_initialization_without_config(self, rewriter):
        """Test rewriter initialization without temporal_domain config"""
        assert rewriter._temporal_domain_config is None
        assert rewriter._current_keywords == []
        assert rewriter._historical_keywords == []

    def test_no_rewriting_in_generic_mode(self, rewriter):
        """Test that queries are returned unchanged in generic mode"""
        test_queries = [
            "What are the current party positions?",
            "Show me previous parliament members",
            "Tell me about climate policy",
            "aktuelle Fraktionen im Bundestag",
            "vorherige Wahlperiode",
        ]

        for query in test_queries:
            assert rewriter.rewrite(query) == query

    def test_empty_query_handling(self, rewriter):
        """Test handling of empty or whitespace queries"""
        assert rewriter.rewrite("") == ""
        assert rewriter.rewrite("   ") == "   "
        assert rewriter.rewrite(None) is None


class TestQueryRewriterBundestagMode:
    """Test suite for QueryRewriter with Bundestag temporal domain"""

    @pytest.fixture
    def bundestag_config(self):
        """Load Bundestag temporal domain configuration"""
        import json
        from pathlib import Path

        config_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "configurations"
            / "temporal_domains"
            / "bundestag.json"
        )
        with open(config_path) as f:
            config_data = json.load(f)
        return TemporalDomainConfiguration(**config_data)

    @pytest.fixture
    def rewriter(self, bundestag_config):
        """Create a QueryRewriter with Bundestag config"""
        return QueryRewriter(temporal_domain_config=bundestag_config)

    def test_initialization_with_bundestag_config(
        self, rewriter, bundestag_config
    ):
        """Test rewriter initialization with Bundestag config"""
        assert rewriter._temporal_domain_config is not None
        assert rewriter._temporal_domain_config.name == "bundestag"
        assert len(rewriter._current_keywords) > 0
        assert len(rewriter._historical_keywords) > 0

    def test_current_query_expansion_german(self, rewriter):
        """Test query expansion for current/temporal queries in German"""
        query = "Wer sind die aktuellen Fraktionen?"
        rewritten = rewriter.rewrite(query)

        # Should contain the original query
        assert query in rewritten
        # Should contain expansion terms
        assert "21. Wahlperiode" in rewritten or "2025" in rewritten

    def test_current_query_expansion_english(self, rewriter):
        """Test query expansion for current/temporal queries in English"""
        query = "What are the current parties?"
        rewritten = rewriter.rewrite(query)

        # Should contain the original query
        assert query in rewritten
        # Should contain expansion terms
        assert "21st legislature" in rewritten or "2025" in rewritten

    def test_historical_query_expansion_german(self, rewriter):
        """Test query expansion for historical queries in German"""
        query = "Wer waren die Fraktionen in der vorherigen Wahlperiode?"
        rewritten = rewriter.rewrite(query)

        # Should contain the original query
        assert query in rewritten
        # Should contain expansion terms
        assert "20. Wahlperiode" in rewritten or "2021" in rewritten

    def test_historical_query_expansion_english(self, rewriter):
        """Test query expansion for historical queries in English"""
        query = "What were the parties in the previous parliament?"
        rewritten = rewriter.rewrite(query)

        # Should contain the original query
        assert query in rewritten
        # Should contain expansion terms
        assert "20th legislature" in rewritten or "2021" in rewritten

    def test_period_identifier_expansion(self, rewriter):
        """Test that period identifiers like WP20 trigger expansion"""
        # Period identifiers like "WP20" are in the historical keywords
        query = "Was passierte in WP20?"
        rewritten = rewriter.rewrite(query)

        # Should contain the original query
        assert query in rewritten
        # Should contain historical expansion terms
        assert len(rewritten) > len(query)  # Query should be expanded

    def test_entity_query_expansion(self, rewriter):
        """Test query expansion for entity-related queries"""
        # When query has both temporal and entity keywords, temporal takes precedence
        query = "Welche Fraktionen gibt es aktuell?"
        rewritten = rewriter.rewrite(query)

        # Should contain original query
        assert query in rewritten
        # Should contain temporal expansion (temporal keywords take precedence)
        assert "21. Wahlperiode" in rewritten or "2025" in rewritten

        # Test pure entity query (without temporal keywords)
        entity_query = "Welche Fraktionen gibt es?"
        entity_rewritten = rewriter.rewrite(entity_query)
        # Should contain entity expansion
        assert len(entity_rewritten) > len(entity_query)

    def test_no_expansion_for_neutral_queries(self, rewriter):
        """Test that queries without temporal keywords are not expanded"""
        query = "What is climate policy?"
        rewritten = rewriter.rewrite(query)

        # Should return query unchanged
        assert rewritten == query

    def test_empty_query_handling(self, rewriter):
        """Test handling of empty or whitespace queries"""
        assert rewriter.rewrite("") == ""
        assert rewriter.rewrite("   ") == "   "
        assert rewriter.rewrite(None) is None

    def test_language_detection(self, rewriter):
        """Test that language detection works correctly"""
        # German query should get German expansion
        german_query = "Was sind die aktuellen Fraktionen?"
        german_rewritten = rewriter.rewrite(german_query)
        assert "21. Wahlperiode" in german_rewritten

        # English query should get English expansion
        english_query = "What are the current fractions?"
        english_rewritten = rewriter.rewrite(english_query)
        assert "21st legislature" in english_rewritten

    def test_case_insensitive_keyword_matching(self, rewriter):
        """Test that keyword matching is case-insensitive"""
        # Uppercase should work
        query_upper = "CURRENT parliament"
        rewritten_upper = rewriter.rewrite(query_upper)
        assert len(rewritten_upper) > len(query_upper)

        # Mixed case should work
        query_mixed = "CuRrEnT parliament"
        rewritten_mixed = rewriter.rewrite(query_mixed)
        assert len(rewritten_mixed) > len(query_mixed)

    def test_multiple_temporal_keywords(self, rewriter):
        """Test that historical keywords take precedence over current"""
        # Query with both current and historical keywords
        # Historical should take precedence
        query = "How did the current topic change from the previous period?"
        rewritten = rewriter.rewrite(query)

        # Should apply historical expansion (contains "previous")
        assert "20th legislature" in rewritten or "20. Wahlperiode" in rewritten
