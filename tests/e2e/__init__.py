"""
End-to-End (E2E) Tests

This package contains end-to-end tests that validate the complete RAG pipeline
with real infrastructure (databases, APIs, embedding models).

Test Scope:
- Full extraction pipeline (API → Document → Embedding → Storage)
- Real infrastructure (PGVector, HuggingFace, DIP API)
- Integration between all components
- Data flow from end to end

These tests are slower than unit/integration tests but provide confidence
that the entire system works together correctly.
"""
