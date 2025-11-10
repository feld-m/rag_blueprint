import logging
from typing import AsyncIterator, Optional

from core import Factory
from core.logger import LoggerConfiguration
from extraction.datasources.bundestag.client import (
    BundestagMineClient,
    BundestagMineClientFactory,
)
from extraction.datasources.bundestag.client_dip import DIPClient
from extraction.datasources.bundestag.configuration import (
    BundestagMineDatasourceConfiguration,
)
from extraction.datasources.core.reader import BaseReader


class BundestagMineDatasourceReader(BaseReader):
    """Reader for extracting data from multiple Bundestag sources.

    Supports multiple data sources:
    - BundestagMine API: Individual speeches from parliamentary sessions
    - DIP API: Comprehensive parliamentary documents (protocols, drucksachen, proceedings)
    """

    def __init__(
        self,
        configuration: BundestagMineDatasourceConfiguration,
        client: Optional[BundestagMineClient] = None,
        dip_client: Optional[DIPClient] = None,
        logger: logging.Logger = LoggerConfiguration.get_logger(__name__),
    ):
        """Initialize the Bundestag reader with multiple data sources.

        Args:
            configuration: Settings for Bundestag data access and export limits
            client: Client for BundestagMine API interactions (optional)
            dip_client: Client for DIP API interactions (optional)
            logger: Logger instance for recording operation information
        """
        super().__init__()
        self.configuration = configuration
        self.export_limit = configuration.export_limit
        self.client = client
        self.dip_client = dip_client
        self.logger = logger

    async def read_all_async(
        self,
    ) -> AsyncIterator[dict]:
        """Asynchronously fetch all documents from enabled Bundestag sources.

        Yields documents from multiple sources based on configuration:
        - BundestagMine: Individual speeches
        - DIP: Comprehensive parliamentary documents

        Each enabled source gets the full export_limit, so if both sources are
        enabled with export_limit=2, you get 2 documents from each source (4 total).

        Returns:
            AsyncIterator[dict]: An async iterator of document dictionaries containing
            content and metadata such as text, speaker data, and last update information
        """
        self.logger.info(
            f"Reading Bundestag documents with limit {self.export_limit} per source"
        )

        # Source 1: BundestagMine speeches
        if self.configuration.include_bundestag_mine and self.client:
            self.logger.info(
                f"Fetching speeches from BundestagMine API (limit: {self.export_limit})..."
            )
            speech_iterator = self.client.fetch_all_speeches()
            mine_counter = 0

            for speech in speech_iterator:
                if self._limit_reached(mine_counter, self.export_limit):
                    break

                self.logger.info(
                    f"Fetched BundestagMine speech {mine_counter + 1}/{self.export_limit}."
                )
                mine_counter += 1
                yield speech

        # Source 2: DIP API documents
        if self.configuration.include_dip and self.dip_client:
            self.logger.info(
                f"Fetching documents from DIP API (limit: {self.export_limit})..."
            )
            dip_iterator = self.dip_client.fetch_all()
            dip_counter = 0

            for dip_document in dip_iterator:
                if self._limit_reached(dip_counter, self.export_limit):
                    break

                self.logger.info(
                    f"Fetched DIP document {dip_counter + 1}/{self.export_limit}."
                )
                dip_counter += 1
                yield dip_document


class BundestagMineDatasourceReaderFactory(Factory):
    """Factory for creating Bundestag reader instances.

    Creates and configures BundestagMineDatasourceReader objects with appropriate
    clients based on the provided configuration. Supports multiple data sources
    including BundestagMine and DIP APIs.
    """

    _configuration_class = BundestagMineDatasourceConfiguration

    @classmethod
    def _create_instance(
        cls, configuration: BundestagMineDatasourceConfiguration
    ) -> BundestagMineDatasourceReader:
        """Creates a configured Bundestag reader instance.

        Initializes the appropriate clients (BundestagMine and/or DIP) based on
        configuration settings.

        Args:
            configuration: Bundestag connection and access settings

        Returns:
            BundestagMineDatasourceReader: Fully configured reader instance
        """
        # Create BundestagMine client if enabled
        bundestag_mine_client = None
        if configuration.include_bundestag_mine:
            bundestag_mine_client = BundestagMineClientFactory.create(
                configuration
            )

        # Create DIP client if enabled
        dip_client = None
        if configuration.include_dip:
            dip_client = DIPClient(
                api_key=configuration.dip_api_key,
                wahlperiode=configuration.dip_wahlperiode,
                fetch_sources=configuration.dip_sources,
            )

        return BundestagMineDatasourceReader(
            configuration=configuration,
            client=bundestag_mine_client,
            dip_client=dip_client,
        )
