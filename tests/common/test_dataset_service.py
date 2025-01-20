import sys

from common.bootstrap.configuration.pipeline.augmentation.langfuse.langfuse_configuration import (
    LangfuseDatasetConfiguration,
)

sys.path.append("./src")

from unittest.mock import Mock

from langfuse.api.resources.commons.errors.not_found_error import NotFoundError
from langfuse.client import DatasetClient, Langfuse

from common.langfuse.dataset import LangfuseDatasetService


class Fixtures:

    def __init__(self):
        self.langfuse_dataset_configuration: LangfuseDatasetConfiguration = None

    def with_langfuse_dataset_configuration(self) -> "Fixtures":
        self.langfuse_dataset_configuration = LangfuseDatasetConfiguration(
            name="dataset_name",
            description="dataset_description",
            metadata={"key": "value"},
        )
        return self

    def with_dataset_client(self) -> "Fixtures":
        self.dataset_client = Mock(spec=DatasetClient)
        return self


class Arrangements:

    def __init__(self, fixtures: Fixtures):
        self.fixtures = fixtures
        self.langfuse_client = Mock(spec=Langfuse)
        self.service = LangfuseDatasetService(
            langfuse_client=self.langfuse_client
        )

    def with_existing_dataset(self) -> "Arrangements":
        self.langfuse_client.get_dataset.return_value = (
            self.fixtures.dataset_client
        )
        return self

    def with_non_existing_dataset(self) -> "Arrangements":
        self.langfuse_client.get_dataset.side_effect = NotFoundError(
            "Error message"
        )
        return self


class Assertions:

    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements

    def assert_get_dataset_called(self) -> "Assertions":
        self.arrangements.langfuse_client.get_dataset.assert_called_once_with(
            self.arrangements.fixtures.langfuse_dataset_configuration.name
        )
        return self

    def assert_create_dataset_called(self) -> "Assertions":
        self.arrangements.langfuse_client.create_dataset.assert_called_once_with(
            name=self.arrangements.fixtures.langfuse_dataset_configuration.name,
            description=self.arrangements.fixtures.langfuse_dataset_configuration.description,
            metadata=self.arrangements.fixtures.langfuse_dataset_configuration.metadata,
        )
        return self

    def assert_dataset_client_is_returned(
        self, dataset_client: DatasetClient
    ) -> "Assertions":
        assert dataset_client is self.arrangements.fixtures.dataset_client
        return self


class Manager:

    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.assertions = Assertions(arrangements)

    def get_service(self) -> LangfuseDatasetService:
        return self.arrangements.service


class TestLangfuseDatasetService:

    def test_given_existing_dataset_when_create_if_does_not_exist_then_nothing_happens(
        self,
    ):
        # Arrange
        manager = Manager(
            Arrangements(
                Fixtures()
                .with_langfuse_dataset_configuration()
                .with_dataset_client()
            ).with_existing_dataset()
        )
        service = manager.get_service()

        # Act
        service.create_if_does_not_exist(
            manager.fixtures.langfuse_dataset_configuration
        )

        # Assert
        manager.assertions.assert_get_dataset_called()

    def test_given_non_existing_dataset_when_create_if_does_not_exist_then_nothing_happens(
        self,
    ):
        # Arrange
        manager = Manager(
            Arrangements(
                Fixtures().with_langfuse_dataset_configuration()
            ).with_non_existing_dataset()
        )
        service = manager.get_service()

        # Act
        service.create_if_does_not_exist(
            manager.fixtures.langfuse_dataset_configuration
        )

        # Assert
        manager.assertions.assert_get_dataset_called().assert_create_dataset_called()

    def test_given_dataset_name_when_get_dataset_then_dataset_is_returned(
        self,
    ):
        # Arrange
        manager = Manager(
            Arrangements(
                Fixtures()
                .with_langfuse_dataset_configuration()
                .with_dataset_client()
            ).with_existing_dataset()
        )
        service = manager.get_service()

        # Act
        dataset_client = service.get_dataset(
            manager.fixtures.langfuse_dataset_configuration.name
        )

        # Assert
        manager.assertions.assert_dataset_client_is_returned(dataset_client)
