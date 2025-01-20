import sys

sys.path.append("./src")

from unittest.mock import Mock

import pytest
from chainlit import Message
from llama_index.core.base.response.schema import StreamingResponse
from llama_index.core.schema import NodeWithScore

from augmentation.utils import ConversationUtils


class Fixtures:

    def __init__(self):
        self.message: Message = None
        self.response: StreamingResponse = None
        self.message_prefix: str = None

    def with_message(self, message_prefix: str) -> "Fixtures":
        self.message = Mock(spec=Message)
        self.message.content = message_prefix
        self.message_prefix = message_prefix
        return self

    def with_response_and_duplicated_nodes(self) -> "Fixtures":
        self.response = Mock(spec=StreamingResponse)
        self.response.source_nodes = [self._create_node(), self._create_node()]
        return self

    def with_response_and_unique_nodes(self) -> "Fixtures":
        self.response = Mock(spec=StreamingResponse)
        self.response.source_nodes = [
            self._create_node("1"),
            self._create_node("2"),
        ]
        return self

    def _create_node(self, index: str = "1") -> NodeWithScore:
        node = Mock(spec=NodeWithScore)
        node.metadata = {}
        node.metadata["title"] = f"title {index}"
        node.metadata["url"] = f"url {index}"
        return node


class Arrangements:

    def __init__(self, fixtures: Fixtures):
        self.fixtures = fixtures

        self.service = ConversationUtils()


class Assertions:

    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements

    def assert_message_content(self) -> "Assertions":
        assert (
            self.fixtures.message.content
            == self.fixtures.message_prefix
            + ConversationUtils.REFERENCES_TEMPLATE.format(
                references="\n".join(self._get_unique_nodes_str())
            )
        )
        return self

    def _get_unique_nodes_str(self):
        return set(
            [
                self._node_to_str(node)
                for node in self.fixtures.response.source_nodes
            ]
        )

    def _node_to_str(self, node: NodeWithScore) -> str:
        return "- [{}]({})".format(node.metadata["title"], node.metadata["url"])


class Manager:

    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.assertions = Assertions(arrangements)

    def get_service(self) -> ConversationUtils:
        return self.arrangements.service


class TestConversationUtils:

    @pytest.mark.parametrize(
        "message_prefix",
        ["Prefix 1", "Prefix 2"],
    )
    def test_given_duplicated_nodes_when_get_welcome_message_then_message_is_returned(
        self, message_prefix: str
    ):
        # Arrange
        manager = Manager(
            Arrangements(
                Fixtures()
                .with_message(message_prefix)
                .with_response_and_duplicated_nodes()
            )
        )
        service = manager.get_service()

        # Act
        service.add_references(
            message=manager.fixtures.message,
            response=manager.fixtures.response,
        )

        # Assert
        manager.assertions.assert_message_content()

    @pytest.mark.parametrize(
        "message_prefix",
        ["Prefix 1", "Prefix 2"],
    )
    def test_given_nodes_when_get_welcome_message_then_message_is_returned(
        self, message_prefix: str
    ):
        # Arrange
        manager = Manager(
            Arrangements(
                Fixtures()
                .with_message(message_prefix)
                .with_response_and_unique_nodes()
            )
        )
        service = manager.get_service()

        # Act
        service.add_references(
            message=manager.fixtures.message,
            response=manager.fixtures.response,
        )

        # Assert
        manager.assertions.assert_message_content()
