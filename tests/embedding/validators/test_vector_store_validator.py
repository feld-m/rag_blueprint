import sys
from typing import Type, Union
from unittest.mock import Mock

import pytest

from common.bootstrap.configuration.pipeline.embedding.vector_store.vector_store_configuration import (
    VectorStoreConfiguration,
)
from embedding.validators.vector_store_validators import (
    ChromaVectorStoreValidator,
    QdrantVectorStoreValidator,
)

sys.path.append("./src")


from chromadb.api import ClientAPI as ChromaClient
from qdrant_client import QdrantClient

from common.exceptions import CollectionExistsException


class Fixtures:

    def __init__(self):
        self.collection_name: str = None
        self.configuration: VectorStoreConfiguration = None
        self.client: Union[QdrantClient, ChromaClient] = None

    def with_configuration(self, collection_name: str) -> "Fixtures":
        self.collection_name = collection_name
        self.configuration: VectorStoreConfiguration = Mock(
            spec=VectorStoreConfiguration
        )
        self.configuration.collection_name = collection_name
        return self

    def with_qdrant_client(self) -> "Fixtures":
        self.client = Mock(spec=QdrantClient)
        return self

    def with_chroma_client(self) -> "Fixtures":
        self.client = Mock(spec=ChromaClient)
        return self


class Arrangements:

    def __init__(self, fixtures: Fixtures, validator_class: Type) -> None:
        self.fixtures = fixtures

        self.service = validator_class(
            self.fixtures.configuration,
            self.fixtures.client,
        )

    def on_qdrant_client_collection_exists_return_true(self) -> "Arrangements":
        self.fixtures.client.collection_exists.return_value = True
        return self

    def on_qdrant_client_collection_exists_return_false(
        self,
    ) -> "Arrangements":
        self.fixtures.client.collection_exists.return_value = False
        return self

    def on_chroma_client_list_collections_has_collection_name(
        self,
    ) -> "Arrangements":
        self.fixtures.client.list_collections.return_value = [
            self.fixtures.collection_name
        ]
        return self

    def on_chroma_client_list_collections_is_empty(self) -> "Arrangements":
        self.fixtures.client.list_collections.return_value = []
        return self


class Assertions:

    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures


class Manager:

    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.assertions = Assertions(arrangements)

    def get_service(self) -> QdrantVectorStoreValidator:
        return self.arrangements.service


class TestQdrantVectorStoreValidator:

    @pytest.mark.parametrize(
        "collection_name",
        ["col1", "col2", "col3"],
    )
    def test_given_existing_qdrant_collection_when_validate_collection_then_exception_raised(
        self, collection_name: str
    ):
        # Arrange
        manager = Manager(
            Arrangements(
                Fixtures()
                .with_configuration(collection_name)
                .with_qdrant_client(),
                QdrantVectorStoreValidator,
            ).on_qdrant_client_collection_exists_return_true()
        )
        service = manager.get_service()

        # Act-Assert
        with pytest.raises(CollectionExistsException):
            service.validate_collection()

    @pytest.mark.parametrize(
        "collection_name",
        ["col1", "col2", "col3"],
    )
    def test_given_non_existing_qdrant_collection_when_validate_collection_then_nothing_happens(
        self, collection_name: str
    ) -> None:
        # Arrange
        manager = Manager(
            Arrangements(
                Fixtures()
                .with_configuration(collection_name)
                .with_qdrant_client(),
                QdrantVectorStoreValidator,
            ).on_qdrant_client_collection_exists_return_false()
        )
        service = manager.get_service()

        # Act
        service.validate_collection()

    @pytest.mark.parametrize(
        "collection_name",
        ["col1", "col2", "col3"],
    )
    def test_given_existing_chroma_collection_when_validate_collection_then_exception_raised(
        self, collection_name: str
    ):
        # Arrange
        manager = Manager(
            Arrangements(
                Fixtures()
                .with_configuration(collection_name)
                .with_chroma_client(),
                ChromaVectorStoreValidator,
            ).on_chroma_client_list_collections_has_collection_name()
        )
        service = manager.get_service()

        # Act-Assert
        with pytest.raises(CollectionExistsException):
            service.validate_collection()

    @pytest.mark.parametrize(
        "collection_name",
        ["col1", "col2", "col3"],
    )
    def test_given_non_existing_chroma_collection_when_validate_collection_then_nothing_happens(
        self, collection_name: str
    ) -> None:
        # Arrange
        manager = Manager(
            Arrangements(
                Fixtures()
                .with_configuration(collection_name)
                .with_chroma_client(),
                ChromaVectorStoreValidator,
            ).on_chroma_client_list_collections_is_empty()
        )
        service = manager.get_service()

        # Act
        service.validate_collection()
