from typing import Type

from augmentation.components.postprocessors.hybrid_filter.configuration import (
    HybridFilterConfiguration,
)
from augmentation.components.postprocessors.hybrid_filter.postprocessor import (
    HybridFilterPostprocessor,
)
from core import Factory


class HybridFilterFactory(Factory):
    """
    Factory for creating HybridFilterPostprocessor instances.

    The Hybrid Filter postprocessor provides multi-stage document filtering:
    1. Score threshold filtering (fast)
    2. Semantic deduplication (fast)
    3. LLM relevance checking (optional, slow but accurate)

    This factory handles the creation of HybridFilterPostprocessor objects
    based on the provided configuration.

    Attributes:
        _configuration_class: The configuration class for the HybridFilterPostprocessor.
    """

    _configuration_class: Type = HybridFilterConfiguration

    @classmethod
    def _create_instance(
        cls, configuration: HybridFilterConfiguration
    ) -> HybridFilterPostprocessor:
        """
        Creates a HybridFilterPostprocessor instance based on the provided configuration.

        Args:
            configuration: Configuration object containing filter thresholds,
                          max documents, LLM settings, etc.

        Returns:
            HybridFilterPostprocessor: An initialized postprocessor that can filter
                and deduplicate retrieved documents before synthesis.
        """
        return HybridFilterPostprocessor(configuration=configuration)
