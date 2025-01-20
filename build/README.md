# Secrets & Configuration

Create `env_vars/.env` file and insert required variables replacing example values:

```bash
# Vector stores
RAGKB__VECTOR_STORES__QDRANT__URL=http://qdrant-url:6333
RAGKB__VECTOR_STORES__QDRANT__PORT_REST=6333
RAGKB__VECTOR_STORES__QDRANT__PORT_GRPC=6334
RAGKB__VECTOR_STORES__QDRANT__COLLECTION_NAME=collection_name

# LLM
RAGKB__LLMS__OPEN_AI_LIKE__API_BASE=http://llm-url:8000
RAGKB__LLMS__OPEN_AI_LIKE__API_KEY=API_KEY

# Notion
RAGKB__DATASOURCES__NOTION__API_TOKEN=API_TOKEN

# Langfuse
RAGKB__LANGFUSE__DATABASE__CONN_INFO=postgresql://user:password@database-url:5532/langfuse
RAGKB__LANGFUSE__DATABASE__PORT=5532
RAGKB__LANGFUSE__DATABASE__USER=user
RAGKB__LANGFUSE__DATABASE__PASSWORD=password
RAGKB__LANGFUSE__DATABASE__NAME=langfuse

RAGKB__LANGFUSE__HOST=http://langfuse-url:3000
RAGKB__LANGFUSE__PORT=3000
RAGKB__LANGFUSE__SECRET_KEY=SECRET_KEY
RAGKB__LANGFUSE__PUBLIC_KEY=PUBLIC_KEY

# Chainlit
RAGKB__CHAINLIT__PORT=8000
```

`RAGKB__LANGFUSE__SECRET_KEY` and `RAGKB__LANGFUSE__PUBLIC_KEY` can be set only after initialization step.

The runtime configuration is available at `src/*/bootstrap/configuration` directories.

# Workstation

## Initialization

### Run

System uses **QDrant** vector database for storing embeddings and database server for **Langfuse**. The last service is **Langfuse** server. If these services are already up and running, change corresponding variables in `.env` and skip initialization.

Otherwise all of them can be created by running the following command:

```bash
build/workstation/init/init.sh
```

It will use configuration from `.env` (e.g. ports) to build the services. If specified port is occupied initialization of the component will be skipped.

### Langfuse project

Go to **Langfuse** UI available at `http://localhost:${RAGKB__LANGFUSE__PORT}`, create the account and setup a project. Save project's keys in `.env` under `RAGKB__LANGFUSE__SECRET_KEY` and `RAGKB__LANGFUSE__PUBLIC_KEY` variables.

## Deployment

### Run

Process is separated into embedding stage and retrieval-augmentation visualized by **Chainlit** UI. In order to build and deploy the scripts, services from **Initialization** step have to be up and all the variables from `.env` have to be set. To run corresponding scripts execute the following command:

```bash
build/workstation/deploy.sh
```

Deploy script includes unit testing, deployment of `embed.py` and `chat.py`. At the end evaluations from `evalute.py` are run and the results can be found in the corresponding datasets in **Langfuse UI**. The script is run in the background, because embedding the whole knowledge base can take a significant amount of time. Note that if used collection name already exists, `embed.py` won't proceed with the embedding process. All the logs can be found in `build/workstation/logs` directory in the latest log file.

# Local

## Initialization and Run

You can use **Workstation** build scripts in order to initialize the services and run the scripts.

## Git setup

File `.pre-commit-config.yaml` contains configuration of the code formatters that are run before the commit. After cloning and installing the `requirements.txt`, you can set up the git hook scripts with this command in your repository:

```
pre-commit install
```
