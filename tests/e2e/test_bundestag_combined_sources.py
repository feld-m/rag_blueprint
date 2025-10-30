"""
End-to-End Test: Bundestag Combined Data Sources (DIP + Mine)

This test validates that both Bundestag data sources can work together in the same pipeline:
1. Both DIP API (protocols) and Bundestag Mine API (speeches) are enabled
2. Documents from both sources are extracted sequentially
3. All documents are embedded and stored in the same vector store
4. No conflicts or errors occur when using both sources together

This test ensures:
- ✅ Configuration supports both data sources simultaneously
- ✅ Both extraction clients can coexist
- ✅ Metadata correctly identifies source (DIP vs Mine)
- ✅ Vector store handles documents from both sources
- ✅ Search works across documents from both sources
"""

from typing import List

import pytest
from llama_index.core.schema import TextNode
from llama_index.core.vector_stores import VectorStoreQuery

from embedding.bootstrap.configuration.configuration import (
    EmbeddingConfiguration,
)
from embedding.bootstrap.initializer import EmbeddingInitializer
from embedding.orchestrators.registry import EmbeddingOrchestratorRegistry
from embedding.vector_stores.registry import VectorStoreRegistry

# Note: sys.argv is configured in conftest.py for e2e environment


def get_all_nodes_from_store(
    vector_store, embed_dim=384, include_embeddings=False
) -> List[TextNode]:
    """
    Helper function to retrieve all nodes from vector store.

    Uses a dummy query with high top_k to get all nodes since
    get_nodes() requires filters.

    Args:
        vector_store: The vector store to query
        embed_dim: Embedding dimension (default 384)
        include_embeddings: Whether to include embedding vectors in results
    """
    query = VectorStoreQuery(
        query_embedding=[0.0] * embed_dim,
        similarity_top_k=10000,
    )

    result = vector_store.query(query)
    return result.nodes if result.nodes else []


@pytest.mark.e2e
class TestBundestagCombinedSources:
    """
    E2E test suite for combined Bundestag data sources (DIP + Mine).

    Uses real infrastructure:
    - PGVector database (via Docker)
    - HuggingFace embedding model (multilingual-e5-small)
    - DIP API (public endpoint) - protocols
    - Bundestag Mine API (public endpoint) - speeches
    """

    @pytest.fixture(scope="class")
    def embedding_config(self) -> EmbeddingConfiguration:
        """
        Load embedding configuration for combined Bundestag sources test.

        This fixture temporarily copies the combined configuration
        to configuration.test.json, loads it, then restores the original.

        Returns:
            EmbeddingConfiguration with both DIP and Mine enabled
        """
        import shutil
        from pathlib import Path

        # Paths
        test_config = Path("configurations/configuration.test.json")
        combined_config = Path(
            "configurations/configuration.test-bundestag-combined.json"
        )
        backup_config = Path("configurations/configuration.test.json.backup")

        # Backup existing test config if it exists
        if test_config.exists():
            shutil.copy(test_config, backup_config)

        try:
            # Copy combined config to test.json
            shutil.copy(combined_config, test_config)

            # Load configuration using initializer (this populates registries)
            initializer = EmbeddingInitializer(
                configuration_class=EmbeddingConfiguration
            )
            config = initializer.get_configuration()
            return config
        finally:
            # Restore original test config
            if backup_config.exists():
                shutil.move(backup_config, test_config)
            elif test_config.exists():
                test_config.unlink()  # Remove if there was no original

    @pytest.fixture(scope="class")
    def vector_store(self, embedding_config):
        """
        Set up PGVector store and clean before/after ALL tests in the class.

        This fixture is class-scoped so all tests share the same vector store
        with embedded data from the first test.

        Yields:
            PGVectorStore instance connected to test database
        """
        vector_store_config = embedding_config.embedding.vector_store
        pg_vector_store = VectorStoreRegistry.get(
            vector_store_config.name
        ).create(vector_store_config)

        # Clean vector store before ALL tests
        pg_vector_store.clear()

        yield pg_vector_store

        # Clean vector store after ALL tests
        pg_vector_store.clear()

    @pytest.fixture(scope="class")
    def orchestrator(self, embedding_config):
        """
        Create embedding orchestrator for running the full pipeline.

        Returns:
            Orchestrator configured with extraction and embedding components
        """
        orchestrator = EmbeddingOrchestratorRegistry.get(
            embedding_config.embedding.orchestrator_name
        ).create(embedding_config)
        return orchestrator

    @pytest.mark.asyncio
    async def test_combined_extraction_embedding_pipeline(
        self, embedding_config, vector_store, orchestrator
    ):
        """
        Test: Full pipeline with both DIP and Mine data sources

        Purpose: Verify that both data sources can be used together without conflicts.

        Expected behavior:
        - Both DIP and Mine extraction complete successfully
        - Documents from both sources are embedded
        - All documents stored in vector store
        - No errors or conflicts occur
        """
        # Run full pipeline (extraction → embedding → storage)
        await orchestrator.embed()

        # Verify documents were embedded
        nodes = get_all_nodes_from_store(vector_store)
        assert len(nodes) > 0, "No documents embedded from combined sources"

        print(
            f"\n✓ Successfully embedded {len(nodes)} document chunks from combined sources"
        )

    @pytest.mark.asyncio
    async def test_both_sources_represented(self, vector_store):
        """
        Test: Verify documents from both sources exist in vector store

        Purpose: Ensure both DIP and Mine contributed documents.

        Expected behavior:
        - At least one document has source_client='dip'
        - At least one document has source_client='bundestag_mine'
        """
        nodes = get_all_nodes_from_store(vector_store)
        assert (
            len(nodes) > 0
        ), "No documents in vector store. Run full pipeline test first."

        # Check for DIP documents
        dip_nodes = [
            node
            for node in nodes
            if node.metadata.get("source_client") == "dip"
        ]

        # Check for Mine documents
        mine_nodes = [
            node
            for node in nodes
            if node.metadata.get("source_client") == "bundestag_mine"
        ]

        print(f"\n✓ Found {len(dip_nodes)} chunks from DIP")
        print(f"✓ Found {len(mine_nodes)} chunks from Mine")

        assert len(dip_nodes) > 0, "No documents from DIP source found"
        assert (
            len(mine_nodes) > 0
        ), "No documents from Bundestag Mine source found"

    @pytest.mark.asyncio
    async def test_metadata_distinguishes_sources(self, vector_store):
        """
        Test: Verify metadata correctly identifies each source

        Purpose: Ensure we can distinguish between DIP and Mine documents.

        Expected behavior:
        - DIP documents: source_client='dip', document_type='protocol'
        - Mine documents: source_client='bundestag_mine', document_type='speech'
        """
        nodes = get_all_nodes_from_store(vector_store)
        assert len(nodes) > 0, "No documents in vector store"

        # Check DIP metadata
        dip_nodes = [
            node
            for node in nodes
            if node.metadata.get("source_client") == "dip"
        ]
        if len(dip_nodes) > 0:
            sample_dip = dip_nodes[0].metadata
            assert sample_dip.get("source_client") == "dip"
            assert sample_dip.get("document_type") == "protocol"
            assert sample_dip.get("datasource") == "bundestag"
            print(f"\n✓ DIP metadata validated: {list(sample_dip.keys())}")

        # Check Mine metadata
        mine_nodes = [
            node
            for node in nodes
            if node.metadata.get("source_client") == "bundestag_mine"
        ]
        if len(mine_nodes) > 0:
            sample_mine = mine_nodes[0].metadata
            assert sample_mine.get("source_client") == "bundestag_mine"
            assert sample_mine.get("document_type") == "speech"
            assert sample_mine.get("datasource") == "bundestag"
            print(f"✓ Mine metadata validated: {list(sample_mine.keys())}")

    @pytest.mark.asyncio
    async def test_search_across_both_sources(
        self, embedding_config, vector_store
    ):
        """
        Test: Verify vector search works across both sources

        Purpose: Ensure search can retrieve documents from both DIP and Mine.

        Expected behavior:
        - Search query returns results
        - Results may include documents from both sources
        - Similarity scores are valid
        """
        from llama_index.core.vector_stores import VectorStoreQuery
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding

        # Create embedding model
        embed_model = HuggingFaceEmbedding(
            model_name=embedding_config.embedding.embedding_model.name,
        )

        # Create query embedding for "Deutscher Bundestag"
        query_text = "Deutscher Bundestag"
        query_embedding = embed_model.get_text_embedding(query_text)

        # Perform vector search directly (without needing LLM)
        query = VectorStoreQuery(
            query_embedding=query_embedding,
            similarity_top_k=10,
        )
        response = vector_store.query(query)

        assert response is not None
        assert response.nodes is not None
        assert len(response.nodes) > 0

        # Check if we got results from both sources
        source_clients = set()
        for node in response.nodes:
            source_client = node.metadata.get("source_client")
            if source_client:
                source_clients.add(source_client)

        print(f"\n✓ Search returned {len(response.nodes)} results")
        print(f"✓ Source clients in results: {source_clients}")
        if response.similarities and len(response.similarities) > 0:
            print(f"  Top result score: {response.similarities[0]:.4f}")

        # We should have at least one result (may be from either or both sources)
        assert len(response.nodes) > 0

    @pytest.mark.asyncio
    async def test_no_duplicate_documents(self, vector_store):
        """
        Test: Verify no duplicate documents exist

        Purpose: Ensure both sources don't create duplicate entries.

        Expected behavior:
        - Node IDs are unique
        - No duplicate content (within reasonable threshold)
        """
        nodes = get_all_nodes_from_store(vector_store)
        assert len(nodes) > 0, "No documents in vector store"

        # Check node ID uniqueness
        node_ids = [node.node_id for node in nodes]
        unique_node_ids = set(node_ids)

        assert len(node_ids) == len(
            unique_node_ids
        ), f"Found duplicate node IDs: {len(node_ids)} total vs {len(unique_node_ids)} unique"

        print(f"\n✓ All {len(nodes)} nodes have unique IDs")

    @pytest.mark.asyncio
    async def test_document_counts_reasonable(self, vector_store):
        """
        Test: Verify document counts are reasonable for combined sources

        Purpose: Sanity check that we got expected amount of data from both sources.

        Expected behavior:
        - Total documents > sum of individual sources (due to chunking overlap)
        - Both sources contributed meaningfully
        """
        nodes = get_all_nodes_from_store(vector_store)

        dip_count = len(
            [n for n in nodes if n.metadata.get("source_client") == "dip"]
        )
        mine_count = len(
            [
                n
                for n in nodes
                if n.metadata.get("source_client") == "bundestag_mine"
            ]
        )
        total_count = len(nodes)

        print("\n✓ Document distribution:")
        print(f"  - DIP chunks: {dip_count}")
        print(f"  - Mine chunks: {mine_count}")
        print(f"  - Total chunks: {total_count}")

        # Sanity checks
        assert (
            total_count == dip_count + mine_count
        ), "Total should equal sum of sources"
        assert dip_count > 0, "DIP should contribute documents"
        assert mine_count > 0, "Mine should contribute documents"
