"""Module to represent a codebase."""

from __future__ import annotations

from pathlib import Path


class Codebase:
    """Class to represent a codebase."""

    PATTERN = "**/*.py"
    """Pattern to match source files to include in the codebase."""

    def __init__(self, codebase_path: str | Path):
        """
        Initalise the Codebase object.

        Parameters
        ----------
        codebase_path : str | Path
            Full path to the root of the codebase.
        """
        self.codebase_path = Path(codebase_path)

        # Mapping of relative file paths to SourceFile objects
        self.files = {}

        # Add all source files in the codebase to the codebase object
        for file_path in self.codebase_path.glob(self.PATTERN):
            relative_file_path = str(file_path.relative_to(self.codebase_path))
            self.add_file(relative_file_path)

    def add_file(self, relative_file_path: str):
        """Add a new source file to the codebase."""
        source_file = SourceFile(self.codebase_path, relative_file_path)
        self.files[relative_file_path] = source_file

    def retrieve_file(self, relative_file_path: str) -> SourceFile:
        """Retrieve a SourceFile object from the codebase."""
        return self.files[relative_file_path]

    def edit_file(self, relative_file_path: str, contents: str):
        """Edit the contents of a source file in the codebase."""
        self.files[relative_file_path].update_contents(contents)

    def formatted_relative_file_paths(self) -> str:
        """Return a formatted string of all relative file paths in the codebase."""
        relative_file_paths_w_bullets = [
            f"* {relative_file_path}"
            for relative_file_path in self._get_relative_file_paths()
        ]
        return "\n".join(relative_file_paths_w_bullets)

    def _get_relative_file_paths(self) -> list[str]:
        """Return a list of all relative file paths in the codebase."""
        return list(self.files.keys())


class SourceFile:
    """Class to represent a source file in a codebase."""

    def __init__(
        self,
        codebase_path: str | Path,
        relative_file_path: str,
    ):
        """
        Initalise the SourceFile object.

        Parameters
        ----------
        codebase_path : str | Path
            Full path to the root of the codebase.

        relative_file_path : str
            Path of the source file relative to the root of the codebase.
        """
        self.codebase_path = Path(codebase_path)
        self._relative_file_path = relative_file_path
        self.file_path = self.codebase_path / self.relative_file_path
        self._file_name = self.file_path.name

        self.versions = []
        self.versions.append(self.file_path.read_text())

    def update_contents(self, contents: str):
        """Add a new version of the source file."""
        self.versions.append(contents)

    @property
    def relative_file_path(self):
        """The path of the source file relative to the root of the codebase."""
        return self._relative_file_path

    @property
    def file_name(self):
        """The name of the source file."""
        return self._file_name

    @property
    def contents(self):
        """The contents of the latest version of the source file."""
        return self.versions[-1]
