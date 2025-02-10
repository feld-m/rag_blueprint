# How To Add New Embedding Model Implementation

This guide outlines the process of adding support for a new embedding model implementation. We use the existing `OpenAIEmbeddingModelConfiguration` as an example, located in [embedding_model_configuration.py](src/common/bootstrap/configuration/pipeline/embedding/embedding_model/embedding_model_configuration.py) file.

## Update Project Dependencies

Since we will use [OpenAI](https://openai.com/)'s embedding models through [llamaindex](https://docs.llamaindex.ai/en/stable/) implementation add correspodning entry to `pyproject.toml`:

```toml
...
llama-index-embeddings-openai=0.2.4
...
```

## Define the Embedding Model Provider

Embedding model configurations in *embedding_model_configuration.py* are scoped by provider. Each provider, such as OpenAI, requires its own Pydantic configuration class. Begin by assigning a meaningful name to the new provider in the `EmbeddingModelProviderNames` enumeration:

```py
class EmbeddingModelProviderNames(str, Enum):
    ...
    OPENAI = "openai"
```

## Configure Embedding Model Secrets

Next, define how secrets for the embedding model are handled. For OpenAI, this includes an `api_key`. Create a secrets class that retrieves these values from environment variables (e.g., from  `env_vars/.env` or a user-specified file):

```py
class OpenAIEmbeddingModelSecrets(BaseSettings):
    model_config = ConfigDict(
        env_file="env_vars/.env",
        env_file_encoding="utf-8",
        env_prefix="RAGKB__EMBEDDING_MODELS__OPEN_AI__",
        env_nested_delimiter="__",
        extra="ignore",
    )

    api_key: Optional[SecretStr] = Field(
        None, description="API key for the embedding model"
    )
```

- `env_prefix`: Prefix for secrets, e.g., `RAGKB__EMBEDDING_MODELS__OPEN_AI__`.
- **Environment Variable Naming**: To populate the api_key, use the variable `RAGKB__EMBEDDING_MODELS__OPEN_AI__API_KEY` in the environment file.

Example `.env` entry:

```sh
...
RAGKB__EMBEDDING_MODELS__OPEN_AI__API_KEY=<openai_api_key>
...
```

## Implement the Embedding Model Configuration

Define the main configuration class for the embedding model, extending the base `EmbeddingModelConfiguration`:

```py
class OpenAIEmbeddingModelConfiguration(EmbeddingModelConfiguration):

    provider: Literal[EmbeddingModelProviderNames.OPENAI] = Field(
        ..., description="The provider of the embedding model."
    )
    max_request_size_in_tokens: int = Field(
        8191,
        description="Maximum size of the request in tokens.",
    )
    secrets: OpenAIEmbeddingModelSecrets = Field(
        None, description="The secrets for the language embedding model."
    )

    builder: Callable = Field(
        OpenAIEmbeddingModelBuilder.build,
        description="The builder for the embedding model.",
        exclude=True,
    )

    def model_post_init(self, __context):
        super().model_post_init(__context)
        self.batch_size = (
            self.max_request_size_in_tokens
            // self.splitting.chunk_size_in_tokens
        )
```

`provider`: Constrained to the openai value, ensuring only configurations matching `EmbeddingModelProviderNames.OPENAI` are valid.

`max_request_size_in_tokens`: Maximum number of tokens being embeded in a single request by specified embedding model. For details visit OpenAI's documentation.

`secrets`: Links the configuration to the `OpenAIEmbeddingModelSecrets` class.

`builder`: Specifies a callable (e.g., `OpenAIEmbeddingModelBuilder.build`) responsible for initializing the embedding instance.

**_Note_**: Because of OpenAI's API nature, we need to calculate the `batch_size` based on the fields from `configuration.json`, it is done in `model_post_init`.

## Setup Tokenizer Initizalization

Each tokenizer corresponds to a specific embedding model. To standardize this, the base class `EmbeddingModelConfiguration` defines the tokenizer_name field, which is required by all subclass implementations, such as `OpenAIEmbeddingModelConfiguration`. Since no single package universally supports initializing all tokenizers, the appropriate encoding function must be specified within the `get_tokenizer` method of `EmbeddingModelConfiguration.`

For the OpenAI embedding models, the `tiktoken` package provides the tokenizer implementation. As a result, the `get_tokenizer` method is customized for OpenAI embeddings to utilize tiktoken for tokenization. This ensures compatibility and consistency in encoding logic across the implementation.

```py
    import tiktoken
    ...
    class EmbeddingModelConfiguration(BaseModel):
        ...
        def get_tokenizer(self) -> Callable:
            match self.provider:
                ...
                case EmbeddingModelProviderNames.OPENAI:
                    return tiktoken.encoding_for_model(self.tokenizer_name).encode
                ...
```


**Example JSON Configuration**

```json
...
    "embedding_model": {
        "provider": "openai",
        "name": "text-embedding-3-small",
        "tokenizer_name": "text-embedding-3-small",
        "splitting": {
            "name": "basic",
            "chunk_overlap_in_tokens": 50,
            "chunk_size_in_tokens": 384
        }
    }
...
```

- `provider`: Matches the provider defined in `EmbeddingModelProviderNames`.

- `name`: Specifies the embedding model (e.g., `text-embedding-3-small`).

- `tokenizer_name`: Sets the tokenizer used in the pipeline.

- `splitting`: Defines the splitting strategy.


## Expose Embedding Model Configuration

To make pydantic parse corresponding json object to our `OpenAIEmbeddingModelConfiguration` we need to add it to `AVAILABLE_EMBEDDING_MODELS` variable:

```py
AVAILABLE_EMBEDDING_MODELS = Union[..., OpenAIEmbeddingModelConfiguration]
```

## Create the Embedding Model Builder

The builder is responsible for initializing the Embedding Model. Our implementation leverages llamaindex, to add the builder logic to [embedding_builders.py](src/common/builders/embedding_builders.py) we add necessary builder.

```py
from typing import TYPE_CHECKING

from injector import inject
from llama_index.embeddings.openai import OpenAIEmbedding

if TYPE_CHECKING:
    from common.bootstrap.configuration.pipeline.embedding.embedding_model.embedding_model_configuration import (
        OpenAIEmbeddingModelConfiguration,
    )


class OpenAIEmbeddingModelBuilder:
    """Builder for creating OpenAI embedding model instances.

    Provides factory method to create configured OpenAIEmbedding objects.
    """

    @staticmethod
    @inject
    def build(
        configuration: "OpenAIEmbeddingModelConfiguration",
    ) -> OpenAIEmbedding:
        """Creates a configured OpenAI embedding model.

        Args:
            configuration: Embedding model settings including API key, name and batch size.

        Returns:
            OpenAIEmbedding: Configured embedding model instance.
        """
        return OpenAIEmbedding(
            api_key=configuration.secrets.api_key.get_secret_value(),
            model_name=configuration.name,
            embed_batch_size=configuration.batch_size,
        )
```

**Explanation**:

- **Dependencies**: Use dependency injection (@inject) to ensure proper initialization.

- **Configuration** Use: Extracts `api_key`, `model_name`, and `embed_batch_size` from the `OpenAIEmbeddingModelConfiguration`.

- **Library Integration**: Uses `llama_index.embeddings.openai.OpenAIEmbedding` to create the embedding model instance.

After all these steps, OpenAI embedding models are ready to be configured and used in RAG System.
