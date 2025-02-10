import logging
from enum import Enum
from typing import Any, Callable, List, Tuple

from more_itertools import chunked
from notion_client import Client

from common.bootstrap.configuration.pipeline.embedding.datasources.datasources_configuration import (
    NotionDatasourceConfiguration,
)
from embedding.datasources.core.reader import BaseReader
from embedding.datasources.notion.document import NotionDocument
from embedding.datasources.notion.exporter import NotionExporter


class NotionObjectType(Enum):
    PAGE = "page"
    DATABASE = "database"


class NotionReader(BaseReader):
    """Reader for extracting documents from Notion workspace.

    Implements document extraction from Notion pages and databases with
    support for batched async operations and export limits.

    Attributes:
        notion_client: Client for Notion API interactions
        export_batch_size: Number of objects to export concurrently
        export_limit: Maximum number of objects to export
        exporter: Component for converting Notion content to documents
        home_page_database_id: ID of root database containing content index
    """

    def __init__(
        self,
        configuration: NotionDatasourceConfiguration,
        notion_client: Client,
        exporter: NotionExporter,
    ):
        """Initialize Notion reader.

        Args:
            configuration: Settings for Notion access and limits
            notion_client: Client for Notion API interaction
            exporter: Component for content export and conversion
        """
        super().__init__()
        self.notion_client = notion_client
        self.export_batch_size = configuration.export_batch_size
        self.export_limit = configuration.export_limit
        self.exporter = exporter
        self.home_page_database_id = configuration.home_page_database_id

    def get_all_documents(self) -> List[NotionDocument]:
        """
        Synchronous implementation for fetching all documents from the data source.
        """
        pass

    async def get_all_documents_async(self) -> List[NotionDocument]:
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
        chunked_database_ids = list(
            chunked(database_ids, self.export_batch_size)
        )
        chunked_page_ids = list(chunked(page_ids, self.export_batch_size))

        database_documents, database_failed = await self._export_documents(
            chunked_database_ids, NotionObjectType.DATABASE
        )
        page_documents, page_failed = await self._export_documents(
            chunked_page_ids, NotionObjectType.PAGE
        )

        # Log failures
        if database_failed:
            logging.warning(
                f"Failed to export {len(database_failed)} databases: {database_failed}"
            )
        if page_failed:
            logging.warning(
                f"Failed to export {len(page_failed)} pages: {page_failed}"
            )

        # Apply limit if needed
        documents = database_documents + page_documents
        return (
            documents
            if self.export_limit is None
            else documents[: self.export_limit]
        )

    async def _export_documents(
        self, chunked_ids: List[List[str]], objects_type: NotionObjectType
    ) -> Tuple[List[NotionDocument], List[str]]:
        """Export documents in batches.

        Args:
            chunked_ids: Batched lists of object IDs
            objects_type: Type of Notion objects to export

        Returns:
            Tuple containing:
                - List of exported documents
                - List of failed export IDs

        Raises:
            ValueError: If unsupported object type provided
        """
        all_documents = []
        failed_exports = []
        num_chunks = len(chunked_ids)

        for i, chunk_ids in enumerate(chunked_ids):
            logging.info(
                f"[{i}/{num_chunks}] Exporting {objects_type.name} objects: {chunk_ids}"
            )

            try:
                documents = await self.exporter.run(
                    page_ids=(
                        chunk_ids
                        if objects_type == NotionObjectType.PAGE
                        else None
                    ),
                    database_ids=(
                        chunk_ids
                        if objects_type == NotionObjectType.DATABASE
                        else None
                    ),
                )
                all_documents.extend(documents)
                logging.info(
                    f"[{i}/{num_chunks}] Added {len(documents)} documents"
                )
            except Exception as e:
                logging.error(
                    f"[{i}/{num_chunks}] Export failed for {objects_type.name}: {chunk_ids}. {e}"
                )
                failed_exports.extend(chunk_ids)

        return all_documents, failed_exports

    def _get_ids_from_home_page(self) -> Tuple[List[str], List[str]]:
        """Extract database and page IDs from home page database.

        Queries the configured home page database and extracts IDs for
        both databases and pages.

        Returns:
            Tuple containing:
                - List of database IDs
                - List of page IDs
        """
        logging.info(
            f"Fetching all object ids from Notion's home page with limit {self.export_limit}..."
        )
        response = self._collect_paginated_api(
            function=self.notion_client.databases.query,
            limit=self.export_limit,
            database_id=self.home_page_database_id,
        )
        database_ids = [
            entry["id"] for entry in response if entry["object"] == "database"
        ]
        page_ids = [
            entry["id"] for entry in response if entry["object"] == "page"
        ]

        logging.info(
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

        logging.info(
            f"Fetching all ids of {objects_type.name} objects from Notion with limit {limit}..."
        )

        params = {
            "filter": {
                "value": objects_type.name.lower(),
                "property": "object",
            },
        }
        results = NotionReader._collect_paginated_api(
            self.notion_client.search, limit, **params
        )
        object_ids = [object["id"] for object in results]
        object_ids = object_ids[:limit] if limit is not None else object_ids

        logging.info(
            f"Found {len(object_ids)} ids of {objects_type.name} objects in Notion."
        )

        return object_ids

    def _get_current_limit(
        self, database_ids: List[str], page_ids: List[str]
    ) -> int:
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

            if NotionReader._limit_reached(result, limit):
                return result[:limit]
            if not NotionReader._has_more_pages(response):
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
