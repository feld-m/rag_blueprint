import sys
from typing import Callable, Dict, List
from unittest.mock import Mock

from embedding.datasources.core.splitter import MarkdownSplitter

sys.path.append("./src")

import pytest
import tiktoken
from llama_index.core import Document
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.core.schema import TextNode


class Fixtures:

    def __init__(self):
        self.chunk_size_in_tokens: int
        self.chunk_overlap_in_tokens: int
        self.tokenize_func: Callable
        self.base_sentence: str
        self.documents: List[Document] = []
        self.nodes: Dict[Mock, List[str]] = {}

    def with_chunk_size_in_tokens(self, chunk_size_in_tokens) -> "Fixtures":
        self.chunk_size_in_tokens = chunk_size_in_tokens
        return self

    def with_chunk_overlap_in_tokens(
        self, chunk_overlap_in_tokens
    ) -> "Fixtures":
        self.chunk_overlap_in_tokens = chunk_overlap_in_tokens
        return self

    def with_base_sentence(self) -> "Fixtures":
        self.base_sentence = "This is a random sentence."
        return self

    def with_tokenize_func(self) -> "Fixtures":
        self.tokenize_func = tiktoken.encoding_for_model("gpt-3.5-turbo").encode
        return self

    def with_big_document(self) -> "Fixtures":
        base_sentence = "This is a random sentence."
        sentence_len = len(self.tokenize_func(base_sentence))
        number_of_sentences = (self.chunk_size_in_tokens // sentence_len) * 10

        document = Mock(
            spec=Document, text=" ".join([base_sentence] * number_of_sentences)
        )
        node = Mock(spec=TextNode, text=document.text)
        self.nodes[document] = [node]
        self.documents.append(document)

        return self

    def with_small_documents(self) -> "Fixtures":
        base_sentence = "This is a random sentence."
        sentence_len = len(self.tokenize_func(base_sentence))
        number_of_documents = (self.chunk_size_in_tokens // sentence_len) * 10

        document = Mock(spec=Document, text="")
        self.documents.append(document)
        self.nodes[document] = []

        for _ in range(number_of_documents):
            document.text += base_sentence + " "
            self.nodes[document].append(Mock(spec=TextNode, text=base_sentence))

        return self


class Arrangements:

    def __init__(self, fixtures: Fixtures) -> None:
        self.fixtures = fixtures

        self.service = MarkdownSplitter(
            chunk_size_in_tokens=fixtures.chunk_size_in_tokens,
            chunk_overlap_in_tokens=fixtures.chunk_overlap_in_tokens,
            tokenize_func=fixtures.tokenize_func,
        )

    def on_markdown_node_parser_get_nodes_from_documents(
        self,
    ) -> "Arrangements":
        def split_mock(documents: List[Document]) -> List[TextNode]:
            nodes = []
            for document in documents:
                nodes.extend(self.fixtures.nodes[document])
            return nodes

        self.service.markdown_node_parser = Mock(spec=MarkdownNodeParser)
        self.service.markdown_node_parser.get_nodes_from_documents.side_effect = (
            split_mock
        )
        return self


class Assertions:

    def __init__(self, arrangements: Arrangements) -> None:
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.service = arrangements.service

    def assert_nodes(self, nodes: List[TextNode]) -> None:
        for node in nodes:
            assert (
                len(self.fixtures.tokenize_func(node.text))
                <= self.fixtures.chunk_size_in_tokens
            )
            remaining_text = node.text.replace(self.fixtures.base_sentence, "")
            remaining_text = remaining_text.replace(" ", "")
            assert remaining_text == ""


class Manager:

    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.assertions = Assertions(arrangements=arrangements)

    def get_service(self) -> MarkdownSplitter:
        return self.arrangements.service


class TestMarkdownSplitter:

    @pytest.mark.parametrize(
        "chunk_size_in_tokens,chunk_overlap_in_tokens",
        [
            (100, 10),
            (200, 20),
            (100, 20),
            (200, 10),
        ],
    )
    def test_given_documents_when_split_then_document_is_split(
        self, chunk_size_in_tokens: int, chunk_overlap_in_tokens: int
    ) -> None:
        # Arrange
        fixtures = (
            Fixtures()
            .with_chunk_size_in_tokens(chunk_size_in_tokens)
            .with_chunk_overlap_in_tokens(chunk_overlap_in_tokens)
            .with_tokenize_func()
            .with_base_sentence()
            .with_big_document()
            .with_small_documents()
        )
        arrangements = Arrangements(
            fixtures
        ).on_markdown_node_parser_get_nodes_from_documents()
        manager = Manager(arrangements)
        service = manager.get_service()

        # Act
        nodes = service.split(fixtures.documents)

        # Assert
        manager.assertions.assert_nodes(nodes)
