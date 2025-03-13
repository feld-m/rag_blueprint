from enum import Enum
from typing import Callable, Literal, Union

from pydantic import ConfigDict, Field, SecretStr
from pydantic_settings import BaseSettings

from common.bootstrap.secrets_configuration import ConfigurationWithSecrets
from common.builders.llm_builders import OpenAIBuilder, OpenAILikeBuilder


# Enums
class OpenAILikeLLMNames(str, Enum):
    NEMO = "nemo"
    LLAMA = "llama"


class LLMProviderNames(str, Enum):
    OPENAI = "openai"
    OPENAI_LIKE = "openai-like"


# Secrets
class OpenAILLMSecrets(BaseSettings):
    model_config = ConfigDict(
        env_file_encoding="utf-8",
        env_prefix="RAG__LLMS__OPENAI__",
        env_nested_delimiter="__",
        extra="ignore",
    )

    api_key: SecretStr = Field(
        ..., description="API key for the model provider."
    )


class OpenAILikeLLMSecrets(OpenAILLMSecrets):
    model_config = ConfigDict(
        env_file_encoding="utf-8",
        env_prefix="RAG__LLMS__OPENAI_LIKE__",
        env_nested_delimiter="__",
        extra="ignore",
    )

    api_key: SecretStr = Field(
        ..., description="API key for the model provider."
    )
    api_base: SecretStr = Field(
        ..., description="Base URL of the model provider."
    )


class LLMConfiguration(ConfigurationWithSecrets):
    name: str = Field(..., description="The name of the language model.")
    max_tokens: int = Field(
        ..., description="The maximum number of tokens for the language model."
    )
    max_retries: int = Field(
        ..., description="The maximum number of retries for the language model."
    )


# Configuration
class OpenAILLMConfiguration(LLMConfiguration):
    provider: Literal[LLMProviderNames.OPENAI] = Field(
        ..., description="The name of the language model provider."
    )
    secrets: OpenAILLMSecrets = Field(
        None, description="The secrets for the language model."
    )

    builder: Callable = Field(
        OpenAIBuilder.build,
        description="The builder for the language model.",
        exclude=True,
    )


class OpenAILikeLLMConfiguration(LLMConfiguration):
    provider: Literal[LLMProviderNames.OPENAI_LIKE] = Field(
        ..., description="The name of the language model provider."
    )
    name: Literal[OpenAILikeLLMNames.LLAMA, OpenAILikeLLMNames.NEMO] = Field(
        ..., description="The name of the language model."
    )
    secrets: OpenAILikeLLMSecrets = Field(
        None, description="The secrets for the language model."
    )
    context_window: int = Field(
        ..., description="The context window size for the language model."
    )

    builder: Callable = Field(
        OpenAILikeBuilder.build,
        description="The builder for the language model.",
        exclude=True,
    )


AVAILABLE_LLMS = Union[OpenAILikeLLMConfiguration, OpenAILLMConfiguration]
