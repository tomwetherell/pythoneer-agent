"""Coding agent implementation."""

import yaml
from pathlib import Path

import anthropic
from loguru import logger

from pythoneer.codebase import Codebase
from pythoneer.messages import MessageLog, InstanceMessage, AssistantMessage, UserMessage
from pythoneer.llm import parse_tool_use_response
from pythoneer.tools.factory import ToolFactory
from pythoneer.tools.tools import OpenFileTool, EditFileTool, CompleteTaskTool
from pythoneer.paths import PY2_TO_PY3_PROMPT_PATH

MODEL = "claude-3-sonnet-20240229"
"""
Anthropic language model to use.

See https://docs.anthropic.com/en/docs/about-claude/models for details and options.
"""


class Agent:
    """Coding agent."""

    TOOLS = (OpenFileTool, EditFileTool, CompleteTaskTool)
    """Tools available to the agent."""

    def __init__(self, codebase_path: str | Path, workspace_path: str | Path):
        """
        Initialise the agent.

        Parameters
        ----------
        codebase_path : str | Path
            Full path to the root of the codebase to work on.

        workspace_path : str | Path
            Full path to the agent's workspace directory. This is where the agent will save
            the modified codebase, and write any other files that it needs to.
        """
        self.workspace_path = Path(workspace_path)

        self.codebase = Codebase(codebase_path)
        self.message_log = MessageLog()

        self.step_number: int = 0
        self.task_completed: bool = False

        self.open_file_relative_path: str | None = None

        # Load the prompts
        with open(PY2_TO_PY3_PROMPT_PATH) as fh:
            prompts = yaml.safe_load(fh)
        self.system_prompt = prompts["system_prompt"]
        self.instance_prompt = prompts["instance_prompt_template"].format(
            codebase_files_list=self.codebase.formatted_relative_file_paths()
        )
        self.next_step_prompt = prompts["next_step_prompt"]

        instance_message = InstanceMessage(self.instance_prompt)
        self.message_log.add_message(instance_message)

    def run(self):
        while not self.task_completed:
            self.step()

        self.finish()

    def step(self):
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

        user_message = UserMessage(
            tool_id=response.tool_id,
            observation=observation.observation_description,
            summarised_observation=observation.summarised_observation_description,
        )
        self.message_log.add_message(user_message)
        logger.info(f"🐼 User message:\n{user_message.return_json_message()}")

        self.step_number += 1

    def finish(self):
        logger.info(f"Task completed in {self.step_number} steps.")
        self.codebase.write_codebase_to_disk(self.workspace_path)
