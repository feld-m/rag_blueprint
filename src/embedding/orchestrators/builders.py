from injector import inject

from common.bootstrap.configuration.pipeline.embedding.datasources.datasources_binding_keys import (
    BoundDatasourceManagers,
)
from embedding.embedders.default_embedder import Embedder
from embedding.orchestrators.datasource_orchestrator import (
    DatasourceOrchestrator,
)


class DatasourceOrchestratorBuilder:
    """Builder for creating datasource orchestrator instances.

    Provides factory method to create configured DatasourceOrchestrator
    with validated datasource managers.
    """

    @staticmethod
    @inject
    def build(
        datasource_managers: BoundDatasourceManagers,
        embedder: Embedder,
    ) -> DatasourceOrchestrator:
        """Create configured orchestrator instance.

        Args:
            embedder: Component for generating embeddings
            datasource_managers: Dictionary of mapped datasource managers

        Returns:
            DatasourceOrchestrator: Configured orchestrator with validated managers
        """
        return DatasourceOrchestrator(
            datasource_managers=datasource_managers,
            embedder=embedder,
        )
