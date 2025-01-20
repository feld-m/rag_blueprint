import sys
from unittest.mock import Mock

import pytest

from common.bootstrap.configuration.pipeline.embedding.vector_store.vector_store_configuration import (
    VectorStoreConfiguration,
)
from embedding.validators.vector_store_validators import (
    QdrantVectorStoreValidator,
)

sys.path.append("./src")


from qdrant_client import QdrantClient

from common.exceptions import QdrantCollectionExistsException


class Fixtures:

    def __init__(self):
        self.collection_name: str = None

    def with_collection_name(self) -> "Fixtures":
        self.collection_name = "collection_name"
        return self


class Arrangements:

    def __init__(self, fixtures: Fixtures) -> None:
        self.fixtures = fixtures

        self.configuration: VectorStoreConfiguration = Mock(
            spec=VectorStoreConfiguration
        )
        self.qdrant_client = Mock(spec=QdrantClient)
        self.service = QdrantVectorStoreValidator(
            configuration=self.configuration,
            qdrant_client=self.qdrant_client,
        )

    def with_collection_name(self) -> "Arrangements":
        self.configuration.collection_name = self.fixtures.collection_name
        return self

    def on_qdrant_client_collection_exists_return_true(self) -> "Arrangements":
        self.qdrant_client.collection_exists.return_value = True
        return self

    def on_qdrant_client_collection_exists_return_false(
        self,
    ) -> "Arrangements":
        self.qdrant_client.collection_exists.return_value = False
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

    def test_given_existing_collection_when_validate_qdrant_collection_then_exception_raised(
        self,
    ):
        # Arrange
        manager = Manager(
            Arrangements(Fixtures().with_collection_name())
            .with_collection_name()
            .on_qdrant_client_collection_exists_return_true()
        )
        service = manager.get_service()

        # Act-Assert
        with pytest.raises(QdrantCollectionExistsException):
            service.validate_qdrant_collection()

    def test_given_non_existing_collection_when_validate_qdrant_collection_then_nothing_happens(
        self,
    ) -> None:
        # Arrange
        manager = Manager(
            Arrangements(Fixtures().with_collection_name())
            .with_collection_name()
            .on_qdrant_client_collection_exists_return_false()
        )
        service = manager.get_service()

        # Act
        service.validate_qdrant_collection()

        # Assert
