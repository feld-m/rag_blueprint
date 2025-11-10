"""Hybrid Filter Postprocessor for intelligent document filtering."""

from augmentation.bootstrap.configuration.components.postprocessors_configuration import (
    PostProcessorConfigurationRegistry,
    PostProcessorName,
)
from augmentation.components.postprocessors.hybrid_filter.configuration import (
    HybridFilterConfiguration,
)
from augmentation.components.postprocessors.hybrid_filter.factory import (
    HybridFilterFactory,
)
from augmentation.components.postprocessors.registry import (
    PostprocessorRegistry,
)


def register() -> None:
    """
    Registers the Hybrid Filter postprocessor component with the postprocessor registry.

    This function registers both the HybridFilterFactory and HybridFilterConfiguration
    with their respective registries, making the hybrid filtering capability
    available to the augmentation pipeline.
    """
    PostprocessorRegistry.register(
        PostProcessorName.HYBRID_FILTER, HybridFilterFactory
    )
    PostProcessorConfigurationRegistry.register(
        PostProcessorName.HYBRID_FILTER, HybridFilterConfiguration
    )
