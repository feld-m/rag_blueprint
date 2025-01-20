from math import isnan
from typing import Callable

from datasets import Dataset
from langfuse.client import DatasetItemClient
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.base.llms.base import BaseLLM
from llama_index.core.base.response.schema import Response
from pandas import Series
from ragas.embeddings import LlamaIndexEmbeddingsWrapper
from ragas.evaluation import evaluate as ragas_evaluate
from ragas.llms import LlamaIndexLLMWrapper
from ragas.metrics import answer_relevancy, context_recall, faithfulness
from ragas.metrics.critique import harmfulness

from common.langfuse.dataset import LangfuseDatasetService
from common.query_engine import RagQueryEngine, SourceProcess


class RagasEvaluator:
    """Evaluator for RAG system quality using RAGAS.

    Wraps LlamaIndex LLM and embedding models for use with RAGAS
    evaluation framework. Supports multiple evaluation metrics.

    Attributes:
        judge_llm: Wrapped LLM for evaluations
        embedding_model: Wrapped embeddings for metrics
        evaluator_function: Function to run evaluations
        metrics: List of RAGAS metrics to evaluate
    """

    def __init__(
        self,
        judge_llm: BaseLLM,
        embedding_model: BaseEmbedding,
        evaluator_function: Callable = ragas_evaluate,
    ) -> None:
        """Initialize RAGAS evaluator with models.

        Args:
            judge_llm: LLM for evaluation judgments
            embedding_model: Model for embedding comparisons
            evaluator_function: Optional custom evaluation function
        """
        self.judge_llm = LlamaIndexLLMWrapper(judge_llm)
        self.embedding_model = LlamaIndexEmbeddingsWrapper(embedding_model)
        self.evaluator_function = evaluator_function

        self.metrics = [
            answer_relevancy,
            faithfulness,
            harmfulness,
            context_recall,
        ]

    def evaluate(self, response: Response, item: DatasetItemClient) -> Series:
        """Evaluate response quality using RAGAS metrics.

        Args:
            response: Query response to evaluate
            item: Dataset item containing ground truth

        Returns:
            Series: Scores for each metric
        """
        dataset = Dataset.from_dict(
            {
                "question": [item.input["query_str"]],
                "contexts": [[n.node.text for n in response.source_nodes]],
                "answer": [response.response],
                "ground_truth": [item.expected_output["result"]],
            }
        )
        return (
            self.evaluator_function(
                metrics=self.metrics,
                dataset=dataset,
                llm=self.judge_llm,
                embeddings=self.embedding_model,
            )
            .to_pandas()
            .iloc[0]
        )


class LangfuseEvaluator:
    """Evaluator for tracking RAG performance in Langfuse.

    Combines query engine execution with RAGAS evaluation and
    uploads results to Langfuse for monitoring.

    Attributes:
        query_engine: Engine for generating responses
        ragas_evaluator: Evaluator for quality metrics
        langfuse_dataset_service: Service for dataset access
        run_name: Name of evaluation run
        run_metadata: Additional run context
    """

    def __init__(
        self,
        query_engine: RagQueryEngine,
        langfuse_dataset_service: LangfuseDatasetService,
        ragas_evaluator: RagasEvaluator,
        run_metadata: dict,
    ) -> None:
        """Initialize Langfuse evaluator.

        Args:
            query_engine: Engine for response generation
            langfuse_dataset_service: Dataset access service
            ragas_evaluator: Quality metrics evaluator
            run_metadata: Run context information
        """
        self.query_engine = query_engine
        self.ragas_evaluator = ragas_evaluator
        self.langfuse_dataset_service = langfuse_dataset_service
        self.run_name = run_metadata["build_name"]
        self.run_metadata = run_metadata

    def evaluate(self, dataset_name: str) -> None:
        """Evaluate dataset and record results in Langfuse.

        Args:
            dataset_name: Name of dataset to evaluate

        Note:
            Uploads scores for answer relevancy, context recall,
            faithfulness and harmfulness when available.
        """
        langfuse_dataset = self.langfuse_dataset_service.get_dataset(
            dataset_name
        )

        for item in langfuse_dataset.items:

            response = self.query_engine.query(
                str_or_query_bundle=item.input["query_str"],
                chainlit_message_id=None,
                source_process=SourceProcess.DEPLOYMENT_EVALUATION,
            ).get_response()

            scores = self.ragas_evaluator.evaluate(response=response, item=item)

            trace = self.query_engine.get_current_langfuse_trace()
            trace.update(output=response.response)
            item.link(
                trace_or_observation=trace,
                run_name=self.run_name,
                run_description="Deployment evaluation",
                run_metadata=self.run_metadata,
            )

            # TODO: How to handle NaNs?
            if not isnan(scores["answer_relevancy"]):
                trace.score(
                    name="Answer Relevancy", value=scores["answer_relevancy"]
                )
            if not isnan(scores["context_recall"]):
                trace.score(
                    name="Context Recall", value=scores["context_recall"]
                )
            if not isnan(scores["faithfulness"]):
                trace.score(name="Faithfulness", value=scores["faithfulness"])
            if not isnan(scores["harmfulness"]):
                trace.score(name="Harmfulness", value=scores["harmfulness"])
