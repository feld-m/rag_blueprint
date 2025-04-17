from abc import ABC
from enum import Enum
from typing import List, Optional

from pydantic import Field

from core import BaseConfigurationWithSecrets
from core.base_factory import ConfigurationRegistry


# Enums
class DatasourceName(str, Enum):
    """
    List of all available datasources.

    Defines the supported data sources that can be used for extraction:
    - CONFLUENCE: Atlassian Confluence wiki pages and spaces
    - NOTION: Notion databases, pages, and blocks
    - PDF: PDF documents from file system or URLs
    """

    CONFLUENCE = "confluence"
    NOTION = "notion"
    PDF = "pdf"
    HACKERNEWS = "hackernews"


# Configuration
class DatasourceConfiguration(BaseConfigurationWithSecrets, ABC):
    """
    Abstract base class for all data source configurations.

    This class serves as the foundation for specific data source implementations,
    providing common configuration parameters. All concrete datasource
    configurations should inherit from this class.
    """

    name: DatasourceName = Field(
        ..., description="The name of the data source."
    )
    export_limit: Optional[int] = Field(
        None, description="The export limit for the data source."
    )


class DatasourceConfigurationRegistry(ConfigurationRegistry):
    """
    Registry for datasource configurations.

    This registry manages all available datasource configurations and provides
    methods to access them based on their type.
    """

    _key_class = DatasourceName

    @classmethod
    def get_union_type(self) -> List[DatasourceConfiguration]:
        """
        Returns the union type of all available datasources.

        This method provides a type hint representing a list of all possible
        datasource configurations, which can be used for validation or
        type checking when working with collections of datasources.

        Returns:
            List[DatasourceConfiguration]: A type representing a list of all
            registered datasource configurations.
        """
        return List[super().get_union_type()]
