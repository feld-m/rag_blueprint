import sys
from unittest.mock import Mock

import pandas as pd

sys.path.append("./src")

from langfuse.client import DatasetItemClient
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.base.llms.base import BaseLLM
from llama_index.core.base.response.schema import Response
from llama_index.core.schema import NodeWithScore

from evaluation.evaluators import RagasEvaluator


class Fixtures:

    def __init__(self):
        self.item: DatasetItemClient = None
        self.response: Response = None

    def with_item(self) -> "Fixtures":
        self.item = Mock(spec=DatasetItemClient)
        self.item.input = {"query_str": "query"}
        self.item.expected_output = {"result": "result"}
        return self

    def with_response(self) -> "Fixtures":
        self.response = Mock(spec=Response)
        self.response.source_nodes = [self._create_node()]
        self.response.response = "response"
        return self

    def _create_node(self) -> NodeWithScore:
        node = Mock(spec=NodeWithScore)
        node.node = Mock()
        node.node.text = "text"
        return node


class Arrangements:

    def __init__(self, fixtures: Fixtures) -> None:
        self.fixtures = fixtures

        self.judge_llm: BaseLLM = Mock(spec=BaseLLM)
        self.embedding_model: BaseEmbedding = Mock(spec=BaseEmbedding)
        self.service = RagasEvaluator(
            judge_llm=self.judge_llm,
            embedding_model=self.embedding_model,
        )
        self.ragas_evaluate_mock = None

    def mock_ragas_evaluate(self) -> "Arrangements":
        class RagasEvaluatorMock:
            def to_pandas(self) -> pd.DataFrame:
                return pd.DataFrame([{"test-value": 0.0}])

        def evaluate(*args, **kwargs):
            return RagasEvaluatorMock()

        self.service.evaluator_function = Mock(side_effect=evaluate)
        return self


class Assertions:

    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements

    def assert_evaluator_called(self) -> "Assertions":
        self.arrangements.service.evaluator_function.assert_called_once()


class Manager:

    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.assertions = Assertions(arrangements)

    def get_service(self) -> RagasEvaluator:
        return self.arrangements.service


class TestRagasEvaluator:

    def test_given_response_and_item_when_evaluate_return_results(self):
        # Arrange
        manager = Manager(
            Arrangements(
                Fixtures().with_item().with_response()
            ).mock_ragas_evaluate()
        )
        service = manager.get_service()

        # Act
        service.evaluate(
            response=manager.fixtures.response,
            item=manager.fixtures.item,
        )

        # Assert
        manager.assertions.assert_evaluator_called()
