from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
"""Path to the root of the project."""

PROMPTS_PATH = PROJECT_ROOT / "prompts"
"""Path to the directory containing the prompts."""

DEMONSTRATIONS_PATH = PROJECT_ROOT / "demonstrations"
"""Path to the directory containing the demonstrations."""

# Capability: Python 2 to Python 3

PY2_TO_PY3_PROMPT_PATH = PROMPTS_PATH / "py2_to_py3.yaml"
"""Path to the Python 2 to Python 3 prompts."""
