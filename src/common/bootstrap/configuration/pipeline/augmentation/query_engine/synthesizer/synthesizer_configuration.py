from enum import Enum
from typing import Literal, Union

from pydantic import BaseModel, Field

from common.bootstrap.configuration.pipeline.augmentation.query_engine.llm_configuration import (
    AVAILABLE_LLMS,
)


# Enums
class SynthesizerName(str, Enum):
    TREE = "tree"


# Configuraiton
class SynthesizerConfiguration(BaseModel):
    name: SynthesizerName = Field(
        ..., description="The name of the synthesizer."
    )
    response_mode: str = Field(
        ..., description="The response mode of the synthesizer."
    )
    llm: AVAILABLE_LLMS = Field(
        ..., description="The language model configuration for the synthesizer."
    )
    streaming: bool = Field(
        True, description="Whether streaming is enabled for the synthesizer."
    )


class TreeSynthesizerConfiguration(SynthesizerConfiguration):
    name: Literal[SynthesizerName.TREE] = Field(
        ..., description="The name of the synthesizer."
    )
    response_mode: str = Field(
        "tree_summarize", description="The response mode of the synthesizer."
    )


AVAILABLE_SYNTHESIZERS = Union[TreeSynthesizerConfiguration]
