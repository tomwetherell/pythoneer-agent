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
from pythoneer.tools import register_all_tools, ToolFactory


class Agent:
    """Coding agent."""

    def __init__(
        self,
        config_file: str | Path,
        codebase_path: str | Path,
        workspace_path: str | Path,
    ) -> None:
        """
        Initialise the agent.

        Parameters
        ----------
        config_file : str | Path
            Path to the config file for the agent. The config file defines the task, the
            agent's parameters, the tools available to the agent, and the prompts. See the
            `/config` directory for examples.

        codebase_path : str | Path
            Full path to the root of the codebase to work on.

        workspace_path : str | Path
            Full path to the agent's workspace directory. This is where the agent will save
            the modified codebase, and write any other files that it needs to.
        """
        with open(config_file) as fh:
            self.config = yaml.safe_load(fh)

        self.model = self.config["model"]["name"]

        self.tools = self.config["agent"]["tools"]
        self.summarise_before_last = self.config["agent"]["summarise_before_last"]

        # Register the tools
        register_all_tools()

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

    def _load_prompts(self) -> None:
        """Load the prompts from the config file."""
        self.system_prompt = self.config["prompts"]["system_prompt"]
        self.instance_prompt = self.config["prompts"]["instance_prompt_template"].format(
            codebase_files_list=self.codebase.formatted_relative_file_paths()
        )
        self.next_step_prompt_template = self.config["prompts"]["next_step_prompt_template"]

        logger.info(f"📝 System prompt:\n{self.system_prompt}")
        logger.info(f"📝 Instance prompt:\n{self.instance_prompt}")

    def run(self) -> None:
        """Run the agent."""
        error_occured = False

        while not self.task_completed:
            try:
                self.step()
            except Exception as exc:
                logger.exception(f"An error occurred: {exc}")
                error_occured = True

        self.finish(error_occured)

    def step(self) -> None:
        """
        A single step of the agent.

        The agent generates a message, uses a tool, and receives an observation.
        """
        self.step_number += 1

        messages = self.message_log.return_messages_list(
            summarise_before_last=self.summarise_before_last
        )
        tool_descriptions = [
            ToolFactory.TOOL_NAME_TO_CLASS[tool_name].json_description() for tool_name in self.tools
        ]

        response = anthropic.Anthropic().messages.create(
            model=self.model,
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

        # Use the tool, and get an observation
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

        # Update the trajectory
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

    def finish(self, error_occured: bool = False) -> None:
        """Write the codebase and trajectory to disk."""
        if error_occured:
            logger.info("Task failed.")
        else:
            logger.info(f"Task completed in {self.step_number} steps.")

        self.codebase.write_codebase_to_disk(self.workspace_path)
        self.trajectory.write_to_disk(self.workspace_path)
