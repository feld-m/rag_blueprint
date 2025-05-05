import logging
from typing import AsyncIterator, Dict, List

from atlassian import Confluence
from pydantic import BaseModel, Field
from requests import HTTPError
from tqdm import tqdm

from core import Factory
from core.logger import LoggerConfiguration
from extraction.datasources.confluence.client import ConfluenceClientFactory
from extraction.datasources.confluence.configuration import (
    ConfluenceDatasourceConfiguration,
)
from extraction.datasources.core.reader import BaseReader


class Space(BaseModel):
    key: str


class BodyView(BaseModel):
    value: str


class Body(BaseModel):
    view: BodyView


class LastUpdated(BaseModel):
    when: str


class History(BaseModel):
    createdDate: str
    lastUpdated: LastUpdated


class Links(BaseModel):
    webui: str


class ConfluencePage(BaseModel):
    """Model representing a Confluence page from the API."""

    id: str
    title: str
    body: Body
    history: History
    links: Links = Field(alias="_links")
    expandable: Dict[str, str] = Field(alias="_expandable")


class ConfluenceDatasourceReader(BaseReader):
    """Reader for extracting documents from Confluence spaces.

    Implements document extraction from Confluence spaces, handling pagination
    and export limits.
    """

    def __init__(
        self,
        configuration: ConfluenceDatasourceConfiguration,
        client: Confluence,
        logger: logging.Logger = LoggerConfiguration.get_logger(__name__),
    ):
        """Initialize the Confluence reader.

        Args:
            configuration: Settings for Confluence access and export limits
            client: Client for Confluence API interactions
            logger: Logger instance for recording operation information
        """
        super().__init__()
        self.export_limit = configuration.export_limit
        self.client = client
        self.logger = logger

    async def read_all_async(
        self,
    ) -> AsyncIterator[ConfluencePage]:
        """Asynchronously fetch all documents from Confluence.

        Retrieves pages from all global spaces in Confluence, respecting the export limit.
        Yields each page as a ConfluencePage containing its content and metadata.

        Returns:
            AsyncIterator[ConfluencePage]: An async iterator of Confluence pages.
        """
        self.logger.info(
            f"Fetching pages from Confluence with limit {self.export_limit}"
        )
        response = self.client.get_all_spaces(space_type="global")
        spaces = [Space.model_validate(space) for space in response["results"]]

        yield_counter = 0

        for space in spaces:
            space_limit = (
                self.export_limit - yield_counter
                if self.export_limit is not None
                else None
            )
            if space_limit is not None and space_limit <= 0:
                break

            space_pages = self._get_all_pages(space.key, space_limit)
            for page in tqdm(
                space_pages,
                desc=f"[Confluence] Reading {space.key} space pages content",
                unit="pages",
            ):
                yield_counter += 1
                if (
                    self.export_limit is not None
                    and yield_counter > self.export_limit
                ):
                    break
                yield page

    def _get_all_pages(self, space: str, limit: int) -> List[ConfluencePage]:
        """Fetch all pages from a specific Confluence space.

        Handles pagination internally to retrieve all pages from the specified space,
        up to the optional limit. Pages include body content and update history.

        Args:
            space: Space key to fetch pages from
            limit: Maximum number of pages to fetch (None for unlimited)

        Returns:
            List[ConfluencePage]: List of Confluence pages with content and metadata
        """
        start = 0
        params = {
            "space": space,
            "start": start,
            "status": None,
            "expand": "body.view,history.lastUpdated",
        }
        all_pages = []

        try:
            while True:
                pages_raw = self.client.get_all_pages_from_space(**params)
                pages = [
                    ConfluencePage.model_validate(page) for page in pages_raw
                ]
                all_pages.extend(pages)

                if len(pages) == 0 or ConfluenceDatasourceReader._limit_reached(
                    all_pages, limit
                ):
                    break

                start = len(all_pages)
                params["start"] = start
        except HTTPError as e:
            self.logger.warning(f"Error while fetching pages from {space}: {e}")

        return all_pages if limit is None else all_pages[:limit]

    @staticmethod
    def _limit_reached(pages: List[ConfluencePage], limit: int) -> bool:
        """Check if the page retrieval limit has been reached.

        Determines whether the number of fetched pages has reached or exceeded
        the specified limit.

        Args:
            pages: List of already retrieved pages
            limit: Maximum number of pages to retrieve (None for unlimited)

        Returns:
            bool: True if limit reached or exceeded, False otherwise
        """
        return limit is not None and len(pages) >= limit


class ConfluenceDatasourceReaderFactory(Factory):
    """Factory for creating Confluence reader instances.

    Creates and configures ConfluenceDatasourceReader objects with appropriate
    clients based on the provided configuration.
    """

    _configuration_class = ConfluenceDatasourceConfiguration

    @classmethod
    def _create_instance(
        cls, configuration: ConfluenceDatasourceConfiguration
    ) -> ConfluenceDatasourceReader:
        """Creates a configured Confluence reader instance.

        Initializes the Confluence client and reader with the given configuration
        settings for credentials, URL, and export limits.

        Args:
            configuration: Confluence connection and access settings

        Returns:
            ConfluenceDatasourceReader: Fully configured reader instance
        """
        client = ConfluenceClientFactory.create(configuration)
        return ConfluenceDatasourceReader(
            configuration=configuration,
            client=client,
        )
