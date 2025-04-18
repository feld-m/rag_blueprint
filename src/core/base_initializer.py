import importlib
import logging
import pkgutil
from abc import ABC, abstractmethod
from typing import List, Type

from core.base_configuration import BaseConfiguration, MetadataConfiguration
from core.configuration_retrievers import (
    BaseConfigurationRetriever,
    ConfiguratioRetriverRegistry,
)
from core.logger import LoggerConfiguration


class BaseInitializer(ABC):
    """Abstract base class for configuration initializers.

    This class defines the interface for initializers that are responsible for
    retrieving and initializing configuration objects. Subclasses must implement
    the get_configuration method to provide a concrete initialization strategy.

    Attributes:
        _configuration_class: The class of the configuration object to be initialized.
    """

    def __init__(self, configuration_class: Type[BaseConfiguration]):
        """Initialize the BaseInitializer.

        Args:
            configuration_class: The configuration class to use for initialization.
        """
        self._configuration_class = configuration_class

    @abstractmethod
    def get_configuration(self) -> BaseConfiguration:
        """Retrieve the configuration instance.

        Returns:
            The initialized configuration object.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        pass


class BasePackageLoader(ABC):
    """Abstract base class for dynamic package loading.

    This class defines the interface for package loaders that dynamically discover and load
    packages from specified locations. Subclasses must implement the load_packages method
    to provide a concrete package loading strategy. The class provides a helper method
    _load_packages that handles the common logic of dynamically importing modules.

    Attributes:
        logger: Logger instance used for logging package loading activities.
    """

    def __init__(
        self, logger: logging.Logger = LoggerConfiguration.get_logger(__name__)
    ):
        """Initialize the BasePackageLoader.

        Args:
            logger: Logger instance for logging package loading activities.
        """
        self.logger = logger

    @abstractmethod
    def load_packages(self) -> None:
        """Load packages dynamically.

        This method should be implemented by subclasses to provide the specific
        package loading logic needed for their application context.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        pass

    def _load_packages(self, parent_packages: List[str]) -> None:
        """Load packages from the specified parent packages.

        This method dynamically imports modules from the provided parent packages
        and calls their register() method to register components with the system.
        It skips the 'core' package and handles import errors gracefully.

        Args:
            parent_packages: List of parent package names to load modules from.
        """

        for parent_package in parent_packages:
            self.logger.info(f"Loading {parent_package} packages...")
            package_path = parent_package.replace(".", "/")

            for _, name, is_package in pkgutil.iter_modules([package_path]):
                if is_package and name != "core":
                    try:
                        module_path = f"{parent_package}.{name}"
                        module = importlib.import_module(module_path)
                        module.register()
                        self.logger.info(f"Loaded package: {name}.")
                    except ImportError as e:
                        self.logger.error(
                            f"Failed to load datasource package {name}: {e}."
                        )
                    except Exception as e:
                        self.logger.error(
                            f"Failed to register package {name}: {e}."
                        )


class BasicInitializer(BaseInitializer):
    """Common initializer for embedding, augmentation and evaluation processes.

    Multiple components are used in the embedding, augmentation and evaluation processes.
    To avoid code duplication, this initializer is used to bind the components to the injector.
    It is intended to be subclassed by the specific initializers for each process.
    """

    def __init__(
        self,
        configuration_class: Type[BaseConfiguration],
        package_loader: BasePackageLoader,
    ):
        """Initialize the BasicInitializer.
        Loads packages and initializes the configuration retriever.

        Args:
            configuration_class: The configuration class to use for initialization.
            package_loader: The package loader to use for loading packages.
        """
        super().__init__(configuration_class)
        self.configuration_retriever: BaseConfigurationRetriever = None

        package_loader.load_packages()
        self._init_configuration_retriever()

    def get_configuration(self) -> BaseConfiguration:
        """Retrieve the configuration instance.

        Returns:
            The initialized configuration object.
        """
        return self.configuration_retriever.get()

    def _init_configuration_retriever(self) -> None:
        """Initialize the configuration retriever.

        Creates an appropriate configuration retriever based on the metadata
        configuration and assigns it to the configuration_retriever attribute.
        """
        metadata = MetadataConfiguration()
        configuration_retriever_class = ConfiguratioRetriverRegistry.get(
            on_prem=metadata.on_prem_config
        )
        self.configuration_retriever = configuration_retriever_class(
            configuration_class=self._configuration_class, metadata=metadata
        )
