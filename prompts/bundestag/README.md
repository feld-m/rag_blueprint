# Bundestag-Specific Prompts

This directory contains domain-specific prompts tailored for the German Bundestag use case.

## Files

- `condense_prompt.txt` - Temporal-aware condense prompt that preserves time-related keywords
- `system_prompt.txt` - System prompt with Bundestag-specific context and instructions

## Usage

### In Langfuse (Production)

These prompts should be loaded into Langfuse for the production deployment:

1. Navigate to Langfuse UI → Prompts
2. Create/update prompts with names:
   - `default_condense_prompt` - use contents from `condense_prompt.txt`
   - `default_system_prompt` - use contents from `system_prompt.txt`

### In Tests

To use these prompts in tests, you can load them programmatically:

```python
from pathlib import Path

def load_bundestag_prompt(prompt_name: str) -> str:
    """Load a Bundestag-specific prompt from the prompts directory."""
    prompts_dir = Path(__file__).parent.parent / "prompts" / "bundestag"
    prompt_file = prompts_dir / f"{prompt_name}.txt"
    return prompt_file.read_text()

# Example usage
system_prompt = load_bundestag_prompt("system_prompt")
condense_prompt = load_bundestag_prompt("condense_prompt")
```

## Rationale

These prompts are kept separate from the main codebase because:

1. **Generic Framework**: The main codebase should remain generic and applicable to any RAG use case
2. **Version Control**: Domain-specific prompts can still be version-controlled for tracking changes
3. **Testing**: Tests can load these prompts when needed for Bundestag-specific scenarios
4. **Deployment Flexibility**: Different deployments can use different prompts via Langfuse without code changes

## Updating Prompts

When updating these prompts:
1. Edit the `.txt` files in this directory
2. Commit the changes to version control
3. Update the corresponding prompts in Langfuse for the deployment
4. Consider whether tests need to be updated to reflect prompt changes
