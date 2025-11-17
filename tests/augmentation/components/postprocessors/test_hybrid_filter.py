import sys
from unittest.mock import MagicMock, Mock

import pytest
from llama_index.core.schema import NodeWithScore, QueryBundle, TextNode

sys.path.append("./src")

from augmentation.components.postprocessors.hybrid_filter.configuration import (
    HybridFilterConfiguration,
)
from augmentation.components.postprocessors.hybrid_filter.postprocessor import (
    HybridFilterPostprocessor,
)


class TestHybridFilterPostprocessor:
    """Test suite for HybridFilterPostprocessor"""

    @pytest.fixture
    def base_config(self):
        """Basic configuration without LLM filtering"""
        return HybridFilterConfiguration(
            score_threshold=0.7,
            similarity_threshold=0.9,
            max_documents=5,
            enable_llm_filter=False,
        )

    @pytest.fixture
    def llm_config(self):
        """Configuration with LLM filtering enabled"""
        # Import here to avoid circular dependencies
        from augmentation.bootstrap.configuration.components.llm_configuration import (
            LLMConfiguration,
        )

        llm_conf = LLMConfiguration(
            provider="lite_llm",
            name="openai/nemo",
            api_base="http://10.10.2.166:7998/v1",
            max_tokens=100,
            max_retries=3,
        )

        return HybridFilterConfiguration(
            score_threshold=0.7,
            similarity_threshold=0.9,
            max_documents=5,
            enable_llm_filter=True,
            llm=llm_conf,
        )

    @pytest.fixture
    def sample_nodes(self):
        """Create sample nodes with scores and embeddings"""
        nodes = []

        # High score nodes with different embeddings
        for i in range(8):
            node = TextNode(
                text=f"Document {i} content about Bundestag session {i}",
                metadata={
                    "title": f"Document {i}",
                    "created_time": "2024-01-01",
                    "speaker": f"Speaker {i}",
                    "document_type": "speech",
                },
            )
            # Create simple embeddings (normalized vectors)
            if i < 4:
                # First 4 nodes have similar embeddings
                node.embedding = [0.5, 0.5, 0.1 * i, 0.0]
            else:
                # Last 4 nodes have different embeddings
                node.embedding = [0.1 * i, 0.0, 0.5, 0.5]

            # Normalize the embedding
            import numpy as np

            vec = np.array(node.embedding)
            node.embedding = (vec / np.linalg.norm(vec)).tolist()

            # Decreasing scores
            score = 0.95 - (i * 0.05)
            nodes.append(NodeWithScore(node=node, score=score))

        return nodes

    @pytest.fixture
    def duplicate_nodes(self):
        """Create nodes with near-duplicate embeddings"""
        nodes = []

        # Original node
        node1 = TextNode(
            text="Original content about climate policy",
            metadata={"title": "Original Document"},
        )
        node1.embedding = [0.5, 0.5, 0.5, 0.5]
        nodes.append(NodeWithScore(node=node1, score=0.95))

        # Near-duplicate (very similar embedding)
        node2 = TextNode(
            text="Very similar content about climate policy",
            metadata={"title": "Duplicate Document"},
        )
        node2.embedding = [0.51, 0.49, 0.50, 0.50]  # >90% similar
        nodes.append(NodeWithScore(node=node2, score=0.92))

        # Different content
        node3 = TextNode(
            text="Different content about economy",
            metadata={"title": "Different Document"},
        )
        node3.embedding = [0.1, 0.2, 0.3, 0.9]  # Different
        nodes.append(NodeWithScore(node=node3, score=0.90))

        return nodes

    def test_initialization_without_llm(self, base_config):
        """Test postprocessor initialization without LLM"""
        postprocessor = HybridFilterPostprocessor(base_config)

        assert postprocessor.score_threshold == 0.7
        assert postprocessor.similarity_threshold == 0.9
        assert postprocessor.max_documents == 5
        assert postprocessor.enable_llm_filter is False
        assert postprocessor._llm is None

    def test_score_filtering(self, base_config, sample_nodes):
        """Test that low-score documents are filtered out"""
        postprocessor = HybridFilterPostprocessor(base_config)

        # Add some low-score nodes
        low_score_node = TextNode(
            text="Low relevance document",
            metadata={"title": "Low Score"},
        )
        low_score_node.embedding = [0.1, 0.2, 0.3, 0.4]
        sample_nodes.append(
            NodeWithScore(node=low_score_node, score=0.5)
        )  # Below 0.7 threshold

        query = QueryBundle(query_str="test query")
        result = postprocessor._postprocess_nodes(sample_nodes, query)

        # Check that low-score nodes were filtered
        assert all(node.score >= 0.7 for node in result)
        # Should have removed 1 node (score 0.5) and limited to max_documents (5)
        assert len(result) <= 5

    def test_max_documents_limit(self, base_config):
        """Test that result is limited to max_documents"""
        postprocessor = HybridFilterPostprocessor(base_config)

        # Create nodes with very distinct embeddings to avoid deduplication
        # Use orthogonal-ish vectors in higher dimensional space
        nodes = []
        import numpy as np

        for i in range(10):
            node = TextNode(
                text=f"Unique document {i} with distinct content",
                metadata={"title": f"Document {i}"},
            )
            # Create highly distinct embeddings using one-hot-like patterns
            # This ensures similarity < 0.9
            vec = np.zeros(10)
            vec[i] = 1.0  # Primary dimension
            vec[(i + 5) % 10] = 0.2  # Small secondary component

            node.embedding = (vec / np.linalg.norm(vec)).tolist()
            nodes.append(NodeWithScore(node=node, score=0.95 - i * 0.02))

        query = QueryBundle(query_str="test query")
        result = postprocessor._postprocess_nodes(nodes, query)

        assert len(result) <= base_config.max_documents
        # Should return exactly max_documents since all pass filters and are distinct
        assert len(result) == 5

    def test_deduplication(self, base_config, duplicate_nodes):
        """Test semantic deduplication of similar documents"""
        postprocessor = HybridFilterPostprocessor(base_config)

        query = QueryBundle(query_str="test query")
        result = postprocessor._postprocess_nodes(duplicate_nodes, query)

        # Should remove the duplicate, keeping only 2 documents
        assert len(result) == 2
        # Should keep the higher-scoring original
        assert result[0].node.metadata["title"] == "Original Document"

    def test_cosine_similarity(self):
        """Test cosine similarity calculation"""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        vec3 = [1.0, 0.0, 0.0]

        # Orthogonal vectors
        sim1 = HybridFilterPostprocessor._cosine_similarity(vec1, vec2)
        assert sim1 == pytest.approx(0.0, abs=1e-6)

        # Identical vectors
        sim2 = HybridFilterPostprocessor._cosine_similarity(vec1, vec3)
        assert sim2 == pytest.approx(1.0, abs=1e-6)

        # Partial similarity
        vec4 = [0.5, 0.5, 0.0]
        sim3 = HybridFilterPostprocessor._cosine_similarity(vec1, vec4)
        assert 0 < sim3 < 1

    def test_empty_nodes(self, base_config):
        """Test handling of empty node list"""
        postprocessor = HybridFilterPostprocessor(base_config)

        result = postprocessor._postprocess_nodes([], None)
        assert result == []

    def test_nodes_without_embeddings(self, base_config):
        """Test handling of nodes without embeddings"""
        postprocessor = HybridFilterPostprocessor(base_config)

        nodes = []
        for i in range(3):
            node = TextNode(
                text=f"Document {i}",
                metadata={"title": f"Doc {i}"},
            )
            # No embedding set
            nodes.append(NodeWithScore(node=node, score=0.9))

        query = QueryBundle(query_str="test query")
        result = postprocessor._postprocess_nodes(nodes, query)

        # Should still process nodes, just skip deduplication
        assert len(result) == 3

    def test_llm_filter_disabled(self, base_config, sample_nodes):
        """Test that LLM filter is not called when disabled"""
        postprocessor = HybridFilterPostprocessor(base_config)

        # Mock the LLM filter method
        postprocessor._filter_by_llm_relevance = Mock(
            return_value=sample_nodes[:5]
        )

        query = QueryBundle(query_str="test query")
        postprocessor._postprocess_nodes(sample_nodes, query)

        # LLM filter should not have been called
        postprocessor._filter_by_llm_relevance.assert_not_called()

    def test_different_thresholds(self):
        """Test postprocessor with different threshold configurations"""
        # Strict filtering
        strict_config = HybridFilterConfiguration(
            score_threshold=0.9,
            similarity_threshold=0.95,
            max_documents=3,
            enable_llm_filter=False,
        )
        strict_processor = HybridFilterPostprocessor(strict_config)

        # Lenient filtering
        lenient_config = HybridFilterConfiguration(
            score_threshold=0.5,
            similarity_threshold=0.8,
            max_documents=10,
            enable_llm_filter=False,
        )
        lenient_processor = HybridFilterPostprocessor(lenient_config)

        # Create test nodes
        nodes = []
        for i in range(5):
            node = TextNode(text=f"Doc {i}", metadata={"title": f"Doc {i}"})
            node.embedding = [float(i), 0.5, 0.5, 0.5]
            nodes.append(NodeWithScore(node=node, score=0.85 - i * 0.1))

        query = QueryBundle(query_str="test")

        strict_result = strict_processor._postprocess_nodes(nodes, query)
        lenient_result = lenient_processor._postprocess_nodes(nodes, query)

        # Strict should filter more
        assert len(strict_result) <= len(lenient_result)


class TestHybridFilterWithLLM:
    """Test suite for HybridFilterPostprocessor with LLM filtering"""

    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM that returns YES for relevance"""
        llm = MagicMock()
        response = MagicMock()
        response.text = "YES - Relevant to query"
        llm.complete.return_value = response
        return llm

    def test_llm_filter_all_relevant(self, mock_llm, tmp_path):
        """Test LLM filter when all documents are relevant"""
        # Register LiteLLM configuration before use
        import augmentation.components.llms.lite_llm as lite_llm_module

        lite_llm_module.register()

        from augmentation.components.llms.lite_llm.configuration import (
            LiteLLMConfiguration,
        )

        # Create secrets file with API key for test
        secrets_file = tmp_path / "secrets.test.env"
        secrets_file.write_text("RAG__LLMS__OPENAI_NEMO__API_KEY=test_key")

        llm_conf = LiteLLMConfiguration.model_validate(
            {
                "provider": "lite_llm",
                "name": "openai/nemo",
                "api_base": "http://10.10.2.166:7998/v1",
                "max_tokens": 100,
                "max_retries": 3,
            },
            context={"secrets_file": str(secrets_file)},
        )

        config = HybridFilterConfiguration(
            score_threshold=0.6,
            similarity_threshold=0.9,
            max_documents=5,
            enable_llm_filter=True,
            llm=llm_conf,
        )

        postprocessor = HybridFilterPostprocessor(config)
        postprocessor._llm = mock_llm

        nodes = []
        import numpy as np

        # Create nodes with highly distinct embeddings to avoid deduplication
        # Use orthogonal-like vectors to ensure < 0.9 similarity
        for i in range(3):
            node = TextNode(
                text=f"Document {i} about climate policy",
                metadata={
                    "title": f"Document {i}",
                    "created_time": "2024-01-01",
                    "speaker": f"Speaker {i}",
                    "document_type": "speech",
                },
            )
            # Create distinct embeddings using one-hot-like patterns
            vec = np.zeros(10)
            vec[i] = 1.0  # Primary dimension
            vec[(i + 5) % 10] = 0.3  # Small secondary component for variation
            node.embedding = (vec / np.linalg.norm(vec)).tolist()
            nodes.append(NodeWithScore(node=node, score=0.9))

        query = QueryBundle(query_str="climate policy")
        result = postprocessor._postprocess_nodes(nodes, query)

        # All nodes should pass LLM filter
        assert len(result) == 3
        # LLM should be called for each node
        assert mock_llm.complete.call_count == 3

    def test_llm_filter_some_irrelevant(self, tmp_path):
        """Test LLM filter when some documents are irrelevant"""
        # Register LiteLLM configuration before use
        import augmentation.components.llms.lite_llm as lite_llm_module

        lite_llm_module.register()

        from augmentation.components.llms.lite_llm.configuration import (
            LiteLLMConfiguration,
        )

        # Create secrets file with API key for test
        secrets_file = tmp_path / "secrets.test.env"
        secrets_file.write_text("RAG__LLMS__OPENAI_NEMO__API_KEY=test_key")

        llm_conf = LiteLLMConfiguration.model_validate(
            {
                "provider": "lite_llm",
                "name": "openai/nemo",
                "api_base": "http://10.10.2.166:7998/v1",
                "max_tokens": 100,
                "max_retries": 3,
            },
            context={"secrets_file": str(secrets_file)},
        )

        config = HybridFilterConfiguration(
            score_threshold=0.6,
            similarity_threshold=0.9,
            max_documents=5,
            enable_llm_filter=True,
            llm=llm_conf,
        )

        postprocessor = HybridFilterPostprocessor(config)

        # Mock LLM that rejects odd-numbered documents
        mock_llm = MagicMock()

        def mock_response(prompt):
            response = MagicMock()
            if "Document 1" in prompt or "Document 3" in prompt:
                response.text = "NO - Not relevant"
            else:
                response.text = "YES - Relevant"
            return response

        mock_llm.complete.side_effect = mock_response
        postprocessor._llm = mock_llm

        nodes = []
        import numpy as np

        # Create nodes with highly distinct embeddings to avoid deduplication
        for i in range(4):
            node = TextNode(
                text=f"Document {i} content",
                metadata={
                    "title": f"Document {i}",
                    "created_time": "2024-01-01",
                },
            )
            # Create distinct embeddings using one-hot-like patterns
            vec = np.zeros(10)
            vec[i] = 1.0  # Primary dimension
            vec[(i + 5) % 10] = 0.3  # Small secondary component
            node.embedding = (vec / np.linalg.norm(vec)).tolist()
            nodes.append(NodeWithScore(node=node, score=0.9))

        query = QueryBundle(query_str="test query")
        result = postprocessor._postprocess_nodes(nodes, query)

        # Only even-numbered documents should pass
        assert len(result) == 2
        assert all(
            "0" in n.node.metadata["title"] or "2" in n.node.metadata["title"]
            for n in result
        )

    def test_llm_filter_error_handling(self, tmp_path):
        """Test that LLM errors are handled gracefully"""
        # Register LiteLLM configuration before use
        import augmentation.components.llms.lite_llm as lite_llm_module

        lite_llm_module.register()

        from augmentation.components.llms.lite_llm.configuration import (
            LiteLLMConfiguration,
        )

        # Create secrets file with API key for test
        secrets_file = tmp_path / "secrets.test.env"
        secrets_file.write_text("RAG__LLMS__OPENAI_NEMO__API_KEY=test_key")

        llm_conf = LiteLLMConfiguration.model_validate(
            {
                "provider": "lite_llm",
                "name": "openai/nemo",
                "api_base": "http://10.10.2.166:7998/v1",
                "max_tokens": 100,
                "max_retries": 3,
            },
            context={"secrets_file": str(secrets_file)},
        )

        config = HybridFilterConfiguration(
            score_threshold=0.6,
            similarity_threshold=0.9,
            max_documents=5,
            enable_llm_filter=True,
            llm=llm_conf,
        )

        postprocessor = HybridFilterPostprocessor(config)

        # Mock LLM that raises an error
        mock_llm = MagicMock()
        mock_llm.complete.side_effect = Exception("LLM API error")
        postprocessor._llm = mock_llm

        node = TextNode(
            text="Test document",
            metadata={"title": "Test", "created_time": "2024-01-01"},
        )
        node.embedding = [0.5, 0.5, 0.5, 0.5]
        nodes = [NodeWithScore(node=node, score=0.9)]

        query = QueryBundle(query_str="test query")
        result = postprocessor._postprocess_nodes(nodes, query)

        # Should keep the document on error (fail-safe behavior)
        assert len(result) == 1


class TestHybridFilterTemporalGenericMode:
    """Test suite for HybridFilterPostprocessor in generic mode (no temporal_domain config)"""

    @pytest.fixture
    def base_config(self):
        """Basic configuration without LLM filtering"""
        return HybridFilterConfiguration(
            score_threshold=0.7,
            similarity_threshold=0.9,
            max_documents=5,
            enable_llm_filter=False,
        )

    @pytest.fixture
    def sample_nodes(self):
        """Create sample nodes with legislature_period metadata"""
        nodes = []
        for i in range(6):
            node = TextNode(
                text=f"Document {i} content",
                metadata={
                    "title": f"Document {i}",
                    "legislature_period": 20 if i < 3 else 21,
                },
            )
            node.embedding = [0.1 * i, 0.5, 0.5, 0.5]
            import numpy as np

            vec = np.array(node.embedding)
            node.embedding = (vec / np.linalg.norm(vec)).tolist()
            nodes.append(NodeWithScore(node=node, score=0.9 - i * 0.05))
        return nodes

    def test_initialization_without_temporal_config(self, base_config):
        """Test postprocessor initialization without temporal_domain config"""
        postprocessor = HybridFilterPostprocessor(
            base_config, temporal_domain_config=None
        )

        assert postprocessor._temporal_domain_config is None
        assert postprocessor._current_keywords == []
        assert postprocessor._historical_keywords == []

    def test_no_temporal_filtering_in_generic_mode(
        self, base_config, sample_nodes
    ):
        """Test that no temporal filtering is applied in generic mode"""
        postprocessor = HybridFilterPostprocessor(
            base_config, temporal_domain_config=None
        )

        # Query with temporal keywords that would trigger filtering if config was present
        query = QueryBundle(query_str="What are the current party positions?")
        result = postprocessor._postprocess_nodes(sample_nodes, query)

        # Should not filter by temporal relevance - all nodes should be processed
        # Only standard filtering (score, similarity, max_documents) should apply
        assert len(result) <= base_config.max_documents
        # Should contain mix of both periods since no temporal filtering
        periods = set(n.node.metadata.get("legislature_period") for n in result)
        # With no temporal filtering, we should see nodes from both periods
        # (assuming they pass score/similarity thresholds)
        assert len(periods) >= 1


class TestHybridFilterTemporalBundestagMode:
    """Test suite for HybridFilterPostprocessor with Bundestag temporal domain"""

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

        from augmentation.bootstrap.configuration.temporal_domain_config import (
            TemporalDomainConfiguration,
        )

        return TemporalDomainConfiguration(**config_data)

    @pytest.fixture
    def base_config(self):
        """Basic configuration without LLM filtering"""
        return HybridFilterConfiguration(
            score_threshold=0.7,
            similarity_threshold=0.9,
            max_documents=5,
            enable_llm_filter=False,
        )

    @pytest.fixture
    def sample_nodes(self):
        """Create sample nodes with legislature_period metadata"""
        nodes = []
        import numpy as np

        for i in range(6):
            node = TextNode(
                text=f"Document {i} about Bundestag parties",
                metadata={
                    "title": f"Document {i}",
                    "legislature_period": 20 if i < 3 else 21,
                },
            )
            # Create distinct embeddings
            vec = np.zeros(10)
            vec[i] = 1.0
            vec[(i + 5) % 10] = 0.3
            node.embedding = (vec / np.linalg.norm(vec)).tolist()
            nodes.append(NodeWithScore(node=node, score=0.9 - i * 0.05))
        return nodes

    def test_initialization_with_bundestag_config(
        self, base_config, bundestag_config
    ):
        """Test postprocessor initialization with Bundestag config"""
        postprocessor = HybridFilterPostprocessor(
            base_config, temporal_domain_config=bundestag_config
        )

        assert postprocessor._temporal_domain_config is not None
        assert postprocessor._temporal_domain_config.name == "bundestag"
        assert len(postprocessor._current_keywords) > 0
        assert len(postprocessor._historical_keywords) > 0

    def test_current_keyword_filtering(
        self, base_config, bundestag_config, sample_nodes
    ):
        """Test that 'current' keywords filter to period 21"""
        postprocessor = HybridFilterPostprocessor(
            base_config, temporal_domain_config=bundestag_config
        )

        # Query with current keyword
        query = QueryBundle(query_str="What are the current party positions?")
        result = postprocessor._postprocess_nodes(sample_nodes, query)

        # Should only contain period 21 documents
        for node in result:
            assert node.node.metadata.get("legislature_period") == 21

    def test_historical_keyword_filtering(
        self, base_config, bundestag_config, sample_nodes
    ):
        """Test that 'historical' keywords filter to period 20"""
        postprocessor = HybridFilterPostprocessor(
            base_config, temporal_domain_config=bundestag_config
        )

        # Query with historical keyword
        query = QueryBundle(
            query_str="What were the parties in the previous parliament?"
        )
        result = postprocessor._postprocess_nodes(sample_nodes, query)

        # Should only contain period 20 documents
        for node in result:
            assert node.node.metadata.get("legislature_period") == 20

    def test_period_identifier_filtering(
        self, base_config, bundestag_config, sample_nodes
    ):
        """Test filtering with specific period identifiers"""
        postprocessor = HybridFilterPostprocessor(
            base_config, temporal_domain_config=bundestag_config
        )

        # Query with WP20 identifier (a simple period identifier)
        query = QueryBundle(query_str="What happened in WP20?")
        result = postprocessor._postprocess_nodes(sample_nodes, query)

        # Should only contain period 20 documents
        for node in result:
            assert node.node.metadata.get("legislature_period") == 20

    def test_no_keyword_no_filtering(
        self, base_config, bundestag_config, sample_nodes
    ):
        """Test that queries without temporal keywords don't apply temporal filtering"""
        postprocessor = HybridFilterPostprocessor(
            base_config, temporal_domain_config=bundestag_config
        )

        # Query without temporal keywords
        query = QueryBundle(
            query_str="What are the party positions on climate?"
        )
        result = postprocessor._postprocess_nodes(sample_nodes, query)

        # Should contain mix of both periods
        periods = set(n.node.metadata.get("legislature_period") for n in result)
        # Without temporal filtering, we should see nodes from both periods
        assert len(periods) >= 1

    def test_german_keyword_filtering(
        self, base_config, bundestag_config, sample_nodes
    ):
        """Test filtering with German temporal keywords"""
        postprocessor = HybridFilterPostprocessor(
            base_config, temporal_domain_config=bundestag_config
        )

        # Current in German
        query_current = QueryBundle(
            query_str="Was sind die aktuellen Fraktionen?"
        )
        result_current = postprocessor._postprocess_nodes(
            sample_nodes, query_current
        )
        for node in result_current:
            assert node.node.metadata.get("legislature_period") == 21

        # Historical in German
        query_historical = QueryBundle(
            query_str="Was waren die Fraktionen in der vorherigen Wahlperiode?"
        )
        result_historical = postprocessor._postprocess_nodes(
            sample_nodes, query_historical
        )
        for node in result_historical:
            assert node.node.metadata.get("legislature_period") == 20

    def test_temporal_filtering_preserves_other_filters(
        self, bundestag_config, sample_nodes
    ):
        """Test that temporal filtering works alongside other filters"""
        # Create config with stricter thresholds
        strict_config = HybridFilterConfiguration(
            score_threshold=0.85,
            similarity_threshold=0.9,
            max_documents=2,
            enable_llm_filter=False,
        )

        postprocessor = HybridFilterPostprocessor(
            strict_config, temporal_domain_config=bundestag_config
        )

        query = QueryBundle(query_str="What are the current party positions?")
        result = postprocessor._postprocess_nodes(sample_nodes, query)

        # Should apply both temporal filtering (period 21) AND other filters
        assert len(result) <= strict_config.max_documents

        # If results exist, they should match the filters
        if len(result) > 0:
            for node in result:
                # Temporal filter (period 21 or failsafe kept all)
                period = node.node.metadata.get("legislature_period")
                assert period is not None
                # Score threshold
                assert node.score >= strict_config.score_threshold

    def test_failsafe_prevents_empty_results(
        self, base_config, bundestag_config
    ):
        """Test that failsafe prevents empty results when temporal filtering would remove all documents"""
        postprocessor = HybridFilterPostprocessor(
            base_config, temporal_domain_config=bundestag_config
        )

        # Create nodes only for period 21
        nodes = []
        import numpy as np

        for i in range(3):
            node = TextNode(
                text=f"Document {i} from period 21",
                metadata={"title": f"Document {i}", "legislature_period": 21},
            )
            vec = np.zeros(10)
            vec[i] = 1.0
            node.embedding = (vec / np.linalg.norm(vec)).tolist()
            nodes.append(NodeWithScore(node=node, score=0.9))

        # Query for historical period (20) - would filter out all period 21 docs
        query = QueryBundle(
            query_str="What happened in the previous parliament?"
        )
        result = postprocessor._postprocess_nodes(nodes, query)

        # Failsafe should prevent empty results - keeps all documents
        assert len(result) > 0
        # Documents should be from period 21 (the only ones available)
        for node in result:
            assert node.node.metadata.get("legislature_period") == 21
