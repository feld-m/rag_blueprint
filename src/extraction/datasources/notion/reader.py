import logging
from enum import Enum
from typing import Any, Callable, List, Tuple

from more_itertools import chunked
from notion_client import Client
from tqdm import tqdm

from core.base_factory import Factory
from core.logger import LoggerConfiguration
from extraction.datasources.core.base.reader import BaseReader
from extraction.datasources.notion.client import NotionClientFactory
from extraction.datasources.notion.configuration import (
    NotionDatasourceConfiguration,
)
from extraction.datasources.notion.document import NotionDocument
from extraction.datasources.notion.exporter import (
    NotionExporter,
    NotionExporterFactory,
)


class NotionObjectType(Enum):
    """
    Enum representing Notion object types.
    This enum is used to specify the type of Notion object being processed,
    such as a page or a database.
    """

    PAGE = "page"
    DATABASE = "database"


class NotionDatasourceReader(BaseReader):
    """Reader for extracting documents from Notion workspace.

    Implements document extraction from Notion pages and databases with
    support for batched async operations and export limits.
    """

    def __init__(
        self,
        configuration: NotionDatasourceConfiguration,
        client: Client,
        exporter: NotionExporter,
        logger: logging.Logger = LoggerConfiguration.get_logger(__name__),
    ):
        """Initialize Notion reader.

        Args:
            configuration: Settings for Notion access and limits
            client: Client for Notion API interaction
            exporter: Component for content export and conversion
            logger: Logger for logging messages and errors
        """
        super().__init__()
        self.client = client
        self.export_batch_size = configuration.export_batch_size
        self.export_limit = configuration.export_limit
        self.exporter = exporter
        self.home_page_database_id = configuration.home_page_database_id
        self.logger = logger

    async def read_all_async(self) -> List[NotionDocument]:
        """Asynchronously retrieve all documents from Notion.

        Fetches pages and databases in batches, respecting export limits
        and batch sizes.

        Returns:
            List[NotionDocument]: Collection of processed documents
        """
        if self.home_page_database_id is None:
            database_ids = []
            page_ids = []
        else:
            database_ids, page_ids = self._get_ids_from_home_page()

        database_ids.extend(
            self._get_all_ids(
                NotionObjectType.DATABASE,
                limit=self._get_current_limit(database_ids, page_ids),
            )
        )
        page_ids.extend(
            self._get_all_ids(
                NotionObjectType.PAGE,
                limit=self._get_current_limit(database_ids, page_ids),
            )
        )

        # Process IDs
        database_ids = set(database_ids)
        database_ids.discard(self.home_page_database_id)
        page_ids = set(page_ids)

        # Batch and export
        chunked_database_ids = list(chunked(database_ids, self.export_batch_size))
        chunked_page_ids = list(chunked(page_ids, self.export_batch_size))

        databases, databases_failed = await self._export_documents(
            chunked_database_ids, NotionObjectType.DATABASE
        )
        pages, pages_failed = await self._export_documents(
            chunked_page_ids, NotionObjectType.PAGE
        )

        # Log failures
        if databases_failed:
            self.logger.warning(
                f"Failed to export {len(databases_failed)} databases: {databases_failed}"
            )
        if pages_failed:
            self.logger.warning(
                f"Failed to export {len(pages_failed)} pages: {pages_failed}"
            )

        # Apply limit if needed
        objects = databases + pages
        return objects if self.export_limit is None else objects[: self.export_limit]

    async def _export_documents(
        self, chunked_ids: List[List[str]], objects_type: NotionObjectType
    ) -> Tuple[List[NotionDocument], List[str]]:
        """Export Notion documents in batches with progress tracking.

        Processes batches of Notion object IDs, exporting them through the exporter
        component. Handles errors gracefully by tracking failed exports and
        continuing with the next batch.

        Args:
            chunked_ids: List of ID batches, where each batch is a list of IDs
                         to be processed together
            objects_type: Type of Notion objects to export (PAGE or DATABASE)

        Returns:
            Tuple containing:
                - List of successfully exported NotionDocument objects
                - List of IDs that failed during export

        Raises:
            ValueError: If objects_type is not a valid NotionObjectType
        """
        all_objects = []
        failed_exports = []
        total_ids = sum(len(chunk) for chunk in chunked_ids)

        with tqdm(
            total=total_ids,
            desc=f"[Notion] Exporting {objects_type.name}s",
            unit="objects",
        ) as pbar:
            for chunk_ids in chunked_ids:
                try:
                    objects = await self.exporter.run(
                        page_ids=(
                            chunk_ids if objects_type == NotionObjectType.PAGE else None
                        ),
                        database_ids=(
                            chunk_ids
                            if objects_type == NotionObjectType.DATABASE
                            else None
                        ),
                    )
                    all_objects.extend(objects)
                    pbar.update(len(chunk_ids))
                    self.logger.debug(f"Added {len(objects)} {objects_type.name}s")
                except Exception as e:
                    self.logger.error(
                        f"Export failed for {objects_type.name}: {chunk_ids}. {e}"
                    )
                    failed_exports.extend(chunk_ids)
                    pbar.update(len(chunk_ids))

        if failed_exports:
            self.logger.warning(
                f"Failed to export {len(failed_exports)} {objects_type.name}s"
            )

        return all_objects, failed_exports

    def _get_ids_from_home_page(self) -> Tuple[List[str], List[str]]:
        """Extract database and page IDs from home page database.

        Queries the configured home page database and extracts IDs for
        both databases and pages.

        Returns:
            Tuple containing:
                - List of database IDs
                - List of page IDs
        """
        self.logger.info(
            f"Fetching all object ids from Notion's home page with limit {self.export_limit}..."
        )
        response = self._collect_paginated_api(
            function=self.client.databases.query,
            limit=self.export_limit,
            database_id=self.home_page_database_id,
        )
        database_ids = [
            entry["id"] for entry in response if entry["object"] == "database"
        ]
        page_ids = [entry["id"] for entry in response if entry["object"] == "page"]

        self.logger.info(
            f"Found {len(database_ids)} database ids and {len(page_ids)} page ids in Notion."
        )

        return database_ids, page_ids

    def _get_all_ids(
        self, objects_type: NotionObjectType, limit: int = None
    ) -> List[str]:
        """Fetch all IDs for specified Notion object type.

        Args:
            objects_type: Type of Notion objects to fetch
            limit: Maximum number of IDs to fetch (None for unlimited)

        Returns:
            List[str]: Collection of object IDs

        Note:
            Returns empty list if limit is 0 or negative
        """
        if limit is not None and limit <= 0:
            return []

        self.logger.info(
            f"Fetching all ids of {objects_type.name} objects from Notion API with limit {limit}..."
        )

        params = {
            "filter": {
                "value": objects_type.name.lower(),
                "property": "object",
            },
        }
        results = NotionDatasourceReader._collect_paginated_api(
            self.client.search, limit, **params
        )
        object_ids = [object["id"] for object in results]
        object_ids = object_ids[:limit] if limit is not None else object_ids

        self.logger.info(
            f"Found {len(object_ids)} ids of {objects_type.name} objects in Notion."
        )

        return object_ids

    def _get_current_limit(self, database_ids: List[str], page_ids: List[str]) -> int:
        """Calculate remaining object limit based on existing IDs.

        Args:
            database_ids: Currently collected database IDs
            page_ids: Currently collected page IDs

        Returns:
            int: Remaining limit (None if no limit configured)

        Note:
            Subtracts total of existing IDs from configured export limit
        """
        return (
            self.export_limit - len(database_ids) - len(page_ids)
            if self.export_limit
            else None
        )

    @staticmethod
    def _collect_paginated_api(
        function: Callable[..., Any], limit: int, **kwargs: Any
    ) -> List[Any]:
        """Collect all results from paginated Notion API endpoint.

        Args:
            function: API function to call
            limit: Maximum number of results to collect
            **kwargs: Additional arguments for API function

        Returns:
            List[Any]: Collected API results
        """
        next_cursor = kwargs.pop("start_cursor", None)
        result = []

        while True:
            response = function(**kwargs, start_cursor=next_cursor)
            result.extend(response.get("results"))

            if NotionDatasourceReader._limit_reached(result, limit):
                return result[:limit]
            if not NotionDatasourceReader._has_more_pages(response):
                return result[:limit] if limit else result

            next_cursor = response.get("next_cursor")

    @staticmethod
    def _limit_reached(result: List[dict], limit: int) -> bool:
        """Check if result count has reached limit.

        Args:
            result: Current results
            limit: Maximum allowed results

        Returns:
            bool: True if limit reached
        """
        return limit is not None and len(result) >= limit

    @staticmethod
    def _has_more_pages(response: dict) -> bool:
        """Check if more pages are available.

        Args:
            response: API response dictionary

        Returns:
            bool: True if more pages available
        """
        return response.get("has_more") and response.get("next_cursor")


class NotionDatasourceReaderFactory(Factory):
    """Factory for creating NotionDatasourceReader instances.

    This class is responsible for creating instances of NotionDatasourceReader
    with the provided configuration and Notion client.

    Attributes:
        _configuration_class: The configuration class used to create the NotionDatasourceReader instance.
    """

    _configuration_class = NotionDatasourceConfiguration

    @classmethod
    def _create_instance(
        cls,
        configuration: NotionDatasourceConfiguration,
    ) -> NotionDatasourceReader:
        client = NotionClientFactory.create(configuration)
        exporter = NotionExporterFactory.create(configuration)
        return NotionDatasourceReader(
            configuration=configuration,
            client=client,
            exporter=exporter,
        )
