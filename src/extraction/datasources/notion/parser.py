from core.base_factory import Factory
from extraction.datasources.core.base.parser import BaseParser
from extraction.datasources.notion.configuration import (
    NotionDatasourceConfiguration,
)
from extraction.datasources.notion.document import NotionDocument


class NotionDatasourceParser(BaseParser[NotionDocument]):
    """Parser for Notion content.

    Transforms raw Notion page data into structured NotionDocument objects.
    """

    def __init__(self):
        """Initialize the Notion parser."""
        pass

    def parse(self, object: str) -> NotionDocument:
        """Parse Notion page data into a structured document.

        Args:
            object: Dictionary containing Notion page content with 'markdown' text
                   and 'metadata' information.

        Returns:
            A NotionDocument containing the parsed content and enhanced metadata.
        """
        markdown = object["markdown"]
        metadata = self._extract_metadata(object["metadata"])
        return NotionDocument(text=markdown, metadata=metadata)

    @staticmethod
    def _extract_metadata(metadata: dict) -> dict:
        """Process and enhance page metadata.

        Args:
            metadata: Raw page metadata dictionary

        Returns:
            dict: Enhanced metadata including source and formatted dates
        """
        metadata["datasource"] = "notion"
        metadata["created_date"] = metadata["created_time"].split("T")[0]
        metadata["last_edited_date"] = metadata["last_edited_time"].split("T")[
            0
        ]
        return metadata


class NotionDatasourceParserFactory(Factory):
    """Factory for creating NotionDatasourceParser instances.

    Creates and configures parser instances for Notion content.
    """

    _configuration_class: NotionDatasourceConfiguration = (
        NotionDatasourceConfiguration
    )

    @classmethod
    def _create_instance(
        cls, _: NotionDatasourceConfiguration
    ) -> NotionDatasourceParser:
        """
        Create a NotionDatasourceParser instance.
        Returns:
            NotionDatasourceParser: Instance of NotionDatasourceParser.
        """
        return NotionDatasourceParser()
