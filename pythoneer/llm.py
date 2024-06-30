"""Functions to work with Anthropic's LM API."""

from dataclasses import dataclass


@dataclass
class ToolUseResponse:
    """Response from the Anthropic LM API."""

    thought: str
    tool_id: str
    tool_name: str
    tool_arguments: dict


def parse_tool_use_response(response: dict) -> ToolUseResponse:
    """
    Parse a tool use response from the Anthropic LM API.

    Parameters
    ----------
    response : dict
        The response from the Anthropic LM API.

    Returns
    -------
    str
        The response from the Anthropic LM API.
    """
    stop_reason = response["stop_reason"]
    if stop_reason != "tool_use":
        raise ValueError(f"Unexpected stop reason: {stop_reason}. Expected 'tool_use'.")

    content = response["content"]

    thought_block = content[0]
    thought = thought_block["text"]

    tool_use_block = content[1]
    tool_id = tool_use_block["id"]
    tool_name = tool_use_block["name"]
    tool_arguments = tool_use_block["input"]

    tool_use_response = ToolUseResponse(
        thought=thought,
        tool_id=tool_id,
        tool_name=tool_name,
        tool_arguments=tool_arguments,
    )

    return tool_use_response
