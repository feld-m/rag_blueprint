from augmentation.chainlit.builders import (
    ChainlitFeedbackServiceBuilder,
    ChainlitServiceBuilder,
)
from augmentation.chainlit.feedback import ChainlitFeedbackService
from augmentation.chainlit.service import ChainlitService
from common.bootstrap.base_binder import BaseBinder


class ChainlitBinder(BaseBinder):
    """Binder for the Chainlit service and feedback service."""

    def bind(self) -> None:
        """Bind components to the injector based on the configuration."""
        self._bind_feedback_service()
        self._bind_service()

    def _bind_feedback_service(self) -> None:
        """Bind the Chainlit feedback service."""
        self.binder.bind(
            ChainlitFeedbackService,
            to=ChainlitFeedbackServiceBuilder.build,
        )

    def _bind_service(self) -> None:
        """Bind the Chainlit service."""
        self.binder.bind(
            ChainlitService,
            to=ChainlitServiceBuilder.build,
        )
