from abc import ABC, abstractmethod
from typing import AsyncIterator, List

from extraction.datasources.core.base.document import BaseDocument
from extraction.datasources.core.base.manager import BaseDatasourceManager


class BaseDatasourceOrchestrator(ABC):
    """Abstract base class for datasource orchestration.

    Defines interface for managing content extraction, embedding generation,
    and vector storage operations across datasources.

    This class serves as a coordinator for multiple datasource managers,
    providing unified methods for extracting and processing documents
    from various data sources in both full and incremental sync modes.

    Note:
        All implementing classes must provide concrete implementations
        of extract, embed, save and update methods.
    """

    def __init__(
        self,
        datasource_managers: List[BaseDatasourceManager],
    ):
        """Initialize the orchestrator with datasource managers.

        Args:
            datasource_managers: A list of datasource manager instances that
                                 implement the BaseDatasourceManager interface.
                                 These managers handle the actual data extraction
                                 from specific datasource types.
        """
        self.datasource_managers = datasource_managers

    @abstractmethod
    async def full_refresh_sync(self) -> AsyncIterator[BaseDocument]:
        """Extract content from configured datasources.

        Performs asynchronous content extraction from all configured
        datasource implementations. This method should perform a complete
        refresh of all available content from the datasources, regardless
        of previous sync state.

        Returns:
            An asynchronous iterator yielding BaseDocument objects representing
            the extracted content from all datasources.
        """
        pass

    @abstractmethod
    async def incremental_sync(self) -> AsyncIterator[BaseDocument]:
        """Perform an incremental sync from configured datasources.

        Extracts only new or modified content since the last sync operation.
        This method is designed for efficient regular updates without
        re-processing unchanged content.

        Returns:
            An asynchronous iterator yielding BaseDocument objects representing
            newly added or modified content from all datasources.
        """
        pass
