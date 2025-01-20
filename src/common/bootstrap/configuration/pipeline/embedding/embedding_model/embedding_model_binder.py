from injector import singleton

from common.bootstrap.base_binder import BaseBinder
from common.bootstrap.configuration.pipeline.embedding.embedding_model.embedding_model_binding_keys import (
    BoundEmbeddingModel,
    BoundEmbeddingModelConfiguration,
    BoundEmbeddingModelMarkdownSplitter,
)
from embedding.datasources.core.builders import MarkdownSplitterBuilder


class EmbeddingModelBinder(BaseBinder):
    """Binder for the embedding model components."""

    def bind(self) -> None:
        """Bind the embedding model components."""
        self._bind_configuration()
        self._bind_embedding_model()
        self._bind_splitter()

    def _bind_configuration(self) -> None:
        """Bind the embedding model configuration."""
        embedding_model_configuration = (
            self.configuration.pipeline.embedding.embedding_model
        )
        self.binder.bind(
            BoundEmbeddingModelConfiguration,
            to=lambda: embedding_model_configuration,
            scope=singleton,
        )

    def _bind_embedding_model(self) -> None:
        """Bind the embedding model."""
        embedding_model_configuration = (
            self.configuration.pipeline.embedding.embedding_model
        )
        self.binder.bind(
            BoundEmbeddingModel,
            to=lambda: embedding_model_configuration.builder(
                embedding_model_configuration
            ),
            scope=singleton,
        )

    def _bind_splitter(self) -> None:
        """Bind the embedding model markdown splitter."""
        self.binder.bind(
            BoundEmbeddingModelMarkdownSplitter,
            to=lambda: MarkdownSplitterBuilder.build(
                self.configuration.pipeline.embedding.embedding_model
            ),
        )
