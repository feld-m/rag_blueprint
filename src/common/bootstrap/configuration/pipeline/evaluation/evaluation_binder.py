from injector import singleton

from common.bootstrap.base_binder import BaseBinder
from common.bootstrap.configuration.pipeline.augmentation.query_engine.retriever.retriever_binding_keys import (
    BoundAutoRetrieverLLM,
)
from common.bootstrap.configuration.pipeline.augmentation.query_engine.retriever.retriever_configuration import (
    AutoRetrieverConfiguration,
)
from common.bootstrap.configuration.pipeline.augmentation.query_engine.synthesizer.synthesizer_binding_keys import (
    BoundLLM,
)
from common.bootstrap.configuration.pipeline.embedding.embedding_model.embedding_model_binding_keys import (
    BoundEmbeddingModel,
)
from common.bootstrap.configuration.pipeline.evaluation.evaluation_binding_keys import (
    BoundJudgeEmbeddingModel,
    BoundJudgeLLM,
)
from evaluation.builders import LangfuseEvaluatorBuilder, RagasEvaluatorBuilder
from evaluation.evaluators import LangfuseEvaluator, RagasEvaluator


class EvaluationBinder(BaseBinder):
    """Binder for the evaluation components."""

    def bind(self) -> None:
        """Bind the evaluation components."""
        self._bind_judge_llm()
        self._bind_judge_embedding_model()
        self._bind_ragas_evaluator()
        self._bind_langfuse_evaluator()

    def _bind_judge_llm(self) -> None:
        """Bind the judge LLM.

        If the judge LLM configuration is the same as the LLM configuration or auto retriever LLM bind the the same LLM to judge LLM.
        """
        judge_llm_configuration = (
            self.configuration.pipeline.evaluation.judge_llm
        )
        llm_configuration = (
            self.configuration.pipeline.augmentation.query_engine.synthesizer.llm
        )
        retriever_configuration = (
            self.configuration.pipeline.augmentation.query_engine.retriever
        )

        if self._pydantic_config_is_equal(
            judge_llm_configuration, llm_configuration
        ):
            self.binder.bind(
                BoundJudgeLLM,
                to=self._get_bind(BoundLLM),
                scope=singleton,
            )
        elif (
            isinstance(retriever_configuration, AutoRetrieverConfiguration)
            and retriever_configuration.llm == judge_llm_configuration
        ):
            self.binder.bind(
                BoundJudgeLLM,
                to=self._get_bind(BoundAutoRetrieverLLM),
                scope=singleton,
            )
        else:
            self.binder.bind(
                BoundJudgeLLM,
                to=lambda: judge_llm_configuration.builder(
                    judge_llm_configuration
                ),
                scope=singleton,
            )

    def _bind_judge_embedding_model(self) -> None:
        """Bind the judge embedding model.

        If the judge embedding model configuration is the same as the embedding model configuration bind the same embedding model to judge embedding model.
        """
        judge_embedding_model_configuration = (
            self.configuration.pipeline.evaluation.judge_embedding_model
        )
        embedding_model_configuration = (
            self.configuration.pipeline.embedding.embedding_model
        )

        if self._pydantic_config_is_equal(
            judge_embedding_model_configuration, embedding_model_configuration
        ):
            self.binder.bind(
                BoundJudgeEmbeddingModel,
                to=self._get_bind(BoundEmbeddingModel),
                scope=singleton,
            )
        else:
            self.binder.bind(
                BoundJudgeEmbeddingModel,
                to=lambda: judge_embedding_model_configuration.builder(
                    judge_embedding_model_configuration
                ),
                scope=singleton,
            )

    def _bind_ragas_evaluator(self) -> None:
        """Bind the Ragas evaluator."""
        self.binder.bind(
            RagasEvaluator,
            to=RagasEvaluatorBuilder.build,
        )

    def _bind_langfuse_evaluator(self) -> None:
        """Bind the Langfuse evaluator."""
        self.binder.bind(
            LangfuseEvaluator,
            to=LangfuseEvaluatorBuilder.build,
        )
