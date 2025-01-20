from injector import singleton
from langfuse import Langfuse
from langfuse.llama_index import LlamaIndexCallbackHandler

from common.bootstrap.base_binder import BaseBinder
from common.bootstrap.configuration.pipeline.augmentation.langfuse.langfuse_binding_keys import (
    BoundFeedbackDatasetConfiguration,
    BoundManualDatasetConfiguration,
)
from common.bootstrap.configuration.pipeline.augmentation.langfuse.langfuse_configuration import (
    LangfuseConfiguration,
)
from common.langfuse.builders import (
    LangfuseCallbackHandlerBuilder,
    LangfuseClientBuilder,
    LangfuseDatasetServiceBuilder,
)
from common.langfuse.dataset import LangfuseDatasetService


class LangfuseBinder(BaseBinder):
    """Binder for the Langfuse service and callback handler."""

    def bind(self) -> None:
        """Bind components to the injector based on the configuration."""
        self._bind_configuration()
        self._bind_client()
        self._bind_callback()
        self._bind_dataset_service()
        self._bind_datasets()

    def _bind_configuration(self) -> None:
        """Bind the Langfuse configuration."""
        self.binder.bind(
            LangfuseConfiguration,
            to=lambda: self.configuration.pipeline.augmentation.langfuse,
            scope=singleton,
        )

    def _bind_client(self) -> None:
        """Bind the Langfuse client."""
        self.binder.bind(
            Langfuse,
            to=LangfuseClientBuilder.build,
            scope=singleton,
        )

    def _bind_callback(self) -> None:
        """Bind the Langfuse callback handler."""
        self.binder.bind(
            LlamaIndexCallbackHandler,
            to=LangfuseCallbackHandlerBuilder.build,
        )

    def _bind_dataset_service(self) -> None:
        """Bind the Langfuse dataset service."""
        self.binder.bind(
            LangfuseDatasetService,
            to=LangfuseDatasetServiceBuilder.build,
        )

    def _bind_datasets(self) -> None:
        """Bind the Langfuse datasets."""
        self.binder.bind(
            BoundFeedbackDatasetConfiguration,
            to=lambda: self.configuration.pipeline.augmentation.langfuse.datasets.feedback_dataset,
            scope=singleton,
        )
        self.binder.bind(
            BoundManualDatasetConfiguration,
            to=lambda: self.configuration.pipeline.augmentation.langfuse.datasets.manual_dataset,
            scope=singleton,
        )
