from typing import List

from pydantic import BaseModel, Field

from common.bootstrap.configuration.pipeline.embedding.datasources.datasources_configuration import (
    AVAIALBLE_DATASOURCES,
)
from common.bootstrap.configuration.pipeline.embedding.embedding_model.embedding_model_configuration import (
    AVAILABLE_EMBEDDING_MODELS,
)
from common.bootstrap.configuration.pipeline.embedding.vector_store.vector_store_configuration import (
    AVAILABLE_VECTOR_STORES,
)


class EmbeddingConfiguration(BaseModel):
    datasources: List[AVAIALBLE_DATASOURCES] = Field(
        ..., description="The list of data sources for the embedding pipeline."
    )
    embedding_model: AVAILABLE_EMBEDDING_MODELS = Field(
        ..., description="The embedding model configuration."
    )
    vector_store: AVAILABLE_VECTOR_STORES = Field(
        ..., description="The vector store configuration."
    )
