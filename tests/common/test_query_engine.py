import sys

sys.path.append("./src")

from typing import List
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from langfuse.client import StatefulTraceClient
from langfuse.llama_index.llama_index import LlamaIndexCallbackHandler
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.callbacks import CallbackManager
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.query_engine import CustomQueryEngine
from llama_index.core.response_synthesizers.base import BaseSynthesizer

from common.query_engine import RagQueryEngine, SourceProcess


class Fixtures:

    def __init__(self):
        self.message_id: str = None
        self.source_process: SourceProcess = None
        self.langfuse_callback_handler: LlamaIndexCallbackHandler = None
        self.query_str: str = None
        self.session_id: str = None

    def with_source_process(self, source_process: SourceProcess) -> "Fixtures":
        self.source_process = source_process
        return self

    def with_message_id(self) -> "Fixtures":
        self.message_id = str(uuid4())
        return self

    def with_langfuse_callback_handler(self) -> "Fixtures":
        self.langfuse_callback_handler = Mock(spec=LlamaIndexCallbackHandler)
        self.langfuse_callback_handler.trace = Mock(spec=StatefulTraceClient)
        return self

    def with_query_str(self) -> "Fixtures":
        self.query_str = "query_str"
        return self

    def with_session_id(self) -> "Fixtures":
        self.session_id = str(uuid4())
        return self


class Arrangements:

    def __init__(self, fixtures: Fixtures):
        self.fixtures = fixtures

        self.retriever: BaseRetriever = Mock(spec=BaseRetriever)
        self.postprocessors: List[BaseNodePostprocessor] = []
        self.synthesier: BaseSynthesizer = Mock(spec=BaseSynthesizer)
        self.callback_manager: CallbackManager = Mock(spec=CallbackManager)
        self.chainlit_tag_format: str = "tag_format: {message_id}"
        self.super_query: Mock = None
        self.service = RagQueryEngine(
            retriever=self.retriever,
            postprocessors=self.postprocessors,
            response_synthesizer=self.synthesier,
            callback_manager=self.callback_manager,
            chainlit_tag_format=self.chainlit_tag_format,
        )

    def add_langfuse_callback_handler_to_callback_manager(
        self,
    ) -> "Arrangements":
        self.callback_manager.handlers = [
            self.fixtures.langfuse_callback_handler
        ]
        return self

    def mock_super_query(self) -> "Arrangements":
        self.super_query = CustomQueryEngine.query = Mock()
        return self

    def mock_super_aquery(self) -> "Arrangements":
        self.super_aquery = CustomQueryEngine.aquery = AsyncMock()
        return self


class Assertions:

    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements

    def assert_chainlit_message_id_is_set(self) -> "Assertions":
        self.fixtures.langfuse_callback_handler.set_trace_params.assert_called_once_with(
            tags=[
                self.arrangements.chainlit_tag_format.format(
                    message_id=self.fixtures.message_id
                ),
                self.fixtures.source_process.name.lower(),
            ]
        )
        return self

    def assert_query_str_is_passed_to_super_query(self) -> "Assertions":
        self.arrangements.super_query.assert_called_once_with(
            self.fixtures.query_str
        )
        return self

    def assert_query_str_is_passed_to_super_aquery(self) -> "Assertions":
        self.arrangements.super_aquery.assert_called_once_with(
            self.fixtures.query_str
        )
        return self

    def assert_retriever_retrieve_is_called(self) -> "Assertions":
        self.arrangements.retriever.retrieve.assert_called_once_with(
            self.fixtures.query_str
        )
        return self

    def assert_response_synthesizer_synthesize_is_called(self) -> "Assertions":
        self.arrangements.synthesier.synthesize.assert_called_once_with(
            self.fixtures.query_str,
            self.arrangements.retriever.retrieve.return_value,
        )
        return self

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

    def get_service(self) -> RagQueryEngine:
        return self.arrangements.service


class TestQueryEngine:

    @pytest.mark.parametrize(
        "source_process",
        [SourceProcess.CHAT_COMPLETION, SourceProcess.DEPLOYMENT_EVALUATION],
    )
    def test_given_message_id_when_query_then_query_is_sent(
        self, source_process: SourceProcess
    ) -> None:
        # Arrange
        manager = Manager(
            Arrangements(
                Fixtures()
                .with_message_id()
                .with_source_process(source_process)
                .with_langfuse_callback_handler()
                .with_query_str()
            )
            .add_langfuse_callback_handler_to_callback_manager()
            .mock_super_query()
        )
        service = manager.get_service()

        # Act
        service.query(
            str_or_query_bundle=manager.fixtures.query_str,
            chainlit_message_id=manager.fixtures.message_id,
            source_process=manager.fixtures.source_process,
        )

        # Assert
        manager.assertions.assert_chainlit_message_id_is_set().assert_query_str_is_passed_to_super_query()

    @pytest.mark.parametrize(
        "source_process",
        [SourceProcess.CHAT_COMPLETION, SourceProcess.DEPLOYMENT_EVALUATION],
    )
    @pytest.mark.asyncio
    async def test_given_message_id_when_query_then_aquery_is_sent(
        self, source_process: SourceProcess
    ) -> None:
        # Arrange
        manager = Manager(
            Arrangements(
                Fixtures()
                .with_message_id()
                .with_source_process(source_process)
                .with_langfuse_callback_handler()
                .with_query_str()
            )
            .add_langfuse_callback_handler_to_callback_manager()
            .mock_super_aquery()
        )
        service = manager.get_service()

        # Act
        await service.aquery(
            str_or_query_bundle=manager.fixtures.query_str,
            chainlit_message_id=manager.fixtures.message_id,
            source_process=manager.fixtures.source_process,
        )

        # Assert
        manager.assertions.assert_chainlit_message_id_is_set().assert_query_str_is_passed_to_super_aquery()

    def test_given_message_id_when_custom_query_then_components_are_invoked(
        self,
    ) -> None:
        # Arrange
        manager = Manager(
            Arrangements(
                Fixtures().with_message_id().with_query_str()
            ).add_langfuse_callback_handler_to_callback_manager()
        )
        service = manager.get_service()

        # Act
        service.custom_query(query_str=manager.fixtures.query_str)

        # Assert
        manager.assertions.assert_retriever_retrieve_is_called().assert_response_synthesizer_synthesize_is_called()

    def test_given_langfuse_callback_handler_when_get_current_langfuse_trace_then_trace_is_returned(
        self,
    ) -> None:
        # Arrange
        manager = Manager(
            Arrangements(
                Fixtures().with_langfuse_callback_handler()
            ).add_langfuse_callback_handler_to_callback_manager()
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
            ).add_langfuse_callback_handler_to_callback_manager()
        )
        service = manager.get_service()

        # Act
        service.set_session_id(session_id=manager.fixtures.session_id)

        # Assert
        manager.assertions.assert_session_id_is_set()
