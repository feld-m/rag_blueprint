#!/bin/bash
#
# E2E Test Runner Script
#
# This script sets up the environment and runs end-to-end tests
# for the Bundestag DIP RAG pipeline.
#
# Usage:
#   ./tests/e2e/run_e2e_tests.sh [pytest options]
#
# Examples:
#   ./tests/e2e/run_e2e_tests.sh                    # Run all e2e tests
#   ./tests/e2e/run_e2e_tests.sh -v                 # Verbose output
#   ./tests/e2e/run_e2e_tests.sh -k test_full       # Run specific test
#   ./tests/e2e/run_e2e_tests.sh --help             # Show pytest help

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Bundestag DIP RAG Pipeline - E2E Test Runner"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

# Step 1: Check Docker is running
echo -e "${YELLOW}[1/4]${NC} Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running${NC}"
    echo "  Please start Docker Desktop and try again."
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"
echo

# Step 2: Check PGVector service
echo -e "${YELLOW}[2/4]${NC} Checking PGVector database..."
PGVECTOR_HOST="${PGVECTOR_HOST:-localhost}"
PGVECTOR_PORT="${PGVECTOR_PORT:-5433}"

# Try to connect to PGVector
if timeout 5 bash -c "cat < /dev/null > /dev/tcp/${PGVECTOR_HOST}/${PGVECTOR_PORT}" 2>/dev/null; then
    echo -e "${GREEN}✓ PGVector database is accessible at ${PGVECTOR_HOST}:${PGVECTOR_PORT}${NC}"
else
    echo -e "${RED}✗ PGVector database not accessible at ${PGVECTOR_HOST}:${PGVECTOR_PORT}${NC}"
    echo
    echo "  Attempting to start Docker services..."

    if [ -f "build/workstation/docker/docker-compose.yml" ]; then
        cd build/workstation/docker
        docker compose up -d
        cd "$PROJECT_ROOT"

        # Wait for PGVector to be ready
        echo "  Waiting for PGVector to be ready..."
        for i in {1..30}; do
            if timeout 2 bash -c "cat < /dev/null > /dev/tcp/${PGVECTOR_HOST}/${PGVECTOR_PORT}" 2>/dev/null; then
                echo -e "${GREEN}✓ PGVector database is now ready${NC}"
                break
            fi
            if [ $i -eq 30 ]; then
                echo -e "${RED}✗ Timeout waiting for PGVector${NC}"
                echo "  Please check Docker logs:"
                echo "    cd build/workstation/docker && docker compose logs -f"
                exit 1
            fi
            sleep 1
        done
    else
        echo -e "${RED}✗ Docker Compose file not found${NC}"
        echo "  Expected: build/workstation/docker/docker-compose.yml"
        exit 1
    fi
fi
echo

# Step 3: Check Python dependencies
echo -e "${YELLOW}[3/4]${NC} Checking Python dependencies..."
if ! python -c "import pytest" 2>/dev/null; then
    echo -e "${RED}✗ pytest not installed${NC}"
    echo "  Please install dependencies:"
    echo "    pip install -e .[all]"
    exit 1
fi

if ! python -c "import llama_index" 2>/dev/null; then
    echo -e "${RED}✗ llama-index not installed${NC}"
    echo "  Please install dependencies:"
    echo "    pip install -e .[all]"
    exit 1
fi
echo -e "${GREEN}✓ Python dependencies installed${NC}"
echo

# Step 4: Run tests
echo -e "${YELLOW}[4/4]${NC} Running E2E tests..."
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# Set environment variables
export ENVIRONMENT=e2e
export ON_PREM_CONFIG=true

# Run pytest with provided arguments or defaults
if [ $# -eq 0 ]; then
    pytest tests/e2e/ -v
else
    pytest tests/e2e/ "$@"
fi

TEST_EXIT_CODE=$?

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All E2E tests passed!${NC}"
else
    echo -e "${RED}✗ Some E2E tests failed${NC}"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit $TEST_EXIT_CODE
