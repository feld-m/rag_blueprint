import json
from pathlib import Path
from typing import Any, Optional, Union

from pydantic import Field, ValidationInfo, field_validator

from augmentation.bootstrap.configuration.chainlit_configuration import (
    ChainlitConfiguration,
)
from augmentation.bootstrap.configuration.components.chat_engine_configuration import (
    ChatEngineConfigurationRegistry,
)
from augmentation.bootstrap.configuration.langfuse_configuration import (
    LangfuseConfiguration,
)
from augmentation.bootstrap.configuration.temporal_domain_config import (
    TemporalDomainConfiguration,
)
from core.base_configuration import BaseConfiguration
from embedding.bootstrap.configuration.configuration import (
    EmbeddingConfiguration,
)


class _AugmentationConfiguration(BaseConfiguration):
    """
    Internal configuration class for augmentation process settings.

    This class defines the structure for augmentation configuration including
    Langfuse monitoring, Chainlit UI, Chat Engine components, and optional
    temporal domain configuration.
    """

    langfuse: LangfuseConfiguration = Field(
        ..., description="Configuration of the Langfuse."
    )
    chainlit: ChainlitConfiguration = Field(
        ..., description="Configuration of the Chainlit."
    )
    chat_engine: Any = Field(
        ..., description="Configuration of the Chat Engine."
    )
    temporal_domain: Optional[Union[str, TemporalDomainConfiguration]] = Field(
        default=None,
        description="Temporal domain configuration. Can be a file path (str) or inline config. "
        "If not provided, system runs in generic mode without temporal filtering.",
    )

    @field_validator("temporal_domain")
    @classmethod
    def _validate_temporal_domain(
        cls, value: Optional[Union[str, TemporalDomainConfiguration]]
    ) -> Optional[TemporalDomainConfiguration]:
        """
        Validates and loads temporal domain configuration.

        If value is a string, treats it as a file path and loads the configuration
        from that file. If value is already a TemporalDomainConfiguration, returns it.
        If value is None, returns None (generic mode).

        Args:
            value: Temporal domain config (file path, config object, or None)

        Returns:
            Loaded TemporalDomainConfiguration or None

        Raises:
            ValueError: If file path is invalid or file content is malformed
        """
        if value is None:
            return None

        if isinstance(value, TemporalDomainConfiguration):
            return value

        if isinstance(value, str):
            # Treat as file path
            file_path = Path(value)

            # If relative path, resolve relative to configurations directory
            if not file_path.is_absolute():
                config_dir = (
                    Path(__file__).parent.parent.parent.parent.parent
                    / "configurations"
                )
                file_path = config_dir / value

            if not file_path.exists():
                raise ValueError(
                    f"Temporal domain configuration file not found: {file_path}"
                )

            try:
                with open(file_path, "r") as f:
                    config_data = json.load(f)
                return TemporalDomainConfiguration(**config_data)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Invalid JSON in temporal domain config file {file_path}: {e}"
                )
            except Exception as e:
                raise ValueError(
                    f"Failed to load temporal domain config from {file_path}: {e}"
                )

        if isinstance(value, dict):
            # Treat as inline configuration
            return TemporalDomainConfiguration(**value)

        raise ValueError(
            f"temporal_domain must be a file path (str), dict, or TemporalDomainConfiguration, got {type(value)}"
        )

    @field_validator("chat_engine")
    @classmethod
    def _validate_chat_engine(cls, value: Any, info: ValidationInfo) -> Any:
        """
        Validates the chat engine configuration using the appropriate registry.

        Args:
            value: The chat engine configuration value to validate
            info: Validation context information provided by Pydantic

        Returns:
            The validated chat engine configuration
        """
        return super()._validate(
            value,
            info=info,
            registry=ChatEngineConfigurationRegistry,
        )


class AugmentationConfiguration(EmbeddingConfiguration):
    """
    Main configuration class for the augmentation module.

    Extends the base embedding configuration with additional augmentation-specific
    settings to provide a complete configuration for text augmentation processes.
    """

    augmentation: _AugmentationConfiguration = Field(
        ..., description="Configuration of the augmentation process."
    )
