import sys
from typing import List
from unittest.mock import AsyncMock, Mock

import pytest
from llama_index_client import Document, TextNode

from embedding.datasources.core.cleaner import BaseCleaner
from embedding.datasources.core.reader import BaseReader

sys.path.append("./src")


from common.bootstrap.configuration.pipeline.embedding.embedding_configuration import (
    EmbeddingConfiguration,
)
from embedding.datasources.core.manager import DatasourceManager
from embedding.datasources.core.splitter import BaseSplitter


class Fixtures:

    def __init__(self):
        self.documents: List[Document] = None
        self.cleaned_documents: List[Document] = None
        self.nodes: List[TextNode] = None

    def with_documents(self) -> "Fixtures":
        self.documents = [Mock(spec=Document), Mock(spec=Document)]
        return self

    def with_cleaned_documents(self) -> "Fixtures":
        self.cleaned_documents = [Mock(spec=Document)]
        return self

    def with_nodes(self) -> "Fixtures":
        self.nodes = [Mock(spec=TextNode)]
        return self


class Arrangements:

    def __init__(self, fixtures: Fixtures) -> None:
        self.fixtures = fixtures

        self.configuration: EmbeddingConfiguration = Mock(
            spec=EmbeddingConfiguration
        )
        self.reader: BaseReader = Mock(spec=BaseReader)
        self.cleaner: BaseCleaner = Mock(spec=BaseCleaner)
        self.splitter: BaseSplitter = Mock(spec=BaseSplitter)
        self.service = DatasourceManager(
            configuration=self.configuration,
            reader=self.reader,
            cleaner=self.cleaner,
            splitter=self.splitter,
        )

    def on_get_all_documents_return_documents(self):
        self.reader.get_all_documents_async = AsyncMock(
            return_value=self.fixtures.documents
        )
        return self

    def on_cleaner_clean_return_cleaned_documents(self):
        self.cleaner.clean.return_value = self.fixtures.cleaned_documents
        return self

    def on_splitter_split_return_nodes(self):
        self.splitter.split.return_value = self.fixtures.nodes
        return self


class Assertions:

    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures

    def assert_documents_are_extracted(
        self, documents: List[Document]
    ) -> "Assertions":
        assert documents == self.fixtures.documents
        return self

    def assert_cleaned_documents_are_extracted(
        self, cleaned_documents: List[Document]
    ) -> "Assertions":
        assert cleaned_documents == self.fixtures.cleaned_documents
        return self

    def assert_nodes_are_extracted(self, nodes: List[TextNode]) -> "Assertions":
        assert nodes == self.fixtures.nodes
        return self


class Manager:

    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.assertions = Assertions(arrangements)

    def get_service(self) -> DatasourceManager:
        return self.arrangements.service


class TestDatasourceManager:

    @pytest.mark.asyncio
    async def test_given_when_extract_then_resources_are_extracted(
        self,
    ) -> None:
        # Arrange
        manager = Manager(
            Arrangements(
                Fixtures()
                .with_documents()
                .with_cleaned_documents()
                .with_nodes()
            )
            .on_get_all_documents_return_documents()
            .on_cleaner_clean_return_cleaned_documents()
            .on_splitter_split_return_nodes()
        )
        service = manager.get_service()

        # Act
        documents, cleaned_documents, nodes = await service.extract()

        # Assert
        manager.assertions.assert_documents_are_extracted(
            documents
        ).assert_cleaned_documents_are_extracted(
            cleaned_documents
        ).assert_nodes_are_extracted(
            nodes
        )
