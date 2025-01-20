from typing import List

from pydantic import BaseModel, Field

from common.bootstrap.configuration.pipeline.augmentation.query_engine.postprocessors.postprocessors_configuration import (
    AVAILABLE_POSTPROCESSORS,
)
from common.bootstrap.configuration.pipeline.augmentation.query_engine.retriever.retriever_configuration import (
    AVAILABLE_RETRIEVERS,
)
from common.bootstrap.configuration.pipeline.augmentation.query_engine.synthesizer.synthesizer_configuration import (
    AVAILABLE_SYNTHESIZERS,
)


class QueryEngineConfiguration(BaseModel):
    retriever: AVAILABLE_RETRIEVERS = Field(
        ...,
        description="The retriever configuration for the augmentation pipeline.",
    )
    synthesizer: AVAILABLE_SYNTHESIZERS = Field(
        ..., description="The synthesizer configuration for the query engine."
    )
    postprocessors: List[AVAILABLE_POSTPROCESSORS] = Field(
        ..., description="The list of postprocessors for the synthesizer."
    )
