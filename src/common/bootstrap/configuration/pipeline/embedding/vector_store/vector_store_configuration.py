from enum import Enum
from typing import Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings


# Enums
class VectorStoreName(str, Enum):
    QDRANT = "qdrant"


# Secrets
class QDrantSecrets(BaseSettings):
    model_config = ConfigDict(
        env_file="env_vars/.env",
        env_file_encoding="utf-8",
        env_prefix="RAGKB__VECTOR_STORES__QDRANT__",
        env_nested_delimiter="__",
        extra="ignore",
    )


class VectorStoreSecretsMapping:
    mapping: dict = {
        VectorStoreName.QDRANT: QDrantSecrets,
    }

    @staticmethod
    def get_secrets(llm_name: VectorStoreName) -> BaseSettings:
        secrets = VectorStoreSecretsMapping.mapping.get(llm_name)()
        if secrets is None:
            raise ValueError(f"Secrets for {llm_name} not found.")
        return secrets


# Configuration
class VectorStorePortsConfiguration(BaseModel):
    rest: int = Field(
        ..., description="The port for the HTTP server of the vector store."
    )
    grpc: Optional[int] = Field(
        None, description="The port for the gRPC server of the vector store."
    )


class VectorStoreConfiguration(BaseModel):
    name: VectorStoreName = Field(
        ..., description="The name of the vector store."
    )
    host: str = Field(
        "http://127.0.0.1", description="Host of the Qdrant server"
    )
    ports: VectorStorePortsConfiguration = Field(
        ..., description="The ports for the vector store."
    )

    def model_post_init(self, __context):
        self.secrets = VectorStoreSecretsMapping.get_secrets(self.name)


class QDrantConfiguration(VectorStoreConfiguration):
    name: Literal[VectorStoreName.QDRANT] = Field(
        ..., description="The name of the vector store."
    )
    collection_name: str = Field(
        ..., description="The collection name in the vector store."
    )
    secrets: Optional[QDrantSecrets] = Field(
        None, description="The secrets for the Qdrant vector store."
    )

    @property
    def url(self) -> str:
        return f"{self.host}:{self.ports.rest}"


AVAILABLE_VECTOR_STORES = Union[QDrantConfiguration]
