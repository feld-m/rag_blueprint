from typing import Optional, Type

from augmentation.bootstrap.configuration.temporal_domain_config import (
    TemporalDomainConfiguration,
)
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
    2. Temporal filtering (based on temporal_domain config, optional)
    3. Semantic deduplication (fast)
    4. LLM relevance checking (optional, slow but accurate)

    This factory handles the creation of HybridFilterPostprocessor objects
    based on the provided configuration.

    Attributes:
        _configuration_class: The configuration class for the HybridFilterPostprocessor.
    """

    _configuration_class: Type = HybridFilterConfiguration

    # Store temporal_domain_config at class level for access during creation
    _temporal_domain_config: Optional[TemporalDomainConfiguration] = None

    @classmethod
    def set_temporal_domain_config(
        cls, temporal_domain_config: Optional[TemporalDomainConfiguration]
    ):
        """Set the temporal domain config to be used when creating instances.

        Args:
            temporal_domain_config: Temporal domain configuration
        """
        cls._temporal_domain_config = temporal_domain_config

    @classmethod
    def _create_instance(
        cls, configuration: HybridFilterConfiguration
    ) -> HybridFilterPostprocessor:
        """
        Creates a HybridFilterPostprocessor instance based on the provided configuration.

        Uses the temporal_domain_config set via set_temporal_domain_config() if available.

        Args:
            configuration: HybridFilterConfiguration containing filter thresholds,
                          max documents, LLM settings, etc.

        Returns:
            HybridFilterPostprocessor: An initialized postprocessor that can filter
                and deduplicate retrieved documents before synthesis.
        """
        return HybridFilterPostprocessor(
            configuration=configuration,
            temporal_domain_config=cls._temporal_domain_config,
        )
