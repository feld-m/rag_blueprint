from typing import Type

from core import Factory
from extraction.datasources.confluence.configuration import (
    ConfluenceDatasourceConfiguration,
)
from extraction.datasources.confluence.parser import (
    ConfluenceDatasourceParserFactory,
)
from extraction.datasources.confluence.reader import (
    ConfluenceDatasourceReaderFactory,
)
from extraction.datasources.core.base.manager import BasicDatasourceManager


class ConfluenceDatasourceManagerFactory(Factory):
    """Factory for creating Confluence datasource managers.

    This factory generates managers that handle the extraction of content from
    Confluence instances. It ensures proper configuration, reading, and parsing
    of Confluence content.

    Attributes:
        _configuration_class: Configuration class used for validating and processing
            Confluence-specific settings.
    """

    _configuration_class: Type = ConfluenceDatasourceConfiguration

    @classmethod
    def _create_instance(
        cls, configuration: ConfluenceDatasourceConfiguration
    ) -> BasicDatasourceManager:
        """Create a configured Confluence datasource manager.

        Sets up the necessary reader and parser components based on the provided
        configuration and assembles them into a functional manager.

        Args:
            configuration: Configuration object containing Confluence-specific
                parameters including authentication details, spaces to extract,
                and other extraction options.

        Returns:
            A fully initialized datasource manager that can extract and process
            data from Confluence.
        """
        reader = ConfluenceDatasourceReaderFactory.create(configuration)
        parser = ConfluenceDatasourceParserFactory.create(configuration)
        return BasicDatasourceManager(configuration, reader, parser)
