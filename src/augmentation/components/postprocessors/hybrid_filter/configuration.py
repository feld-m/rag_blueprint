from typing import Any, Literal, Optional

from pydantic import Field, ValidationInfo, field_validator

from augmentation.bootstrap.configuration.components.llm_configuration import (
    LLMConfiguration,
    LLMConfigurationRegistry,
)
from augmentation.bootstrap.configuration.components.postprocessors_configuration import (
    PostProcessorConfiguration,
    PostProcessorName,
)


class HybridFilterConfiguration(PostProcessorConfiguration):
    """
    Configuration for the Hybrid Filter postprocessor.

    This postprocessor implements multi-stage filtering:
    1. Score threshold - removes low-similarity documents
    2. Semantic deduplication - removes near-duplicate content
    3. LLM relevance check (optional) - verifies semantic relevance
    """

    name: Literal[PostProcessorName.HYBRID_FILTER] = Field(
        default=PostProcessorName.HYBRID_FILTER,
        description="Name of the postprocessor (hybrid_filter)",
    )

    score_threshold: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
        description=(
            "Minimum similarity score to keep a document (0-1). "
            "Documents below this threshold are filtered out. "
            "Typical values: 0.6-0.7 for strict filtering, 0.5-0.6 for lenient."
        ),
    )

    similarity_threshold: float = Field(
        default=0.90,
        ge=0.0,
        le=1.0,
        description=(
            "Threshold for considering documents as duplicates (0-1). "
            "Documents with embedding similarity above this are considered duplicates. "
            "Higher values (0.9-0.95) for near-exact duplicates, "
            "lower values (0.8-0.85) for semantic duplicates."
        ),
    )

    max_documents: int = Field(
        default=8,
        ge=1,
        le=20,
        description=(
            "Maximum number of documents to return after filtering. "
            "This controls the final document count sent to the LLM for synthesis."
        ),
    )

    enable_llm_filter: bool = Field(
        default=False,
        description=(
            "Whether to use LLM for final relevance checking. "
            "When enabled, each remaining document is checked for relevance using an LLM. "
            "This is most accurate but adds cost and latency (1 LLM call per document). "
            "Recommended: false for fast mode, true for high-accuracy mode."
        ),
    )

    llm: Optional[LLMConfiguration] = Field(
        default=None,
        description=(
            "LLM configuration for relevance checking. "
            "Only required if enable_llm_filter is true. "
            "Should be a fast, cheap model (e.g., gpt-4o-mini)."
        ),
    )

    @field_validator("llm", mode="before")
    @classmethod
    def _validate_llm(cls, value: Any, info: ValidationInfo) -> Any:
        """Validate LLM configuration using the registry to support all LLM providers."""
        if value is None:
            return value
        return LLMConfiguration._validate(value, info, LLMConfigurationRegistry)
