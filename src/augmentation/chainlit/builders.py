from injector import inject
from langfuse import Langfuse

from augmentation.chainlit.feedback import ChainlitFeedbackService
from augmentation.chainlit.service import ChainlitService
from common.bootstrap.configuration.pipeline.augmentation.langfuse.langfuse_binding_keys import (
    BoundFeedbackDatasetConfiguration,
    BoundManualDatasetConfiguration,
)
from common.bootstrap.configuration.pipeline.augmentation.langfuse.langfuse_configuration import (
    LangfuseConfiguration,
)
from common.langfuse.dataset import LangfuseDatasetService


class ChainlitFeedbackServiceBuilder:

    @staticmethod
    @inject
    def build(
        langfuse_dataset_service: LangfuseDatasetService,
        langfuse_client: Langfuse,
        feedback_dataset: BoundFeedbackDatasetConfiguration,
        configuration: LangfuseConfiguration,
    ) -> ChainlitFeedbackService:
        """Build and return the Chainlit feedback service.

        Args:
            langfuse_dataset_service: Service for managing Langfuse datasets.
            langfuse_client: Client for interacting with Langfuse API.
            feedback_dataset: Configuration for feedback dataset.
            configuration: General Langfuse configuration settings.

        Returns:
            ChainlitFeedbackService: Configured feedback service instance.
        """
        return ChainlitFeedbackService(
            langfuse_dataset_service=langfuse_dataset_service,
            langfuse_client=langfuse_client,
            feedback_dataset=feedback_dataset,
            chainlit_tag_format=configuration.chainlit_tag_format,
        )


class ChainlitServiceBuilder:

    @staticmethod
    @inject
    def build(
        langfuse_dataset_service: LangfuseDatasetService,
        feedback_service: ChainlitFeedbackService,
        manual_dataset: BoundManualDatasetConfiguration,
    ) -> ChainlitService:
        """Build and return a ChainlitService instance.

        Args:
            langfuse_dataset_service: Service for managing Langfuse datasets.
            feedback_service: Service handling Chainlit feedback.
            manual_dataset: Configuration for manual dataset.

        Returns:
            ChainlitService: Configured Chainlit service instance.
        """
        return ChainlitService(
            langfuse_dataset_service=langfuse_dataset_service,
            feedback_service=feedback_service,
            manual_dataset=manual_dataset,
        )
