# Quickstart Setup

This guide outlines the steps to set up and deploy the RAG system on your server or local machine.

Requirements:

 - Python >=3.10,<3.13
 - Docker

## Configuration & Secrets

First, clone the repository and navigate to `rag_blueprint`:

```
git clone https://github.com/feld-m/rag_blueprint.git
cd rag_blueprint
```

The default configuration is located in [configuration.default.json](https://github.com/feld-m/rag_blueprint/blob/main/configurations/configuration.default.json). This file configures toy PDF dataset as the document datasource and defines default settings for embedding, augmentation, and evaluation stages. To customize the setup, refer to the [How to Configure the RAG System](../how_to/how_to_configure.md) guide.

### Secrets Configuration
Create a secrets file at `configurations/secrets.default.env`. Below is a template:

```sh
# LLMs
RAG__LLMS__GPT_4O_MINI__API_KEY={your-openai-api-key}

# Langfuse
RAG__LANGFUSE__DATABASE__USER=user
RAG__LANGFUSE__DATABASE__PASSWORD=password

RAG__LANGFUSE__SECRET_KEY=required_placeholder
RAG__LANGFUSE__PUBLIC_KEY=required_placeholder
```

- `RAG__LLMS__GPT_4O_MINI__API_KEY`: Required for connecting to [OpenAI](https://openai.com/) GPT-4o-mini LLM.
- **Langfuse Keys**: `RAG__LANGFUSE__SECRET_KEY` and `RAG__LANGFUSE__PUBLIC_KEY` are generated after initialization and will need to be updated later.

## Initialization

### Python Environment

1. Install uv on your OS following this [installation](https://docs.astral.sh/uv/getting-started/installation/) guide.

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
build/workstation/init.sh --env default
```

**_NOTE:_**  Depending on your OS and the setup you might need to give execute permission to the initialization script e.g. `chmod u+x build/workstation/init.sh`

Once initialized, access the Langfuse web server on your localhost (port defined in [configuration.default.json](https://github.com/feld-m/rag_blueprint/blob/main/configurations/configuration.default.json) under `augmentation.langfuse.port`). Use the Langfuse UI to:

1. Create a user.
2. Set up a project for the application.
3. Generate secret and public keys for the project.

Add the generated keys to the `configurations/secrets.default.env` file as follows:

```sh
RAG__LANGFUSE__SECRET_KEY=<generated_secret_key>
RAG__LANGFUSE__PUBLIC_KEY=<generated_public_key>
```


## Deployment

After completing the initialization, deploy the RAG system using the following command:

```sh
build/workstation/deploy.sh --env default
```

This command sets up and runs the RAG system on your workstation, enabling it for use.
