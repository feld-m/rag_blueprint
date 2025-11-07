"""Postprocessor components for document filtering and reranking."""

# Import and register all postprocessors
from augmentation.components.postprocessors import colbert_rerank, hybrid_filter

colbert_rerank.register()
hybrid_filter.register()
