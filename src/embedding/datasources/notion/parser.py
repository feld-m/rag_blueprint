import logging

from notion2md.convertor.richtext import richtext_convertor
from notion_exporter.block_converter import BlockConverter
from notion_exporter.property_converter import PropertyConverter

from common.bootstrap.configuration.pipeline.embedding.datasources.datasources_configuration import (
    DatasourceName,
)
from embedding.datasources.notion.document import NotionDocument


def extract(dict: dict, *args) -> str:
    try:
        property_type = args[0]
        value = dict[property_type]
        for arg in args[1:]:
            value = value[arg]
        return value
    except Exception:
        logging.info(
            f"Couldn't find value for {''.join([f'[{arg}]' for arg in args])} for {property_type}."
        )
        return ""


class _PropertyConverter(PropertyConverter):

    def __init__(self):
        super().__init__(None)
        self.type_specific_converters["button"] = lambda prop: ""
        self.type_specific_converters["verification"] = lambda prop: extract(
            prop, "verification", "state"
        )

    @staticmethod
    def last_edited_by(property_item: dict) -> str:
        """
        Converts a last_edited_by property to a Markdown string.
        """
        return f"{extract(property_item, 'last_edited_by', 'object')}: {extract(property_item, 'last_edited_by', 'id')}"


class _BlockConverter(BlockConverter):

    @staticmethod
    def callout(block: dict) -> str:
        """
        Converts a callout block to a Markdown.
        """
        text = richtext_convertor(extract(block, "callout", "rich_text"))
        icon = extract(block, "callout", "icon", "emoji")
        return f"{icon} {text}"


class NotionParser:

    def __init__(self):
        self.block_converter = _BlockConverter()
        self.property_converter = _PropertyConverter()

    def parse_page(self, page: dict) -> NotionDocument:
        """Parse a Notion json page into a NotionDocument object.
        `page` is an json response from the Notion API enhanced by
        `blocks` field containing the blocks of the page.

        Args:
            page: Notion page dictionary

        Returns:
            NotionDocument object
        """
        return NotionDocument(
            attachments={},
            text=self.get_page_content(page),
            metadata=self.get_page_metadata(page),
        )

    def get_page_content(self, page: dict) -> str:
        """Extract content from Notion page.

        Args:
            page: Notion page dictionary

        Returns:
            str: Page content
        """
        return "\n\n".join(
            [
                self.block_converter.convert_block(block)
                for block in page["blocks"]
            ]
        )

    def get_page_metadata(self, page: dict) -> dict:
        """Extract metadata from Notion page.

        Args:
            page: Notion page dictionary

        Returns:
            dict: Metadata dictionary
        """
        return {
            "datasource": DatasourceName.NOTION_POSTGRES_AIRBYTE,
            "id": page["id"],
            "type": NotionDocument.Type.PAGE,
            "parent": page["parent"],
            "title": self.extract_title(page),
            "url": page["url"],
            "created_by": page["created_by"],
            "created_time": page["created_time"],
            "last_edited_by": page["last_edited_by"],
            "last_edited_time": page["last_edited_time"],
        }

    def extract_title(self, page: dict) -> str:
        """Extract page title from url.

        Args:
            page: Notion page dictionary

        Returns:
            str: Page title
        """
        clean_id = page["id"].replace("-", "")
        notion_url_prefix = "https://www.notion.so/"
        return (
            page["url"]
            .replace(notion_url_prefix, "")
            .replace("-" + clean_id, "")
        )

    def parse_database(self, database: dict) -> NotionDocument:
        """Parse a Notion json database into a NotionDocument object.
        `database` is an json response from the Notion API enhanced by
        `pages` field containing the pages of the database.

        Args:
            database: Notion database dictionary

        Returns:
            NotionDocument object
        """
        return NotionDocument(
            attachments={},
            text=self.get_database_content(database),
            metadata=self.get_database_metadata(database),
        )

    def get_database_content(self, database: dict) -> str:
        """Extract content from Notion database.

        Args:
            database: Notion database dictionary

        Returns:
            str: Database content
        """
        title = database["title"][0]["plain_text"] if database["title"] else ""
        db_page_header = f"{title}\n\n"
        table_header = (
            f"|{'|'.join([prop['name'] for prop in database['properties']])}|\n"
        )
        table_header += "|" + "---|" * (len(database["properties"])) + "\n"
        table_body = ""
        for page in database["pages"]:
            table_body += "|".join(
                [
                    self.property_converter.convert_property(prop["value"])
                    for prop in page["properties"]
                ]
            )
            table_body += "|\n"

        return f"{db_page_header}{table_header}{table_body}"

    def get_database_metadata(self, database: dict) -> dict:
        return {
            "datasource": DatasourceName.NOTION_POSTGRES_AIRBYTE,
            "id": database["id"],
            "type": NotionDocument.Type.DATABASE,
            "parent": database["parent"],
            "title": (
                database["title"][0]["plain_text"] if database["title"] else ""
            ),
            "url": database["url"],
            "created_by": database["created_by"],
            "created_time": database["created_time"],
            "last_edited_by": database["last_edited_by"],
            "last_edited_time": database["last_edited_time"],
        }
