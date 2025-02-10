from typing import Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, SecretStr
from pydantic_settings import BaseSettings


# Secrets
class LangfuseSecrets(BaseSettings):
    model_config = ConfigDict(
        env_file="env_vars/.env",
        env_file_encoding="utf-8",
        env_prefix="RAGKB__LANGFUSE__",
        env_nested_delimiter="__",
        extra="ignore",
    )

    public_key: SecretStr = Field(
        ..., description="Public key for the langfuse callback"
    )
    secret_key: SecretStr = Field(
        ..., description="Secret key for the langfuse callback"
    )


class LangfuseDatabaseSecrets(BaseSettings):
    model_config = ConfigDict(
        env_file="env_vars/.env",
        env_file_encoding="utf-8",
        env_prefix="RAGKB__LANGFUSE__DATABASE__",
        env_nested_delimiter="__",
        extra="ignore",
    )

    user: SecretStr = Field(
        ..., description="User for the langfuse database server"
    )
    password: SecretStr = Field(
        ..., description="Password for the langfuse database server"
    )


# Configuration
class LangfuseDatabaseConfiguration(BaseModel):
    host: str = Field(
        "127.0.0.1", description="Host of the Langfuse database server"
    )
    port: int = Field(
        5432,
        description="Port of the langfuse database server",
    )
    db: str = Field(
        "langfuse",
        description="Name of the langfuse database server's database.",
    )
    secrets: Optional[LangfuseDatabaseSecrets] = Field(
        None, description="The secrets for the langfuse database."
    )

    def model_post_init(self, __context):
        secrets = LangfuseDatabaseSecrets()
        if secrets is None:
            raise ValueError("Secrets for Langfuse not found.")
        self.secrets = secrets


class LangfuseDatasetConfiguration(BaseModel):
    name: str = Field(
        ...,
        description="Name of the dataset in the Langfuse server",
    )
    description: str = Field(
        ...,
        description="Description of the dataset in the Langfuse server",
    )
    metadata: dict = Field(
        {}, description="Metadata of the dataset in the Langfuse server"
    )


class LangfuseDatasetsConfiguration(BaseModel):
    feedback_dataset: LangfuseDatasetConfiguration = Field(
        LangfuseDatasetConfiguration(
            name="feedback-dataset",
            description="Dataset created out of positive feedbacks from the chatbot",
        ),
        description="Feedback dataset in the Langfuse server",
    )
    manual_dataset: LangfuseDatasetConfiguration = Field(
        LangfuseDatasetConfiguration(
            name="manual-dataset",
            description="Dataset created directly by the user indicating the query and the correct answer",
        ),
        description="Feedback dataset in the Langfuse server",
    )


class LangfuseConfiguration(BaseModel):
    host: str = Field("127.0.0.1", description="Host of the Langfuse server")
    protocol: Union[Literal["http"], Literal["https"]] = Field(
        "http", description="The protocol for the vector store."
    )
    port: int = Field(3000, description="Port of the Langfuse server")
    database: LangfuseDatabaseConfiguration = Field(
        description="Connection info for the Langfuse server",
        default_factory=LangfuseDatabaseConfiguration,
    )
    datasets: LangfuseDatasetsConfiguration = Field(
        description="Datasets in the langfuse server",
        default_factory=LangfuseDatasetsConfiguration,
    )
    chainlit_tag_format: str = Field(
        "chainlit_message_id: {message_id}",
        description="Format of the tag used to retrieve the trace by chainlit message id in langfuse",
    )
    secrets: Optional[LangfuseSecrets] = Field(
        None, description="The secrets for the Langfuse."
    )

    @property
    def url(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}"

    def model_post_init(self, __context):
        secrets = LangfuseSecrets()
        if secrets is None:
            raise ValueError("Secrets for Langfuse not found.")
        self.secrets = secrets
