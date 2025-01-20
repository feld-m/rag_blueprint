from injector import singleton
from llama_index.core.base.base_retriever import BaseRetriever

from common.bootstrap.base_binder import BaseBinder
from common.bootstrap.configuration.pipeline.augmentation.query_engine.retriever.retriever_binding_keys import (
    BoundAutoRetrieverLLM,
)
from common.bootstrap.configuration.pipeline.augmentation.query_engine.retriever.retriever_configuration import (
    AutoRetrieverConfiguration,
    BasicRetrieverConfiguration,
    RetrieverName,
)
from common.bootstrap.configuration.pipeline.augmentation.query_engine.synthesizer.synthesizer_binding_keys import (
    BoundLLM,
)
from common.builders.retriever_builders import (
    AutoRetrieverBuilder,
    BasicRetrieverBuilder,
)


class BasicRetrieverBinder(BaseBinder):
    """Binder for the basic retriever components."""

    def bind(self) -> None:
        """Bind components to the injector based on the configuration."""
        self._bind_configuration()
        self._bind_retriever()

    def _bind_configuration(self) -> None:
        """Bind the basic retriever configuration."""
        self.binder.bind(
            BasicRetrieverConfiguration,
            to=self.configuration.pipeline.augmentation.query_engine.retriever,
            scope=singleton,
        )

    def _bind_retriever(self) -> None:
        """Bind the basic retriever."""
        self.binder.bind(
            BaseRetriever,
            to=BasicRetrieverBuilder.build,
        )


class AutoRetrieverBinder(BaseBinder):
    """Binder for the auto retriever components."""

    def bind(self) -> None:
        """Bind components to the injector based on the configuration."""
        self._bind_configuration()
        self._bind_llm()
        self._bind_retriever()

    def _bind_configuration(self) -> None:
        """Bind the auto retriever configuration."""
        self.binder.bind(
            AutoRetrieverConfiguration,
            to=self.configuration.pipeline.augmentation.query_engine.retriever,
            scope=singleton,
        )

    def _bind_llm(self) -> None:
        """Bind the LLM based on the configuration.

        If the LLM configuration for the synthesizer and retriever are the same, bind the same LLM instance to both.
        Otherwise, bind separate LLM instances to the synthesizer and retriever.
        """
        llm_configuration = (
            self.configuration.pipeline.augmentation.query_engine.synthesizer.llm
        )
        auto_retriever_llm_configuration = (
            self.configuration.pipeline.augmentation.query_engine.retriever.llm
        )

        if self._pydantic_config_is_equal(
            llm_configuration, auto_retriever_llm_configuration
        ):
            self.binder.bind(
                BoundAutoRetrieverLLM,
                to=self._get_bind(BoundLLM),
                scope=singleton,
            )
        else:
            self.binder.bind(
                BoundAutoRetrieverLLM,
                to=lambda: auto_retriever_llm_configuration.builder(
                    configuration=auto_retriever_llm_configuration
                ),
                scope=singleton,
            )

    def _bind_retriever(self) -> None:
        """Bind the auto retriever."""
        self.binder.bind(
            BaseRetriever,
            to=AutoRetrieverBuilder.build,
        )


class RetrieverBinder(BaseBinder):
    """Binder for the retriever components."""

    mapping = {
        RetrieverName.BASIC: BasicRetrieverBinder,
        RetrieverName.AUTO_RETRIEVER: AutoRetrieverBinder,
    }

    def bind(self) -> None:
        """Binds specific retriever based on the configuration."""
        retriever_name = (
            self.configuration.pipeline.augmentation.query_engine.retriever.name
        )
        RetrieverBinder.mapping[retriever_name](
            configuration=self.configuration, binder=self.binder
        ).bind()
