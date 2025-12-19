from typing import Literal
from pydantic import Field
from augmentation.bootstrap.configuration.components.retriever_configuration import (
    RetrieverConfiguration,
    RetrieverName,
)

class HybridRetrieverConfiguration(RetrieverConfiguration):
    \"\"\"
    Configuration for the Hybrid Retriever component.
    This class defines the configuration parameters needed for initializing
    and operating the hybrid retriever, extending the base RetrieverConfiguration.
    \"\"\"
    name: Literal[RetrieverName.HYBRID] = Field(
        ..., description=\"The name of the retriever.\"
    )
