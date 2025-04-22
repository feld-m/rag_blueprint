import sys
from typing import AsyncGenerator, List
from unittest.mock import Mock

sys.path.append("./src")

import pytest
from llama_index.core import Document
from llama_index.core.schema import TextNode

from embedding.bootstrap.configuration.configuration import (
    EmbeddingConfiguration,
)
from extraction.datasources.core.base.manager import BasicDatasourceManager
from extraction.datasources.core.base.reader import BaseReader


class Fixtures:
    def __init__(self):
        self.raw_data: List[Document] = None
        self.cleaned_documents: List[Document] = None
        self.nodes: List[TextNode] = None

    def with_raw_data(self) -> "Fixtures":
        self.raw_data = ["Raw markdown text", "Raw markdown text 2"]
        return self

    def with_nodes(self) -> "Fixtures":
        self.nodes = [Mock(spec=TextNode)]
        return self


class Arrangements:
    def __init__(self, fixtures: Fixtures) -> None:
        self.fixtures = fixtures

        self.configuration: EmbeddingConfiguration = Mock(spec=EmbeddingConfiguration)
        self.reader: BaseReader = Mock(spec=BaseReader)
        self.service = BasicDatasourceManager(
            configuration=self.configuration,
            reader=self.reader,
        )

    def on_read_all_async_return_documents(self) -> "Arrangements":
        async def mock_read_all_async() -> AsyncGenerator[str, None]:
            for markdown in self.fixtures.raw_data:
                yield markdown

        self.reader.read_all_async = mock_read_all_async
        return self


class Assertions:
    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures

    async def assert_documents_are_extracted(
        self, document_generator: AsyncGenerator[Document, None]
    ) -> "Assertions":
        async for document in document_generator:
            assert isinstance(document, Document)
        return self


class Manager:
    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.assertions = Assertions(arrangements)

    def get_service(self) -> BasicDatasourceManager:
        return self.arrangements.service


class TestDatasourceManager:
    @pytest.mark.asyncio
    async def test_given_when_full_refresh_sync_then_resources_are_extracted(
        self,
    ) -> None:
        # Arrange
        manager = Manager(
            Arrangements(
                Fixtures().with_raw_data()
            ).on_read_all_async_return_documents()
        )
        service = manager.get_service()

        # Act
        documents_generator = service.full_refresh_sync()

        # Assert
        await manager.assertions.assert_documents_are_extracted(documents_generator)
