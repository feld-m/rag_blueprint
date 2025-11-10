"""
DIP API Client for Bundestag datasource using deutschland package.

This client provides access to the DIP (Dokumentations- und Informationssystem
für Parlamentsmaterialien) API, which is the official German Bundestag API
for parliamentary materials.
"""

import logging
from typing import Any, Dict, Iterator, List, Optional

from deutschland import dip_bundestag
from deutschland.dip_bundestag.api import (
    drucksachen_api,
    plenarprotokolle_api,
    vorgnge_api,
)
from pydantic import BaseModel, ConfigDict


class DIPDocument(BaseModel):
    """
    Unified model for all DIP data types.

    This wrapper provides a consistent interface for different
    document types from the DIP API (protocols, drucksachen, proceedings).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    source_type: str  # "protocol", "proceeding", "drucksache"
    content: Dict[str, Any]  # Raw content from deutschland package

    @property
    def text(self) -> str:
        """Extract text based on source type."""
        if self.source_type in ["protocol", "drucksache"]:
            return self.content.get("text", "")
        elif self.source_type == "proceeding":
            # For proceedings, use abstract as text
            return self.content.get("abstract", "")
        return ""


class DIPClient:
    """
    Client for DIP (Dokumentations- und Informationssystem) API.

    Uses the deutschland Python package for API access, providing
    access to plenary protocols, printed materials, and proceedings.
    """

    DEFAULT_API_KEY = "OSOegLs.PR2lwJ1dwCeje9vTj7FPOt3hvpYKtwKkhw"

    def __init__(
        self,
        api_key: Optional[str] = None,
        wahlperiode: int = 21,
        fetch_sources: Optional[List[str]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize DIP client.

        Args:
            api_key: DIP API key. If not provided, uses public test key.
            wahlperiode: Electoral period number (default: 20).
            fetch_sources: List of data sources to fetch.
                Options: "protocols", "drucksachen", "proceedings"
            logger: Logger instance for logging.
        """
        self.api_key = api_key or self.DEFAULT_API_KEY
        self.wahlperiode = wahlperiode
        self.fetch_sources = fetch_sources or ["protocols", "drucksachen"]
        self.logger = logger or logging.getLogger(__name__)

        # Configure deutschland package
        self.configuration = dip_bundestag.Configuration(
            host="https://search.dip.bundestag.de/api/v1"
        )
        # Use query parameter auth (more reliable)
        self.configuration.api_key["ApiKeyQuery"] = self.api_key

        self.logger.info(
            f"Initialized DIP client for Wahlperiode {self.wahlperiode}, "
            f"sources: {self.fetch_sources}"
        )

    def fetch_all(self) -> Iterator[DIPDocument]:
        """
        Fetch all enabled data sources.

        Yields:
            DIPDocument instances wrapping different content types.
        """
        with dip_bundestag.ApiClient(self.configuration) as api_client:
            if "protocols" in self.fetch_sources:
                yield from self._fetch_protocols(api_client)

            if "drucksachen" in self.fetch_sources:
                yield from self._fetch_drucksachen(api_client)

            if "proceedings" in self.fetch_sources:
                yield from self._fetch_proceedings(api_client)

    def _fetch_protocols(self, api_client) -> Iterator[DIPDocument]:
        """
        Fetch plenary protocols with full text.

        Args:
            api_client: deutschland API client instance.

        Yields:
            DIPDocument instances for protocols.
        """
        self.logger.info(
            f"Fetching protocols for Wahlperiode {self.wahlperiode}"
        )

        protokoll_api = plenarprotokolle_api.PlenarprotokolleApi(api_client)

        try:
            # Get list of protocols - need to paginate to find Bundestag protocols
            # The API returns Bundesrat protocols first, so we need to paginate
            all_bt_protocols = []
            cursor = "*"
            max_pages = 10  # Limit pagination to avoid excessive API calls
            page_count = 0

            while cursor and page_count < max_pages:
                response = protokoll_api.get_plenarprotokoll_list(
                    f_wahlperiode=self.wahlperiode, format="json", cursor=cursor
                )

                # Filter for Bundestag protocols only (not Bundesrat)
                # herausgeber is a Zuordnung object, need to convert to string
                bt_protocols = [
                    p
                    for p in response.documents
                    if str(getattr(p, "herausgeber", "")) == "BT"
                ]
                all_bt_protocols.extend(bt_protocols)

                # Check if we have more results
                cursor = getattr(response, "cursor", None)
                page_count += 1

                self.logger.debug(
                    f"Page {page_count}: Found {len(bt_protocols)} BT protocols, "
                    f"total so far: {len(all_bt_protocols)}"
                )

                # Stop if we have enough
                if len(all_bt_protocols) >= 50:  # Reasonable limit for testing
                    break

            protocol_ids = [p.id for p in all_bt_protocols]

            self.logger.info(
                f"Found {len(protocol_ids)} Bundestag protocols "
                f"for Wahlperiode {self.wahlperiode} (across {page_count} pages)"
            )

            # Fetch full text for each protocol
            for protocol_id in protocol_ids:
                try:
                    # API expects integer ID
                    fulltext = protokoll_api.get_plenarprotokoll_text(
                        id=int(protocol_id), format="json"
                    )

                    # Only yield if we have text
                    if hasattr(fulltext, "text") and fulltext.text:
                        # Convert to dict for serialization
                        content_dict = fulltext.to_dict()

                        yield DIPDocument(
                            source_type="protocol", content=content_dict
                        )

                        dokumentnummer = getattr(
                            fulltext, "dokumentnummer", "unknown"
                        )
                        text_length = len(fulltext.text)
                        self.logger.debug(
                            f"Fetched protocol {dokumentnummer} "
                            f"({text_length} chars)"
                        )

                except Exception as e:
                    self.logger.warning(
                        f"Failed to fetch protocol {protocol_id}: {e}"
                    )
                    continue

        except Exception as e:
            self.logger.error(f"Failed to list protocols: {e}", exc_info=True)

    def _fetch_drucksachen(self, api_client) -> Iterator[DIPDocument]:
        """
        Fetch printed materials (drucksachen) with full text.

        Args:
            api_client: deutschland API client instance.

        Yields:
            DIPDocument instances for drucksachen.
        """
        self.logger.info(
            f"Fetching drucksachen for Wahlperiode {self.wahlperiode}"
        )

        drucksache_api = drucksachen_api.DrucksachenApi(api_client)

        try:
            cursor = None
            fetched_count = 0
            page = 1

            while True:
                # Fetch page of documents
                cursor_param = cursor if cursor else ""
                response = drucksache_api.get_drucksache_list(
                    f_wahlperiode=self.wahlperiode,
                    cursor=cursor_param,
                    format="json",
                )

                # Try to get full text for each document
                for doc_meta in response.documents:
                    try:
                        fulltext = drucksache_api.get_drucksache_text(
                            id=doc_meta.id, format="json"
                        )

                        # Only yield if we have text
                        if hasattr(fulltext, "text") and fulltext.text:
                            # Convert to dict for serialization
                            content_dict = fulltext.to_dict()

                            yield DIPDocument(
                                source_type="drucksache", content=content_dict
                            )

                            fetched_count += 1

                    except Exception:
                        # Many drucksachen don't have full text, log at debug level
                        self.logger.debug(
                            f"No full text for drucksache {doc_meta.id}"
                        )
                        continue

                # Log progress
                self.logger.info(
                    f"Drucksachen: page {page} complete, "
                    f"{fetched_count} with full text so far"
                )

                # Check pagination
                new_cursor = getattr(response, "cursor", None)
                if not new_cursor or new_cursor == cursor:
                    break

                cursor = new_cursor
                page += 1

            self.logger.info(
                f"Completed fetching drucksachen. "
                f"Total with full text: {fetched_count}"
            )

        except Exception as e:
            self.logger.error(
                f"Failed to fetch drucksachen: {e}", exc_info=True
            )

    def _fetch_proceedings(self, api_client) -> Iterator[DIPDocument]:
        """
        Fetch proceedings (vorgänge) - legislative processes.

        Args:
            api_client: deutschland API client instance.

        Yields:
            DIPDocument instances for proceedings.
        """
        self.logger.info(
            f"Fetching proceedings for Wahlperiode {self.wahlperiode}"
        )

        vorgang_api = vorgnge_api.VorgngeApi(api_client)

        try:
            cursor = None
            fetched_count = 0
            page = 1

            while True:
                # Fetch page of proceedings
                cursor_param = cursor if cursor else ""
                response = vorgang_api.get_vorgang_list(
                    f_wahlperiode=self.wahlperiode,
                    cursor=cursor_param,
                    format="json",
                )

                for vorgang in response.documents:
                    # Convert to dict for serialization
                    content_dict = vorgang.to_dict()

                    yield DIPDocument(
                        source_type="proceeding", content=content_dict
                    )

                    fetched_count += 1

                # Log progress
                self.logger.info(
                    f"Proceedings: page {page} complete, "
                    f"{fetched_count} total so far"
                )

                # Check pagination
                new_cursor = getattr(response, "cursor", None)
                if not new_cursor or new_cursor == cursor:
                    break

                cursor = new_cursor
                page += 1

            self.logger.info(
                f"Completed fetching proceedings. " f"Total: {fetched_count}"
            )

        except Exception as e:
            self.logger.error(
                f"Failed to fetch proceedings: {e}", exc_info=True
            )
