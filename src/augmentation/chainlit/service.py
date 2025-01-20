from chainlit.data.sql_alchemy import BaseDataLayer
from chainlit.types import Feedback

from augmentation.chainlit.feedback import ChainlitFeedbackService
from common.bootstrap.configuration.pipeline.augmentation.langfuse.langfuse_configuration import (
    LangfuseDatasetConfiguration,
)
from common.langfuse.dataset import LangfuseDatasetService


class ChainlitService(BaseDataLayer):
    """Data layer implementation for Chainlit integration with Langfuse.

    Handles persistence of feedback and dataset management through Langfuse.

    Attributes:
        manual_dataset: Configuration for manual dataset in Langfuse.
        feedback_service: Service handling Chainlit feedback persistence.
    """

    def __init__(
        self,
        langfuse_dataset_service: LangfuseDatasetService,
        feedback_service: ChainlitFeedbackService,
        manual_dataset: LangfuseDatasetConfiguration,
    ):
        """Initialize the Chainlit service.

        Args:
            langfuse_dataset_service: Service for managing Langfuse datasets.
            feedback_service: Service handling Chainlit feedback.
            manual_dataset: Configuration for manual dataset.
        """
        self.manual_dataset = manual_dataset
        self.feedback_service = feedback_service

        langfuse_dataset_service.create_if_does_not_exist(self.manual_dataset)

    async def upsert_feedback(self, feedback: Feedback) -> bool:
        """Upsert Chainlit feedback to Langfuse database.

        Args:
            feedback: Feedback object containing user feedback details.

        Returns:
            bool: True if feedback was successfully upserted, False otherwise.
        """
        return await self.feedback_service.upsert(feedback)
