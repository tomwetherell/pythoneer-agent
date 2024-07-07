"""Coding agent implementation."""

import shutil
import yaml
from pathlib import Path

import anthropic
from loguru import logger

from pythoneer.codebase import Codebase
from pythoneer.messages import MessageLog, InstanceMessage, AssistantMessage, UserMessage
from pythoneer.trajectory import Trajectory, TrajectoryStep
from pythoneer.llm import parse_tool_use_response
from pythoneer.tools.factory import ToolFactory
from pythoneer.tools.tools import OpenFileTool, EditFileTool, CompleteTaskTool
from pythoneer.paths import PY2_TO_PY3_PROMPT_PATH, PYTORCH_TO_TENSORFLOW_PROMPT_PATH


MODEL = "claude-3-sonnet-20240229"
"""
Anthropic language model to use.

See https://docs.anthropic.com/en/docs/about-claude/models for details and options.
"""


class Agent:
    """Coding agent."""

    TASKS = ("py2_to_py3", "pytorch_to_tensorflow", "tensorflow_to_pytorch")
    """Tasks that the agent can complete."""

    TOOLS = (OpenFileTool, EditFileTool, CompleteTaskTool)
    """Tools available to the agent."""

    def __init__(
        self,
        codebase_path: str | Path,
        workspace_path: str | Path,
        task: str,
    ):
        """
        Initialise the agent.

        Parameters
        ----------
        codebase_path : str | Path
            Full path to the root of the codebase to work on.

        workspace_path : str | Path
            Full path to the agent's workspace directory. This is where the agent will save
            the modified codebase, and write any other files that it needs to.

        task : str
            The task that the agent should complete. Must be one of `Agent.TASKS`.

        Raises
        ------
        ValueError
            If `task` is not one of `Agent.TASKS`.
        """
        if task not in self.TASKS:
            raise ValueError(f"Task must be one of {self.TASKS}, not {task}.")
        self.task = task

        # Set up the agent's workspace directory
        self.workspace_path = Path(workspace_path)
        if self.workspace_path.exists() and self.workspace_path.is_dir():
            shutil.rmtree(workspace_path)
        self.workspace_path.mkdir(parents=True, exist_ok=True)

        self.codebase = Codebase(codebase_path)
        self.message_log = MessageLog()
        self.trajectory = Trajectory()

        self.step_number: int = 0
        self.task_completed: bool = False

        self.open_file_relative_path: str | None = None

        # Load the prompts
        self._load_prompts()

        instance_message = InstanceMessage(self.instance_prompt)
        self.message_log.add_message(instance_message)

    def _load_prompts(self):
        """Load the prompts from the prompts file corresponding to the task."""
        if self.task == "py2_to_py3":
            prompts_path = PY2_TO_PY3_PROMPT_PATH
        elif self.task == "pytorch_to_tensorflow":
            prompts_path = PYTORCH_TO_TENSORFLOW_PROMPT_PATH

        with open(prompts_path) as fh:
            prompts = yaml.safe_load(fh)

        self.system_prompt = prompts["system_prompt"]
        self.instance_prompt = prompts["instance_prompt_template"].format(
            codebase_files_list=self.codebase.formatted_relative_file_paths()
        )
        self.next_step_prompt_template = prompts["next_step_prompt_template"]

    def run(self):
        error = False
        try:
            while not self.task_completed:
                self.step()
        except Exception as exc:
            logger.exception(f"An error occurred: {exc}")
            error = True
        finally:
            self.finish(error)

    def step(self):
        self.step_number += 1

        messages = self.message_log.return_messages_list()
        tool_descriptions = [tool.json_description() for tool in self.TOOLS]

        response = anthropic.Anthropic().messages.create(
            model=MODEL,
            messages=messages,
            max_tokens=2056,
            system=self.system_prompt,
            tools=tool_descriptions,
        )
        response = parse_tool_use_response(response)

        assistant_message = AssistantMessage(
            thought=response.thought,
            tool_id=response.tool_id,
            tool_name=response.tool_name,
            tool_arguments=response.tool_arguments,
        )
        self.message_log.add_message(assistant_message)
        logger.info(f"🤖 Assistant message:\n{assistant_message.return_json_message()}")

        tool_instance = ToolFactory.create_tool(response.tool_name, **response.tool_arguments)

        # Use the tool, and get the observation
        observation = tool_instance.use(self)

        next_step_prompt = self.next_step_prompt_template.format(
            open_file=self.open_file_relative_path
        )

        if observation.review_comment:
            logger.info(f"🔍 Review comment:\n{observation.review_comment}")

        user_message = UserMessage(
            tool_id=response.tool_id,
            observation=observation.observation_description,
            summarised_observation=observation.summarised_observation_description,
            next_step_prompt=next_step_prompt,
            review_comment=observation.review_comment,
        )
        self.message_log.add_message(user_message)
        logger.info(f"🐼 User message:\n{user_message.return_json_message()}")

        if self.open_file_relative_path:
            file_viewer_content = self.codebase.retrieve_file(self.open_file_relative_path).contents
        else:
            file_viewer_content = None

        trajectory_step = TrajectoryStep(
            step_number=self.step_number,
            thought=response.thought,
            tool_name=response.tool_name,
            tool_arguments=response.tool_arguments,
            terminal_output=observation.terminal_output,
            terminal_content=observation.terminal_content,
            file_viewer_changed=observation.file_viewer_changed,
            open_file_name=self.open_file_relative_path,
            file_viewer_content=file_viewer_content,
            review_comment=observation.review_comment,
        )
        self.trajectory.add_step(trajectory_step)

    def finish(self, error: bool = False):
        if error:
            logger.info("Task failed.")
        else:
            logger.info(f"Task completed in {self.step_number} steps.")

        self.codebase.write_codebase_to_disk(self.workspace_path)
        self.trajectory.write_to_disk(self.workspace_path)
