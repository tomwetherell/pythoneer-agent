"""Messages from the user and the agent."""

from __future__ import annotations

from abc import ABC, abstractmethod


class MessageLog:
    """Class to represent a log of messages."""

    def create_messages(summarise_after: int | None = None):
        pass


class Message(ABC):
    """Abstract class to represent a message."""

    @abstractmethod
    def return_json_message(self) -> dict:
        pass


class AssistantMessage(Message):
    """Class to represent a message from the assistant."""

    ROLE = "assistant"

    def __init__(
        self,
        thought: str,
        tool_id: str,
        tool_name: str,
        tool_arguments: dict,
    ):
        """
        Initalise the AssistantMessage object.

        Parameters
        ----------
        thought : str
            The language model's reasoning.

        tool_id : str

        tool_name : str

        tool_arguments : dict
        """
        self.thought = thought
        self.tool_id = tool_id
        self.tool_name = tool_name
        self.tool_arguments = tool_arguments
        self.summarised_tool_arguments = self.create_summarised_tool_arguments(
            tool_name, tool_arguments
        )

    def create_summarised_tool_arguments(self, tool_name, tool_arguments) -> dict:
        if tool_name == "edit":
            summarised_tool_arguments = {
                "commit_message": tool_arguments["commit_message"],
                "new_contents": (
                    "The full, updated contents of the file. Not shown here for brevity."
                ),
            }
        else:
            summarised_tool_arguments = tool_arguments

        return summarised_tool_arguments

    def return_json_message(self, summarised: bool = False) -> dict:
        """
        Return the message as a JSON serialisable dictionary.

        This is the format that the message will be passed to the language model in.

        Parameters
        ----------
        summarised : bool
            Whether to include the full tool arguments or a summarised version.

        Returns
        -------
        message : dict
            The message as a JSON serialisable dictionary.
        """
        if summarised:
            tool_arguments = self.summarised_tool_arguments
        else:
            tool_arguments = self.tool_arguments

        content = [
            {
                "type": "text",
                "text": self.thought,
            },
            {
                "type": "tool_use",
                "id": self.tool_id,
                "name": self.tool_name,
                "inputs": tool_arguments,
            },
        ]

        message = {
            "role": self.ROLE,
            "content": content,
        }

        return message


class UserMessage(Message):
    """Class to represent a tool result message from the user."""

    ROLE = "user"

    def __init__(
        self,
        tool_id: str,
        observation: str,
        summarised_observation: str,
        review_comment: str | None,
    ):
        """
        Initalise the UserMessage object.

        Parameters
        ----------
        tool_id : str
            The id of the tool use request that this is a result for.

        observation: str
            The result of using the tool.

        summarised_observation: str
            A summarised version of the observation.

        review_comment: str | None
            A comment from the reviewer about the result.
        """
        self.tool_id = tool_id
        self.observation = observation
        self.summarised_observation = summarised_observation
        self.review_comment = review_comment

    def return_json_message(
        self,
        summarised: bool = False,
        include_review_comment: bool = True,
    ) -> dict:
        """
        Return the message as a JSON serialisable dictionary.

        This is the format that the message will be passed to the language model in.
        Currently assumes that the Anthropic LM API is being used.

        Parameters
        ----------
        summarised : bool
            Whether to include the full observation or the summarised version.

        include_review_comment : bool
            Whether to include the review comment, if it exists.

        Returns
        -------
        message : dict
            The message as a JSON serialisable dictionary.
        """
        if summarised:
            tool_result_content = self.summarised_observation
        else:
            tool_result_content = self.observation

        content = [
            {
                "type": "tool_result",
                "tool_use_id": self.tool_id,
                "content": tool_result_content,
            }
        ]

        if self.review_comment and include_review_comment:
            content.append(
                {
                    "type": "text",
                    "text": self.review_comment,
                }
            )

        # TODO: Add a content block to encourage the agent to take the next step.

        message = {
            "role": self.ROLE,
            "content": content,
        }

        return message
