from typing import Type

from injector import Binder, singleton
from llama_index.postprocessor.colbert_rerank import ColbertRerank

from common.bootstrap.base_binder import BaseBinder
from common.bootstrap.configuration.pipeline.augmentation.query_engine.postprocessors.postprocessors_binding_key import (
    BoundPostprocessors,
)
from common.bootstrap.configuration.pipeline.augmentation.query_engine.postprocessors.postprocessors_configuration import (
    ColbertRerankConfiguration,
    PostProcessorName,
)
from common.builders.postprocessor_builders import ColbertRerankBuilder


class ColbertRerankBinder(BaseBinder):
    """Binder for the Colbert rerank postprocessor."""

    def __init__(
        self, configuration: ColbertRerankConfiguration, binder: Binder
    ):
        """Initialize the Colbert rerank binder.

        Args:
            configuration: Colbert rerank configuration
            binder: Injector binder
        """
        self.configuration = configuration
        self.binder = binder

    def bind(self) -> Type:
        """Bind components to the injector based on the configuration.

        Returns:
            Type: Colbert rerank postprocessor class"""
        self._bind_configuration()
        self._bind_postprocessor()
        return ColbertRerank

    def _bind_configuration(self) -> None:
        """Bind the Colbert rerank configuration."""
        self.binder.bind(
            ColbertRerankConfiguration,
            to=self.configuration,
            scope=singleton,
        )

    def _bind_postprocessor(self) -> None:
        """Bind the Colbert rerank postprocessor."""
        self.binder.bind(
            ColbertRerank,
            to=ColbertRerankBuilder.build,
        )


class PostprocessorsBinder(BaseBinder):
    """Binder for the postprocessors."""

    mapping = {
        PostProcessorName.COLBERT_RERANK: ColbertRerankBinder,
    }

    def bind(self) -> None:
        """Bind components to the injector based on the configuration.

        Only the postprocessors present in the configuration are bound."""
        postprocessors_configuration = (
            self.configuration.pipeline.augmentation.query_engine.postprocessors
        )
        postprocessors = []

        for postprocessor_configuration in postprocessors_configuration:
            postprocessor_name = postprocessor_configuration.name
            postprocessor_binder = self.mapping[postprocessor_name](
                postprocessor_configuration, self.binder
            )
            postprocessor_key = postprocessor_binder.bind()
            postprocessors.append(self._get_bind(postprocessor_key)())

        self.binder.bind(
            BoundPostprocessors,
            to=lambda: postprocessors,
        )
