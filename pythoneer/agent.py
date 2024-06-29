"""Coding agent implementation."""

import yaml
from pathlib import Path

from pythoneer.codebase import Codebase
from pythoneer.messages import MessageLog, InstanceMessage
from pythoneer.config import PY2_TO_PY3_PROMPT_PATH


class Agent:
    """Coding agent."""

    def __init__(self, codebase_path: str | Path):
        self.codebase = Codebase(codebase_path)
        self.message_log = MessageLog()

        self.step_number: int = 0
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

    def step(self):
        pass
