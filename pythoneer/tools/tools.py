"""Tools."""

from __future__ import annotations
from typing import TYPE_CHECKING

import os  # TODO: Replace with pathlib?
import subprocess
import tempfile

from pythoneer.tools.observations import Observation
from pythoneer.tools.base import Tool, Parameter
from pythoneer.tools.factory import ToolFactory

if TYPE_CHECKING:
    from pythoneer.agent import Agent


class OpenFileTool(Tool):
    """Tool to open a file."""

    NAME = "open_file"
    DESCRIPTION = (
        "Open a file in the file editor. The path must be the full path to an existing "
        "file in the codebase that you are working on. The file will be opened in the "
        "file editor, so that you can see its contents (and possibly decide to edit it "
        "at a later step)."
    )
    PARAMETERS = [
        Parameter(
            name="file_path",
            type="string",
            description="The full path to the file to open. e.g., 'data/processing.py'",
        )
    ]

    def _validate_argument_values(self, agent: Agent):
        """Check that the file exists in the codebase."""
        file_path = self.arguments["file_path"]

        if file_path not in agent.codebase.get_relative_file_paths():
            raise ValueError(
                f"The file '{file_path}' does not exist in the codebase."
                f"The files in the codebase are: {agent.codebase.formatted_relative_file_paths()}"
            )

    def _use(self, agent: Agent) -> Observation:
        """Open the file."""
        file_path = self.arguments["file_path"]
        agent.open_file_relative_path = file_path

        file_contents = agent.codebase.retrieve_file(file_path).contents

        observation_description = (
            f"Opened the file '{file_path}'. "
            f"Contents of {file_path}: \n```python\n{file_contents}\n```"
        )

        summarised_observation_description = f"Opened the file '{file_path}'"

        observation = Observation(
            observation_description=observation_description,
            summarised_observation_description=summarised_observation_description,
            file_viewer_changed=True,
            file_viewer_new_content=file_contents,
        )

        return observation


class EditFileTool(Tool):
    """Tool to edit the contents of a file."""

    NAME = "edit_file"
    DESCRIPTION = "Edit the contents of the file open in your file editor."
    PARAMETERS = [
        Parameter(
            name="commit_message",
            type="string",
            description=(
                "The commit message is a short description of the changes you made to the file. "
                "This should be detailed enough to allow other develoeprs to understand the changes "
                "you made (without having to read the entire diff), but succinct enough to fit in a "
                "a couple of sentences."  # Modify when review comments are added - message should make it clear that the commit addresses the review comment
            ),
        ),
        Parameter(
            name="new_file_contents",
            type="string",
            description=(
                "The new contents of the file. This should be the full, updated contents of the file. "
                "This will be used to update the file in the codebase (the contents of the file "
                "open in the file editor will be replaced with this new content)."
            ),
        ),
    ]

    def _validate_argument_values(self, agent: Agent):
        """TODO: Run linter on the new contents of the file."""
        pass

    def _use(self, agent: Agent) -> Observation:
        """Edit the file open in the file editor."""
        commit_message = self.arguments["commit_message"]
        new_contents = self.arguments["new_file_contents"]
        file_path = agent.open_file_relative_path

        agent.codebase.edit_file(file_path, new_contents)

        observation_description = (
            f"Edited the file '{file_path}'.\nCommit message: {commit_message}"
            f"New contents of {file_path}: \n```python\n{new_contents}\n```"
        )

        summarised_observation_description = (
            f"Edited the file '{file_path}'.\nCommit message: {commit_message}"
        )

        observation = Observation(
            observation_description=observation_description,
            summarised_observation_description=summarised_observation_description,
            file_viewer_changed=True,
            file_viewer_new_content=new_contents,
        )

        return observation


class RunPythonScriptTool(Tool):
    """Tool to run a Python script."""

    NAME = "run_python_script"
    DESCRIPTION = "Run a Python script."
    PARAMETERS = [
        Parameter(
            name="script_path",
            type="string",
            description="The full path to the Python script to run. e.g., 'data/processing.py'",
        ),
        # TODO: Add enum
        Parameter(
            name="environment",
            type="string",
            description=(
                "The name of the environment to run the script in, either 'python2' or 'python3'."
                "The 'python2' environment should be used when running Python 2 scripts, and the "
                "'python3' environment should be used when running Python 3 scripts."
            ),
        ),
    ]

    ENVIRONMENT_TO_IMAGE = {
        "python2": "python2-base:latest",
        "python3": "python3-base:latest",
    }
    """Mapping of environment names to Docker image names."""

    def _validate_argument_values(self, agent: Agent):
        """Check that the file exists in the codebase, and that the environment is valid."""
        script_path = self.arguments["script_path"]

        if script_path not in agent.codebase.get_relative_file_paths():
            raise ValueError(
                f"The file '{script_path}' does not exist in the codebase."
                f"The files in the codebase are: {agent.codebase.formatted_relative_file_paths()}"
            )

        environment = self.arguments["environment"]
        environments = self.ENVIRONMENT_TO_IMAGE.keys()
        if environment not in environments:
            raise ValueError(
                f"The environment '{environment}' is not valid. "
                f"Valid environments are: {environments}"
            )

    def _use(self, agent: Agent) -> Observation:
        """Run the Python script."""
        script_path = self.arguments["script_path"]
        environment = self.arguments["environment"]

        docker_image = self.ENVIRONMENT_TO_IMAGE[environment]

        # Temporarily write the codebase to the agent's workspace. This will be mounted into the
        # Docker container, and the script will be run in the container. The temporary directory
        # will be deleted after the script has been run.
        agent.codebase.write_codebase_to_disk(output_path=agent.workspace_path)

        with tempfile.TemporaryDirectory() as temp_dir:
            command = [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{agent.workspace_path}:/app:ro",  # Mount the codebase into the container
                "-v",
                f"{temp_dir}:/output",  # Mount a temporary directory to store the output
                "-w",
                "/app",  # Set the working directory to the codebase
                docker_image,  # Docker image to run
                "bash",
                "-c",
                f"python {script_path} > /output/stdout.txt 2> /output/stderr.txt",
            ]

            try:
                subprocess.run(command, check=True)

                with open(os.path.join(temp_dir, "stdout.txt"), "r") as f:
                    stdout = f.read()
                with open(os.path.join(temp_dir, "stderr.txt"), "r") as f:
                    stderr = f.read()

            except subprocess.CalledProcessError as e:
                stdout = ""
                stderr = f"Error running script: {e}"

        observation_description = (
            f"Ran the Python script '{script_path}' in the '{environment}' environment.\n"
            f"stdout:\n```\n{stdout}\n```\nstderr:\n```\n{stderr}\n```"
        )

        summarised_observation_description = (
            f"Ran the Python script '{script_path}' in the '{environment}' environment."
        )

        observation = Observation(
            observation_description=observation_description,
            summarised_observation_description=summarised_observation_description,
        )

        return observation


class CompleteTaskTool(Tool):
    """Tool to declare the task as complete."""

    NAME = "complete_task"
    DESCRIPTION = "Declare the task you are working on as complete."
    PARAMETERS = []

    def _use(self, agent: Agent) -> Observation:
        """Complete the task."""
        agent.task_completed = True

        observation_description = "Task completed."
        summarised_observation_description = "Task completed."

        observation = Observation(
            observation_description=observation_description,
            summarised_observation_description=summarised_observation_description,
        )

        return observation


ToolFactory.register_tool(OpenFileTool)
ToolFactory.register_tool(EditFileTool)
ToolFactory.register_tool(CompleteTaskTool)
