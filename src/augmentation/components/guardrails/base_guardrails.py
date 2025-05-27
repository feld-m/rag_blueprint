from abc import ABC, abstractmethod
from typing import Optional

from llama_index.core.chat_engine.types import AgentChatResponse


class BaseGuardrailsEngine(ABC):

    @abstractmethod
    def input_guard(
        self, message: str, is_stream: bool
    ) -> Optional[AgentChatResponse]:
        """
        Check if the input message is allowed based on guardrail rules.
        If it does it returns None, otherwise it returns an AgentChatResponse
        containing a message indicating the input is not allowed.

        Args:
            message: Generated response message to validate
            is_stream: Flag indicating if the response is a stream

        Returns:
            bool: None if the input is allowed, otherwise an AgentChatResponse
            containing a message indicating the input is not allowed.
        """
        pass

    @abstractmethod
    def output_guard(
        self, message: str, is_stream: bool
    ) -> Optional[AgentChatResponse]:
        """
        Check if the output message is allowed based on guardrail rules.
        If it does it returns None, otherwise it returns an AgentChatResponse
        containing a message indicating the output is not allowed.

        Args:
            message: User input message to validate
            is_stream: Flag indicating if the response is a stream

        Returns:
            bool: None if the output is allowed, otherwise an AgentChatResponse
            containing a message indicating the output is not allowed.
        """
        pass
