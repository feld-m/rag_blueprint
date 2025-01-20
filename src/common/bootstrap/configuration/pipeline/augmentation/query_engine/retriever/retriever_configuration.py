from enum import Enum
from typing import Literal, Union

from pydantic import BaseModel, Field

from common.bootstrap.configuration.pipeline.augmentation.query_engine.llm_configuration import (
    AVAILABLE_LLMS,
)


# Enums
class RetrieverName(str, Enum):
    BASIC = "basic"
    AUTO_RETRIEVER = "auto_retriever"


# Configuration
class RetrieverConfiguration(BaseModel):
    name: RetrieverName = Field(..., description="The name of the retriever.")
    similarity_top_k: int = Field(
        ..., description="The number of top similar items to retrieve."
    )


class BasicRetrieverConfiguration(RetrieverConfiguration):
    name: Literal[RetrieverName.BASIC] = Field(
        ..., description="The name of the retriever."
    )


class AutoRetrieverConfiguration(RetrieverConfiguration):
    name: Literal[RetrieverName.AUTO_RETRIEVER] = Field(
        ..., description="The name of the retriever."
    )
    llm: AVAILABLE_LLMS = Field(
        ...,
        description="The LLM configuration used to extract metadata from the query.",
    )


AVAILABLE_RETRIEVERS = Union[
    BasicRetrieverConfiguration, AutoRetrieverConfiguration
]
