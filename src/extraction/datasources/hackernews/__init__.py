from extraction.bootstrap.configuration.datasources import (
    DatasourceConfigurationRegistry,
    DatasourceName,
)
from extraction.datasources.hackernews.configuration import (
    HackerNewsDatasourceConfiguration,
)
from extraction.datasources.hackernews.manager import (
    HackerNewsDatasourceManagerFactory,
)
from extraction.datasources.registry import DatasourceManagerRegistry


def register() -> None:
    DatasourceManagerRegistry.register(
        DatasourceName.HACKERNEWS, HackerNewsDatasourceManagerFactory
    )
    DatasourceConfigurationRegistry.register(
        DatasourceName.HACKERNEWS, HackerNewsDatasourceConfiguration
    )