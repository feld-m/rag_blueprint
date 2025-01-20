import sys

from embedding.datasources.notion.exporter import NotionExporter
from embedding.datasources.notion.reader import NotionReader

sys.path.append("./src")

from typing import List
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from notion_client import Client

from common.bootstrap.configuration.pipeline.embedding.datasources.datasources_configuration import (
    NotionDatasourceConfiguration,
)
from embedding.datasources.notion.document import NotionDocument


class Fixtures:

    def __init__(self):
        self.database_home_ids: List[str] = []
        self.page_home_ids: List[str] = []
        self.database_api_ids: List[str] = []
        self.page_api_ids: List[str] = []
        self.export_limit: int = None
        self.export_batch_size: int = None
        self.home_page_database_id: str = None
        self.documents: List[NotionDocument] = []

    def with_database_home_ids(
        self, number_of_home_databases: int
    ) -> "Fixtures":
        self.database_home_ids = [
            str(uuid4()) for _ in range(number_of_home_databases)
        ]
        return self

    def with_page_home_ids(self, number_of_home_pages: int) -> "Fixtures":
        self.page_home_ids = [str(uuid4()) for _ in range(number_of_home_pages)]
        return self

    def with_database_api_ids(self, number_of_api_databases: int) -> "Fixtures":
        self.database_api_ids = [
            {"id": str(uuid4())} for _ in range(number_of_api_databases)
        ]
        return self

    def with_page_api_ids(self, number_of_api_pages: int) -> "Fixtures":
        self.page_api_ids = [
            {"id": str(uuid4())} for _ in range(number_of_api_pages)
        ]
        return self

    def with_export_limit(self, export_limit: int) -> "Fixtures":
        self.export_limit = export_limit
        return self

    def with_export_batch_size(self, export_batch_size: int) -> "Fixtures":
        self.export_batch_size = export_batch_size
        return self

    def with_home_page_database_id(self) -> "Fixtures":
        self.home_page_database_id = str(uuid4())
        return self


class Arrangements:

    def __init__(self, fixtures: Fixtures) -> None:
        self.fixtures = fixtures

        self.configuration: NotionDatasourceConfiguration = Mock(
            spec=NotionDatasourceConfiguration
        )
        self.configuration.export_limit = fixtures.export_limit
        self.configuration.export_batch_size = fixtures.export_batch_size
        self.configuration.home_page_database_id = (
            fixtures.home_page_database_id
        )
        self.notion_client: Client = Mock(spec=Client)
        self.exporter: NotionExporter = Mock(spec=NotionExporter)
        self.service = NotionReader(
            configuration=self.configuration,
            notion_client=self.notion_client,
            exporter=self.exporter,
        )

    def on_get_ids_from_home_page_return_ids(self) -> "Arrangements":
        NotionReader._get_ids_from_home_page = Mock(
            return_value=(
                self.fixtures.database_home_ids,
                self.fixtures.page_home_ids,
            )
        )
        return self

    def on_notion_client_search_return_ids(self) -> "Arrangements":
        def mock_search(**kwargs):
            if kwargs["filter"]["value"] == "database":
                return {
                    "results": self.fixtures.database_api_ids,
                    "next_cursor": str(uuid4()),
                }
            elif kwargs["filter"]["value"] == "page":
                return {
                    "results": self.fixtures.page_api_ids,
                    "next_cursor": str(uuid4()),
                }

        self.notion_client.search = Mock(side_effect=mock_search)
        return self

    def on_exporter_run_return_documents(self) -> "Arrangements":
        def mock_run(
            page_ids: List[str] = None, database_ids: List[str] = None
        ) -> List[NotionDocument]:
            number_of_documents = (
                len(page_ids) if page_ids else len(database_ids)
            )
            documents = [
                Mock(spec=NotionDocument) for _ in range(number_of_documents)
            ]
            self.fixtures.documents.extend(documents)
            return documents

        self.exporter.run = AsyncMock(side_effect=mock_run)
        return self


class Assertions:

    def __init__(self, arrangements: Arrangements) -> None:
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.service = arrangements.service

    def assert_documents_number(
        self,
        documents: List[NotionDocument],
        expected_number_of_documents: int,
    ) -> None:
        assert len(documents) <= expected_number_of_documents
        for document in documents:
            assert document in self.fixtures.documents
        return self


class Manager:

    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.assertions = Assertions(arrangements=arrangements)

    def get_service(self) -> NotionReader:
        return self.arrangements.service


class TestNotionReader:

    @pytest.mark.parametrize(
        "export_batch_size,export_limit,expected_number_of_documents,number_of_home_pages,number_of_home_databases,number_of_api_pages,number_of_api_databases",
        [
            (2, 10, 8, 2, 2, 2, 2),
            (2, 10, 10, 4, 2, 2, 2),
            (2, 10, 10, 4, 4, 4, 4),
            (4, 10, 8, 2, 2, 2, 2),
            (4, 10, 10, 4, 2, 2, 2),
            (4, 10, 10, 4, 4, 4, 4),
        ],
    )
    @pytest.mark.asyncio
    async def test(
        self,
        export_batch_size: int,
        export_limit: int,
        expected_number_of_documents: int,
        number_of_home_pages: int,
        number_of_home_databases: int,
        number_of_api_pages: int,
        number_of_api_databases: int,
    ) -> None:
        # Arrange
        manager = Manager(
            Arrangements(
                fixtures=Fixtures()
                .with_export_limit(export_limit)
                .with_export_batch_size(export_batch_size)
                .with_home_page_database_id()
                .with_database_home_ids(number_of_home_databases)
                .with_page_home_ids(number_of_home_pages)
                .with_database_api_ids(number_of_api_databases)
                .with_page_api_ids(number_of_api_pages)
            )
            .on_get_ids_from_home_page_return_ids()
            .on_notion_client_search_return_ids()
            .on_exporter_run_return_documents()
        )
        service = manager.get_service()

        # Act
        all_documents = await service.get_all_documents_async()

        # Assert
        manager.assertions.assert_documents_number(
            documents=all_documents,
            expected_number_of_documents=expected_number_of_documents,
        )
