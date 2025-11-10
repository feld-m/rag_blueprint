"""Utility for loading domain-specific prompts in tests."""

from pathlib import Path


def load_domain_prompt(domain: str, prompt_name: str) -> str:
    """Load a domain-specific prompt from the prompts directory.

    Args:
        domain: The domain name (e.g., "bundestag")
        prompt_name: The prompt file name without extension (e.g., "system_prompt", "condense_prompt")

    Returns:
        str: The prompt template content

    Raises:
        FileNotFoundError: If the prompt file doesn't exist

    Example:
        >>> system_prompt = load_domain_prompt("bundestag", "system_prompt")
        >>> condense_prompt = load_domain_prompt("bundestag", "condense_prompt")
    """
    # Navigate from tests/ to project root
    project_root = Path(__file__).parent.parent.parent
    prompts_dir = project_root / "prompts" / domain
    prompt_file = prompts_dir / f"{prompt_name}.txt"

    if not prompt_file.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {prompt_file}\n"
            f"Available prompts in {prompts_dir}: "
            f"{', '.join(f.stem for f in prompts_dir.glob('*.txt')) if prompts_dir.exists() else 'directory does not exist'}"
        )

    return prompt_file.read_text()


def load_bundestag_prompt(prompt_name: str) -> str:
    """Load a Bundestag-specific prompt.

    Convenience wrapper around load_domain_prompt for Bundestag prompts.

    Args:
        prompt_name: The prompt file name without extension

    Returns:
        str: The prompt template content

    Example:
        >>> system_prompt = load_bundestag_prompt("system_prompt")
    """
    return load_domain_prompt("bundestag", prompt_name)
