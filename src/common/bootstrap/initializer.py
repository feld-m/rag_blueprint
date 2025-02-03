import argparse
import time
from abc import ABC

import chainlit.data as cl_data
from injector import Binder, Injector, singleton

from augmentation.chainlit.service import ChainlitService
from common.bootstrap.configuration.configuration import Configuration
from common.bootstrap.configuration.pipeline.augmentation.chainlit.chainlit_binder import (
    ChainlitBinder,
)
from common.bootstrap.configuration.pipeline.augmentation.langfuse.langfuse_binder import (
    LangfuseBinder,
)
from common.bootstrap.configuration.pipeline.augmentation.query_engine.query_engine_binder import (
    QueryEngineBinder,
)
from common.bootstrap.configuration.pipeline.embedding.datasources.datasources_binder import (
    DatasourcesBinder,
)
from common.bootstrap.configuration.pipeline.embedding.embedding_model.embedding_model_binder import (
    EmbeddingModelBinder,
)
from common.bootstrap.configuration.pipeline.embedding.vector_store.vector_store_binder import (
    VectorStoreBinder,
)
from common.bootstrap.configuration.pipeline.evaluation.evaluation_binder import (
    EvaluationBinder,
)
from common.logger import LoggerConfiguration


class CommonInitializer(ABC):
    """Common initializer for embedding, augmentation and evaluation processes.

    Multiple components are used in the embedding, augmentation and evaluation processes.
    To avoid code duplication, this initializer is used to bind the components to the injector.
    It is intended to be subclassed by the specific initializers for each process.

    Attributes:
        configuration: Configuration object
        configuration_json: Configuration JSON string
    """

    def __init__(self):
        """Initialize the CommonInitializer.

        Parse the command line arguments and read the configuration file.
        Setup the logger configuration.
        """
        args = self._parse_args()
        configuration_filename = args.config_file
        build_name = args.build_name

        with open(configuration_filename) as f:
            self.configuration_json = f.read()
        self.configuration = Configuration.model_validate_json(
            self.configuration_json
        )
        self.configuration.metadata.build_name = build_name
        print(f"::{configuration_filename}")
        print(self.configuration.model_dump_json(indent=4))

        LoggerConfiguration.config()  # TODO: Pass log level from configuration
        LoggerConfiguration.filterwarnings()

    def init_injector(self) -> Injector:
        """Bind components to the injector based on the configuration and return the injector.

        Returns:
            Injector: Injector with components bound"""
        return Injector([self._bind])

    def _bind(self, binder: Binder) -> None:
        """Bind common components to the injector based on the configuration.

        Args:
            binder: Injector binder
        """
        binder.bind(Configuration, to=self.configuration, scope=singleton)
        EmbeddingModelBinder(
            configuration=self.configuration, binder=binder
        ).bind()
        VectorStoreBinder(
            configuration=self.configuration, binder=binder
        ).bind()

    def _parse_args(self):
        """Parse the command line arguments.

        Returns:
            argparse.Namespace: Parsed command line arguments
        """
        parser = argparse.ArgumentParser(
            description="Run the embedding process."
        )
        parser.add_argument(
            "--config-file",
            type=str,
            help="Path to the configuration file.",
            default="src/common/bootstrap/configuration/configuration.json",
        )
        parser.add_argument(
            "--build-name",
            type=str,
            help="The name of the build.",
            default=f"build-local-{time.time()}",  # Removed trailing comma
        )
        parser.add_argument(
            "--secrets-file",
            type=str,
            help="Path to the secrets file.",
            default="env_vars/.env",
        )
        return parser.parse_args()


class EmbeddingInitializer(CommonInitializer):
    """Initializer for the embedding process.

    Bind the components required for the embedding process to the injector.
    """

    def _bind(self, binder: Binder) -> None:
        """Bind components required for the embedding process to the injector.

        Args:
            binder: Injector binder
        """
        super()._bind(binder)
        DatasourcesBinder(
            configuration=self.configuration, binder=binder
        ).bind()


class AugmentationInitializer(CommonInitializer):
    """Initializer for the augmentation process.

    Bind the components required for the augmentation process to the injector.
    """

    def init_injector(self) -> Injector:
        """Bind components to the injector based on the configuration and return the injector.

        Returns:
            Injector: Injector with components bound"""
        injector = super().init_injector()
        cl_data._data_layer = injector.get(ChainlitService)
        return injector

    def _bind(self, binder: Binder) -> None:
        """Bind components required for the augmentation process to the injector.

        Args:
            binder: Injector binder
        """
        super()._bind(binder)
        LangfuseBinder(configuration=self.configuration, binder=binder).bind()
        QueryEngineBinder(
            configuration=self.configuration, binder=binder
        ).bind()
        ChainlitBinder(configuration=self.configuration, binder=binder).bind()


class EvaluationInitializer(AugmentationInitializer):
    """Initializer for the evaluation process.

    Bind the components required for the evaluation process to the injector."""

    def init_injector(self) -> Injector:
        """Bind components to the injector based on the configuration and return the injector.

        Returns:
            Injector: Injector with components bound"""
        return Injector([self._bind])

    def _bind(self, binder: Binder) -> None:
        """Bind components required for the evaluation process to the injector.

        Args:
            binder: Injector binder
        """
        super()._bind(binder)
        EvaluationBinder(configuration=self.configuration, binder=binder).bind()
