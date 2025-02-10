from enum import Enum
from typing import Literal, Union

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


# Enums
class VectorStoreName(str, Enum):
    QDRANT = "qdrant"
    CHROMA = "chroma"


# Secrets
class QDrantSecrets(BaseSettings):
    pass


class ChromaSecrets(BaseSettings):
    pass


# Configuration
class VectorStorePortsConfiguration(BaseModel):
    rest: int = Field(
        ..., description="The port for the HTTP server of the vector store."
    )


class VectorStoreConfiguration(BaseModel):
    name: VectorStoreName = Field(
        ..., description="The name of the vector store."
    )
    ports: VectorStorePortsConfiguration = Field(
        ..., description="The ports for the vector store."
    )
    collection_name: str = Field(
        ..., description="The collection name in the vector store."
    )
    host: str = Field(
        "127.0.0.1", description="Host of the vector store server"
    )
    protocol: Union[Literal["http"], Literal["https"]] = Field(
        "http", description="The protocol for the vector store."
    )

    def model_post_init(self, __context):
        self.secrets = self.get_secrets()

    def get_secrets(self) -> BaseSettings:
        secrets_class = self.model_fields["secrets"].annotation
        secrets = secrets_class()
        if secrets is None:
            raise ValueError(f"Secrets for {self.name} not found.")
        return secrets


class QDrantConfiguration(VectorStoreConfiguration):
    name: Literal[VectorStoreName.QDRANT] = Field(
        ..., description="The name of the vector store."
    )
    secrets: QDrantSecrets = Field(
        None, description="The secrets for the Qdrant vector store."
    )

    @property
    def url(self) -> str:
        return f"{self.protocol}://{self.host}:{self.ports.rest}"


class ChromaConfiguration(VectorStoreConfiguration):
    name: Literal[VectorStoreName.CHROMA] = Field(
        ..., description="The name of the vector store."
    )
    secrets: ChromaSecrets = Field(
        None, description="The secrets for the Qdrant vector store."
    )


AVAILABLE_VECTOR_STORES = Union[QDrantConfiguration, ChromaConfiguration]
