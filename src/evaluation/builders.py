from injector import inject
from llama_index.core.base.base_query_engine import BaseQueryEngine

from common.bootstrap.configuration.configuration import Configuration
from common.bootstrap.configuration.pipeline.evaluation.evaluation_binding_keys import (
    BoundJudgeEmbeddingModel,
    BoundJudgeLLM,
)
from common.langfuse.dataset import LangfuseDatasetService
from evaluation.evaluators import LangfuseEvaluator, RagasEvaluator


class RagasEvaluatorBuilder:
    """Builder for creating Ragas evaluator instances.

    Provides factory method to create configured RagasEvaluator
    with required LLM and embedding components.
    """

    @staticmethod
    @inject
    def build(
        judge_llm: BoundJudgeLLM,
        judge_embedding_model: BoundJudgeEmbeddingModel,
    ) -> RagasEvaluator:
        """Create configured Ragas evaluator instance.

        Args:
            judge_llm: LLM for evaluation judgments
            judge_embedding_model: Model for embedding evaluations

        Returns:
            RagasEvaluator: Configured evaluator instance
        """
        return RagasEvaluator(
            judge_llm=judge_llm, embedding_model=judge_embedding_model
        )


class LangfuseEvaluatorBuilder:
    """Builder for creating Langfuse evaluator instances.

    Provides factory method to create configured LangfuseEvaluator
    with required components and metadata.
    """

    @staticmethod
    @inject
    def build(
        query_engine: BaseQueryEngine,
        langfuse_dataset_service: LangfuseDatasetService,
        ragas_evaluator: RagasEvaluator,
        configuration: Configuration,
    ) -> LangfuseEvaluator:
        """Create configured Langfuse evaluator instance.

        Args:
            query_engine: Engine for generating responses
            langfuse_dataset_service: Service for dataset operations
            ragas_evaluator: Evaluator for quality metrics
            configuration: Evaluation settings

        Returns:
            LangfuseEvaluator: Configured evaluator instance
        """
        return LangfuseEvaluator(
            query_engine=query_engine,
            langfuse_dataset_service=langfuse_dataset_service,
            ragas_evaluator=ragas_evaluator,
            run_metadata={
                "build_name": configuration.metadata.build_name,
                "llm_configuration": configuration.pipeline.augmentation.query_engine.synthesizer.llm.name,
                "judge_llm_configuration": configuration.pipeline.evaluation.judge_llm.name,
            },
        )
