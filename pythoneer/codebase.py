"""Module to represent a codebase."""

from __future__ import annotations

import shutil
from pathlib import Path


class Codebase:
    """Class to represent a codebase."""

    PATTERNS = ["**/*.py", "**/*.toml"]
    """Patterns to match source files to include in the codebase."""

    def __init__(self, codebase_path: str | Path) -> None:
        """
        Initialise the Codebase object.

        Parameters
        ----------
        codebase_path : str | Path
            Full path to the root of the codebase.
        """
        self.codebase_path = Path(codebase_path)

        # Mapping of relative file paths to SourceFile objects
        self.files = {}

        # Add all source files in the codebase to the codebase object
        for pattern in self.PATTERNS:
            for file_path in self.codebase_path.glob(pattern):
                relative_file_path = file_path.relative_to(self.codebase_path)
                # Skip hidden files
                if not any(part.startswith(".") for part in relative_file_path.parts):
                    file_contents = file_path.read_text()
                    self.add_file(str(relative_file_path), file_contents)

    def add_file(self, relative_file_path: str, file_contents: str) -> None:
        """Add a new source file to the codebase."""
        source_file = SourceFile(relative_file_path, file_contents)
        self.files[relative_file_path] = source_file

    def retrieve_file(self, relative_file_path: str) -> SourceFile:
        """Retrieve a SourceFile object from the codebase."""
        return self.files[relative_file_path]

    def edit_file(self, relative_file_path: str, contents: str) -> None:
        """Edit the contents of a source file in the codebase."""
        self.files[relative_file_path].update_contents(contents)

    def formatted_relative_file_paths(self) -> str:
        """Return a formatted string of all relative file paths in the codebase."""
        relative_file_paths_w_bullets = [
            f"* {relative_file_path}" for relative_file_path in self.get_relative_file_paths()
        ]
        return "\n".join(relative_file_paths_w_bullets)

    def get_relative_file_paths(self) -> list[str]:
        """Return a list of all relative file paths in the codebase."""
        return list(self.files.keys())

    def write_codebase_to_disk(self, output_path: str | Path) -> None:
        """
        Write the codebase to disk.

        Writes the codebase to a new directory at the specified output path. The directory
        structure of the codebase is preserved.

        Parameters
        ----------
        output_path : str | Path
            Full path to the directory to write the codebase to. A subdirectory called
            'codebase' will be created within this directory to contain the codebase.
        """
        output_path = Path(output_path)

        # Check if the output path exists
        if not output_path.exists():
            raise ValueError(f"Output path '{output_path}' does not exist.")

        codebase_path = output_path / "codebase"

        # Remove the codebase directory if it exists
        if codebase_path.exists():
            shutil.rmtree(codebase_path)

        # Recreate the codebase directory
        codebase_path.mkdir(parents=True, exist_ok=True)

        for source_file in self.files.values():
            file_path = codebase_path / source_file.relative_file_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(source_file.contents)


class SourceFile:
    """Class to represent a source file in a codebase."""

    def __init__(
        self,
        relative_file_path: str,
        contents: str,
    ) -> None:
        """
        Initalise the SourceFile object.

        Parameters
        ----------
        relative_file_path : str
            Path of the source file relative to the root of the codebase.

        contents : str
            The contents of the source file.
        """
        self._relative_file_path = relative_file_path
        self._file_name = Path(self._relative_file_path).name

        self.versions = []
        self.versions.append(contents)

    def update_contents(self, contents: str) -> None:
        """Add a new version of the source file."""
        self.versions.append(contents)

    @property
    def relative_file_path(self) -> str:
        """The path of the source file relative to the root of the codebase."""
        return self._relative_file_path

    @property
    def file_name(self) -> str:
        """The name of the source file."""
        return self._file_name

    @property
    def contents(self) -> str:
        """The contents of the latest version of the source file."""
        return self.versions[-1]
