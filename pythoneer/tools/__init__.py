"""
This subpackage contains the tools and utilities for the Pythoneer coding agent.

It includes various tools for file manipulation, code execution, and task completion,
as well as a factory for creating and managing these tools.

Available tools:
- OpenFileTool: For opening files in the codebase
- EditFileTool: For editing files in the codebase
- CreateFileTool: For creating new files in the codebase
- RunPythonScriptTool: For executing Python scripts
- RunAllTestsTool: For running all tests in the codebase
- CompleteTaskTool: For marking a task as complete
"""

from .factory import ToolFactory
from .tools import (
    OpenFileTool,
    EditFileTool,
    CreateFileTool,
    RunPythonScriptTool,
    RunAllTestsTool,
    CompleteTaskTool,
)


def register_all_tools():
    ToolFactory.register_tool(OpenFileTool)
    ToolFactory.register_tool(EditFileTool)
    ToolFactory.register_tool(CreateFileTool)
    ToolFactory.register_tool(RunPythonScriptTool)
    ToolFactory.register_tool(RunAllTestsTool)
    ToolFactory.register_tool(CompleteTaskTool)


__all__ = [
    "ToolFactory",
    "OpenFileTool",
    "EditFileTool",
    "CreateFileTool",
    "RunPythonScriptTool",
    "RunAllTestsTool",
    "CompleteTaskTool",
    "register_all_tools",
]
