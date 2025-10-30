"""
Pytest configuration for E2E tests.

Provides shared fixtures and configuration for end-to-end testing.
"""

import os
import sys
from pathlib import Path

import pytest

# Add src directory to path for all e2e tests
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def pytest_addoption(parser):
    """
    Add custom command-line options for e2e tests.

    Registers application options so pytest doesn't complain about unknown args.
    """
    # Register application arguments so pytest accepts them
    parser.addoption(
        "--on-prem-config",
        action="store_true",
        default=False,
        help="Use on-premise configuration (for application, not pytest)",
    )
    parser.addoption(
        "--env",
        type=str,
        default="test",
        help="Environment name (for application, not pytest)",
    )

    # Now inject into sys.argv if not present (for MetadataConfiguration)
    if "--on-prem-config" not in sys.argv:
        sys.argv.insert(1, "--on-prem-config")
    if "--env" not in sys.argv:
        sys.argv.insert(1, "--env")
        sys.argv.insert(2, "test")


@pytest.fixture(scope="session")
def docker_compose_project_name():
    """
    Docker Compose project name for test infrastructure.

    Returns the project name used by Docker Compose to identify
    the test environment containers.
    """
    return "rag_e2e_test"


@pytest.fixture(scope="session")
def pgvector_connection_params():
    """
    Connection parameters for PGVector test database.

    Returns:
        dict: Connection parameters (host, port, database)
    """
    return {
        "host": os.getenv("PGVECTOR_HOST", "localhost"),
        "port": int(os.getenv("PGVECTOR_PORT", "5433")),
        "database": os.getenv("PGVECTOR_DB", "rag-local"),
    }


@pytest.fixture(scope="session", autouse=True)
def verify_docker_infrastructure():
    """
    Verify Docker infrastructure is running before tests.

    This fixture runs automatically for all e2e tests to ensure
    required services (PGVector) are available.

    Raises:
        RuntimeError: If required Docker services are not running
    """
    import socket

    # Check if PGVector is accessible
    host = os.getenv("PGVECTOR_HOST", "localhost")
    port = int(os.getenv("PGVECTOR_PORT", "5433"))

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()

        if result != 0:
            raise RuntimeError(
                f"PGVector database not accessible at {host}:{port}. "
                f"Please start Docker services:\n"
                f"  $ docker compose -f build/workstation/docker/docker-compose.yml up -d"
            )
    except Exception as e:
        raise RuntimeError(
            f"Failed to verify Docker infrastructure: {e}\n"
            f"Please ensure Docker services are running."
        )


def pytest_configure(config):
    """
    Pytest configuration hook.

    Registers custom markers for e2e tests.
    """
    config.addinivalue_line(
        "markers",
        "e2e: mark test as end-to-end test (deselect with '-m \"not e2e\"')",
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow (deselect with '-m \"not slow\"')",
    )


def pytest_collection_modifyitems(config, items):
    """
    Modify test items during collection.

    Automatically marks all tests in e2e/ directory with 'e2e' and 'slow' markers.
    """
    for item in items:
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)
