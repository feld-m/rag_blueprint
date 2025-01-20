from injector import singleton
from llama_index.core.response_synthesizers import BaseSynthesizer

from common.bootstrap.base_binder import BaseBinder
from common.bootstrap.configuration.pipeline.augmentation.query_engine.synthesizer.synthesizer_binding_keys import (
    BoundLLM,
)
from common.bootstrap.configuration.pipeline.augmentation.query_engine.synthesizer.synthesizer_configuration import (
    SynthesizerName,
    TreeSynthesizerConfiguration,
)
from common.builders.synthesizer_builders import TreeSynthesizerBuilder


class TreeSynthesizerBinder(BaseBinder):
    """Binder for the tree synthesizer components."""

    def bind(self):
        """Bind components to the injector based on the configuration."""
        self._bind_configuration()
        self._bind_llm()
        self._bind_synthesizer()

    def _bind_configuration(self) -> None:
        """Bind the tree synthesizer configuration."""
        self.binder.bind(
            TreeSynthesizerConfiguration,
            to=self.configuration.pipeline.augmentation.query_engine.synthesizer,
            scope=singleton,
        )

    def _bind_llm(self) -> None:
        """Bind the LLM."""
        llm_configuration = (
            self.configuration.pipeline.augmentation.query_engine.synthesizer.llm
        )
        self.binder.bind(
            BoundLLM,
            to=lambda: llm_configuration.builder(
                configuration=llm_configuration
            ),
            scope=singleton,
        )

    def _bind_synthesizer(self) -> None:
        """Bind the tree synthesizer."""
        self.binder.bind(
            BaseSynthesizer,
            to=TreeSynthesizerBuilder.build,
        )


class SynthezierBinder(BaseBinder):
    """Binder for the synthesizer component."""

    mapping = {
        SynthesizerName.TREE: TreeSynthesizerBinder,
    }

    def bind(self) -> None:
        """Bind specific synthesizer component to the injector based on the configuration."""
        synthesizer_name = (
            self.configuration.pipeline.augmentation.query_engine.synthesizer.name
        )
        SynthezierBinder.mapping[synthesizer_name](
            configuration=self.configuration, binder=self.binder
        ).bind()
