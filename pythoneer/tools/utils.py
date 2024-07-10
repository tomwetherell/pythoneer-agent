"""Utility functions for tools."""

import json
import subprocess
import tempfile
from pathlib import Path


def lint_code(code_string: str) -> list[str] | None:
    """
    Lint a code block using Ruff.

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
