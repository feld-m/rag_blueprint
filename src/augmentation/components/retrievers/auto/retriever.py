from typing import Type

from llama_index.core import VectorStoreIndex
from llama_index.core.retrievers import VectorIndexAutoRetriever
from llama_index.core.vector_stores.types import MetadataInfo, VectorStoreInfo

from augmentation.bootstrap.configuration.configuration import (
    AugmentationConfiguration,
)
from augmentation.components.llms.registry import LLMRegistry
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
    ) -> VectorIndexAutoRetriever:
        """
        Creates a VectorIndexAutoRetriever instance based on the provided configuration.

        This method:
        1. Sets up the vector store using the configuration
        2. Initializes the embedding model
        3. Creates a VectorStoreIndex from the vector store and embedding model
        4. Configures the LLM for the retriever
        5. Returns a fully configured VectorIndexAutoRetriever

        Args:
            configuration: AugmentationConfiguration object containing all necessary settings
                          for creating the retriever component

        Returns:
            VectorIndexAutoRetriever: A configured auto-retriever for dynamic query processing
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

        return VectorIndexAutoRetriever(
            index=index,
            similarity_top_k=retriever_configuration.similarity_top_k,
            llm=llm,
            vector_store_info=VectorStoreInfo(
                content_info="Knowledge base of German Bundestag parliamentary documents including speeches, protocols, drucksachen, and proceedings from various legislative periods.",
                metadata_info=[
                    # Date fields (for temporal queries)
                    MetadataInfo(
                        name="created_time",
                        type="str",
                        description=(
                            "Date when the document was created or the parliamentary session occurred. "
                            "Format: YYYY-MM-DD (e.g., '2025-01-29'). Use this for queries about specific dates, "
                            "recent events, or time-based filtering like 'current', 'last session', or 'in 2024'."
                        ),
                    ),
                    MetadataInfo(
                        name="last_edited_time",
                        type="str",
                        description=(
                            "Date of the last edit or update to the document. "
                            "Format: YYYY-MM-DD. Use for finding recently updated documents."
                        ),
                    ),
                    # Legislative period fields (for session queries)
                    MetadataInfo(
                        name="legislature_period",
                        type="str",
                        description=(
                            "The legislative period number (Wahlperiode) as a string, e.g., '20' or '21' (NOT 20 or 21). "
                            "Each period spans approximately 4 years. Period 20: 2021-2025, Period 21: 2025-2029. "
                            "Use string equality comparisons only. Use for queries about specific legislative periods."
                        ),
                    ),
                    MetadataInfo(
                        name="document_number",
                        type="str",
                        description=(
                            "The document identifier in format 'legislature/protocol', e.g., '20/212' or '21/34'. "
                            "For speeches: format is 'legislature/protocol' (e.g., '20/123'). "
                            "For protocols: same as protocol_number field (e.g., '20/212'). "
                            "Use for exact document identification. Do NOT use numeric comparisons - this is a text field."
                        ),
                    ),
                    # Document type fields (for content filtering)
                    MetadataInfo(
                        name="document_type",
                        type="str",
                        description=(
                            "Type of document: 'speech' (individual speech), 'protocol' (full session transcript), "
                            "'drucksache' (printed document), or 'proceeding' (legislative process). "
                            "Use to filter by document type."
                        ),
                    ),
                    MetadataInfo(
                        name="source_client",
                        type="str",
                        description=(
                            "Source of the document: 'bundestag_mine' for individual speeches, "
                            "'dip' for protocols, drucksachen, and proceedings. "
                            "Generally not needed for user queries."
                        ),
                    ),
                    # Speaker information (for person-specific queries)
                    MetadataInfo(
                        name="speaker",
                        type="str",
                        description=(
                            "Full name of the speaker (for speeches only), e.g., 'Friedrich Merz', 'Christian Lindner'. "
                            "Use for queries about specific politicians or speakers."
                        ),
                    ),
                    MetadataInfo(
                        name="speaker_party",
                        type="str",
                        description=(
                            "Political party affiliation of the speaker, e.g., 'CDU', 'SPD', 'FDP', 'Grüne', 'AfD', 'Linke'. "
                            "Use for queries about party positions or statements by party members."
                        ),
                    ),
                    # Topic fields (for content filtering)
                    MetadataInfo(
                        name="agenda_item_number",
                        type="str",
                        description=(
                            "Agenda item number for the topic discussed in a session, e.g., '5a'. "
                            "Use for queries about specific agenda topics."
                        ),
                    ),
                ],
            ),
        )
