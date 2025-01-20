import logging
from typing import List

from atlassian import Confluence
from requests import HTTPError
from tqdm import tqdm

from common.bootstrap.configuration.pipeline.embedding.datasources.datasources_configuration import (
    ConfluenceDatasourceConfiguration,
)
from embedding.datasources.confluence.document import ConfluenceDocument
from embedding.datasources.core.reader import BaseReader


class ConfluenceReader(BaseReader):
    """Reader for extracting documents from Confluence spaces.

    Implements document extraction from Confluence spaces, handling pagination
    and export limits. Supports both synchronous and asynchronous retrieval.

    Attributes:
        export_limit: Maximum number of documents to extract
        confluence_client: Client for Confluence API interactions
    """

    def __init__(
        self,
        configuration: ConfluenceDatasourceConfiguration,
        confluence_client: Confluence,
    ):
        """Initialize the Confluence reader.

        Args:
            configuration: Settings for Confluence access and limits
            confluence_client: Client for Confluence API interactions
        """
        super().__init__()
        self.export_limit = configuration.export_limit
        self.confluence_client = confluence_client

    def get_all_documents(self) -> List[ConfluenceDocument]:
        """Synchronously fetch all documents from Confluence.

        Returns:
            List[ConfluenceDocument]: List of extracted documents

        Note:
            Not implemented - use get_all_documents_async instead.
        """
        pass

    async def get_all_documents_async(self) -> List[ConfluenceDocument]:
        """Asynchronously fetch all documents from Confluence.

        Retrieves documents from all global spaces, respecting export limit.

        Returns:
            List[ConfluenceDocument]: List of extracted and processed documents
        """
        logging.info(
            f"Fetching documents from Confluence with limit {self.export_limit}"
        )
        response = self.confluence_client.get_all_spaces(space_type="global")
        pages = []

        for space in response["results"]:
            space_limit = (
                self.export_limit - len(pages)
                if self.export_limit is not None
                else None
            )
            pages.extend(self._get_all_pages(space["key"], space_limit))
            if (
                self.export_limit is not None
                and len(pages) >= self.export_limit
            ):
                break

        pages = (
            pages if self.export_limit is None else pages[: self.export_limit]
        )
        documents = [
            ConfluenceDocument.from_page(page, self.confluence_client.url)
            for page in pages
        ]
        return documents

    def _get_all_pages(self, space: str, limit: int) -> List[dict]:
        """Fetch all pages from a Confluence space.

        Args:
            space: Space key to fetch pages from
            limit: Maximum number of pages to fetch (None for unlimited)

        Returns:
            List[dict]: List of page details from the space
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
            with tqdm(
                desc=f"[Confluence] Reading {space}'s pages content",
                unit="pages",
            ) as pbar:
                while True:
                    pages = self.confluence_client.get_all_pages_from_space(
                        **params
                    )
                    all_pages.extend(pages)
                    pbar.update(len(pages))

                    if len(pages) == 0 or ConfluenceReader._limit_reached(
                        all_pages, limit
                    ):
                        break

                    start = len(all_pages)
                    params["start"] = start
        except HTTPError as e:
            logging.debug(f"Error while fetching pages from {space}: {e}")

        return all_pages if limit is None else all_pages[:limit]

    @staticmethod
    def _limit_reached(pages: List[dict], limit: int) -> bool:
        """Check if page limit has been reached.

        Args:
            pages: List of retrieved pages
            limit: Maximum number of pages (None for unlimited)

        Returns:
            bool: True if limit reached, False otherwise
        """
        return limit is not None and len(pages) >= limit
