from typing import Type

from llama_index.core import VectorStoreIndex
from llama_index.core.retrievers import BaseRetriever, VectorIndexAutoRetriever
from llama_index.core.vector_stores.types import VectorStoreInfo

from augmentation.bootstrap.configuration.configuration import (
    AugmentationConfiguration,
)
from augmentation.components.llms.registry import LLMRegistry
from augmentation.components.retrievers.query_rewriter import QueryRewriter
from augmentation.components.retrievers.query_rewriting_retriever import (
    QueryRewritingRetriever,
)
from core.base_factory import Factory
from embedding.embedding_models.registry import EmbeddingModelRegistry
from embedding.vector_stores.registry import VectorStoreRegistry


class AutoRetrieverFactory(Factory):
    """
    Factory class for creating VectorIndexAutoRetriever instances.

    This factory builds auto-retriever components that utilize LLMs to dynamically
    construct queries for vector store retrieval based on user inputs.

    Attributes:
        _configuration_class: The configuration class for the auto retriever.
    """

    _configuration_class: Type = AugmentationConfiguration

    @classmethod
    def _create_instance(
        cls, configuration: AugmentationConfiguration
    ) -> BaseRetriever:
        """
        Creates a VectorIndexAutoRetriever wrapped with query rewriting.

        This method:
        1. Sets up the vector store using the configuration
        2. Initializes the embedding model
        3. Creates a VectorStoreIndex from the vector store and embedding model
        4. Configures the LLM for the retriever
        5. Wraps the retriever with query rewriting for improved retrieval
        6. Returns a fully configured retriever with query rewriting

        Args:
            configuration: AugmentationConfiguration object containing all necessary settings
                          for creating the retriever component

        Returns:
            BaseRetriever: A query-rewriting retriever wrapping the auto-retriever
        """
        vector_store_configuration = configuration.embedding.vector_store
        vector_store = VectorStoreRegistry.get(
            vector_store_configuration.name
        ).create(vector_store_configuration)
        embedding_model_config = configuration.embedding.embedding_model
        embedding_model = EmbeddingModelRegistry.get(
            embedding_model_config.provider
        ).create(embedding_model_config)
        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            embed_model=embedding_model,
        )
        retriever_configuration = (
            configuration.augmentation.chat_engine.retriever
        )
        llm = LLMRegistry.get(retriever_configuration.llm.provider).create(
            retriever_configuration.llm
        )

        base_retriever = VectorIndexAutoRetriever(
            index=index,
            similarity_top_k=retriever_configuration.similarity_top_k,
            llm=llm,
            vector_store_info=VectorStoreInfo(
                content_info="Knowledge base containing documents for retrieval process in RAG system.",
                metadata_info=[
                    # No metadata filters defined - rely purely on semantic search.
                    # Metadata filters often become overly specific and eliminate all results,
                    # especially with temporal queries where exact dates may not exist in the DB.
                    # The LLM also tends to hallucinate dates or infer temporal relationships
                    # from context (e.g., applying date from question 1 to question 2).
                    # Semantic search with embeddings is generally more effective for finding
                    # relevant documents than strict metadata filtering.
                ],
            ),
        )

        # Wrap with query rewriting for improved retrieval on specific query patterns
        query_rewriter = QueryRewriter()
        return QueryRewritingRetriever(
            base_retriever=base_retriever, query_rewriter=query_rewriter
        )
