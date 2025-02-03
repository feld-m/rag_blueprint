# RAG Blueprint

A comprehensive open-source framework for building production-ready Retrieval-Augmented Generation (RAG) systems. This blueprint simplifies the development of RAG applications while providing full control over performance, resource usage, and evaluation capabilities.

While building or buying RAG systems has become increasingly accessible, deploying them as production-ready data products remains challenging. Our framework bridges this gap by providing a streamlined development experience with easy configuration and customization options, while maintaining complete oversight of performance and resource usage.

It comes with built-in monitoring and observability tools for better troubleshooting, integrated LLM-based metrics for evaluation, and human feedback collection capabilities. Whether you're building a lightweight knowledge base or an enterprise-grade application, this blueprint offers the flexibility and scalability needed for production deployments.

<div align="center">
  <img src="res/readme/Architecture.png" width="1200">
</div>

## 🚀 Features

- **Multiple Knowledge Sources**: Native integration with Notion, Confluence and PDF files, while also being extensible for other data sources
- **RAG Pipeline**:
  - Chunking with markdown-aware text splitting
  - Local high-performance embedding with `BAAI/bge-small-en`
  - Vector storage with Qdrant
- **Production Ready**:
  - Comprehensive evaluation metrics using RAGAS
  - Human feedback collection
  - Full observability with Langfuse integration
- **Interactive UI**: User-friendly chat interface powered by Chainlit

## 🛠️ Tech Stack

### Core
- [Python](https://www.python.org/)
- [LlamaIndex](https://www.llamaindex.ai/) - RAG framework
- [Chainlit](https://chainlit.io/) - Chat interface
- [Langfuse](https://langfuse.com/) - LLM observability
- [RAGAS](https://docs.ragas.io/) - RAG evaluation

### Data Sources
- [Notion](https://developers.notion.com/)
- [Confluence](https://developer.atlassian.com/cloud/confluence/rest/v2/intro/#about)
- PDF files support

### Models

#### Embedding Models
- [BAAI/bge-small-en](https://huggingface.co/BAAI/bge-small-en) - Base embedding model
- [VoyageAI](https://www.voyageai.com/)
- [OpenAI](https://openai.com/) embeddings support
- Any embedding model in the [Hugging Face](https://huggingface.co/) model hub

#### Language Models
- [NVIDIA NeMo](https://www.nvidia.com/en-us/ai-data-science/generative-ai/nemo-framework/)
- Support for:
  - [Llama 3.1](https://ai.meta.com/llama/)
  - [Phi-4](https://www.microsoft.com/en-us/research/project/phi-2/)
  - Any OpenAI-compatible API
  - OpenAI models

### Infrastructure
- [Qdrant](https://qdrant.tech/) - Vector database
- [PostgreSQL](https://www.postgresql.org/) - Metadata storage
- Docker for containerization

## 🚀 Quick Start

1. Check the detailed [Build Guide](build/README.md)
2. Access points after deployment:
   - Chat UI: `http://localhost:8001`
   - Qdrant Dashboard: `http://localhost:6333/dashboard`
   - Langfuse: `http://localhost:3003`

## 🏗️ Architecture

### Data Flow

1. **Extraction**:
   - Fetches content from the data sources pages through their respective APIs
   - Handles rate limiting and retries
   - Extracts metadata (title, creation time, URLs, etc.)

2. **Processing**:
   - Markdown-aware chunking using LlamaIndex's MarkdownNodeParser
   - Embedding generation using the selected embedding model
   - Vector storage in Qdrant

3. **Retrieval & Generation**:
   - Context-aware retrieval with configurable filters
   - LLM-powered response generation
   - Human feedback collection

### Evaluation

<div align="center">
  <img src="res/readme/Human_feedback.png" width="800">
</div>

The system includes comprehensive evaluation capabilities:

- **Automated Metrics** (via RAGAS):
  - Faithfulness
  - Answer Relevancy
  - Context Precision
  - Context Recall
  - Harmfulness

- **Human Feedback**:
  - Integrated feedback collection through Chainlit
  - Automatic dataset creation from positive feedback
  - Manual expert feedback support

- **Observability**:
  - Full tracing and monitoring with Langfuse
  - Separate traces for chat completion and deployment evaluation
  - Integration between Chainlit and Langfuse for comprehensive tracking

## 📁 Project Structure

```
.
├── build/          # Build and deployment scripts
│   └── workstation/  # Local deployment configs
├── env_vars/       # Environment configuration
├── res/           # Assets
└── src/           # Source code
    ├── augmentation/  # Retrieval and UI components
    ├── common/        # Shared utilities
    ├── embedding/     # Data extraction and embedding
    └── evaluate/      # Evaluation system
```

## 📚 Documentation

For detailed documentation on setup, configuration, and development:
- [Documentation Site](https://feld-m.github.io/rag_blueprint/)
- [Build Guide](build/README.md)
