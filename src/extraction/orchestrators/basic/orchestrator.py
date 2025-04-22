from typing import AsyncIterator, Type

from core import Factory
from extraction.bootstrap.configuration.configuration import (
    ExtractionConfiguration,
)
from extraction.datasources.core.base.document import BaseDocument
from extraction.datasources.registry import DatasourceManagerRegistry
from extraction.orchestrators.base_orchestator import BaseDatasourceOrchestrator


class BasicDatasourceOrchestrator(BaseDatasourceOrchestrator):
    """
    Orchestrator for multi-datasource content processing.
    """

    async def full_refresh_sync(self) -> AsyncIterator[BaseDocument]:
        """Extract and process content from all datasources.

        Processes each configured datasource to extract documents and clean content.

        Returns:
            AsyncIterator[BaseDocument]: Stream of documents extracted from all datasources
        """
        for datasource_manager in self.datasource_managers:
            async for document in datasource_manager.full_refresh_sync():
                yield document

    async def incremental_sync(self) -> AsyncIterator[BaseDocument]:
        """
        Not implemented yet.
        """
        raise NotImplementedError("Incremental sync is not supported yet.")


class BasicDatasourceOrchestratorFactory(Factory):
    """Factory for creating BasicDatasourceOrchestrator instances.

    Creates orchestrator instances configured with appropriate datasource managers
    based on the provided extraction configuration.
    """

    _configuration_class: Type = ExtractionConfiguration

    @classmethod
    def _create_instance(
        cls, configuration: ExtractionConfiguration
    ) -> BasicDatasourceOrchestrator:
        """Creates a configured BasicDatasourceOrchestrator.

        Initializes datasource managers for each configured datasource
        and creates an orchestrator instance with those managers.

        Args:
            configuration: Settings for extraction process configuration

        Returns:
            BasicDatasourceOrchestrator: Configured orchestrator instance
        """
        datasource_managers = [
            DatasourceManagerRegistry.get(datasource_configuration.name).create(
                datasource_configuration
            )
            for datasource_configuration in configuration.extraction.datasources
        ]
        return BasicDatasourceOrchestrator(
            datasource_managers=datasource_managers
        )
