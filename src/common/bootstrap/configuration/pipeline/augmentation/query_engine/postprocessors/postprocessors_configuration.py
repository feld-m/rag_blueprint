from enum import Enum
from typing import Literal, Union

from pydantic import BaseModel, Field


# Enums
class PostProcessorName(str, Enum):
    COLBERT_RERANK = "colbert_reranker"


# Configuration
class PostProcessorConfiguration(BaseModel):
    name: PostProcessorName = Field(
        ..., description="The name of the postprocessor."
    )


class ColbertRerankConfiguration(PostProcessorConfiguration):
    class Models(str, Enum):
        COLBERTV2 = "colbert-ir/colbertv2.0"

    class Tokenizers(str, Enum):
        COLBERTV2 = "colbert-ir/colbertv2.0"

    name: Literal[PostProcessorName.COLBERT_RERANK] = Field(
        ..., description="The name of the postprocessor."
    )
    model: Models = Field(
        Models.COLBERTV2, description="Model used for reranking"
    )
    tokenizer: Tokenizers = Field(
        Tokenizers.COLBERTV2, description="Tokenizer used for reranking"
    )
    top_n: int = Field(5, description="Number of documents to be reranked")
    keep_retrieval_score: bool = Field(
        True,
        description="Toggle to keep the retrieval score after the reranking",
    )


AVAILABLE_POSTPROCESSORS = Union[ColbertRerankConfiguration]
