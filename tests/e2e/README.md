# End-to-End (E2E) Tests for Bundestag RAG Pipeline

## Overview

This directory contains end-to-end tests that validate the complete RAG (Retrieval-Augmented Generation) pipeline for Bundestag data sources. These tests use **real infrastructure** and the **highest abstraction level** to ensure the entire system works correctly from API extraction to vector storage.

### Available Test Suites

1. **Bundestag DIP API** ([test_bundestag_dip_full_pipeline.py](test_bundestag_dip_full_pipeline.py))
   - Tests extraction from DIP API (parliamentary protocols)
   - Configuration: [configuration.test-bundestag-dip.json](../../configurations/configuration.test-bundestag-dip.json)
   - Collection: `e2e_test_bundestag_dip`

2. **Bundestag Mine API** ([test_bundestag_mine_full_pipeline.py](test_bundestag_mine_full_pipeline.py))
   - Tests extraction from Bundestag Mine API (parliamentary speeches)
   - Configuration: [configuration.test-bundestag-mine.json](../../configurations/configuration.test-bundestag-mine.json)
   - Collection: `e2e_test_bundestag_mine`

## Test Architecture

### Highest Abstraction Level
The e2e test uses `EmbeddingOrchestrator.embed()` - the single entry point that orchestrates:

1. **Extraction**: Fetch documents from DIP API
2. **Parsing**: Convert API responses to `BundestagMineDocument`
3. **Cleaning**: Clean markdown/text content
4. **Splitting**: Split documents into 384-token chunks (50-token overlap)
5. **Embedding**: Generate embeddings using HuggingFace `multilingual-e5-small`
6. **Storage**: Store embeddings in PGVector database

### Why Highest Abstraction?
Using the orchestrator as the entry point ensures:
- ✅ **Refactoring-proof**: Internal component changes don't break tests
- ✅ **Real-world validation**: Tests the actual user-facing API
- ✅ **Full integration**: All components work together correctly
- ✅ **Maintenance**: One stable test interface to maintain

## Infrastructure Requirements

### Required Services

The e2e tests require the following Docker services to be running:

1. **PGVector Database**
   - Host: `localhost`
   - Port: `5433`
   - Database: `rag-local`
   - Used for: Vector storage and retrieval

2. **HuggingFace Embedding Model** (auto-downloaded)
   - Model: `intfloat/multilingual-e5-small`
   - Dimensions: 384
   - Language: Multilingual (German support)

3. **DIP API** (public endpoint)
   - Endpoint: `https://search.dip.bundestag.de/api/v1`
   - API Key: Public test key (configured automatically)

### Starting Docker Services

```bash
# From project root
cd build/workstation/docker

# Start required services
docker compose up -d

# Verify PGVector is running
docker compose ps
# Should show pgvector service as "Up"

# Check PGVector connection
docker compose exec pgvector psql -U postgres -d rag-local -c "SELECT 1;"
```

## Configuration

### E2E Test Configuration

The e2e tests use a dedicated configuration file:

**File**: `configurations/configuration.e2e.json`

```json
{
  "extraction": {
    "orchestrator_name": "basic",
    "datasources": [
      {
        "name": "bundestag",
        "include_bundestag_mine": false,
        "include_dip": true,
        "dip_wahlperiode": 21,
        "dip_sources": ["protocols"],
        "export_limit": 3
      }
    ]
  },
  "embedding": {
    "vector_store": {
      "name": "pgvector",
      "database_name": "rag-local",
      "collection_name": "e2e_test_bundestag_dip",
      "host": "localhost",
      "port": 5433
    },
    "embedding_model": {
      "provider": "hugging_face",
      "name": "intfloat/multilingual-e5-small",
      "chunk_size_in_tokens": 384,
      "chunk_overlap_in_tokens": 50
    }
  }
}
```

### Configuration Highlights

- **`export_limit: 3`**: Only fetch 3 protocols (fast tests)
- **`dip_sources: ["protocols"]`**: Only protocols (most reliable)
- **`collection_name: "e2e_test_bundestag_dip"`**: Isolated test data
- **HuggingFace model**: No API key required, runs locally

## Running the Tests

### Quick Start

```bash
# From project root

# 1. Ensure Docker services are running
cd build/workstation/docker && docker compose up -d && cd ../../..

# 2. Run all e2e tests (both DIP and Mine)
PYTHONPATH=src uv run pytest tests/e2e/ --on-prem-config --env test -v

# 3. Run specific test suite
PYTHONPATH=src uv run pytest tests/e2e/test_bundestag_dip_full_pipeline.py --on-prem-config --env test -v
PYTHONPATH=src uv run pytest tests/e2e/test_bundestag_mine_full_pipeline.py --on-prem-config --env test -v

# 4. Run specific test
PYTHONPATH=src uv run pytest tests/e2e/test_bundestag_dip_full_pipeline.py::TestBundestagDIPFullPipeline::test_full_extraction_embedding_pipeline --on-prem-config --env test -v
```

### How Multiple Test Configurations Work

Each test suite uses a different configuration file:
- `test_bundestag_dip_full_pipeline.py` → Uses `configuration.test-bundestag-dip.json`
- `test_bundestag_mine_full_pipeline.py` → Uses `configuration.test-bundestag-mine.json`

The test fixtures temporarily copy the appropriate configuration to `configuration.test.json` during test execution, then restore the original. This allows:
- ✅ Multiple test configurations to coexist
- ✅ Tests to run independently or together
- ✅ Different vector store collections (no data conflicts)
- ✅ Different data sources (DIP protocols vs Mine speeches)

### Test Execution Options

```bash
# Run with detailed output
PYTHONPATH=src uv run pytest tests/e2e/ --on-prem-config --env test -v -s

# Run and stop on first failure
PYTHONPATH=src uv run pytest tests/e2e/ --on-prem-config --env test -x

# Run only e2e tests (skip unit/integration)
PYTHONPATH=src uv run pytest -m e2e --on-prem-config --env test

# Skip e2e tests (for fast CI)
PYTHONPATH=src uv run pytest -m "not e2e" --on-prem-config --env test

# Run with short traceback for cleaner output
PYTHONPATH=src uv run pytest tests/e2e/ --on-prem-config --env test --tb=short
```

## Test Suite

### Test: `test_full_extraction_embedding_pipeline`

**Purpose**: Validate the complete pipeline from DIP API to PGVector.

**Test Steps**:
1. Initialize `EmbeddingOrchestrator` with e2e configuration
2. Execute `orchestrator.embed()` (full pipeline)
3. Verify documents are stored in PGVector
4. Validate minimum chunk count (10+ chunks)

**Validation**:
- ✅ Documents extracted from DIP API
- ✅ Documents split into chunks
- ✅ Embeddings generated
- ✅ Embeddings stored in PGVector

---

### Test: `test_document_metadata_preservation`

**Purpose**: Ensure metadata is preserved through the pipeline.

**Validation**:
- ✅ Datasource metadata: `datasource=bundestag`
- ✅ Source client: `source_client=dip`
- ✅ Document type: `document_type=protocol`
- ✅ DIP metadata: `document_number`, `legislature_period`
- ✅ Chunk metadata: `chunk_id`, `node_id`

---

### Test: `test_vector_search_retrieval`

**Purpose**: Validate vector search functionality.

**Test Steps**:
1. Create `VectorStoreIndex` from PGVector
2. Execute semantic search: `"Bundestag Sitzung Protokoll"`
3. Verify results returned (top-k=5)
4. Validate similarity scores (0-1 range)

**Validation**:
- ✅ Search returns relevant results
- ✅ Similarity scores are valid
- ✅ Retrieved chunks have content

---

### Test: `test_embedding_dimensions`

**Purpose**: Verify embedding dimensions match the model.

**Validation**:
- ✅ Embedding vectors have 384 dimensions
- ✅ Matches `multilingual-e5-small` model spec

---

### Test: `test_document_chunking_strategy`

**Purpose**: Validate document splitting configuration.

**Validation**:
- ✅ Chunks within token limits (384 tokens)
- ✅ Chunks have overlap (50 tokens)
- ✅ Chunks maintain parent document relationships

---

## Expected Test Output

### Running All Tests

```
$ PYTHONPATH=src uv run pytest tests/e2e/ --on-prem-config --env test -v

============================= test session starts ==============================
tests/e2e/test_bundestag_dip_full_pipeline.py::TestBundestagDIPFullPipeline::test_full_extraction_embedding_pipeline PASSED [ 10%]
tests/e2e/test_bundestag_dip_full_pipeline.py::TestBundestagDIPFullPipeline::test_document_metadata_preservation PASSED [ 20%]
tests/e2e/test_bundestag_dip_full_pipeline.py::TestBundestagDIPFullPipeline::test_vector_search_retrieval PASSED [ 30%]
tests/e2e/test_bundestag_dip_full_pipeline.py::TestBundestagDIPFullPipeline::test_embedding_dimensions PASSED [ 40%]
tests/e2e/test_bundestag_dip_full_pipeline.py::TestBundestagDIPFullPipeline::test_document_chunking_strategy PASSED [ 50%]
tests/e2e/test_bundestag_mine_full_pipeline.py::TestBundestagMineFullPipeline::test_full_extraction_embedding_pipeline PASSED [ 60%]
tests/e2e/test_bundestag_mine_full_pipeline.py::TestBundestagMineFullPipeline::test_document_metadata_preservation PASSED [ 70%]
tests/e2e/test_bundestag_mine_full_pipeline.py::TestBundestagMineFullPipeline::test_vector_search_retrieval PASSED [ 80%]
tests/e2e/test_bundestag_mine_full_pipeline.py::TestBundestagMineFullPipeline::test_embedding_dimensions PASSED [ 90%]
tests/e2e/test_bundestag_mine_full_pipeline.py::TestBundestagMineFullPipeline::test_document_chunking_strategy PASSED [100%]

================== 10 passed in 73.14s (0:01:13) ==================
```

### Running Individual Test Suite

**Bundestag DIP Tests** (~45 seconds):
```
$ PYTHONPATH=src uv run pytest tests/e2e/test_bundestag_dip_full_pipeline.py --on-prem-config --env test -v

✓ Successfully embedded 47 document chunks from DIP
✓ Metadata validation passed for 47 nodes
✓ Vector search returned 5 results
✓ Embedding dimensions validated: 384D
✓ Chunking strategy validated for 10 sample chunks

======================== 5 passed in 45.23s ========================
```

**Bundestag Mine Tests** (~28 seconds):
```
$ PYTHONPATH=src uv run pytest tests/e2e/test_bundestag_mine_full_pipeline.py --on-prem-config --env test -v

✓ Successfully embedded 15 document chunks from Bundestag Mine
✓ Metadata validation passed for 15 nodes
✓ Vector search returned 5 results
✓ Embedding dimensions validated: 384D
✓ Chunking strategy validated for 10 sample chunks

======================== 5 passed in 28.51s ========================
```

## Troubleshooting

### Issue: `RuntimeError: PGVector database not accessible`

**Cause**: PGVector Docker service not running.

**Solution**:
```bash
cd build/workstation/docker
docker compose up -d
docker compose ps  # Verify services are running
```

---

### Issue: `ModuleNotFoundError: No module named 'embedding'`

**Cause**: Python path not set correctly.

**Solution**:
```bash
# Run pytest from project root
cd /Users/joao/Documents/rag_blueprint
pytest tests/e2e/ -v
```

---

### Issue: `No documents found in vector store after embedding`

**Cause**: DIP API rate limiting or network issues.

**Solution**:
1. Check DIP API status: `https://search.dip.bundestag.de/api/v1`
2. Increase `export_limit` in `configuration.e2e.json`
3. Check logs for API errors

---

### Issue: `AssertionError: Expected at least 10 chunks, but got 3`

**Cause**: Documents not split correctly or too few documents.

**Solution**:
1. Verify `chunk_size_in_tokens: 384` in config
2. Increase `export_limit` in config (e.g., 5 protocols)
3. Check splitter configuration

---

### Issue: Tests are very slow (>5 minutes)

**Cause**: HuggingFace model download or too many documents.

**Solutions**:
- **First run**: HuggingFace downloads model (~100MB) - this is normal
- **Subsequent runs**: Should be fast (<1 minute)
- **Reduce `export_limit`**: Set to 2 for faster tests
- **Use pytest-xdist**: `pytest tests/e2e/ -n auto` (parallel execution)

---

## Best Practices

### ✅ Do's

- **Run e2e tests before commits**: Ensure pipeline works end-to-end
- **Clean vector store**: Tests clean automatically, but verify manually if needed
- **Use test configuration**: Don't modify `configuration.local.json` for tests
- **Check Docker logs**: `docker compose logs -f pgvector` for debugging
- **Monitor test duration**: Should complete in <2 minutes after first run

### ❌ Don'ts

- **Don't mock components**: E2e tests use real infrastructure
- **Don't skip infrastructure checks**: Always verify Docker is running
- **Don't increase `export_limit` too much**: Keep tests fast (<5 documents)
- **Don't commit test data**: Tests clean up automatically

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: rag-local
        ports:
          - 5433:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install uv
          uv pip install -e .[all]

      - name: Run E2E tests
        run: pytest tests/e2e/ -v
        env:
          PGVECTOR_HOST: localhost
          PGVECTOR_PORT: 5433
```

---

## Maintenance

### When to Update Tests

- **New datasource**: Add separate e2e test file
- **New embedding model**: Update `configuration.e2e.json`
- **Pipeline changes**: Tests should pass without changes (highest abstraction!)
- **Breaking changes**: Update validation assertions only

### Test Data Management

- **Vector store**: Auto-cleaned before/after each test
- **Configuration**: Versioned in `configurations/configuration.e2e.json`
- **Fixtures**: DIP API responses in `fixtures/dip_api/`

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review test logs: `pytest tests/e2e/ -v -s --log-cli-level=DEBUG`
3. Check Docker logs: `docker compose logs -f`
4. Open issue in repository

---

## Summary

This e2e test suite provides:
- ✅ **Complete pipeline validation**: API → Embedding → Storage → Retrieval
- ✅ **Highest abstraction level**: `EmbeddingOrchestrator.embed()`
- ✅ **Real infrastructure**: PGVector, HuggingFace, DIP API
- ✅ **Refactoring confidence**: Internal changes don't break tests
- ✅ **Fast execution**: <2 minutes (after first run)
- ✅ **Comprehensive validation**: 5 test scenarios covering all aspects

Run these tests regularly to ensure your RAG pipeline works end-to-end! 🚀
