from typing import Type
from extraction.datasources.core.parser import BaseParser
from extraction.datasources.hackernews.configuration import HackerNewsDatasourceConfiguration
from extraction.datasources.hackernews.document import HackerNewsDocument
from core.base_factory import Factory

class HackerNewsDatasourceParser(BaseParser[HackerNewsDocument]):
    """Parser for HackerNews content.

    Transforms raw HackerNews story data into structured HackerNewsDocument objects.
    """

    def parse(self, story: dict) -> HackerNewsDocument:
        """Parse HackerNews story data into a structured document.

        Args:
            story: Dictionary containing HackerNews story content.

        Returns:
            A HackerNewsDocument containing the parsed content and metadata.
        """
        text = story.get("title", "")
        metadata = {
            "id": story.get("id"),
            "url": story.get("url"),
            "datasource": "hackernews",
        }
        return HackerNewsDocument(text=text, metadata=metadata)

class HackerNewsDatasourceParserFactory(Factory):
    """Factory for creating HackerNewsDatasourceParser instances.

    Creates and configures parser instances for HackerNews content.
    """

    _configuration_class: Type = HackerNewsDatasourceConfiguration

    @classmethod
    def _create_instance(cls, _: HackerNewsDatasourceConfiguration) -> HackerNewsDatasourceParser:
        """
        Create a HackerNewsDatasourceParser instance.

        Returns:
            HackerNewsDatasourceParser: Instance of HackerNewsDatasourceParser.
        """
        return HackerNewsDatasourceParser()
