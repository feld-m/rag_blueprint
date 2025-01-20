from pydantic import BaseModel, Field

from common.bootstrap.configuration.pipeline.augmentation.augmentation_configuration import (
    AugmentationConfiguration,
)
from common.bootstrap.configuration.pipeline.embedding.embedding_configuration import (
    EmbeddingConfiguration,
)
from common.bootstrap.configuration.pipeline.evaluation.evaluation_configuration import (
    EvaluationConfiguration,
)


class PipelineConfiguration(BaseModel):
    embedding: EmbeddingConfiguration = Field(
        ...,
        description="The embedding pipeline configuration.",
    )
    augmentation: AugmentationConfiguration = Field(
        ...,
        description="The augmentation pipeline configuration.",
    )
    evaluation: EvaluationConfiguration = Field(
        ...,
        description="The evaluation pipeline configuration.",
    )
