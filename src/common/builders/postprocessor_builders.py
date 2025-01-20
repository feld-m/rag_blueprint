from injector import inject
from llama_index.postprocessor.colbert_rerank import ColbertRerank

from common.bootstrap.configuration.pipeline.augmentation.query_engine.postprocessors.postprocessors_configuration import (
    ColbertRerankConfiguration,
)


class ColbertRerankBuilder:
    """Builder for creating ColBERT reranking postprocessor.

    Provides factory method to create configured ColbertRerank instance.
    """

    @staticmethod
    @inject
    def build(configuration: ColbertRerankConfiguration) -> ColbertRerank:
        """Creates a configured ColBERT reranking postprocessor.

        Args:
            configuration: Settings for ColBERT reranking including model and scoring.

        Returns:
            ColbertRerank: Configured reranking postprocessor instance.
        """
        return ColbertRerank(
            top_n=configuration.top_n,
            model=configuration.model.value,
            tokenizer=configuration.tokenizer.value,
            keep_retrieval_score=configuration.keep_retrieval_score,
        )
