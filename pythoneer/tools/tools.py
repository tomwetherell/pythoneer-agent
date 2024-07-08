"""Tools that the agent can use to complete tasks."""

from __future__ import annotations
from typing import TYPE_CHECKING

import os
import subprocess
import tempfile
from pathlib import Path

from pythoneer.tools.observations import Observation
from pythoneer.tools.base import Tool, Parameter
from pythoneer.tools.utils import lint_code


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
                f"The file '{file_path}' does not exist in the codebase. "
                f"The files in the codebase are:\n{agent.codebase.formatted_relative_file_paths()}"
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
    DESCRIPTION = (
        "Edit the contents of the file open in your file editor. Important: this tool should be "
        "used after you have opened the file you want to edit using the 'open_file' tool."
    )
    PARAMETERS = [
        Parameter(
            name="commit_message",
            type="string",
            description=(
                "The commit message is a short description of the changes you made to the file. "
                "This should be detailed enough to allow other develoeprs to understand the changes "
                "you made (without having to read the entire diff), but succinct enough to fit in a "
                "a couple of sentences."  # TODO: Modify when review comments are added - message should make it clear that the commit addresses the review comment
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
        pass

    def _use(self, agent: Agent) -> Observation:
        """Edit the file open in the file editor."""
        commit_message = self.arguments["commit_message"]
        new_contents = self.arguments["new_file_contents"]
        file_path = agent.open_file_relative_path

        if new_contents.startswith("```python"):
            new_contents = new_contents[9:]
        if new_contents.endswith("```"):
            new_contents = new_contents[:-3]
        new_contents = new_contents.lstrip()

        agent.codebase.edit_file(file_path, new_contents)

        if file_path.endswith(".py"):
            lint_results = lint_code(new_contents)
            python_file = True
        else:
            lint_results = None

        # If there were linting issues, provide a review comment
        if lint_results:
            lint_results_bulleted = "\n* ".join(lint_results)
            review_comment = (
                f"The code you provided has the following issues:\n* {lint_results_bulleted}\n\n"
                f"Please address these issues before continuing."
            )
        else:
            review_comment = None

        observation_description = (
            f"Edited the file '{file_path}'.\nCommit message: '{commit_message}'.\n"
            f"New contents of {file_path}:\n```{'python' if python_file else ''}\n{new_contents}\n```"
        )

        summarised_observation_description = (
            f"Edited the file '{file_path}'.\nCommit message: {commit_message}"
        )

        observation = Observation(
            observation_description=observation_description,
            summarised_observation_description=summarised_observation_description,
            file_viewer_changed=True,
            file_viewer_new_content=new_contents,
            review_comment=review_comment,
        )

        return observation


class CreateFileTool(Tool):
    """Tool to create a new file."""

    NAME = "create_file"
    DESCRIPTION = (
        "Create a new file in the codebase. The path must be the full path to the new file you want to create. "
        "You must provide also the full contents of the new file."
    )
    PARAMETERS = [
        Parameter(
            name="file_path",
            type="string",
            description=(
                "The full path to the new file to create, e.g., 'data/new_file.py'. "
                "If the directory does not exist, it will be created."
            ),
        ),
        Parameter(
            name="file_contents",
            type="string",
            description="The full contents of the new file.",
        ),
    ]

    def _validate_argument_values(self, agent: Agent):
        """Check that the file does not already exist in the codebase."""
        file_path = self.arguments["file_path"]

        if file_path in agent.codebase.get_relative_file_paths():
            raise ValueError(
                f"The file '{file_path}' already exists in the codebase. "
                f"The files in the codebase are:\n{agent.codebase.formatted_relative_file_paths()}"
            )

    def _use(self, agent: Agent) -> Observation:
        """Write the new file to the codebase."""
        file_path = self.arguments["file_path"]
        file_contents = self.arguments["file_contents"]

        agent.codebase.add_file(file_path, file_contents)

        # Open the new file in the file editor
        agent.open_file_relative_path = file_path

        if file_path.endswith(".py"):
            python_file = True
            lint_results = lint_code(file_contents)
        else:
            lint_results = None

        # If there were linting issues, provide a review comment
        if lint_results:
            lint_results_bulleted = "\n* ".join(lint_results)
            review_comment = (
                f"The code you provided for the new file has the following issues:\n* {lint_results_bulleted}\n\n"
                f"Please address these issues before continuing."
            )
        else:
            review_comment = None

        observation_description = (
            f"Created a new file '{file_path}', and opened it in the file editor.\n"
            f"The codebase now contains the following files:\n{agent.codebase.formatted_relative_file_paths()}\n\n"
            f"Contents of {file_path}:\n```{'python' if python_file else ''}\n{file_contents}\n```"
        )

        summarised_observation_description = f"Created a new file '{file_path}'"

        observation = Observation(
            observation_description=observation_description,
            summarised_observation_description=summarised_observation_description,
            file_viewer_changed=True,
            file_viewer_new_content=file_contents,
            review_comment=review_comment,
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
        Parameter(
            name="script_arguments",
            type="string",
            description=(
                "The arguments to pass to the Python script when running it, if any. "
                "These should be formatted as a string, e.g., '--arg1 value1 --arg2 value2'. "
                "The arguments should be formatted as they would be passed on the command line."
                "This field is not required if the script does not take any arguments, or if "
                "no arguments are to be passed."
            ),
            required=False,
        ),
        Parameter(
            name="environment",
            type="string",
            description=(
                "The name of the environment to run the script in, either 'python2' or 'python3'."
                "The 'python2' environment should be used when running Python 2 scripts, and the "
                "'python3' environment should be used when running Python 3 scripts."
            ),
            enum=["python2", "python3"],
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
        # TODO: Add docstring explaining use of Docker.
        # TODO: Fix this function, similar to the RunAllTestsTool function.
        script_path = self.arguments["script_path"]
        script_arguments = self.arguments.get("script_arguments", "")
        environment = self.arguments["environment"]

        docker_image = self.ENVIRONMENT_TO_IMAGE[environment]

        with tempfile.TemporaryDirectory() as temp_dir:
            # Write the codebase to the temporary directory
            agent.codebase.write_codebase_to_disk(output_path=temp_dir)

            command = [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{temp_dir}:/workspace",  # Mount the temporary directory to /workspace in the container
                "-w",
                "/workspace/codebase",  # Set the working directory to the codebase
                docker_image,
                "bash",
                "-c",
                f"pip install . && python -B {script_path} {script_arguments} > /workspace/stdout.txt 2> /workspace/stderr.txt",
            ]

            try:
                subprocess.run(command, check=True)
            except subprocess.CalledProcessError:
                # stdout = ""
                # stderr = f"Error running script: {exc}"
                pass

            stdout_path = Path(temp_dir) / "stdout.txt"
            stderr_path = Path(temp_dir) / "stderr.txt"

            with stdout_path.open("r") as fh:
                stdout = fh.read()
            with stderr_path.open("r") as fh:
                stderr = fh.read()

        observation_description, summarised_observation_description = (
            self._create_observation_description(script_path, environment, stdout, stderr)
        )

        terminal_output = True
        if stdout or stderr:
            terminal_contents = f"{stdout}\n{stderr}"
        else:
            terminal_contents = "The script ran successfully with no output."

        observation = Observation(
            observation_description=observation_description,
            summarised_observation_description=summarised_observation_description,
            terminal_output=terminal_output,
            terminal_content=terminal_contents,
        )

        return observation

    def _create_observation_description(
        self, script_path: str, environment: str, stdout: str, stderr: str
    ) -> tuple[str, str]:
        """Create the observation description and summarised observation description."""
        # TODO: Maybe the stdout shouldn't be summarised, as that will stop the agent from
        # comparing the functionality before changes have been made to the functionality after
        # changes have been made.
        # TODO: Construct this in a more readable way (lots of repetition here).
        if stdout and stderr:
            observation_description = (
                f"Ran the Python script '{script_path}' in the '{environment}' environment.\n"
                f"stdout:\n```\n{stdout}\n```\nstderr:\n```\n{stderr}\n```"
            )
            summarised_observation_description = (
                f"Ran the Python script '{script_path}' in the '{environment}' environment."
            )

        elif stdout:
            observation_description = (
                f"Ran the Python script '{script_path}' in the '{environment}' environment.\n"
                f"stdout:\n```\n{stdout}\n```"
            )
            summarised_observation_description = (
                f"Ran the Python script '{script_path}' in the '{environment}' environment."
                f"The script ran successfully with no errors."
            )

        elif stderr:
            observation_description = (
                f"Ran the Python script '{script_path}' in the '{environment}' environment.\n"
                f"stderr:\n```\n{stderr}\n```"
            )
            summarised_observation_description = (
                f"Ran the Python script '{script_path}' in the '{environment}' environment."
                f"The script ran with errors."
            )

        else:
            observation_description = (
                f"Ran the Python script '{script_path}' in the '{environment}' environment."
                f"The script ran successfully with no output."
            )
            summarised_observation_description = (
                f"Ran the Python script '{script_path}' in the '{environment}' environment."
                f"The script ran successfully with no output."
            )

        return observation_description, summarised_observation_description


class RunAllTestsTool(Tool):
    """Tool to run all tests in the codebase."""

    NAME = "run_all_tests"
    DESCRIPTION = "Run all tests in the codebase."
    PARAMETERS = [
        Parameter(
            name="environment",
            type="string",
            description=(
                "The name of the environment to run the tests in, either 'python2' or 'python3'."
                "The 'python2' environment should be used when working with a codebase "
                "that uses Python 2, and the 'python3' environment should be used when working "
                "with a codebase that uses Python 3."
            ),
            enum=["python2", "python3"],
        ),
    ]

    ENVIRONMENT_TO_IMAGE = {
        "python2": "python2-base:latest",
        "python3": "python3-base:latest",
    }

    def _validate_argument_values(self, agent: Agent):
        """Check that the environment is valid."""
        environment = self.arguments["environment"]
        environments = self.ENVIRONMENT_TO_IMAGE.keys()
        if environment not in environments:
            raise ValueError(
                f"The environment '{environment}' is not valid. "
                f"Valid environments are: {environments}"
            )

    def _use(self, agent: Agent) -> Observation:
        """Run all tests in the codebase."""
        environment = self.arguments["environment"]
        docker_image = self.ENVIRONMENT_TO_IMAGE[environment]

        user_id = os.getuid()
        group_id = os.getgid()

        with tempfile.TemporaryDirectory() as temp_dir:
            agent.codebase.write_codebase_to_disk(output_path=temp_dir)

            # Create a directory for pip cache and local
            os.makedirs(os.path.join(temp_dir, "pip_cache"), exist_ok=True)
            os.makedirs(os.path.join(temp_dir, "local"), exist_ok=True)

            command = [
                "docker",
                "run",
                "--rm",
                "--user",
                f"{user_id}:{group_id}",
                "-v",
                f"{temp_dir}:/workspace",
                "-w",
                "/workspace/codebase",
                "-e",
                "HOME=/workspace",
                "-e",
                "PIP_CACHE_DIR=/workspace/pip_cache",
                "-e",
                "PYTHONUSERBASE=/workspace/local",
                docker_image,
                "bash",
                "-c",
                "pip install --no-python-version-warning --disable-pip-version-check --user -q . && pytest > /workspace/stdout.txt 2> /workspace/stderr.txt",
            ]

            try:
                subprocess.run(command, check=True)
            except subprocess.CalledProcessError:
                tests_passed = False
            else:
                tests_passed = True

            stdout_path = Path(temp_dir) / "stdout.txt"
            stderr_path = Path(temp_dir) / "stderr.txt"

            with stdout_path.open("r") as fh:
                stdout = fh.read()
            with stderr_path.open("r") as fh:
                stderr = fh.read()

        observation_description, summarised_observation_description = (
            self._create_observation_description(environment, stdout, stderr, tests_passed)
        )

        terminal_output = True
        if stdout or stderr:
            terminal_contents = f"{stdout}\n{stderr}"
        else:
            terminal_contents = "All tests ran successfully with no output."

        observation = Observation(
            observation_description=observation_description,
            summarised_observation_description=summarised_observation_description,
            terminal_output=terminal_output,
            terminal_content=terminal_contents,
        )

        return observation

    def _create_observation_description(
        self, environment: str, stdout: str, stderr: str, tests_passed: bool
    ) -> tuple[str, str]:
        """Create the observation description and summarised observation description."""
        if tests_passed:
            observation_description = (
                f"Ran all tests in the codebase in the '{environment}' environment.\n"
                f"All tests ran successfully with no errors."
            )
            summarised_observation_description = (
                f"Ran all tests in the codebase in the '{environment}' environment.\n"
                f"All tests ran successfully with no errors."
            )

        else:
            observation_description = (
                f"Ran all tests in the codebase in the '{environment}' environment.\n"
                f"There were errors when running the tests."
            )
            summarised_observation_description = (
                f"Ran all tests in the codebase in the '{environment}' environment.\n"
                f"There were errors when running the tests."
            )

            if stdout:
                observation_description += f"\STDOUT:\n```\n{stdout}\n```"
            if stderr:
                observation_description += f"\nSTDERR:\n```\n{stderr}\n```"

        return observation_description, summarised_observation_description


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
