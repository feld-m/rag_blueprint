from enum import Enum
from typing import Type

from pydantic import Field

from core.base_configuration import BaseConfiguration
from core.base_factory import ConfigurationRegistry


class RetrieverName(str, Enum):
    """Enumeration of supported retriever types."""

    BASIC = "basic"
    AUTO = "auto"
    DYNAMIC_TEMPORAL = "dynamic_temporal"


class RetrieverConfiguration(BaseConfiguration):
    """
    Configuration class for retrievers.

    This class defines the parameters needed to configure a retriever component
    in the RAG pipeline.
    """

    name: RetrieverName = Field(..., description="The name of the retriever.")
    similarity_top_k: int = Field(
        ..., description="The number of top similar items to retrieve."
    )


class RetrieverConfigurationRegistry(ConfigurationRegistry):
    """
    Registry for retriever configurations.

    Maps RetrieverName enum values to their corresponding configuration classes.
    Used for dynamic instantiation of retriever components based on configuration.

    Attributes:
        _key_class: The enumeration class for retriever names.
    """

    _key_class: Type = RetrieverName
