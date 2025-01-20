from llama_index.core.base.base_query_engine import BaseQueryEngine
from llama_index.core.callbacks import CallbackManager

from common.bootstrap.base_binder import BaseBinder
from common.bootstrap.configuration.pipeline.augmentation.query_engine.postprocessors.postprocessors_binder import (
    PostprocessorsBinder,
)
from common.bootstrap.configuration.pipeline.augmentation.query_engine.retriever.retriever_binder import (
    RetrieverBinder,
)
from common.bootstrap.configuration.pipeline.augmentation.query_engine.synthesizer.synthesizer_binder import (
    SynthezierBinder,
)
from common.builders.callback_builders import CallbackManagerBuilder
from common.builders.query_engine_builders import QueryEngineBuilder


class QueryEngineBinder(BaseBinder):
    """Binder for the query engine components."""

    def bind(self) -> None:
        """Bind components to the injector based on the configuration."""
        RetrieverBinder(
            configuration=self.configuration, binder=self.binder
        ).bind()
        SynthezierBinder(
            configuration=self.configuration, binder=self.binder
        ).bind()
        PostprocessorsBinder(
            configuration=self.configuration, binder=self.binder
        ).bind()
        self._bind_callback_manager()
        self._bind_query_engine()

    def _bind_callback_manager(self) -> None:
        """Bind the callback manager."""
        self.binder.bind(CallbackManager, to=CallbackManagerBuilder.build)

    def _bind_query_engine(self) -> None:
        """Bind the query engine."""
        self.binder.bind(
            BaseQueryEngine,
            to=QueryEngineBuilder.build,
        )
