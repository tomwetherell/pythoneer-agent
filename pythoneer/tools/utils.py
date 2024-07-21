"""Utility functions for tools."""

import json
import subprocess
import tempfile
from pathlib import Path


EXTENSION_TO_MARKDOWN_IDENTIFIER = {
    "py": "python",
    "java": "java",
    "ts": "typescript",
    "js": "javascript",
    "html": "html",
    "json": "json",
    "txt": "plaintext",
}
"""A mapping from file extensions to the corresponding Markdown code block identifier."""


def retrieve_file_identifier(file_path: str | Path) -> str:
    """
    Return the Markdown code block identifier for a given file.

    Parameters
    ----------
    file_path : Path
        The path to the file.

    Returns
    -------
    identifier : str
        The Markdown code block identifier for the file, e.g. 'python', 'java', etc.
    """
    file_path = Path(file_path)
    extension = file_path.suffix.lstrip(".")
    identifier = EXTENSION_TO_MARKDOWN_IDENTIFIER.get(extension, extension)
    return identifier


def remove_code_block_tags(code_string: str) -> str:
    """
    Remove the code block tags from a code string, if present.

    Example:

    ```python
    print("Hello, world!")
    ```
    becomes

    print("Hello, world!")

    Parameters
    ----------
    code_string : str
        The code string to process, which may or may not be enclosed in code block tags.

    Returns
    -------
    code_string : str
        The code string with no code block tags.
    """
    if code_string.startswith("```"):
        # Remove up until and including the newline after the first ```. This will also
        # remove the language identifier (e.g. python, typescript, etc.), if present.
        code_string = code_string[code_string.find("\n") + 1 :]

    if code_string.endswith("```"):
        # Remove the last ```.
        code_string = code_string[:-3]

    code_string = code_string.lstrip()

    return code_string


def lint_code(code_string: str) -> list[str] | None:
    """
    Lint a Python code block using Ruff.

    Parameters
    ----------
    code_string : str
        The code string to lint.

    Returns
    -------
    formatted_violations : list[str] | None
        A list of formatted violations, where each violation is a string in the format
        'line:column - code: message'. If there are no violations, returns None.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=True) as temp_file:
        # Write the code to the temporary file
        temp_file.write(code_string)
        temp_file.flush()
        temp_file_path = Path(temp_file.name)

        # Run Ruff on the temporary file
        result = subprocess.run(
            ["ruff", "check", str(temp_file_path), "--output-format=json"],
            capture_output=True,
            text=True,
        )

        # Parse the JSON output
        if result.stdout:
            violations = json.loads(result.stdout)
            formatted_violations = [
                f"{v['location']['row']}:{v['location']['column']} - {v['code']}: {v['message']}"
                for v in violations
            ]
        else:
            formatted_violations = None

        return formatted_violations
