from pydantic import BaseModel, Field

from common.bootstrap.configuration.pipeline.augmentation.chainlit.chainlit_configuration import (
    ChainlitConfiguration,
)
from common.bootstrap.configuration.pipeline.augmentation.langfuse.langfuse_configuration import (
    LangfuseConfiguration,
)
from common.bootstrap.configuration.pipeline.augmentation.query_engine.query_engine_configuration import (
    QueryEngineConfiguration,
)


class AugmentationConfiguration(BaseModel):
    query_engine: QueryEngineConfiguration = Field(
        ...,
        description="The query engine configuration for the augmentation pipeline.",
    )
    langfuse: LangfuseConfiguration = Field(
        ...,
        description="The Langfuse configuration for the augmentation pipeline.",
    )
    chainlit: ChainlitConfiguration = Field(
        description="The Chainlit configuration for the augmentation pipeline.",
        default_factory=ChainlitConfiguration,
    )
