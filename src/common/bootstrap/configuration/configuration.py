from pydantic import BaseModel, Field

from common.bootstrap.configuration.metadata.metadata_configuration import (
    ConfigurationMetadata,
)
from common.bootstrap.configuration.pipeline.pipeline_configuration import (
    PipelineConfiguration,
)


class Configuration(BaseModel):
    metadata: ConfigurationMetadata = Field(
        ..., description="The metadata of the configuration."
    )
    pipeline: PipelineConfiguration = Field(
        ..., description="The pipeline configuration."
    )
