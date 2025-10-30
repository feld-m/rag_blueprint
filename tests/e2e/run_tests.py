#!/usr/bin/env python3
"""
E2E Test Runner

This script properly sets up the environment and runs e2e tests.
It ensures that --on-prem-config and --env arguments are set before
any modules are imported.
"""

import subprocess
import sys
from pathlib import Path

# Set up sys.argv BEFORE any other imports
# Insert application args at the beginning (after script name)
if "--on-prem-config" not in sys.argv:
    sys.argv.insert(1, "--on-prem-config")
if "--env" not in sys.argv:
    sys.argv.insert(1, "--env")
    sys.argv.insert(2, "e2e")

# Now run pytest with remaining arguments
project_root = Path(__file__).parent.parent.parent
test_path = Path(__file__).parent / "test_bundestag_dip_full_pipeline.py"

# Build pytest command
pytest_args = [
    "uv",
    "run",
    "python",
    "-m",
    "pytest",
    str(test_path),
    "-v",
    "--tb=short",
]

# Add any additional args passed to this script
pytest_args.extend(
    sys.argv[4:]
)  # Skip script name, --on-prem-config, --env, e2e

print(f"Running: {' '.join(pytest_args)}")
print("With args: --on-prem-config --env e2e")
print()

# Run pytest
result = subprocess.run(pytest_args, cwd=project_root)
sys.exit(result.returncode)
