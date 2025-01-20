from injector import inject
from llama_index.core import VectorStoreIndex
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.vector_stores.types import (
    MetadataInfo,
    VectorStore,
    VectorStoreInfo,
)

from common.bootstrap.configuration.pipeline.augmentation.query_engine.retriever.retriever_binding_keys import (
    BoundAutoRetrieverLLM,
)
from common.bootstrap.configuration.pipeline.augmentation.query_engine.retriever.retriever_configuration import (
    AutoRetrieverConfiguration,
    BasicRetrieverConfiguration,
)
from common.bootstrap.configuration.pipeline.embedding.embedding_model.embedding_model_binding_keys import (
    BoundEmbeddingModel,
)
from common.retrievers import CustomVectorIndexAutoRetriever


class BasicRetrieverBuilder:
    """Builder for creating basic vector similarity retrievers.

    Provides factory method to create configured vector retrievers.
    """

    @staticmethod
    @inject
    def build(
        vector_store: VectorStore,
        embedding_model: BoundEmbeddingModel,
        configuration: BasicRetrieverConfiguration,
    ) -> VectorIndexRetriever:
        """Creates a configured vector similarity retriever.

        Args:
            vector_store: Vector storage backend.
            embedding_model: Text embedding model.
            configuration: Basic retriever parameters.

        Returns:
            VectorIndexRetriever: Configured retriever instance.
        """
        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            embed_model=embedding_model,
        )
        return VectorIndexRetriever(
            index=index,
            similarity_top_k=configuration.similarity_top_k,
        )


class AutoRetrieverBuilder:
    """Builder for creating auto-configured retrievers.

    Provides factory method to create retrievers with dynamic configuration.
    """

    @staticmethod
    def build(
        vector_store: VectorStore,
        embedding_model: BoundEmbeddingModel,
        configuration: AutoRetrieverConfiguration,
        llm: BoundAutoRetrieverLLM,
    ) -> CustomVectorIndexAutoRetriever:
        """Creates a configured auto-retriever instance.

        Args:
            vector_store: Vector storage backend.
            embedding_model: Text embedding model.
            configuration: Auto retriever parameters.
            llm: Language model for metadata extraction.

        Returns:
            CustomVectorIndexAutoRetriever: Configured auto-retriever instance.
        """
        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            embed_model=embedding_model,
        )
        return CustomVectorIndexAutoRetriever(
            index=index,
            similarity_top_k=configuration.similarity_top_k,
            llm=llm,
            vector_store_info=VectorStoreInfo(
                content_info="Knowledge base of FELD M company used for retrieval process in RAG system.",
                metadata_info=[
                    MetadataInfo(
                        name="creation_date",
                        type="date",
                        description=(
                            "Date of creation of the chunk's document"
                        ),
                    ),
                    MetadataInfo(
                        name="last_update_date",
                        type="date",
                        description=(
                            "Date of the last update of the chunk's document."
                        ),
                    ),
                ],
            ),
        )
