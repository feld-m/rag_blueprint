# How to Add a New LLM Implementation

This guide demonstrates how to add support for a new Language Model (LLM) implementation, using OpenAI as an example. The implementation is defined in [llm_configuration.py](https://github.com/feld-m/rag_blueprint/blob/main/src/common/bootstrap/configuration/pipeline/augmentation/query_engine/llm_configuration.py).

## Step 1: Add Dependencies

Add the required packages to `pyproject.toml`:

```toml
...
llama-index-llms-openai==0.2.16
...
```

## Step 2: Define the LLM Provider

LLM configurations in [llm_configuration.py](https://github.com/feld-m/rag_blueprint/blob/main/src/common/bootstrap/configuration/pipeline/augmentation/query_engine/llm_configuration.py) are scoped by provider. Each provider, such as [OpenAI](https://openai.com/), requires its own Pydantic configuration class. Begin by assigning a meaningful name to the new provider in the `LLMProviderNames` enumeration:

```py
class LLMProviderNames(str, Enum):
    ...
    OPENAI = "openai"
```

## Step 3: Configure LLM Secrets

Next, define how secrets for the LLM are handled. For OpenAI, this includes an `api_key`. Create a secrets class that retrieves these values from environments secrets file:

```py
class OpenAILLMSecrets(BaseSettings):
    model_config = ConfigDict(
        env_file_encoding="utf-8",
        env_prefix="RAG__LLMS__OPENAI__",
        env_nested_delimiter="__",
        extra="ignore",
    )

    api_key: Optional[SecretStr] = Field(
        None, description="API key for the model provider."
    )
```

- `env_prefix`: Prefix for secrets, e.g., `RAG__LLMS__OPENAI__`.
- **Environment Variable Naming**: To populate the api_key, use the variable `RAG__LLMS__OPENAI__API_KEY` in the environment file.

Example `configurations/secrets.{environment}.env` entry:

```sh
...
RAG__LLMS__OPENAI__API_KEY=<openai_api_key>
...
```

## Step 4: Implement the LLM Configuration

Define the main configuration class for the LLM, extending the base `LLMConfiguration`:

```py
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
```

`provider`: Constrained to the OpenAI value, ensuring only configurations matching `LLMProviderNames.OPENAI` are valid.

`secrets`: Links the configuration to the `OpenAILLMSecrets` class.

`builder`: Specifies a callable (e.g., `OpenAIBuilder.build`) responsible for initializing the LLM instance.

**Example JSON Configuration**

```json
...
    "llm": {
        "provider": "openai", // only openai is accepted for `OpenAILLMConfiguration`
        "name": "gpt-4o",     // any model name compatible with OpenAI API
        "max_tokens": 1024,
        "max_retries": 3,
    }
...
```

- `provider`: Matches the provider defined in `LLMProviderNames`.

- `name`: Specifies the LLM model (e.g., `gpt-4o`).

- `max_tokens`: Sets the maximum token limit for the LLM.

- `max_retries`: Defines the retry policy for API calls.


## Step 5: Expose LLM Configuration

To make pydantic parse corresponding json object to our `OpenAILLMConfiguration` we need to add it to `AVAILABLE_LLMS` variable:

```py
AVAILABLE_LLMS = Union[..., OpenAILLMConfiguration]
```

## Step 6: Create the LLM Builder

The builder is responsible for initializing the LLM. Our implementation leverages [llamaindex](https://docs.llamaindex.ai/en/stable/), to add the builder logic to [llm_builders.py](https://github.com/feld-m/rag_blueprint/blob/main/src/common/builders/llm_builders.py) we add necessary builder.

```py
from typing import TYPE_CHECKING

from injector import inject
from llama_index.llms.openai import OpenAI

if TYPE_CHECKING:
    from common.bootstrap.configuration.pipeline.augmentation.query_engine.llm_configuration import (
        OpenAILLMConfiguration,
    )


class OpenAIBuilder:
    """Builder for creating OpenAI language model instances.

    Provides factory method to create configured OpenAI objects.
    """

    @staticmethod
    @inject
    def build(configuration: "OpenAILLMConfiguration") -> OpenAI:
        """Creates a configured OpenAI language model.

        Args:
            configuration: Model settings including API key and parameters.

        Returns:
            OpenAI: Configured language model instance.
        """
        return OpenAI(
            api_key=configuration.secrets.api_key.get_secret_value(),
            model=configuration.name,
            max_tokens=configuration.max_tokens,
            max_retries=configuration.max_retries,
        )
```

**Explanation**:

- **Dependencies**: Use dependency injection (@inject) to ensure proper initialization.

- **Configuration**: Extracts `api_key`, `model`, `max_tokens`, and `max_retries` from the `OpenAILLMConfiguration`.

- **Library Integration**: Uses `llama_index.llms.openai.OpenAI` to create the LLM instance.

After all these steps, OpenAI models are ready to be configured and used in RAG System.
