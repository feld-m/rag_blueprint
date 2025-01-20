import sys
from unittest.mock import Mock
from uuid import uuid4

sys.path.append("./src")
import pytest
from chainlit.types import Feedback

from augmentation.chainlit.feedback import ChainlitFeedbackService
from augmentation.chainlit.service import ChainlitService
from common.bootstrap.configuration.pipeline.augmentation.langfuse.langfuse_configuration import (
    LangfuseDatasetConfiguration,
)
from common.langfuse.dataset import LangfuseDatasetService


class Fixtures:

    def __init__(self):
        self.feedback: Feedback = None

    def with_feedback(self, value: int) -> "Fixtures":
        self.feedback = Feedback(
            forId=str(uuid4()),
            value=value,
        )
        return self


class Arrangements:

    def __init__(self, fixtures: Fixtures) -> None:
        self.fixtures = fixtures

        self.langfuse_dataset_service: LangfuseDatasetService = Mock(
            spec=LangfuseDatasetService
        )
        self.manual_dataset: LangfuseDatasetConfiguration = Mock(
            spec=LangfuseDatasetConfiguration
        )
        self.feedback_service: ChainlitFeedbackService = Mock(
            spec=ChainlitFeedbackService
        )
        self.service = ChainlitService(
            langfuse_dataset_service=self.langfuse_dataset_service,
            feedback_service=self.feedback_service,
            manual_dataset=self.manual_dataset,
        )


class Assertions:

    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements

    def assert_create_if_does_not_exist_called(self) -> "Assertions":
        self.arrangements.langfuse_dataset_service.create_if_does_not_exist.assert_called_once_with(
            self.arrangements.manual_dataset
        )
        return self

    def assert_feedback_service_upsert_called(self) -> "Assertions":
        self.arrangements.feedback_service.upsert.assert_called_once_with(
            self.fixtures.feedback
        )
        return self


class Manager:

    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.assertions = Assertions(arrangements)

    def get_service(self) -> ChainlitService:
        return self.arrangements.service


class TestChainlitService:

    @pytest.mark.asyncio
    async def test_given_when_service_init_then_manual_dataset_created(self):
        # Arrange
        manager = Manager(Arrangements(Fixtures()))
        manager.get_service()

        # Act
        # Assert
        manager.assertions.assert_create_if_does_not_exist_called()

    @pytest.mark.parametrize(
        "feedback_value",
        [1, 0],
    )
    @pytest.mark.asyncio
    async def test_given_feedback_when_upsert_feedback_then_feedback_service_is_invoked(
        self, feedback_value: int
    ):
        # Arrange
        manager = Manager(
            Arrangements(Fixtures().with_feedback(feedback_value))
        )
        service = manager.get_service()

        # Act
        await service.upsert_feedback(manager.fixtures.feedback)

        # Assert
        manager.assertions.assert_feedback_service_upsert_called()
