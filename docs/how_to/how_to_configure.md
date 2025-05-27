# How to Configure the RAG System

This guide explains how to customize the RAG system pipeline through configuration files.

## Environments

### Definition

The following environments are supported:

```py
class EnvironmentName(str, Enum):
    DEFAULT = "default"
    LOCAL = "local"
    DEV = "dev"
    TEST = "test"
    PROD = "prod"
```

Each environment requires corresponding configuration and secrets files in the [configurations](https://github.com/feld-m/rag_blueprint/tree/main/configurations) directory:

- Configuration files: `configuration.{environment}.json`
- Secrets files: `secrets.{environment}.env`

The configuration files define the pipeline setup, while secrets files store credentials and tokens. For security, all files in the configurations directory are git-ignored except for `configuration.default.json` and `configuration.local.json`.

### Usage

Run the pipeline with a specific configuration using the `--env` flag:

```sh
build/workstation/init.sh --env default
python src/embed.py --env default
```

## Datasource Configuration

Currently, the following datasources are available:

```py
class DatasourceName(str, Enum):
    NOTION = "notion"
    CONFLUENCE = "confluence"
    PDF = "pdf"
```

Blueprint allows the usage of single or multiple datasources. Adjust the corresponding configuration accordingly:

```json
{
    "extraction": {
        "datasources": [
            {
                "name": "notion",
                "export_limit": 100
            },
            {
                "name": "pdf",
                "export_limit": 100,
                "base_path": "data/"
            }
        ]
    }
}
```

Each entry in `datasources` corresponds to a single source that will be sequentially used for the extraction of documents to be further processed. The `name` of each entry must correspond to one of the implemented enums. Datasources' secrets must be added to the environment's secret file. To check configurable options for specific datasources, visit `configuration.py` of a datasource.

## LLM Configuration

The system supports the following LLM providers:

```py
class LLMProviderName(str, Enum):
    LITE_LLM = "lite_llm"
```

`LITE_LLM` leverages the [LiteLLM](https://docs.litellm.ai/) service, providing a unified interface for cloud-hosted models (e.g., OpenAI, Google, Anthropic) and self-hosted LLMs. Minimal setup requires the use of LLMs in augmentation and evaluation processes. To configure this, adjust the following JSON entries:

```json
{
    "pipeline": {
        "augmentation": {
            "chat_engine": {
                "guardrails": {
                        "llm": {
                            "provider": "lite_llm",
                            "name": "gemini-2.0-flash-exp",
                        },
                },
                "llm": {
                    "provider": "lite_llm",
                    "name": "gemini-2.0-flash-exp",
                    "max_tokens": 1024,
                    "max_retries": 3,
                    "context_window": 16384
                }
            }
        },
        "evaluation": {
            "judge_llm": {
                "provider": "lite_llm",
                "name": "gemini-2.0-flash-exp",
                "max_tokens": 1024,
                "max_retries": 3,
                "context_window": 16384
            }
        }
    }
}
```

 The `provider` field must be one of the values from `LLMProviderName`, and the `name` field indicates the specific model exposed by the provider. To check configurable options for specific providers, visit `configuration.py` of an LLM.

In the above case, augmentation and evaluation processes use the same LLM, which might be suboptimal. To change it, simply adjust the entry of one of these:

```json
{
    "pipeline": {
        "augmentation": {
            "chat_engine": {
                "guardrails": {
                        "llm": {
                            "provider": "lite_llm",
                            "name": "gemini-2.0-flash-exp",
                        },
                },
                "llm": {
                    "provider": "lite_llm",
                    "name": "gemini-2.0-flash-exp",
                    "max_tokens": 1024,
                    "max_retries": 3,
                    "context_window": 16384
                }
            }
        },
        "evaluation": {
            "judge_llm": {
                "provider": "lite_llm",
                "name": "gpt-4o-mini",      // another llm
                "max_tokens": 512           // different parameters
            }
        }
    }
}
```

*__Note__*: You can also use different LLM for any other component like `guardrails`.

### Secrets

Each model requires api key. For the above LLMs add following secrets:

```sh
RAG__LLMS__GEMINI_2_0_FLASH_EXP_API_KEY={your-gemini-api-key}
RAG__LLMS__GPT_4O_MINI__API_KEY={your-openai-api-key}
```

The variable name includes the uppercased name of the model you are using, whereas all non-alphanumeric characters are replaced by underscores e.g. `gpt-3.5-turbo` -> `GPT_3_5_TURBO`.

If you want to use your local model called for instance `my-llm`, which is exposed via openai-like API you can use the following configuration:

```json
"provider": "lite_llm",
"name": "openai/my-llm",
"api_base": "http://127.0.0.1/v1
```

And the secrets will look as follows:

```
RAG__LLMS__OPENAI_MY_LLM__API_KEY={your-api-key}
```

> **_Note_** You can use different API structure for your local LLMs, then just replace `openai/` prefix with corresponding provider.

## Embedding Model Configuration

Currently, embedding models from these providers are supported:

```py
class EmbeddingModelProviderName(str, Enum):
    HUGGING_FACE = "hugging_face"
    OPENAI = "openai"
    VOYAGE = "voyage"
```

Any model exposed by these providers can be used in the setup.

Minimal setup requires the use of embedding models in different processes. To configure this, adjust the following JSON entries:

```json
{
    "embedding": {
        "embedding_model": {
            "provider": "hugging_face",
            "name": "BAAI/bge-small-en-v1.5",
            "tokenizer_name": "BAAI/bge-small-en-v1.5",
            "splitter": {
                "chunk_overlap_in_tokens": 50,
                "chunk_size_in_tokens": 384
            }
        }
    },
    "evaluation": {
        "judge_embedding_model": {
            "provider": "hugging_face",
            "name": "BAAI/bge-small-en-v1.5",
            "tokenizer_name": "BAAI/bge-small-en-v1.5"
        }
    }
}
```

Providers' secrets must be added to the environment's secret file. The `provider` field must be one of the values from `EmbeddingModelProviderName`, and the `name` field indicates the specific model exposed by the provider. The `tokenizer_name` field indicates the tokenizer used in pair with the embedding model, and it should be compatible with the specified embedding model. The `splitter` defines how the documents should be chunked in the embedding process and is required for `embedding` configuration. To check configurable options for specific providers, visit `configuration.py` of a embedding model.

**_Note_**: The same embedding model is used for embedding and retrieval processes, therefore it is defined in the `embedding` configuration only.

In the above case, embedding/retrieval and evaluation processes use the same embedding model, which might be suboptimal. To change it, simply adjust the entry of one of these:

```json
{
    "embedding": {
        "embedding_model": {
            "provider": "hugging_face",
            "name": "BAAI/bge-small-en-v1.5",
            "tokenizer_name": "BAAI/bge-small-en-v1.5",
            "splitting": {
                "name": "basic",
                "chunk_overlap_in_tokens": 50,
                "chunk_size_in_tokens": 384
            }
        }
    },
    "evaluation": {
        "judge_embedding_model": {
            "provider": "openai",                       // different provider
            "name": "text-embedding-3-small",           // different embedding model
            "tokenizer_name": "text-embedding-3-small", // different tokenizer
            "batch_size": 64                            // different parameters
        }
    }
}
```

## Vector Store Configuration

Currently, the following vector stores are supported:

```py
class VectorStoreName(str, Enum):
    QDRANT = "qdrant"
    CHROMA = "chroma"
    PGVECTOR = "pgvector"
```

To configure the vector store, update the following entry:

```json
{
    "embedding": {
        "vector_store": {
            "name": "qdrant",
            "collection_name": "collection-default",
            "host": "qdrant",
            "protocol": "http",
            "port": 6333
        }
    }
}
```

The `name` field indicates one of the vector stores from `VectorStoreName`, and the `collection_name` defines the vector store collection for embedded documents. The next fields define the connection to the vector store. Corresponding secrets must be added to the environment's secrets file. To check configurable options for specific datasources, visit `configuration.py` of a vector store.

**_Note_**: If `collection_name` already exists in the vector store, the embedding process will be skipped. To run it, delete the collection or use a different name.

## Langfuse and Chainlit Configuration

Configuration contains the entries related to Langfuse and Chainlit:

```json
{
    "augmentation": {
        "langfuse": {
            "host": "langfuse",
            "protocol": "http",
            "port": 3000,
            "database": {
                "host": "langfuse-db",
                "port": 5432,
                "db": "langfuse"
            }
        },
        "chainlit": {
            "port": 8000
        }
    }
}
```

Field `chailit.port` defines on which port chat UI should be run. Fields in `langfuse` define connection details to Langfuse server and `langfuse.database` details of its database. Corresponding secrets for Langfuse have to be added to environment's secrets file.

## Prompt Templates Configuration

For prompts management system uses [Langfuse Prompt](https://langfuse.com/docs/prompts/get-started) service. By default four prompt templates are created in Langfuse Prompts service - `default_system_prompt`, `default_context_refine_prompt`, `default_context_prompt`, `default_condense_prompt`, `default_input_guardrail_prompt` and `default_output_guardrail_prompt`. To find out more about these templates visit [Llamaindex guide](https://docs.llamaindex.ai/en/stable/examples/chat_engine/chat_engine_condense_plus_context/).

Prompts are used during the augmentation process, which affects the final answers of the system. They can be adjusted via Langfuse Prompts UI. If you want to provide and use templates under different names, you need to add them to Langfuse Prompts and change the configuration as follows:

```json
{
  "augmentation": {
    "chat_engine": {
      "guardrails": {
        "input_prompt_name": "default_input_guardrail_prompt",
        "output_prompt_name": "default_output_guardrail_prompt",
      },
      "prompt_templates": {
        "condense_prompt_name": "new_condense_prompt",
        "context_prompt_name": "new_context_prompt",
        "context_refine_prompt_name": "new_context_refine_prompt",
        "system_prompt_name": "new_system_prompt"
      }
    }
  }
}
```

## Upcoming Docs

Docs about configurable retrievers, postprocessors and others are in progress..
