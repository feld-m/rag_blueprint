from typing import Type

from core import Factory
from extraction.datasources.core.manager import BasicDatasourceManager
from extraction.datasources.hackernews.configuration import HackerNewsDatasourceConfiguration
from extraction.datasources.hackernews.parser import HackerNewsDatasourceParserFactory
from extraction.datasources.hackernews.reader import HackerNewsDatasourceReaderFactory



class HackerNewsDatasourceManagerFactory(Factory):
    """Factory for creating HackerNews datasource managers.

    This factory generates managers that handle the extraction of content from
    HackerNews instances. It ensures proper configuration, reading, and parsing
    of HackerNews content.

    Attributes:
        _configuration_class: Configuration class used for validating and processing
            HackerNews-specific settings.
    """

    _configuration_class: Type = HackerNewsDatasourceConfiguration

    @classmethod
    def _create_instance(
        cls, configuration: HackerNewsDatasourceConfiguration
    ) -> BasicDatasourceManager:
        """Create a configured HackerNews datasource manager.

        Sets up the necessary reader and parser components based on the provided
        configuration and assembles them into a functional manager.

        Args:
            configuration: Configuration object containing HackerNews-specific
                parameters including authentication details, spaces to extract,
                and other extraction options.

        Returns:
            A fully initialized datasource manager that can extract and process
            data from HackerNews.
        """
        reader = HackerNewsDatasourceReaderFactory.create(configuration)
        parser = HackerNewsDatasourceParserFactory.create(configuration)
        return BasicDatasourceManager(configuration, reader, parser)

