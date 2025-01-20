from enum import Enum

from pydantic import BaseModel, Field


# Enums
class SplittingName(str, Enum):
    BASIC = "basic"


# Configuration
class SplittingConfiguration(BaseModel):
    name: SplittingName = Field(
        ..., description="The name of the splitting configuration."
    )
    chunk_overlap_in_tokens: int = Field(
        ..., description="The number of tokens that overlap between chunks."
    )
    chunk_size_in_tokens: int = Field(
        ..., description="The size of each chunk in tokens."
    )
