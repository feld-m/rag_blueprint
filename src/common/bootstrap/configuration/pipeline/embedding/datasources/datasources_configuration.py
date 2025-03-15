from abc import ABC
from enum import Enum
from typing import Literal, Optional, Union

from pydantic import ConfigDict, Field, SecretStr
from pydantic_settings import BaseSettings

from common.bootstrap.secrets_configuration import ConfigurationWithSecrets

# Enums


class DatasourceName(str, Enum):
    CONFLUENCE = "confluence"
    NOTION_POSTGRES_AIRBYTE = "notion-postgres-airbyte"
    PDF = "pdf"


# Secrets


class ConfluenceSecrets(BaseSettings):
    model_config = ConfigDict(
        env_file_encoding="utf-8",
        env_prefix="RAG__DATASOURCES__CONFLUENCE__",
        env_nested_delimiter="__",
        extra="ignore",
    )

    username: SecretStr = Field(
        ...,
        description="The username for the confluence data source",
    )
    password: SecretStr = Field(
        ...,
        description="The password for the confluence data source",
    )


# Configuration


class DatasourceConfiguration(ConfigurationWithSecrets, ABC):
    name: DatasourceName = Field(
        ..., description="The name of the data source."
    )
    export_limit: Optional[int] = Field(
        None, description="The export limit for the data source."
    )


class ConfluenceDatasourceConfiguration(DatasourceConfiguration):
    host: str = Field(
        "127.0.0.1", description="Host of the vector store server"
    )
    protocol: Union[Literal["http"], Literal["https"]] = Field(
        "http", description="The protocol for the vector store."
    )
    name: Literal[DatasourceName.CONFLUENCE] = Field(
        ..., description="The name of the data source."
    )
    secrets: ConfluenceSecrets = Field(
        None, description="The secrets for the data source."
    )

    @property
    def base_url(self) -> str:
        return f"{self.protocol}://{self.host}"


class PdfDatasourceConfiguration(DatasourceConfiguration):
    name: Literal[DatasourceName.PDF] = Field(
        ..., description="The name of the data source."
    )
    base_path: str = Field(
        ..., description="Base path to the directory containing PDF files"
    )
    nlm_parser_enabled: bool = Field(
        False, description="Use NLM parser for PDF files"
    )
    nlm_parser_api_base: str = Field(
        None, description="NLM parser API base URL"
    )


class NotionPostgresAirbyteDatasourceConfiguration(DatasourceConfiguration):

    class PostgresAirbyteDestinationConfiguration(ConfigurationWithSecrets):
        class Secrets(BaseSettings):
            model_config = ConfigDict(
                env_file_encoding="utf-8",
                env_prefix="RAG__DATASOURCES__NOTION_POSTGRES_AIRBYTE__",
                env_nested_delimiter="__",
                extra="ignore",
            )

            username: SecretStr = Field(
                ..., description="Username to connect to the database."
            )
            password: SecretStr = Field(
                ..., description="Password to connect to the database."
            )

        database_name: str = Field(..., description="Database name")
        protocol: str = Field("postgresql", description="Database protocol")
        host: str = Field("127.0.0.1", description="Database host")
        port: int = Field(5432, description="Database port")
        secrets: Secrets = Field(
            None, description="The secrets for the data source."
        )

        @property
        def connection_url(self) -> str:
            return f"{self.protocol}://{self.secrets.username.get_secret_value()}:{self.secrets.password.get_secret_value()}@{self.host}:{self.port}/{self.database_name}"

    name: Literal[DatasourceName.NOTION_POSTGRES_AIRBYTE] = Field(
        ..., description="The name of the data source."
    )
    destination: PostgresAirbyteDestinationConfiguration = Field(
        ..., description="Destination configuration"
    )


AVAIALBLE_DATASOURCES = Union[
    NotionPostgresAirbyteDatasourceConfiguration,
    ConfluenceDatasourceConfiguration,
    PdfDatasourceConfiguration,
]
