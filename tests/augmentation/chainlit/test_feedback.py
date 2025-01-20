import sys
from unittest.mock import Mock
from uuid import uuid4

sys.path.append("./src")
import pytest
from chainlit.types import Feedback
from langfuse import Langfuse
from langfuse.api.resources.commons.types.observations_view import (
    ObservationsView,
)
from langfuse.api.resources.commons.types.trace_with_details import (
    TraceWithDetails,
)
from langfuse.client import FetchObservationsResponse, FetchTracesResponse

from augmentation.chainlit.feedback import ChainlitFeedbackService
from common.bootstrap.configuration.pipeline.augmentation.langfuse.langfuse_configuration import (
    LangfuseDatasetConfiguration,
)
from common.langfuse.dataset import LangfuseDatasetService


class Fixtures:

    def __init__(self):
        self.message_id: str = None
        self.feedback: Feedback = None
        self.trace: TraceWithDetails = None
        self.observation: ObservationsView = None

    def with_feedback(self, value: int) -> "Fixtures":
        self.message_id = str(uuid4())
        self.feedback = Feedback(
            forId=self.message_id,
            value=value,
        )
        return self

    def with_negative_feedback(self) -> "Fixtures":
        return self.with_feedback(0)

    def with_positive_feedback(self) -> "Fixtures":
        return self.with_feedback(1)

    def with_trace(self) -> "Fixtures":
        self.trace = Mock(spec=TraceWithDetails)
        self.trace.id = str(uuid4())
        self.trace.input = "input"
        self.trace.output = {
            "text": "output",
            "raw": {
                "model": "model",
            },
        }
        return self

    def with_observation(self) -> "Fixtures":
        self.observation = Mock(spec=ObservationsView)
        self.observation.id = str(uuid4())
        self.observation.input = "input"
        self.observation.output = {"nodes": []}
        self.observation.createdAt = "2021-01-01T00:00:00.000Z"
        return self


class Arrangements:

    def __init__(self, fixtures: Fixtures):
        self.fixtures = fixtures

        self.langfuse_dataset_service: LangfuseDatasetService = Mock(
            spec=LangfuseDatasetService
        )
        self.langfuse_client: Langfuse = Mock(spec=Langfuse)
        self.feedback_dataset: LangfuseDatasetConfiguration = Mock(
            spec=LangfuseDatasetConfiguration
        )
        self.feedback_dataset.name = "feedback_dataset"
        self.chainlit_tag_format: str = "chainlit_tag_format: {message_id}"
        self.service = ChainlitFeedbackService(
            langfuse_dataset_service=self.langfuse_dataset_service,
            langfuse_client=self.langfuse_client,
            feedback_dataset=self.feedback_dataset,
            chainlit_tag_format=self.chainlit_tag_format,
        )

    def on_fetch_traces_return_no_traces(self) -> "Arrangements":
        self.langfuse_client.fetch_traces.return_value = FetchTracesResponse(
            data=[], meta=None
        )
        return self

    def on_fetch_traces_return_trace(self) -> "Arrangements":
        self.langfuse_client.fetch_traces.return_value = FetchTracesResponse(
            data=[self.fixtures.trace], meta=None
        )
        return self

    def on_fetch_observation_return_observation(self) -> "Arrangements":
        self.langfuse_client.fetch_observations.return_value = (
            FetchObservationsResponse(
                data=[self.fixtures.observation], meta=None
            )
        )
        return self


class Assertions:

    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements

    def assert_result_is_false(self, result: bool) -> "Assertions":
        assert result is False
        return self

    def assert_result_is_true(self, result: bool) -> "Assertions":
        assert result is True
        return self

    def assert_fetch_traces_called_with_message_id(self) -> "Assertions":
        self.arrangements.langfuse_client.fetch_traces.assert_called_with(
            tags=[
                self.arrangements.chainlit_tag_format.format(
                    message_id=self.fixtures.message_id
                )
            ]
        )
        return self

    def assert_score_called(self) -> "Assertions":
        self.arrangements.langfuse_client.score.assert_called_with(
            trace_id=self.fixtures.trace.id,
            name=ChainlitFeedbackService.SCORE_NAME,
            value=self.fixtures.feedback.value,
            comment=self.fixtures.feedback.comment,
        )
        return self

    def assert_score_never_called(self) -> "Assertions":
        self.arrangements.langfuse_client.score.assert_not_called()
        return self

    def assert_create_dataset_item_called(self) -> "Assertions":
        self.arrangements.langfuse_client.create_dataset_item.assert_called()
        return self

    def assert_create_dataset_item_never_called(self) -> "Assertions":
        self.arrangements.langfuse_client.create_dataset_item.assert_not_called()
        return self


class Manager:

    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.assertions = Assertions(arrangements)

    def get_service(self) -> ChainlitFeedbackService:
        return self.arrangements.service


class TestChainlitFeedbackService:

    @pytest.mark.parametrize(
        "feedback_value",
        [1, 0],
    )
    @pytest.mark.asyncio
    async def test_given_non_existing_message_id_when_upsert_then_feedback_not_upserted(
        self, feedback_value: int
    ) -> None:
        # Arrange
        manager = Manager(
            Arrangements(
                Fixtures().with_feedback(feedback_value)
            ).on_fetch_traces_return_no_traces()
        )
        service = manager.get_service()

        # Act
        result = await service.upsert(manager.fixtures.feedback)

        # Assert
        manager.assertions.assert_result_is_false(
            result
        ).assert_fetch_traces_called_with_message_id().assert_score_never_called()

    @pytest.mark.asyncio
    async def test_given_negative_feedback_when_upsert_then_feedback_not_saved_in_dataset(
        self,
    ):
        # Arrange
        manager = Manager(
            Arrangements(
                Fixtures().with_negative_feedback().with_trace()
            ).on_fetch_traces_return_trace()
        )
        service = manager.get_service()

        # Act
        result = await service.upsert(manager.fixtures.feedback)

        # Assert
        manager.assertions.assert_result_is_true(
            result
        ).assert_score_called().assert_create_dataset_item_never_called()

    @pytest.mark.asyncio
    async def test_given_positive_feedback_when_upsert_then_feedback_saved_in_dataset(
        self,
    ):
        # Arrange
        manager = Manager(
            Arrangements(
                Fixtures()
                .with_positive_feedback()
                .with_trace()
                .with_observation()
            )
            .on_fetch_traces_return_trace()
            .on_fetch_observation_return_observation()
        )
        service = manager.get_service()

        # Act
        result = await service.upsert(manager.fixtures.feedback)

        # Assert
        manager.assertions.assert_result_is_true(
            result
        ).assert_score_called().assert_create_dataset_item_called()
