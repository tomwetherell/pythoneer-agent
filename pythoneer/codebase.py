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
            self.add_file(file_path)

    def add_file(self, file_path: str | Path):
        """Add a new source file to the codebase."""
        file_path = Path(file_path)
        source_file = SourceFile(self.codebase_path, file_path)
        self.files[source_file.relative_file_path] = source_file

    def retrieve_file(self, relative_file_path: str) -> SourceFile:
        """Retrieve a SourceFile object from the codebase."""
        return self.files[relative_file_path]

    def edit_file(self, relative_file_path: str, contents: str):
        """Edit the contents of a source file in the codebase."""
        self.files[relative_file_path].update_contents(contents)


class SourceFile:
    """Class to represent a source file in a codebase."""

    def __init__(
        self,
        codebase_path: str | Path,
        file_path: str | Path,
    ):
        """
        Initalise the SourceFile object.

        Parameters
        ----------
        codebase_path : str | Path
            Full path to the root of the codebase.

        file_path : str | Path
            Full path to the source file.
        """
        self.codebase_path = Path(codebase_path)
        self.file_path = Path(file_path)

        self._relative_file_path = str(self.file_path.relative_to(self.codebase_path))
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
