from pydantic import BaseModel, Field

from common.bootstrap.configuration.pipeline.augmentation.query_engine.llm_configuration import (
    AVAILABLE_LLMS,
)
from common.bootstrap.configuration.pipeline.embedding.embedding_model.embedding_model_configuration import (
    AVAILABLE_EMBEDDING_MODELS,
)


class EvaluationConfiguration(BaseModel):
    judge_llm: AVAILABLE_LLMS = Field(
        ...,
        description="The judge language model configuration for the evaluation pipeline.",
    )
    judge_embedding_model: AVAILABLE_EMBEDDING_MODELS = Field(
        ...,
        description="The judge embedding model configuration for the evaluation pipeline.",
    )
