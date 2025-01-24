# RAG Blueprint Documentation

## Overview
The RAG blueprint project is a Retrieval-Augmented Generation system that integrates with several datasources to provide intelligent document search and analysis. The system combines the power of different large language models with knowledge bases to deliver accurate, context-aware responses through a chat interface.

## Data Sources

| Data Source | Description | Configuration Guide |
|-------------|-------------|---------------------|
| Confluence | Enterprise wiki and knowledge base integration | Docs in progress |
| Notion | Workspace and document management integration | Docs in progress |
| PDF | PDF document processing and text extraction | Docs in progress |


## Embeddding Models

| Models | Provider | Description | Configuration Guide |
|-------|----------|-------------|---------------|
|   *   | [HuggingFace](https://huggingface.co/) | Open-sourced, run locally embedding models provided by HuggingFace | Docs in progress |
|   *   | [OpenAI](https://openai.com/) | Embedding models provided by OpenAI | Docs in progress |
|   *   | [VoyageAI](https://www.voyageai.com/) | Embedding models provided by VoyageAI | Docs in progress |

## Language Models

| Model | Provider | Description | Configuration Guide |
|-------|----------|-------------|---------------|
|   *   |  [OpenAI](https://openai.com/)  | Language models provided by OpenAI | Docs in progress |
|   *   |  OpenAILike  | Self-hosted language models shared through OpenAI like API | Docs in progress |


## Vector Databases

| Vector Store | Description | Configuration |
|--------------|-------------|---------------|
| Qdrant | High-performance vector similarity search engine | Docs in progress |
| Chroma |  Lightweight embedded vector database | Docs in progress |


## Key Features

- **Multiple Knowledge Base Integration**: Seamless extraction from several Data Sources(Confluence, Notion, PDF)
- **Vector Search**: Efficient similarity search using vector stores
- **Interactive Chat**: User-friendly interface for querying knowledge on [Chainlit](https://chainlit.io/)
- **Performance Monitoring**: Query and response tracking with [Langfuse](https://langfuse.com/)

### Quick Start
- [Docs in progress]
