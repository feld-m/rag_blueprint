import logging

from chainlit.types import Feedback
from langfuse import Langfuse
from langfuse.api.resources.commons.types.observations_view import (
    ObservationsView,
)
from langfuse.api.resources.commons.types.trace_with_details import (
    TraceWithDetails,
)

from common.bootstrap.configuration.pipeline.augmentation.langfuse.langfuse_configuration import (
    LangfuseDatasetConfiguration,
)
from common.exceptions import TraceNotFoundException
from common.langfuse.dataset import LangfuseDatasetService


class ChainlitFeedbackService:
    """Service for handling Chainlit feedback and Langfuse integration.

    This service associates feedbacks with value, comment and message, and persists
    information about retrieved nodes used for message generation in Langfuse database
    as trace scores. This allows feedback display in the Langfuse UI.

    Attributes:
        SCORE_NAME: Name used for feedback scores in Langfuse.
        langfuse_dataset_service: Service for managing Langfuse datasets.
        langfuse_client: Client for Langfuse API interactions.
        feedback_dataset: Configuration for feedback dataset.
        chainlit_tag_format: Format string for trace retrieval tags.
    """

    SCORE_NAME = "User Feedback"

    def __init__(
        self,
        langfuse_dataset_service: LangfuseDatasetService,
        langfuse_client: Langfuse,
        feedback_dataset: LangfuseDatasetConfiguration,
        chainlit_tag_format: str,
    ):
        """Initialize the feedback service.

        Args:
            langfuse_dataset_service: Service for managing Langfuse datasets.
            langfuse_client: Client for Langfuse API interactions.
            feedback_dataset: Configuration for feedback dataset.
            chainlit_tag_format: Format string for trace retrieval tags.
        """
        self.langfuse_dataset_service = langfuse_dataset_service
        self.langfuse_client = langfuse_client
        self.feedback_dataset = feedback_dataset
        self.chainlit_tag_format = chainlit_tag_format

        self.langfuse_dataset_service.create_if_does_not_exist(feedback_dataset)

    async def upsert(self, feedback: Feedback) -> bool:
        """Upsert Chainlit feedback to Langfuse database.

        Updates or inserts feedback as a score of associated trace and saves positive
        feedback in the associated dataset.

        Args:
            feedback: Feedback object containing value and comment.

        Returns:
            bool: True if feedback was successfully upserted, False otherwise.
        """
        trace = None
        try:
            trace = self._fetch_trace(feedback.forId)

            if self._is_positive(feedback):
                logging.info(
                    f"Uploading trace {trace.id} to dataset {self.feedback_dataset.name}."
                )
                self._upload_trace_to_dataset(trace)

            self.langfuse_client.score(
                trace_id=trace.id,
                name=ChainlitFeedbackService.SCORE_NAME,
                value=feedback.value,
                comment=feedback.comment,
            )
            logging.info(
                f"Upserted feedback for {trace.id} trace with value {feedback.value}."
            )
            return True
        except Exception as e:
            trace_id = trace.id if trace else None
            logging.warning(
                f"Failed to upsert feedback for {trace_id} trace: {e}"
            )
            return False

    def _fetch_trace(self, message_id: str) -> TraceWithDetails:
        """Fetch trace by message ID.

        Args:
            message_id: Message identifier to fetch trace for.

        Returns:
            TraceWithDetails: Found trace object.

        Raises:
            TraceNotFoundException: If no trace is found for message ID.
        """
        response = self.langfuse_client.fetch_traces(
            tags=[self.chainlit_tag_format.format(message_id=message_id)]
        )
        trace = response.data[0] if response.data else None
        if trace is None:
            raise TraceNotFoundException(message_id)
        return trace

    def _upload_trace_to_dataset(self, trace: TraceWithDetails) -> None:
        """Upload trace details to feedback dataset.

        Args:
            trace: Trace object containing interaction details.
        """
        retrieve_observation = self._fetch_last_retrieve_observation(trace)
        last_templating_observation = self._fetch_last_templating_observation(
            trace
        )
        self.langfuse_client.create_dataset_item(
            dataset_name=self.feedback_dataset.name,
            input={
                "query_str": trace.input,
                "nodes": retrieve_observation.output.get("nodes"),
                "templating": last_templating_observation.input,
            },
            expected_output={
                "result": trace.output.get("text"),
            },
            source_trace_id=trace.id,
            metadata={
                "generated_by": trace.output.get("raw").get("model"),
            },
        )

    def _fetch_last_retrieve_observation(
        self, trace: TraceWithDetails
    ) -> ObservationsView:
        """Fetch most recent retrieve observation for trace.

        Args:
            trace: Trace object containing observations.

        Returns:
            ObservationsView: Latest retrieve observation sorted by creation time.
        """
        retrieve_observations = self.langfuse_client.fetch_observations(
            trace_id=trace.id,
            name="retrieve",
        )
        return max(retrieve_observations.data, key=lambda x: x.createdAt)

    def _fetch_last_templating_observation(
        self, trace: TraceWithDetails
    ) -> ObservationsView:
        """Fetch most recent templating observation for trace.

        Args:
            trace: Trace object containing observations.

        Returns:
            ObservationsView: Latest templating observation sorted by creation time.
        """
        templating_observations = self.langfuse_client.fetch_observations(
            trace_id=trace.id,
            name="templating",
        )
        return max(templating_observations.data, key=lambda x: x.createdAt)

    @staticmethod
    def _is_positive(feedback: Feedback) -> bool:
        """Check if feedback value is positive.

        Args:
            feedback: Feedback object containing user feedback.

        Returns:
            bool: True if feedback value is greater than 0.
        """
        return feedback.value > 0
