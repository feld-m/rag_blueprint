"""Dynamic temporal retriever package."""

from augmentation.bootstrap.configuration.components.retriever_configuration import (
    RetrieverConfigurationRegistry,
    RetrieverName,
)
from augmentation.components.retrievers.dynamic_temporal.configuration import (
    DynamicTemporalRetrieverConfiguration,
)
from augmentation.components.retrievers.dynamic_temporal.retriever import (
    DynamicTemporalRetriever,
    DynamicTemporalRetrieverFactory,
)
from augmentation.components.retrievers.registry import RetrieverRegistry


def register() -> None:
    """Register Dynamic Temporal Retriever components with the system."""
    RetrieverConfigurationRegistry.register(
        RetrieverName.DYNAMIC_TEMPORAL, DynamicTemporalRetrieverConfiguration
    )
    RetrieverRegistry.register(
        RetrieverName.DYNAMIC_TEMPORAL, DynamicTemporalRetrieverFactory
    )


__all__ = [
    "DynamicTemporalRetriever",
    "DynamicTemporalRetrieverFactory",
    "register",
]
