"""Coding agent implementation."""

from pathlib import Path

from pythoneer.codebase import Codebase


class Agent:
    def __init__(self, codebase_path: str | Path):
        self.codebase = Codebase(codebase_path)

        self.step_number: int = 0
        self.open_file_relative_path: str | None = None

    def step(self):
        pass
