"""Messages from the user and the agent."""

from __future__ import annotations

from abc import ABC, abstractmethod


class MessageLog:
    """Class to represent a log of messages."""

    def __init__(self):
        self.messages: list[Message] = []

    def add_message(self, message: Message):
        """Add a message to the log."""
        self.messages.append(message)

    def return_messages_list(self, summarise_before_last: int | None = None):
        """
        Return a list of json-formatted messages.

        This is the input for the 'messages' parameter of Anthropic's language model
        messages API. The messages alternate between user and assistant messages.

        Parameters
        ----------
        summarise_before_last : int | None
            Summarise the tool arguments (for assistant messages) and observations (for
            user messages) for all messages except the last `summarise_before_last`.
            If None, summarise no messages.

        Returns
        -------
        messages_list : list[dict]
            A list of json-formatted messages.
        """
        num_messages = len(self.messages)
        if summarise_before_last is None:
            summarise_until = 0
        else:
            summarise_until = num_messages - summarise_before_last

        messages_list = []

        for num, message in enumerate(self.messages):
            if num >= summarise_until:
                summarised = False
            else:
                summarised = True

            if isinstance(message, InstanceMessage):
                json_message = message.return_json_message()
            elif isinstance(message, AssistantMessage):
                json_message = message.return_json_message(summarised=summarised)
            elif isinstance(message, UserMessage):
                json_message = message.return_json_message(
                    summarised=summarised, include_review_comment=True
                )
            else:
                raise ValueError("Message type not recognised.")

            messages_list.append(json_message)

        return messages_list


class Message(ABC):
    """Abstract base class for messages."""

    @abstractmethod
    def return_json_message(self) -> dict:
        """Return the message as a JSON serialisable dictionary."""
        pass


class InstanceMessage(Message):
    """Class to represent the initial message that describes the task."""

    ROLE = "user"

    def __init__(self, instance_prompt: str):
        """
        Initalise the InstanceMessage object.

        Parameters
        ----------
        instance_prompt : str
            The prompt that describes the task.
        """
        self.instance_prompt = instance_prompt

    def return_json_message(self) -> dict:
        """
        Return the message as a JSON serialisable dictionary.

        This is the format that the message will be passed to the language model in.

        Returns
        -------
        message : dict
            The message as a JSON serialisable dictionary.
        """
        content = [
            {
                "type": "text",
                "text": self.instance_prompt,
            }
        ]

        message = {
            "role": self.ROLE,
            "content": content,
        }

        return message


# Rename to tool use assistant message?
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
        """
        Create a summarised version of the tool arguments.

        For example, when editing a file, the full contents of the file are not shown.

        Parameters
        ----------
        tool_name : str
            The name of the tool.

        tool_arguments : dict
            The full tool arguments.

        Returns
        -------
        summarised_tool_arguments : dict
            A summarised version of the tool arguments.
        """
        if tool_name == "edit_file":
            summarised_tool_arguments = {
                "commit_message": tool_arguments["commit_message"],
                "new_file_contents": (
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
                "input": tool_arguments,
            },
        ]

        message = {
            "role": self.ROLE,
            "content": content,
        }

        return message


# Rename to tool result user message?
class UserMessage(Message):
    """Class to represent a tool result message from the user."""

    ROLE = "user"

    def __init__(
        self,
        tool_id: str,
        observation: str,
        summarised_observation: str,
        next_step_prompt: str,
        review_comment: str | None = None,
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

        next_step_prompt: str
            The prompt for the next step.

        review_comment: str | None
            A comment from the reviewer about the result.
        """
        self.tool_id = tool_id
        self.observation = observation
        self.summarised_observation = summarised_observation
        self.next_step_prompt = next_step_prompt
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

        content.append(
            {
                "type": "text",
                "text": self.next_step_prompt,
            }
        )

        message = {
            "role": self.ROLE,
            "content": content,
        }

        return message
