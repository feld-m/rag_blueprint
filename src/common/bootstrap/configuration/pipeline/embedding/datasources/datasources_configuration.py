from enum import Enum
from typing import Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, SecretStr
from pydantic_settings import BaseSettings

# Enums


class DatasourceName(str, Enum):
    NOTION = "notion"
    CONFLUENCE = "confluence"
    PDF = "pdf"


# Secrets


class NotionSecrets(BaseSettings):
    model_config = ConfigDict(
        env_file="env_vars/.env",
        env_file_encoding="utf-8",
        env_prefix="RAGKB__DATASOURCES__NOTION__",
        env_nested_delimiter="__",
        extra="ignore",
    )

    api_token: SecretStr = Field(
        ..., description="The token for the notion data source"
    )


class ConfluenceSecrets(BaseSettings):
    model_config = ConfigDict(
        env_file="env_vars/.env",
        env_file_encoding="utf-8",
        env_prefix="RAGKB__DATASOURCES__CONFLUENCE__",
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


class PdfSecrets(BaseSettings):
    pass


class DatasourceSecretsMapping:
    mapping: dict = {
        DatasourceName.NOTION: NotionSecrets,
        DatasourceName.CONFLUENCE: ConfluenceSecrets,
        DatasourceName.PDF: PdfSecrets,
    }

    @staticmethod
    def get_secrets(datasource_name: DatasourceName) -> BaseSettings:
        secrets = DatasourceSecretsMapping.mapping.get(datasource_name)()
        if secrets is None:
            raise ValueError(f"Secrets for {datasource_name} not found.")
        return secrets


# Configuration


class DatasourceConfiguration(BaseModel):
    name: DatasourceName = Field(
        ..., description="The name of the data source."
    )
    export_limit: Optional[int] = Field(
        None, description="The export limit for the data source."
    )

    def model_post_init(self, __context):
        self.secrets = DatasourceSecretsMapping.get_secrets(self.name)


class ConfluenceDatasourceConfiguration(DatasourceConfiguration):
    host: str = Field(
        "http://127.0.0.1", description="Host of the Confluence server"
    )
    name: Literal[DatasourceName.CONFLUENCE] = Field(
        ..., description="The name of the data source."
    )
    secrets: Optional[ConfluenceSecrets] = Field(
        None, description="The secrets for the data source."
    )


class NotionDatasourceConfiguration(DatasourceConfiguration):
    name: Literal[DatasourceName.NOTION] = Field(
        ..., description="The name of the data source."
    )
    home_page_database_id: str = Field(
        ...,
        description="The home page database ID for the data source. Used for notion",
    )
    export_batch_size: int = Field(
        3,
        description="Number of pages being exported ansychronously. Decrease to avoid NotionAPI rate limits, smaller batch slows the export down.",
    )
    secrets: Optional[NotionSecrets] = Field(
        None, description="The secrets for the data source."
    )


class PdfDatasourceConfiguration(DatasourceConfiguration):
    """Configuration for PDF data source.

    Settings for accessing and processing PDF files.

    Attributes:
        base_path: Root directory containing PDF files
    """

    base_path: str = Field(
        ..., description="Base path to the directory containing PDF files"
    )
    nlm_parser_enabled: bool = Field(
        False, description="Use NLM parser for PDF files"
    )
    nlm_parser_api_base: str = Field(
        None, description="NLM parser API base URL"
    )
    secrets: Optional[PdfSecrets] = Field(
        None, description="The secrets for the data source."
    )


AVAIALBLE_DATASOURCES = Union[
    NotionDatasourceConfiguration,
    ConfluenceDatasourceConfiguration,
    PdfDatasourceConfiguration,
]
