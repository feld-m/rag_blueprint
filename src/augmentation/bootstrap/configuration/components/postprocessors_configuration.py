from enum import Enum
from typing import List, Type

from pydantic import Field

from core.base_configuration import BaseConfiguration
from core.base_factory import ConfigurationRegistry


class PostProcessorName(str, Enum):
    """Enumeration of supported post-processor names.

    These identify the different post-processing options available for refining search results.
    """

    COLBERT_RERANK = "colbert_reranker"
    HYBRID_FILTER = "hybrid_filter"


class PostProcessorConfiguration(BaseConfiguration):
    """Base configuration for post-processors.

    Post-processors refine search results after initial retrieval to improve relevance and quality.
    Each post-processor implementation should inherit from this class and add its specific
    configuration parameters.
    """

    name: PostProcessorName = Field(
        ..., description="The name of the postprocessor."
    )


class PostProcessorConfigurationRegistry(ConfigurationRegistry):
    """Registry for post-processor configurations.

    This registry maintains a collection of available post-processor configurations
    and provides methods for retrieving them based on the PostProcessorName.

    Attributes:
        _key_class: The enumeration class for post-processor names.
    """

    _key_class: Type = PostProcessorName

    @classmethod
    def get_union_type(self) -> List[PostProcessorConfiguration]:
        """Returns the union type of all registered post-processor configurations.

        This method is used for type validation and dynamic configuration loading,
        allowing the system to work with any of the registered post-processor types.

        Returns:
            List[PostProcessorConfiguration]: A type representing all available post-processor configurations.
        """
        return List[super().get_union_type()]
