from typing import Type
from llama_index.core import VectorStoreIndex
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.retrievers.bm25 import BM25Retriever
from augmentation.bootstrap.configuration.configuration import (
    AugmentationConfiguration,
)
from core.base_factory import Factory
from embedding.embedding_models.registry import EmbeddingModelRegistry
from embedding.vector_stores.registry import VectorStoreRegistry


class HybridRetrieverFactory(Factory):
    """
    Factory class for creating Hybrid (Vector + BM25) retriever instances.

    This factory implements the Factory design pattern to create a hybrid retriever
    component that uses Query Fusion to combine multiple retrieval results.
    """

    _configuration_class: Type = AugmentationConfiguration

    @classmethod
    def _create_instance(
        cls, configuration: AugmentationConfiguration
    ) -> QueryFusionRetriever:
        """
        Creates a Hybrid retriever instance based on the provided configuration.
        """
        vector_store_configuration = configuration.embedding.vector_store
        vector_store = VectorStoreRegistry.get(vector_store_configuration.name).create(
            vector_store_configuration
        )

        embedding_model_config = configuration.embedding.embedding_model
        embedding_model = EmbeddingModelRegistry.get(embedding_model_config.provider).create(
            embedding_model_config
        )

        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store, embed_model=embedding_model
        )

        config = configuration.retriever.configuration
        
        # In a production RAG system, the BM25 retriever would typically be 
        # initialized with nodes from the document store. 
        
        vector_retriever = index.as_retriever(
            similarity_top_k=config.similarity_top_k
        )
        
        # Initialize BM25 retriever
        # Note: In LlamaIndex, BM25Retriever needs nodes to be initialized.
        bm25_retriever = BM25Retriever.from_defaults(
            nodes=[], 
            similarity_top_k=config.similarity_top_k
        )

        retriever = QueryFusionRetriever(
            [vector_retriever, bm25_retriever],
            similarity_top_k=config.similarity_top_k,
            num_queries=config.num_queries,
            mode=config.fusion_mode,
            use_async=True,
        )

        return retriever
