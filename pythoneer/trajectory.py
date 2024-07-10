"""
Module containing classes to represent the agent's trajectory.

The trajectory is a sequence of thoughts, actions, and observations that the agent makes while
working on a task. The trajectory is written to a file, to allow for later analysis of the agent's
behaviour.
"""

from __future__ import annotations

import json

from dataclasses import dataclass, asdict
from pathlib import Path


class Trajectory:
    """Class to represent an agent's trajectory."""

    def __init__(self) -> None:
        self.steps: list[TrajectoryStep] = []

    def add_step(self, step: TrajectoryStep) -> None:
        """
        Add a step to the trajectory.

        Parameters
        ----------
        step : TrajectoryStep
            The step to add to the trajectory.
        """
        self.steps.append(step)

    def write_to_disk(self, output_dir: str | Path) -> None:
        """
        Write the trajectory to disk as a JSON file.

        Parameters
        ----------
        output_dir : str | Path
            The directory to write the trajectory to.
        """
        file_name = "trajectory.json"
        output_dir = Path(output_dir)
        file_path = output_dir / file_name

        with open(file_path, "w") as fh:
            trajectory = [asdict(step) for step in self.steps]
            json.dump(trajectory, fh, indent=4)


@dataclass
class TrajectoryStep:
    """
    Class to represent a step in the agent's trajectory.

    Parameters
    ----------
    step_number : int
        The step number.

    thought : str
        The thought that the agent had at this step.

    tool_name : str
        The name of the tool that the agent used at this step.

    tool_arguments : dict
        The arguments that the agent used with the tool.

    terminal_output : bool
        Whether the tool produced terminal output.

    terminal_content : str | None
        The content of the terminal output, if applicable.

    file_viewer_changed : bool
        Whether the tool changed the contents of the file viewer.

    open_file_name : str | None
        The name of the file that the agent most recently opened in the file viewer.

    file_viewer_content : str
        The most recent contents of the file viewer. This is the content after the tool was used.

    review_comment : str | None
        A comment from the reviewer about the step.
    """

    step_number: int
    thought: str
    tool_name: str
    tool_arguments: dict
    terminal_output: bool = False
    terminal_content: str | None = None
    file_viewer_changed: bool = False
    open_file_name: str | None = None
    file_viewer_content: str | None = None
    review_comment: str | None = None
