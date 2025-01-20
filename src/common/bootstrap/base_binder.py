from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from injector import Binder
from pydantic import BaseModel

if TYPE_CHECKING:
    from common.bootstrap.configuration.configuration import Configuration


class BaseBoundKey(ABC):
    """Base class for bound keys. Used to bind and extract instances from the injector."""

    @abstractmethod
    def _(self):
        """Empty function to avoid unintended initialization."""
        pass


class BaseBinder(ABC):
    """Base class for binders.

    Attributes:
        configuration: Configuration object
        binder: Injector binder
    """

    def __init__(self, configuration: "Configuration", binder: Binder) -> None:
        """Initialize the BaseBinder.

        Args:
            configuration: Configuration object
            binder: Injector binder
        """
        self.configuration = configuration
        self.binder = binder

    @abstractmethod
    def bind(self) -> None:
        """Bind components to the injector based on the configuration."""
        pass

    def _get_bind(self, key: Any) -> Any:
        """Get the bind function for the given key.

        Args:
            key: Key to bind

        Returns:
            Any: Bind function
        """
        return lambda: self.binder.injector.get(key)

    def _pydantic_config_is_equal(self, a: BaseModel, b: BaseModel) -> bool:
        """Check if two Pydantic configuration objects are equal.

        Args:
            a: Pydantic configuration object
            b: Pydantic configuration object

        Returns:
            bool: True if the objects are equal, False otherwise"""
        return a.model_dump() == b.model_dump()
