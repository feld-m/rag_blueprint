import logging

from langfuse.api.resources.commons.errors.not_found_error import NotFoundError
from langfuse.client import DatasetClient, Langfuse

from common.bootstrap.configuration.pipeline.augmentation.langfuse.langfuse_configuration import (
    LangfuseDatasetConfiguration,
)


class LangfuseDatasetService:
    """Service for managing Langfuse datasets.

    Provides methods to create and retrieve datasets in Langfuse platform.

    Attributes:
        langfuse_client: Client instance for Langfuse API interactions.
    """

    def __init__(self, langfuse_client: Langfuse):
        """Initialize the dataset service.

        Args:
            langfuse_client: Client for Langfuse API interactions.
        """
        self.langfuse_client = langfuse_client

    def create_if_does_not_exist(
        self, dataset: LangfuseDatasetConfiguration
    ) -> None:
        """Create dataset in Langfuse if it doesn't exist.

        Args:
            dataset: Configuration containing dataset details.

        Note:
            NotFoundError exception is caught but still logged due to
            Langfuse implementation.
        """
        try:
            self.langfuse_client.get_dataset(dataset.name)
            logging.info(f"Dataset {dataset.name} exists.")
        except NotFoundError:
            logging.info(f"Dataset {dataset.name} does not exist. Creating...")
            self.langfuse_client.create_dataset(
                name=dataset.name,
                description=dataset.description,
                metadata=dataset.metadata,
            )

    def get_dataset(self, dataset_name: str) -> DatasetClient:
        """Retrieve a dataset client by name.

        Args:
            dataset_name: Name of the dataset to retrieve.

        Returns:
            DatasetClient: Client for interacting with the specified dataset.
        """
        return self.langfuse_client.get_dataset(dataset_name)
