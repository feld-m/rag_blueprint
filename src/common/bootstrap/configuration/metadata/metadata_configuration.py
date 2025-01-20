from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LogLevelName(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EnvironmentName(str, Enum):
    LOCAL = "local"
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


class ConfigurationMetadata(BaseModel):
    build_name: Optional[str] = Field(
        None,
        description="The name of the build.",
    )
    log_level: LogLevelName = Field(
        LogLevelName.INFO, description="The log level of the application."
    )
    environment: EnvironmentName = Field(
        EnvironmentName.LOCAL,
        description="The environment of the application.",
    )
