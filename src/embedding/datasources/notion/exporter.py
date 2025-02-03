import asyncio
import logging
import traceback
from typing import List, Optional

from notion_client import APIResponseError
from notion_client.helpers import async_collect_paginated_api
from notion_exporter import NotionExporter as NotionExporterCore
from notion_exporter.block_converter import BlockConverter
from notion_exporter.property_converter import PropertyConverter
from notion_exporter.retry_utils import (
    is_rate_limit_exception,
    is_unavailable_exception,
    wait_for_retry_after_header,
)
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from embedding.datasources.notion.document import NotionDocument

retry_decorator = retry(
    retry=(
        retry_if_exception(predicate=is_rate_limit_exception)
        | retry_if_exception(predicate=is_unavailable_exception)
    ),
    wait=wait_for_retry_after_header(fallback=wait_exponential()),
    stop=stop_after_attempt(3),
)


class _PropertyConverter(PropertyConverter):

    def __init__(self, notion_exporter: NotionExporterCore):
        super().__init__(notion_exporter)
        self.type_specific_converters["verification"] = self.verification

    def verification(self, property_item: dict) -> str:
        """
        Converts a verification property to a Markdown string.
        """
        return property_item["verification"]["state"]

    def convert_property(self, property_item: dict) -> str:
        """
        Converts a Notion property to a Markdown string.
        """
        try:
            return super().convert_property(property_item)
        except Exception:
            logging.warning(
                f"Failed to convert property: {traceback.format_exc()}. Using 'None'."
            )
            return "None"


class _BlockConverter(BlockConverter):

    def convert_block(
        self, block: dict, indent: bool = False, indent_level: int = 0
    ) -> str:
        """
        Converts a block to a Markdown string.
        """
        try:
            return super().convert_block(block, indent, indent_level)
        except Exception:
            logging.warning(
                f"Failed to convert property: {traceback.format_exc()}. Using 'None'."
            )
            return "None"


class _NotionExporterCore(NotionExporterCore):
    """
    Custom version of `notion_exporter.exporter.NotionExporter`. Modifications are related to metadata parsing and asynchronous execution.
    Large amount of code corresponds to the original implementation. Modifications are marked with `Custom modification` comments.
    """

    def __init__(
        self,
        notion_token: str,
        export_child_pages: bool = False,
        extract_page_metadata: bool = False,
        exclude_title_containing: Optional[str] = None,
    ):
        super().__init__(
            notion_token=notion_token,
            export_child_pages=export_child_pages,
            extract_page_metadata=extract_page_metadata,
            exclude_title_containing=exclude_title_containing,
        )
        self.property_converter = _PropertyConverter(self)
        self.block_converter = _BlockConverter()

    @retry_decorator
    async def _get_page_meta(self, page_id: str) -> dict:
        """
        Retrieve metadata of a page from Notion.
        Custom modification:
            - Remove `created_by` and `last_edited_by` calls.
            - Add `created_time`, `type` and `format`.

        :param page_id: The ID of the page.
        :return: A dictionary containing metadata of the page.
        """
        page_object = await self.notion.pages.retrieve(page_id)
        # Custom modification ---
        # Remove user-related calls
        # --- Custom modification

        # Database entries don't have an explicit title property, but a title column
        # Also, we extract all properties from the database entry to be able to add them to the markdown page as
        # key-value pairs
        properties = {}
        if page_object["parent"]["type"] == "database_id":
            title = ""
            for prop_name, prop in page_object["properties"].items():
                if prop["type"] == "title":
                    title = (
                        prop["title"][0]["plain_text"] if prop["title"] else ""
                    )
                properties[prop_name] = (
                    self.property_converter.convert_property(prop)
                )
        else:
            try:
                if "Page" in page_object["properties"]:
                    title = page_object["properties"]["Page"]["title"][0][
                        "plain_text"
                    ]
                elif "title" in page_object["properties"]:
                    title = page_object["properties"]["title"]["title"][0][
                        "plain_text"
                    ]
            except Exception:
                logging.warning(
                    f"Failed to extract title: {traceback.format_exc()}. Using 'None'."
                )
                title = "None"

        page_meta = {
            "title": title,
            "url": page_object["url"],
            # Custom modification ---
            # Remove user-related calls `created_by` and `last_edited_by`
            "created_time": page_object["created_time"],
            "type": "page",
            "format": "md",
            # --- Custom modification
            "last_edited_time": page_object["last_edited_time"],
            "page_id": page_object["id"],
            "parent_id": page_object["parent"][page_object["parent"]["type"]],
        }
        if properties:
            page_meta["properties"] = properties

        return page_meta

    @retry_decorator
    async def _get_database_meta(self, database_id: str) -> dict:
        """
        Retrieve metadata of a database from Notion.
        Custom modification:
            - Remove `created_by` and `last_edited_by` calls.
            - Add `created_time`, `type` and `format`.

        :param database_id: The ID of the database.
        :return: A dictionary containing metadata of the database.
        """
        try:
            database_object = await self.notion.databases.retrieve(database_id)
            # Custom modification ---
            # Remove user-related calls
            # --- Custom modification

            database_meta = {
                "title": (
                    database_object["title"][0]["plain_text"]
                    if database_object["title"]
                    else "Untitled"
                ),
                "url": database_object["url"],
                # Custom modification ---
                # Remove user-related calls `created_by` and `last_edited_by`
                "type": "database",
                "created_time": database_object["created_time"],
                "format": "md",
                # --- Custom modification
                "last_edited_time": database_object["last_edited_time"],
                "page_id": database_object["id"],
                "parent_id": database_object["parent"][
                    database_object["parent"]["type"]
                ],
            }
        except APIResponseError as exc:
            # Database is not available via API, might be a linked database
            if exc.code in ["object_not_found", "validation_error"]:
                database_meta = {
                    "title": "Untitled",
                    "url": "",
                    # Custom modification ---
                    # Remove user-related calls `created_by` and `last_edited_by`
                    "type": "database",
                    "created_time": "",
                    "format": "md",
                    # --- Custom modification
                    "last_edited_time": "",
                    "page_id": database_id,
                    "parent_id": "",
                }
            else:
                raise exc

        return database_meta

    @retry(
        retry=(
            retry_if_exception(predicate=is_rate_limit_exception)
            | retry_if_exception(predicate=is_unavailable_exception)
        ),
        wait=wait_for_retry_after_header(fallback=wait_exponential()),
        stop=stop_after_attempt(3),
    )
    async def _get_database_content(
        self, database_id: str
    ) -> tuple[str, set[str]]:
        try:
            database = await self.notion.databases.retrieve(database_id)
            database_entries = await async_collect_paginated_api(
                self.notion.databases.query, database_id=database_id
            )
            entry_ids = set()

            description = (
                database["description"][0]["plain_text"]
                if database["description"]
                else ""
            )

            title_column = [
                col_name
                for col_name, col in database["properties"].items()
                if col["type"] == "title"
            ][0]
            db_page_header = f"{description}\n\n"
            table_header = f"|{title_column}|{'|'.join([prop['name'] for prop in database['properties'].values() if prop['name'] != title_column])}|\n"
            table_header += "|" + "---|" * (len(database["properties"])) + "\n"
            table_body = ""

            for entry in database_entries:
                table_body += f"|{self.property_converter.convert_property(entry['properties'][title_column]).replace('|', ' ')}|"
                table_body += "|".join(
                    [
                        self.property_converter.convert_property(prop).replace(
                            "|", " "
                        )
                        for prop_name, prop in entry["properties"].items()
                        if prop_name != title_column
                    ]
                )
                table_body += "|\n"
                entry_ids.add(entry["id"])

            db_page = f"{db_page_header}{table_header}{table_body}"
        except APIResponseError as exc:
            # Database is not available via API, might be a linked database
            if exc.code in ["object_not_found", "validation_error"]:
                db_page = ""
                entry_ids = set()
            else:
                raise exc

        return db_page, entry_ids

    async def async_export_pages(
        self,
        page_ids: Optional[list[str]] = None,
        database_ids: Optional[list[str]] = None,
        ids_to_exclude: Optional[list[str]] = None,
    ) -> dict[str, str]:
        """
        Export pages and databases to markdown files.

        :param page_ids: List of page IDs to export.
        :param database_ids: List of database IDs to export.
        :param ids_to_exclude: List of IDs to ignore.
        """
        if page_ids is None and database_ids is None:
            raise ValueError(
                "Either page_ids or database_ids must be specified."
            )

        if ids_to_exclude is None:
            ids_to_exclude = set()
        if page_ids is None:
            page_ids = set()
        if database_ids is None:
            database_ids = set()

        page_ids = set(map(self._normalize_id, page_ids))
        database_ids = set(map(self._normalize_id, database_ids))
        ids_to_exclude = set(map(self._normalize_id, ids_to_exclude))

        page_ids = page_ids - ids_to_exclude
        database_ids = database_ids - ids_to_exclude

        extracted_pages, _, _ = await self._async_export_pages(
            page_ids=page_ids,
            database_ids=database_ids,
            ids_to_exclude=ids_to_exclude,
        )

        return extracted_pages

    async def _async_export_pages(
        self,
        page_ids: set[str],
        database_ids: set[str],
        ids_to_exclude: Optional[set] = None,
        parent_page_ids: Optional[dict] = None,
        page_paths: Optional[dict] = None,
    ):
        """
        Export pages and databases to markdown format.

        :param page_ids: List of page IDs to export.
        :param database_ids: List of database IDs to export.
        :param ids_to_exclude: List of IDs to ignore.
        """
        if ids_to_exclude is None:
            ids_to_exclude = set()
        if page_paths is None:
            page_paths = {}
        if parent_page_ids is None:
            parent_page_ids = {}

        page_ids -= ids_to_exclude
        database_ids -= ids_to_exclude
        ids_to_exclude.update(page_ids)
        ids_to_exclude.update(database_ids)

        extracted_pages = {}
        child_pages = set()
        child_databases = set()
        if page_ids:
            for page_id in page_ids:
                logging.info(f"Fetching page {page_id}.")
            page_meta_tasks = [
                self._get_page_meta(page_id) for page_id in page_ids
            ]
            page_content_tasks = [
                self._get_block_content(page_id) for page_id in page_ids
            ]
            page_details_results = await asyncio.gather(*page_meta_tasks)
            page_content_results = await asyncio.gather(*page_content_tasks)
            ids_to_exclude.update(
                page["page_id"] for page in page_details_results
            )

            for page_details, (
                markdown,
                child_page_ids,
                child_database_ids,
            ) in zip(page_details_results, page_content_results):
                if (
                    self.exclude_title_containing
                    and self.exclude_title_containing.lower()
                    in page_details.get("title", "").lower()
                ):
                    continue
                for child_page_id in child_page_ids:
                    parent_page_ids[child_page_id] = page_details["page_id"]
                for child_database_id in child_database_ids:
                    parent_page_ids[child_database_id] = page_details["page_id"]
                ## Custom modification ---
                # Remove frontmatter
                extracted_pages[page_details["page_id"]] = {
                    "content": "\n".join(markdown),
                    "metadata": page_details,
                }
                ## --- Custom modification
                child_pages.update(child_page_ids)
                child_databases.update(child_database_ids)

        if database_ids:
            for database_id in database_ids:
                logging.info(f"Fetching database {database_id}.")
            database_meta_tasks = [
                self._get_database_meta(database_id)
                for database_id in database_ids
            ]
            database_content_tasks = [
                self._get_database_content(database_id)
                for database_id in database_ids
            ]
            database_content_results = await asyncio.gather(
                *database_content_tasks
            )
            database_details_results = await asyncio.gather(
                *database_meta_tasks
            )
            ids_to_exclude.update(
                database["page_id"] for database in database_details_results
            )

            for db_details, (markdown, entry_ids) in zip(
                database_details_results, database_content_results
            ):
                if (
                    self.exclude_title_containing
                    and self.exclude_title_containing.lower()
                    in db_details.get("title", "").lower()
                ):
                    continue
                for entry_id in entry_ids:
                    parent_page_ids[entry_id] = db_details["page_id"]
                # Custom modification ---
                # Remove frontmatter
                extracted_pages[db_details["page_id"]] = {
                    "content": markdown,
                    "metadata": db_details,
                }
                # --- Custom modification
                child_pages.update(entry_ids)

        if self.export_child_pages and (child_pages or child_databases):
            extracted_child_pages, _, _ = await self._async_export_pages(
                page_ids=child_pages,
                database_ids=child_databases,
                ids_to_exclude=ids_to_exclude,
                parent_page_ids=parent_page_ids,
                page_paths=page_paths,
            )
            extracted_pages.update(extracted_child_pages)

        return extracted_pages, child_pages, child_databases


class NotionExporter:
    """Exporter for converting Notion pages to markdown documents.

    Handles extraction and conversion of Notion pages and databases
    to NotionDocument instances with markdown content.

    Attributes:
        notion_exporter: Core exporter instance for content extraction
    """

    def __init__(
        self,
        api_token: str,
    ):
        """Initialize Notion exporter.

        Args:
            api_token: Authentication token for Notion API
        """
        self.notion_exporter = _NotionExporterCore(
            notion_token=api_token,
            export_child_pages=False,
            extract_page_metadata=True,
        )

    async def run(
        self, page_ids: List[str] = None, database_ids: List[str] = None
    ) -> List[NotionDocument]:
        """Export Notion content to document collection.

        Args:
            page_ids: List of page IDs to export
            database_ids: List of database IDs to export

        Returns:
            List[NotionDocument]: Collection of exported documents

        Raises:
            ValueError: If neither page_ids nor database_ids provided
        """
        extracted_objects = await self.notion_exporter.async_export_pages(
            page_ids=page_ids, database_ids=database_ids
        )

        documents = []
        for object_id, extracted_data in extracted_objects.items():
            document = NotionDocument.from_page(
                metadata=extracted_data["metadata"],
                text=extracted_data["content"],
            )
            documents.append(document)

        return documents
