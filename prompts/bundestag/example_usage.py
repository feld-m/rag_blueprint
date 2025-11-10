"""Example showing how to use Bundestag-specific prompts in tests.

This file demonstrates how to load domain-specific prompts
for testing or deployment-specific configurations.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / "tests"))

from utils.prompt_loader import load_bundestag_prompt


def example_test_with_bundestag_prompts():
    """Example test that uses Bundestag-specific prompts."""
    # Load Bundestag-specific prompts
    system_prompt = load_bundestag_prompt("system_prompt")
    condense_prompt = load_bundestag_prompt("condense_prompt")

    # Use prompts in your test setup
    print("System Prompt Preview:")
    print(system_prompt[:300] + "...\n")

    print("Condense Prompt Preview:")
    print(condense_prompt[:200] + "...\n")

    # In a real test, you would use these with Langfuse:
    # langfuse_prompt_service.create_prompt_if_not_exists(
    #     prompt_name="default_system_prompt",
    #     prompt_template=system_prompt,
    # )


def example_deployment_script():
    """Example script for deploying prompts to Langfuse."""
    from langfuse import Langfuse

    # Load Bundestag prompts
    system_prompt = load_bundestag_prompt("system_prompt")
    condense_prompt = load_bundestag_prompt("condense_prompt")

    # Initialize Langfuse client
    # langfuse = Langfuse()

    # Upload prompts to Langfuse
    # langfuse.create_prompt(
    #     name="default_system_prompt",
    #     prompt=system_prompt,
    #     labels=["bundestag", "production"]
    # )
    #
    # langfuse.create_prompt(
    #     name="default_condense_prompt",
    #     prompt=condense_prompt,
    #     labels=["bundestag", "production"]
    # )

    print("✓ Deployment script would upload prompts to Langfuse")


if __name__ == "__main__":
    print("=" * 60)
    print("Example: Using Bundestag Prompts in Tests")
    print("=" * 60)
    example_test_with_bundestag_prompts()

    print("\n" + "=" * 60)
    print("Example: Deploying Prompts to Langfuse")
    print("=" * 60)
    example_deployment_script()
