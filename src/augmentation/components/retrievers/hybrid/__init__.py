from augmentation.bootstrap.configuration.components.retriever_configuration import (
    RetrieverConfigurationRegistry,
    RetrieverName,
)
from augmentation.components.retrievers.hybrid.retriever import (
    HybridRetrieverFactory,
)
from augmentation.components.retrievers.registry import RetrieverRegistry


def register() -> None:
    \"\"\"Register Hybrid Retriever components with the system.\"\"\"
    RetrieverRegistry.register(RetrieverName.HYBRID, HybridRetrieverFactory)
