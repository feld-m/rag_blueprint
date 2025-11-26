import sys
from unittest.mock import MagicMock

import pytest
from llama_index.core import VectorStoreIndex
from llama_index.core.schema import NodeWithScore, QueryBundle, TextNode
from llama_index.core.vector_stores.types import FilterOperator, MetadataFilters

sys.path.append("./src")

from augmentation.bootstrap.configuration.temporal_domain_config import (
    TemporalDomainConfiguration,
)
from augmentation.components.retrievers.dynamic_temporal.retriever import (
    DynamicTemporalRetriever,
)


class TestDynamicTemporalRetrieverGenericMode:
    """Test suite for DynamicTemporalRetriever in generic mode (no temporal_domain config)"""

    @pytest.fixture
    def mock_index(self):
        """Create a mock VectorStoreIndex"""
        return MagicMock(spec=VectorStoreIndex)

    @pytest.fixture
    def sample_nodes(self):
        """Create sample nodes for testing"""
        nodes = []
        for i in range(5):
            node = TextNode(
                text=f"Document {i} content",
                metadata={
                    "title": f"Document {i}",
                    "legislature_period": 20 if i < 3 else 21,
                },
            )
            nodes.append(NodeWithScore(node=node, score=0.9 - i * 0.05))
        return nodes

    def test_initialization_without_config(self, mock_index):
        """Test retriever initialization without temporal_domain config"""
        retriever = DynamicTemporalRetriever(
            index=mock_index,
            similarity_top_k=10,
            temporal_domain_config=None,
        )

        assert retriever._temporal_domain_config is None
        assert retriever._current_keywords == []
        assert retriever._historical_keywords == []
        assert retriever._similarity_top_k == 10

    def test_no_temporal_filtering_in_generic_mode(
        self, mock_index, sample_nodes
    ):
        """Test that no temporal filtering is applied in generic mode"""
        retriever = DynamicTemporalRetriever(
            index=mock_index,
            similarity_top_k=10,
            temporal_domain_config=None,
        )

        # Mock the retriever from index
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = sample_nodes
        mock_index.as_retriever.return_value = mock_retriever

        # Query with temporal keywords that would trigger filtering if config was present
        query = "Show me current legislature documents"
        query_bundle = QueryBundle(query_str=query)

        result = retriever._retrieve(query_bundle)

        # Should call as_retriever WITHOUT filters
        mock_index.as_retriever.assert_called_once_with(
            similarity_top_k=10,
        )
        # Should return all nodes without filtering
        assert len(result) == 5
        assert result == sample_nodes

    def test_keyword_detection_returns_none_without_config(self, mock_index):
        """Test that keyword detection always returns 'none' without config"""
        retriever = DynamicTemporalRetriever(
            index=mock_index,
            similarity_top_k=10,
            temporal_domain_config=None,
        )

        # Test with various temporal keywords
        assert (
            retriever._get_temporal_filter_mode("current legislature") == "none"
        )
        assert (
            retriever._get_temporal_filter_mode("previous parliament") == "none"
        )
        assert retriever._get_temporal_filter_mode("historical data") == "none"
        assert retriever._get_temporal_filter_mode("recent documents") == "none"

    def test_query_rewriter_in_generic_mode(self, mock_index):
        """Test that query rewriter doesn't modify queries in generic mode"""
        retriever = DynamicTemporalRetriever(
            index=mock_index,
            similarity_top_k=10,
            temporal_domain_config=None,
        )

        original_query = "What are the current party positions?"

        # The query rewriter should return the query unchanged
        assert (
            retriever._query_rewriter.rewrite(original_query) == original_query
        )


class TestDynamicTemporalRetrieverBundestagMode:
    """Test suite for DynamicTemporalRetriever with Bundestag temporal domain"""

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
    def mock_index(self):
        """Create a mock VectorStoreIndex"""
        return MagicMock(spec=VectorStoreIndex)

    @pytest.fixture
    def sample_nodes(self):
        """Create sample nodes with Bundestag metadata"""
        nodes = []
        for i in range(5):
            node = TextNode(
                text=f"Bundestag document {i} content",
                metadata={
                    "title": f"Document {i}",
                    "legislature_period": 20 if i < 3 else 21,
                },
            )
            nodes.append(NodeWithScore(node=node, score=0.9 - i * 0.05))
        return nodes

    def test_initialization_with_bundestag_config(
        self, mock_index, bundestag_config
    ):
        """Test retriever initialization with Bundestag config"""
        retriever = DynamicTemporalRetriever(
            index=mock_index,
            similarity_top_k=10,
            temporal_domain_config=bundestag_config,
        )

        assert retriever._temporal_domain_config is not None
        assert retriever._temporal_domain_config.name == "bundestag"
        # Should have loaded keywords
        assert len(retriever._current_keywords) > 0
        assert len(retriever._historical_keywords) > 0
        # Check some expected keywords
        assert "current" in retriever._current_keywords
        assert "aktuell" in retriever._current_keywords
        assert "previous" in retriever._historical_keywords
        assert "vorherig" in retriever._historical_keywords

    def test_current_keyword_detection(self, mock_index, bundestag_config):
        """Test detection of 'current' temporal keywords"""
        retriever = DynamicTemporalRetriever(
            index=mock_index,
            similarity_top_k=10,
            temporal_domain_config=bundestag_config,
        )

        # Test English keywords
        assert (
            retriever._get_temporal_filter_mode("current legislature")
            == "current"
        )
        assert (
            retriever._get_temporal_filter_mode("recent developments")
            == "current"
        )
        assert (
            retriever._get_temporal_filter_mode("latest information")
            == "current"
        )

        # Test German keywords (use exact forms from config)
        assert (
            retriever._get_temporal_filter_mode("aktuell im Bundestag")
            == "current"
        )
        assert (
            retriever._get_temporal_filter_mode("jetzt im Bundestag")
            == "current"
        )

    def test_historical_keyword_detection(self, mock_index, bundestag_config):
        """Test detection of 'historical' temporal keywords"""
        retriever = DynamicTemporalRetriever(
            index=mock_index,
            similarity_top_k=10,
            temporal_domain_config=bundestag_config,
        )

        # Test English keywords
        assert (
            retriever._get_temporal_filter_mode("previous parliament")
            == "historical"
        )
        assert (
            retriever._get_temporal_filter_mode("past legislature")
            == "historical"
        )
        assert (
            retriever._get_temporal_filter_mode("former government")
            == "historical"
        )

        # Test German keywords (use exact forms from config)
        assert (
            retriever._get_temporal_filter_mode("vorherig Wahlperiode")
            == "historical"
        )
        assert (
            retriever._get_temporal_filter_mode("vergangen Regierung")
            == "historical"
        )

        # Test period identifiers
        assert (
            retriever._get_temporal_filter_mode("20. Wahlperiode")
            == "historical"
        )
        assert retriever._get_temporal_filter_mode("WP20") == "historical"

    def test_no_keyword_returns_none(self, mock_index, bundestag_config):
        """Test that queries without temporal keywords return 'none'"""
        retriever = DynamicTemporalRetriever(
            index=mock_index,
            similarity_top_k=10,
            temporal_domain_config=bundestag_config,
        )

        assert (
            retriever._get_temporal_filter_mode("What are the party positions?")
            == "none"
        )
        assert (
            retriever._get_temporal_filter_mode("Tell me about climate policy")
            == "none"
        )

    def test_current_period_filtering(
        self, mock_index, bundestag_config, sample_nodes
    ):
        """Test that 'current' queries apply the correct metadata filter"""
        retriever = DynamicTemporalRetriever(
            index=mock_index,
            similarity_top_k=10,
            temporal_domain_config=bundestag_config,
        )

        # Mock the retriever from index
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = sample_nodes[
            3:
        ]  # Only period 21
        mock_index.as_retriever.return_value = mock_retriever

        query = "What are the current party positions?"
        query_bundle = QueryBundle(query_str=query)

        retriever._retrieve(query_bundle)

        # Should call as_retriever WITH current period filter
        call_args = mock_index.as_retriever.call_args
        assert call_args[1]["similarity_top_k"] == 10

        # Check the filter
        filters = call_args[1]["filters"]
        assert isinstance(filters, MetadataFilters)
        assert len(filters.filters) == 1
        assert filters.filters[0].key == "legislature_period"
        assert filters.filters[0].value == 21
        assert filters.filters[0].operator == FilterOperator.EQ

    def test_historical_period_filtering(
        self, mock_index, bundestag_config, sample_nodes
    ):
        """Test that 'historical' queries apply the correct metadata filter"""
        retriever = DynamicTemporalRetriever(
            index=mock_index,
            similarity_top_k=10,
            temporal_domain_config=bundestag_config,
        )

        # Mock the retriever from index
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = sample_nodes[
            :3
        ]  # Only period 20
        mock_index.as_retriever.return_value = mock_retriever

        query = "What were the parties in the previous parliament?"
        query_bundle = QueryBundle(query_str=query)

        retriever._retrieve(query_bundle)

        # Should call as_retriever WITH historical period filter
        call_args = mock_index.as_retriever.call_args
        assert call_args[1]["similarity_top_k"] == 10

        # Check the filter
        filters = call_args[1]["filters"]
        assert isinstance(filters, MetadataFilters)
        assert len(filters.filters) == 1
        assert filters.filters[0].key == "legislature_period"
        assert filters.filters[0].value == 20
        assert filters.filters[0].operator == FilterOperator.EQ

    def test_no_filtering_without_keywords(
        self, mock_index, bundestag_config, sample_nodes
    ):
        """Test that queries without temporal keywords don't apply filters"""
        retriever = DynamicTemporalRetriever(
            index=mock_index,
            similarity_top_k=10,
            temporal_domain_config=bundestag_config,
        )

        # Mock the retriever from index
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = sample_nodes
        mock_index.as_retriever.return_value = mock_retriever

        query = "What are the party positions on climate?"
        query_bundle = QueryBundle(query_str=query)

        result = retriever._retrieve(query_bundle)

        # Should call as_retriever WITHOUT filters
        mock_index.as_retriever.assert_called_once_with(
            similarity_top_k=10,
        )
        assert result == sample_nodes
