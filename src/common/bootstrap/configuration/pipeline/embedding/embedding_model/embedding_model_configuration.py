from enum import Enum
from typing import Callable, Literal, Optional, Union

import tiktoken
from pydantic import BaseModel, ConfigDict, Field, SecretStr
from pydantic_settings import BaseSettings
from transformers import AutoTokenizer

from common.bootstrap.configuration.pipeline.embedding.embedding_model.splitting_configuration import (
    SplittingConfiguration,
)
from common.builders.embedding_builders import (
    HuggingFaceEmbeddingModelBuilder,
    OpenAIEmbeddingModelBuilder,
    VoyageEmbeddingModelBuilder,
)


# Enums
class EmbeddingModelName(str, Enum):
    BAAI_BGE_SMALL = "BAAI/bge-small-en-v1.5"
    OPENAI_TEXT_EMBEDDING_3_SMALL = "text-embedding-3-small"
    VOYAGE = "voyage-large-2-instruct"


class EmbeddingModelTokenizerName(str, Enum):
    BAAI_BGE_SMALL = "BAAI/bge-small-en-v1.5"
    OPENAI_TEXT_EMBEDDING_3_SMALL = "text-embedding-3-small"
    VOYAGE = "voyage-large-2-instruct"


# Secrets
class BGESecrets(BaseSettings):
    pass


class OpenAIEmbeddingModelSecrets(BaseSettings):
    model_config = ConfigDict(
        env_file="env_vars/.env",
        env_file_encoding="utf-8",
        env_prefix="RAGKB__EMBEDDING_MODELS__OPEN_AI__",
        env_nested_delimiter="__",
        extra="ignore",
    )

    api_key: Optional[SecretStr] = Field(
        None, description="API key for the model"
    )


class VoyageSecrets(BaseSettings):
    model_config = ConfigDict(
        env_file="env_vars/.env",
        env_file_encoding="utf-8",
        env_prefix="RAGKB__EMBEDDING_MODELS__VOYAGE__",
        env_nested_delimiter="__",
        extra="ignore",
    )

    api_key: Optional[SecretStr] = Field(
        None, description="API key for the model"
    )


class EmbeddingModelSecretsMapping:

    mapping: dict = {
        EmbeddingModelName.BAAI_BGE_SMALL: BGESecrets,
        EmbeddingModelName.OPENAI_TEXT_EMBEDDING_3_SMALL: OpenAIEmbeddingModelSecrets,
        EmbeddingModelName.VOYAGE: VoyageSecrets,
    }

    @staticmethod
    def get_secrets(embedding_model_name: EmbeddingModelName) -> BaseSettings:
        secrets = EmbeddingModelSecretsMapping.mapping.get(
            embedding_model_name
        )()
        if secrets is None:
            raise ValueError(f"Secrets for {embedding_model_name} not found.")
        return secrets


# Configuration
class EmbeddingModelTokenizerMapping:

    @staticmethod
    def get_tokenizer(
        embedding_model_name: EmbeddingModelName,
        tokenizer_name: EmbeddingModelTokenizerName,
    ) -> Callable:
        match embedding_model_name:
            case EmbeddingModelName.BAAI_BGE_SMALL | EmbeddingModelName.VOYAGE:
                return AutoTokenizer.from_pretrained(
                    tokenizer_name.value
                ).tokenize
            case EmbeddingModelName.OPENAI_TEXT_EMBEDDING_3_SMALL:
                return tiktoken.encoding_for_model(tokenizer_name.value).encode
            case _:
                raise ValueError(
                    f"Tokenizer for {embedding_model_name} not found."
                )


class EmbeddingModelConfiguration(BaseModel):
    name: EmbeddingModelName = Field(
        ..., description="The name of the embedding model."
    )
    tokenizer_name: EmbeddingModelTokenizerName = Field(
        ...,
        description="The name of the tokenizer used by the embedding model.",
    )
    batch_size: int = Field(64, description="The batch size for embedding.")

    splitting: Optional[SplittingConfiguration] = Field(
        None, description="The splitting configuration for the embedding model."
    )
    tokenizer_func: Optional[Callable] = Field(
        None,
        description="The tokenizer function used by the embedding model.",
        exclude=True,
    )

    def model_post_init(self, __context):
        self.secrets = EmbeddingModelSecretsMapping.get_secrets(self.name)
        self.tokenizer_func = EmbeddingModelTokenizerMapping.get_tokenizer(
            self.name, self.tokenizer_name
        )


class BGEConfiguration(EmbeddingModelConfiguration):
    name: Literal[EmbeddingModelName.BAAI_BGE_SMALL] = Field(
        ..., description="The name of the embedding model."
    )
    tokenizer_name: Literal[EmbeddingModelTokenizerName.BAAI_BGE_SMALL] = Field(
        ...,
        description="The name of the tokenizer used by the embedding model.",
    )
    secrets: Optional[BGESecrets] = Field(
        None, description="The secrets for the language model."
    )

    builder: Callable = Field(
        HuggingFaceEmbeddingModelBuilder.build,
        description="The builder for the embedding model.",
        exclude=True,
    )


class OpenAIEmbeddingModelConfiguration(EmbeddingModelConfiguration):

    name: Literal[EmbeddingModelName.OPENAI_TEXT_EMBEDDING_3_SMALL] = Field(
        ..., description="The name of the embedding model."
    )
    tokenizer_name: Literal[
        EmbeddingModelTokenizerName.OPENAI_TEXT_EMBEDDING_3_SMALL
    ] = Field(
        ...,
        description="The name of the tokenizer used by the embedding model.",
    )
    max_request_size_in_tokens: int = Field(
        8191,
        description="Maximum size of the request in tokens.",
    )
    secrets: Optional[OpenAIEmbeddingModelSecrets] = Field(
        None, description="The secrets for the language model."
    )

    builder: Callable = Field(
        OpenAIEmbeddingModelBuilder.build,
        description="The builder for the embedding model.",
        exclude=True,
    )

    @property
    def batch_size(self) -> int:
        "Size of the batch for embedding. Batch of strings to be embedded cannot exceed `max_request_size_in_tokens`."
        return (
            self.max_request_size_in_tokens
            // self.splitting.chunk_size_in_tokens
        )


class VoyageConfiguration(EmbeddingModelConfiguration):

    name: Literal[EmbeddingModelName.VOYAGE] = Field(
        ..., description="The name of the embedding model."
    )
    tokenizer_name: Literal[EmbeddingModelTokenizerName.VOYAGE] = Field(
        ...,
        description="The name of the tokenizer used by the embedding model.",
    )
    secrets: Optional[VoyageSecrets] = Field(
        None, description="The secrets for the language model."
    )

    builder: Callable = Field(
        VoyageEmbeddingModelBuilder.build,
        description="The builder for the embedding model.",
        exclude=True,
    )


AVAILABLE_EMBEDDING_MODELS = Union[
    OpenAIEmbeddingModelConfiguration, BGEConfiguration, VoyageConfiguration
]
