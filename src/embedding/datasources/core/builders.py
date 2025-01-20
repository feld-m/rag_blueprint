from injector import inject

from common.bootstrap.configuration.pipeline.embedding.embedding_model.embedding_model_configuration import (
    EmbeddingModelConfiguration,
)
from embedding.datasources.core.splitter import MarkdownSplitter


class MarkdownSplitterBuilder:
    """Builder for creating markdown content splitter instances.

    Provides factory method to create configured MarkdownSplitter objects
    using embedding model settings for chunking parameters.
    """

    @staticmethod
    @inject
    def build(
        embedding_model_configuration: EmbeddingModelConfiguration,
    ) -> MarkdownSplitter:
        """Creates a configured markdown splitter instance.

        Args:
            embedding_model_configuration: Configuration containing tokenization
                and chunking parameters.

        Returns:
            MarkdownSplitter: Configured splitter instance using model's
                chunk size, overlap, and tokenization settings.
        """
        return MarkdownSplitter(
            chunk_size_in_tokens=embedding_model_configuration.splitting.chunk_size_in_tokens,
            chunk_overlap_in_tokens=embedding_model_configuration.splitting.chunk_overlap_in_tokens,
            tokenize_func=embedding_model_configuration.tokenizer_func,
        )
