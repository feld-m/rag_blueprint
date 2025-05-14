import sys

sys.path.append("./src")

from typing import List
from unittest.mock import Mock
from uuid import uuid4

from langfuse.client import StatefulTraceClient
from langfuse.llama_index.llama_index import LlamaIndexCallbackHandler
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.callbacks import CallbackManager
from llama_index.core.llms.llm import LLM
from llama_index.core.memory import BaseMemory
from llama_index.core.postprocessor.types import BaseNodePostprocessor

from augmentation.components.chat_engines.langfuse.chat_engine import (
    GuardrailsEngine,
    LangfuseChatEngine,
)


class Fixtures:
    def __init__(self):
        self.langfuse_callback_handler: LlamaIndexCallbackHandler = None
        self.session_id: str = None

    def with_langfuse_callback_handler(self) -> "Fixtures":
        self.langfuse_callback_handler = Mock(spec=LlamaIndexCallbackHandler)
        self.langfuse_callback_handler.trace = Mock(spec=StatefulTraceClient)
        return self

    def with_session_id(self) -> "Fixtures":
        self.session_id = str(uuid4())
        return self


class Arrangements:
    def __init__(self, fixtures: Fixtures):
        self.fixtures = fixtures

        self.retriever: BaseRetriever = Mock(spec=BaseRetriever)
        self.llm: LLM = Mock(spec=LLM)
        self.memory: BaseMemory = Mock(spec=BaseMemory)
        self.postprocessors: List[BaseNodePostprocessor] = []
        self.callback_manager: CallbackManager = Mock(spec=CallbackManager)
        self.chainlit_tag_format: str = "tag_format: {message_id}"
        self.guardrails_engine = Mock(spec=GuardrailsEngine)

        self.service = LangfuseChatEngine(
            retriever=self.retriever,
            llm=self.llm,
            memory=self.memory,
            node_postprocessors=self.postprocessors,
            callback_manager=self.callback_manager,
            chainlit_tag_format=self.chainlit_tag_format,
            guardrails_engine=self.guardrails_engine,
        )

    def add_langfuse_callback_handler_to_callback_manager(
        self,
    ) -> "Arrangements":
        self.callback_manager.handlers = [
            self.fixtures.langfuse_callback_handler
        ]
        return self

    def on_input_guard_skip(self) -> "Arrangements":
        self.guardrails_engine.input_guard = Mock(return_value=None)
        return self

    def on_output_guard_skip(self) -> "Arrangements":
        self.guardrails_engine.output_guard = Mock(return_value=None)
        return self


class Assertions:
    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements

    def assert_trace_is_returned(self, trace) -> "Assertions":
        assert trace == self.fixtures.langfuse_callback_handler.trace
        return self

    def assert_session_id_is_set(self) -> "Assertions":
        self.fixtures.langfuse_callback_handler.session_id = (
            self.fixtures.session_id
        )
        return self


class Manager:
    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.assertions = Assertions(arrangements)

    def get_service(self) -> LangfuseChatEngine:
        return self.arrangements.service


class TestChatEngine:
    def test_given_langfuse_callback_handler_when_get_current_langfuse_trace_then_trace_is_returned(
        self,
    ) -> None:
        # Arrange
        manager = Manager(
            Arrangements(Fixtures().with_langfuse_callback_handler())
            .add_langfuse_callback_handler_to_callback_manager()
            .on_input_guard_skip()
            .on_output_guard_skip()
        )
        service = manager.get_service()

        # Act
        trace = service.get_current_langfuse_trace()

        # Assert
        manager.assertions.assert_trace_is_returned(trace)

    def test_given_session_id_when_set_session_id_then_session_id_is_set(
        self,
    ) -> None:
        # Arrange
        manager = Manager(
            Arrangements(
                Fixtures().with_langfuse_callback_handler().with_session_id()
            )
            .add_langfuse_callback_handler_to_callback_manager()
            .on_input_guard_skip()
            .on_output_guard_skip()
        )
        service = manager.get_service()

        # Act
        service.set_session_id(session_id=manager.fixtures.session_id)

        # Assert
        manager.assertions.assert_session_id_is_set()
