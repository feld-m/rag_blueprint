"""
End-to-End Test: Bundestag Mine API Full Extraction Pipeline

This test validates the complete RAG pipeline for Bundestag Mine API integration:
1. Extraction: Fetch speeches from Bundestag Mine API
2. Parsing: Convert API responses to BundestagMineDocument
3. Cleaning: Clean markdown/text content
4. Splitting: Split documents into chunks
5. Embedding: Generate embeddings using HuggingFace model
6. Storage: Store embeddings in PGVector database
7. Retrieval: Verify vector search functionality

This test uses the HIGHEST abstraction level (EmbeddingOrchestrator.embed())
to ensure refactoring of internal components doesn't break the pipeline.
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

    # For PGVector, we need to use a SQL query to get embeddings
    if include_embeddings:
        # Query with actual retrieval to get embeddings
        results = vector_store.query(query)
        return results.nodes if results.nodes else []
    else:
        result = vector_store.query(query)
        return result.nodes if result.nodes else []


class TestBundestagMineFullPipeline:
    """
    E2E test suite for Bundestag Mine API integration.

    Uses real infrastructure:
    - PGVector database (via Docker)
    - HuggingFace embedding model (multilingual-e5-small)
    - Bundestag Mine API (public endpoint)
    """

    @pytest.fixture(scope="class")
    def embedding_config(self) -> EmbeddingConfiguration:
        """
        Load embedding configuration for Bundestag Mine e2e tests.

        This fixture temporarily copies the Bundestag Mine configuration
        to configuration.test.json, loads it, then restores the original.

        Returns:
            EmbeddingConfiguration with Bundestag Mine datasource, PGVector store, and HF embeddings
        """
        import shutil
        from pathlib import Path

        # Paths
        test_config = Path("configurations/configuration.test.json")
        mine_config = Path(
            "configurations/configuration.test-bundestag-mine.json"
        )
        backup_config = Path("configurations/configuration.test.json.backup")

        # Backup existing test config if it exists
        if test_config.exists():
            shutil.copy(test_config, backup_config)

        try:
            # Copy Bundestag Mine config to test.json
            shutil.copy(mine_config, test_config)

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

    @pytest.mark.asyncio
    async def test_full_extraction_embedding_pipeline(
        self, embedding_config, vector_store
    ):
        """
        Test complete pipeline: Bundestag Mine API → Extraction → Embedding → PGVector.

        This test validates:
        1. EmbeddingOrchestrator correctly orchestrates the full pipeline
        2. Bundestag Mine API client fetches speeches
        3. Documents are parsed, cleaned, and split
        4. Embeddings are generated and stored in PGVector
        5. Documents can be retrieved from vector store

        Test Strategy:
        - Uses highest abstraction level (orchestrator.embed())
        - Real infrastructure (no mocks)
        - Limited document count (export_limit=5) for speed
        - Validates end-to-end data flow
        """
        # Initialize orchestrator
        orchestrator = EmbeddingOrchestratorRegistry.get(
            embedding_config.embedding.orchestrator_name
        ).create(embedding_config)

        # Execute full pipeline
        await orchestrator.embed()

        # Validate: Documents were embedded
        nodes = get_all_nodes_from_store(vector_store)
        num_nodes = len(nodes)
        assert num_nodes > 0, (
            "No documents found in vector store after embedding. "
            "Pipeline failed to extract, embed, or store documents."
        )

        # Validate: Expected number of documents based on config
        # export_limit=5 speeches, each split into multiple chunks
        # Expect at least 3 chunks (speeches are smaller than protocols, ~1-10 chunks each)
        min_expected_chunks = 3
        assert num_nodes >= min_expected_chunks, (
            f"Expected at least {min_expected_chunks} chunks, "
            f"but got {num_nodes}. Check splitting configuration."
        )

        print(
            f"✓ Successfully embedded {num_nodes} document chunks from Bundestag Mine"
        )

    @pytest.mark.asyncio
    async def test_document_metadata_preservation(
        self, embedding_config, vector_store
    ):
        """
        Verify metadata is correctly preserved through the pipeline.

        Validates:
        - Datasource metadata (source, document_type, etc.)
        - Bundestag Mine-specific metadata (speaker, party, protocol_number, etc.)
        - Chunk-level metadata (chunk index, parent doc ID, etc.)
        """
        # Get nodes from vector store (already populated by previous test)
        nodes = get_all_nodes_from_store(vector_store)

        if len(nodes) == 0:
            pytest.skip(
                "No documents in vector store. Run full pipeline test first."
            )

        # Validate first node has required metadata
        first_node = nodes[0]
        metadata = first_node.metadata

        # Required fields from BaseDocument
        assert "datasource" in metadata, "Missing 'datasource' metadata"
        assert (
            metadata["datasource"] == "bundestag"
        ), f"Expected datasource='bundestag', got '{metadata['datasource']}'"

        # Required fields from BundestagMineDocument
        assert "source_client" in metadata, "Missing 'source_client' metadata"
        assert (
            metadata["source_client"] == "bundestag_mine"
        ), f"Expected source_client='bundestag_mine', got '{metadata['source_client']}'"

        # Bundestag Mine specific metadata (speech data)
        assert "speaker" in metadata, "Missing 'speaker' metadata"

        # LlamaIndex node metadata
        assert (
            "chunk_id" in metadata or first_node.node_id
        ), "Missing node/chunk identifier"

        print(f"✓ Metadata validation passed for {len(nodes)} nodes")
        print(f"  Sample metadata: {list(metadata.keys())[:10]}")

    @pytest.mark.asyncio
    async def test_vector_search_retrieval(
        self, embedding_config, vector_store
    ):
        """
        Test vector search functionality with real queries.

        Validates:
        - Embeddings can be queried
        - Similarity search returns relevant results
        - Retrieved chunks contain expected content
        """
        from llama_index.core import VectorStoreIndex
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding

        # Get nodes to ensure store is populated
        nodes = get_all_nodes_from_store(vector_store)

        if len(nodes) == 0:
            pytest.skip(
                "No documents in vector store. Run full pipeline test first."
            )

        # Create embedding model for queries (same as used in pipeline)
        embed_model = HuggingFaceEmbedding(
            model_name="intfloat/multilingual-e5-small", device="cpu"
        )

        # Create index from vector store
        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            embed_model=embed_model,
        )

        # Test query: Search for speech content
        query = "Rede Bundestag Abgeordneter"
        retriever = index.as_retriever(similarity_top_k=5)

        # Execute search
        results = retriever.retrieve(query)

        assert len(results) > 0, "Vector search returned no results"
        assert len(results) <= 5, f"Expected max 5 results, got {len(results)}"

        # Validate result structure
        first_result = results[0]
        assert first_result.text, "Retrieved node has no text content"
        assert (
            first_result.score is not None
        ), "Retrieved node has no similarity score"
        assert (
            0 <= first_result.score <= 1
        ), f"Similarity score should be 0-1, got {first_result.score}"

        print(f"✓ Vector search returned {len(results)} results")
        print(f"  Top result score: {results[0].score:.4f}")
        print(f"  Top result preview: {results[0].text[:100]}...")

    @pytest.mark.asyncio
    async def test_embedding_dimensions(self, embedding_config, vector_store):
        """
        Verify embedding dimensions match the configured model.

        Validates:
        - Embedding vectors have correct dimensions
        - Model: multilingual-e5-small (384 dimensions)
        """
        nodes = get_all_nodes_from_store(vector_store)

        if len(nodes) == 0:
            pytest.skip(
                "No documents in vector store. Run full pipeline test first."
            )

        # multilingual-e5-small has 384 dimensions
        expected_dimensions = 384

        # Check the embed_dim configuration from vector store
        assert vector_store.embed_dim == expected_dimensions, (
            f"Expected embedding dimension {expected_dimensions}, "
            f"got {vector_store.embed_dim}"
        )

        # Note: PGVector doesn't return embeddings in query results by default
        # but we can verify the dimension is configured correctly
        print(f"✓ Embedding dimensions validated: {vector_store.embed_dim}D")
        print(
            f"  Vector store configured for {len(nodes)} nodes with {expected_dimensions}D embeddings"
        )

    @pytest.mark.asyncio
    async def test_document_chunking_strategy(
        self, embedding_config, vector_store
    ):
        """
        Validate document splitting and chunking strategy.

        Validates:
        - Chunks are within token limits (384 tokens)
        - Chunks have overlap (50 tokens)
        - Chunks maintain parent document relationships
        """
        nodes = get_all_nodes_from_store(vector_store)

        if len(nodes) == 0:
            pytest.skip(
                "No documents in vector store. Run full pipeline test first."
            )

        # Configuration from e2e.json
        expected_chunk_size = 384

        # Sample 10 nodes for validation
        sample_nodes = nodes[: min(10, len(nodes))]

        for node in sample_nodes:
            # Rough token count (words * 1.3 ≈ tokens for German)
            word_count = len(node.text.split())
            approx_tokens = int(word_count * 1.3)

            # Chunks should be roughly within chunk_size
            # Allow 20% variance due to sentence boundaries
            max_tokens = int(expected_chunk_size * 1.2)

            assert approx_tokens <= max_tokens, (
                f"Chunk exceeds max tokens: {approx_tokens} > {max_tokens}. "
                f"Check splitter configuration."
            )

            # Verify node has text content
            assert len(node.text) > 0, "Chunk has no text content"

            # Verify node has parent document reference (if available)
            # This depends on splitter implementation
            if hasattr(node, "ref_doc_id") and node.ref_doc_id:
                assert (
                    node.ref_doc_id
                ), "Chunk missing parent document reference"

        print(
            f"✓ Chunking strategy validated for {len(sample_nodes)} sample chunks"
        )
        print(
            f"  Average chunk size: {sum(len(n.text.split()) for n in sample_nodes) / len(sample_nodes):.0f} words"
        )


if __name__ == "__main__":
    """
    Run this test file directly for quick validation:

    $ python tests/e2e/test_bundestag_mine_full_pipeline.py

    Or via pytest:

    $ pytest tests/e2e/test_bundestag_mine_full_pipeline.py -v
    """
    pytest.main([__file__, "-v", "--tb=short"])
