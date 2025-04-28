from typing import Literal, Optional

from pydantic import Field, ConfigDict

from core.base_configuration import BaseSecrets
from extraction.bootstrap.configuration.datasources import (
    DatasourceConfiguration,
    DatasourceName,
)

class HackerNewsDatasourceConfiguration(DatasourceConfiguration):
    """Configuration for Hacker News data source.

    This class defines the configuration parameters required for extracting data from Hacker News.
    It inherits from the base DatasourceConfiguration class.
    """

    name: Literal[DatasourceName.HACKERNEWS] = Field(
        ..., description="The name of the data source."
    )
    base_url: str = Field(
        "https://hacker-news.firebaseio.com/v0",
        description="Base URL for the Hacker News API",
    )    
    stories_limit: Optional[int] = Field(
        10,
        description="Maximum number of top stories to fetch. Set to None for no limit (use with caution).",
    )
    fetch_batch_size: int = Field(
        20,
        description="Number of story details to fetch concurrently.",
    )
    request_timeout: float = Field(
        10.0,
        description="Timeout in seconds for individual HTTP requests to the HackerNews API."
    )