import sys

from common.bootstrap.configuration.pipeline.embedding.datasources.datasources_configuration import (
    DatasourceName,
)
from embedding.datasources.core.manager import BaseDatasourceManager
from embedding.embedders.base import BaseEmbedder
from embedding.orchestrators.datasource_orchestrator import (
    DatasourceOrchestrator,
)

sys.path.append("./src")

from typing import Dict, List
from unittest.mock import AsyncMock, Mock

import pytest
from llama_index_client import Document, TextNode


class Fixtures:

    def __init__(self):
        self.datasources: List[DatasourceName] = None
        self.documents: Dict[DatasourceName, List[Document]] = {}
        self.cleaned_documents: Dict[DatasourceName, List[Document]] = {}
        self.nodes: Dict[DatasourceName, List[TextNode]] = {}

    def with_datasources(self, datasources: List[DatasourceName]) -> "Fixtures":
        self.datasources = datasources
        return self

    def with_documents(self) -> "Fixtures":
        for datasource in self.datasources:
            self.documents[datasource] = [
                Mock(spec=Document),
                Mock(spec=Document),
            ]
        return self

    def with_cleaned_documents(self) -> "Fixtures":
        for datasource in self.datasources:
            self.cleaned_documents[datasource] = [Mock(spec=Document)]
        return self

    def with_nodes(self) -> "Fixtures":
        for datasource in self.datasources:
            self.nodes[datasource] = [Mock(spec=TextNode)]
        return self


class Arrangements:

    def __init__(self, fixtures: Fixtures) -> None:
        self.fixtures = fixtures

        self.datasource_manager: Dict[DatasourceName, BaseDatasourceManager] = {
            datasource: Mock(spec=BaseDatasourceManager)
            for datasource in self.fixtures.datasources
        }

        self.embedder: BaseEmbedder = Mock(spec=BaseEmbedder)
        self.service = DatasourceOrchestrator(
            datasource_managers=self.datasource_manager, embedder=self.embedder
        )

    def on_datasource_manager_extract_return_resources(self) -> "Arrangements":
        for datasource in self.fixtures.datasources:
            self.datasource_manager[datasource].extract = AsyncMock(
                return_value=(
                    self.fixtures.documents[datasource],
                    self.fixtures.cleaned_documents[datasource],
                    self.fixtures.nodes[datasource],
                )
            )
        return self

    def mock_embedder_embed(self) -> "Arrangements":
        self.embedder.embed = Mock()
        return self

    def add_nodes_to_service(self) -> "Arrangements":
        for datasource in self.fixtures.datasources:
            self.service.nodes.extend(self.fixtures.nodes[datasource])
        return self


class Assertions:

    def __init__(self, arrangements: Arrangements) -> None:
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.service = arrangements.service

    def assert_extracted_resources(self) -> "Assertions":
        all_documents = []
        all_cleaned_documents = []
        all_nodes = []
        for datasource in self.fixtures.datasources:
            self.arrangements.datasource_manager[
                datasource
            ].extract.assert_called_once()
            all_documents.extend(self.fixtures.documents[datasource])
            all_cleaned_documents.extend(
                self.fixtures.cleaned_documents[datasource]
            )
            all_nodes.extend(self.fixtures.nodes[datasource])
        assert self.service.documents == all_documents
        assert self.service.cleaned_documents == all_cleaned_documents
        assert self.service.nodes == all_nodes
        return self

    def assert_embedded_nodes(self) -> "Assertions":
        all_nodes = [
            node for nodes in self.fixtures.nodes.values() for node in nodes
        ]
        self.arrangements.embedder.embed.assert_called_once_with(all_nodes)
        return self

    def assert_saved_nodes(self) -> "Assertions":
        all_nodes = [
            node for nodes in self.fixtures.nodes.values() for node in nodes
        ]
        self.arrangements.embedder.save.assert_called_once_with(all_nodes)
        return self


class Manager:

    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.assertions = Assertions(arrangements=arrangements)

    def get_service(self) -> DatasourceOrchestrator:
        return self.arrangements.service


class TestDatasourceOrchestrator:

    @pytest.mark.parametrize(
        "datasources",
        [
            [DatasourceName.NOTION],
            [DatasourceName.CONFLUENCE],
            [DatasourceName.PDF],
            [
                DatasourceName.NOTION,
                DatasourceName.CONFLUENCE,
                DatasourceName.PDF,
            ],
        ],
    )
    @pytest.mark.asyncio
    async def test_given_when_extract_then_resources_are_extracted(
        self, datasources: List[DatasourceName]
    ) -> None:
        # Arrange
        manager = Manager(
            Arrangements(
                Fixtures()
                .with_datasources(datasources)
                .with_documents()
                .with_cleaned_documents()
                .with_nodes()
            ).on_datasource_manager_extract_return_resources()
        )
        service = manager.get_service()

        # Act
        await service.extract()

        # Assert
        manager.assertions.assert_extracted_resources()

    @pytest.mark.parametrize(
        "datasources",
        [
            [DatasourceName.NOTION],
            [DatasourceName.CONFLUENCE],
            [DatasourceName.PDF],
            [
                DatasourceName.NOTION,
                DatasourceName.CONFLUENCE,
                DatasourceName.PDF,
            ],
        ],
    )
    def test_given_nodes_when_embed_then_nodes_are_embedded(
        self, datasources: List[DatasourceName]
    ) -> None:
        # Arrange
        manager = Manager(
            Arrangements(Fixtures().with_datasources(datasources).with_nodes())
            .mock_embedder_embed()
            .add_nodes_to_service()
        )
        service = manager.get_service()

        # Act
        service.embed()

        # Assert
        manager.assertions.assert_embedded_nodes()

    @pytest.mark.parametrize(
        "datasources",
        [
            [DatasourceName.NOTION],
            [DatasourceName.CONFLUENCE],
            [DatasourceName.PDF],
            [
                DatasourceName.NOTION,
                DatasourceName.CONFLUENCE,
                DatasourceName.PDF,
            ],
        ],
    )
    def test_given_nodes_when_save_to_vector_storage_then_nodes_are_saved(
        self, datasources: List[DatasourceName]
    ) -> None:
        # Arrange
        manager = Manager(
            Arrangements(Fixtures().with_datasources(datasources).with_nodes())
            .mock_embedder_embed()
            .add_nodes_to_service()
        )
        service = manager.get_service()

        # Act
        service.save_to_vector_storage()

        # Assert
        manager.assertions.assert_saved_nodes()
