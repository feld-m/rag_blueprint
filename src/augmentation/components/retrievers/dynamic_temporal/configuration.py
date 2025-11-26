"""Configuration for dynamic temporal retriever."""

from augmentation.bootstrap.configuration.components.retriever_configuration import (
    RetrieverConfiguration,
)


class DynamicTemporalRetrieverConfiguration(RetrieverConfiguration):
    """Configuration for dynamic temporal retriever.

    This retriever detects temporal keywords and applies filters dynamically.
    No additional configuration needed beyond base retriever settings.
    """

    pass
