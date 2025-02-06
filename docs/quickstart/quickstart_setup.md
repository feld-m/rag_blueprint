# Quickstart Setup

This guide outlines the steps to set up and deploy the RAG system on your desired server or local machine.

Requirements:

 - Python 3.12
 - Docker

## Configuration & Secrets

The default configuration is located in `configuration.json`. This file configures Notion as the document datasource and defines default settings for embedding, augmentation, and evaluation stages. To customize the setup, refer to the configuration guide [Docs in Progress].

### Secrets Configuration

Secrets are stored in the `env_vars/.env` file. Use the following template to define the necessary values:

```sh
# Datasources
RAGKB__DATASOURCES__NOTION__API_TOKEN=...

# LLMs
RAGKB__LLMS__OPEN_AI_LIKE__API_BASE=...
RAGKB__LLMS__OPEN_AI_LIKE__API_KEY=...

# Langfuse
RAGKB__LANGFUSE__DATABASE__USER=user
RAGKB__LANGFUSE__DATABASE__PASSWORD=password

RAGKB__LANGFUSE__SECRET_KEY=...
RAGKB__LANGFUSE__PUBLIC_KEY=...
```

- `RAGKB__LLMS__OPEN_AI_LIKE__*`: Required for connecting to the LLM, accessible via `RAGKB__LLMS__OPEN_AI_LIKE__API_BASE` and `RAGKB__LLMS__OPEN_AI_LIKE__API_KEY`. The LLM uses [TabbyAPI](https://api-docs.tabby.ai/) and integrates through the [OpenAILike](https://docs.llamaindex.ai/en/stable/api_reference/llms/openai_like/) client.
- **Langfuse Keys**: `RAGKB__LANGFUSE__SECRET_KEY` and `RAGKB__LANGFUSE__PUBLIC_KEY` are generated during initialization and will need to be updated later.


## Initialization

### Python Environment

1. Install uv on you OS following this [installation](https://docs.astral.sh/uv/getting-started/installation/) guide.

2. In the root of the project, create a virtual environment and activate it:

```sh
uv venv
source .venv/bin/activate
```

3. Install the required dependencies:

```sh
uv sync --all-extras
```

### Services Initialization

To initialize the Langfuse and vector store services, run the initialization script:

```sh
build/workstation/init.sh
```

**_NOTE:_**  Depending on your OS and the setup you might need to give execute permission to the initialization script e.g. `chmod u+x build/workstation/init.sh`

Once initialized, access the Langfuse web server on your localhost (port defined in `configuration.json` under `pipeline.augmentation.langfuse.port`). Use the Langfuse UI to:

1. Create a user.
2. Set up a project for the application.
3. Generate secret and public keys for the project.

Add the generated keys to the `env_vars/.env` file as follows:

```sh
RAGKB__LANGFUSE__SECRET_KEY=<generated_secret_key>
RAGKB__LANGFUSE__PUBLIC_KEY=<generated_public_key>
```


## Deployment

After completing the initialization, deploy the RAG system using the following command:

```sh
build/workstation/deploy.sh
```

This command sets up and runs the RAG system on your workstation, enabling it for use.
