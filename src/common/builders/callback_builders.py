from injector import inject
from langfuse.llama_index import LlamaIndexCallbackHandler
from llama_index.core.callbacks import CallbackManager


class CallbackManagerBuilder:
    """Builder for creating configured CallbackManager instances.

    Provides factory method to create CallbackManager with Langfuse handler.
    """

    @staticmethod
    @inject
    def build(handler: LlamaIndexCallbackHandler) -> CallbackManager:
        """Create a CallbackManager instance with configured handlers.

        Args:
            handler: LlamaIndex callback handler for Langfuse integration.

        Returns:
            CallbackManager: Configured manager instance with handlers.
        """
        return CallbackManager(handlers=[handler])
