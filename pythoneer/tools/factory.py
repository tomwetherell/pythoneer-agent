"""Tool factory for creating tools."""

from pythoneer.tools.base import Tool


class ToolFactory:
    """A factory for creating tools."""

    TOOL_NAME_TO_CLASS = {}
    """
    Mapping of tool names to tool classes. This is populated by the `register_tool`
    method.
    """

    @staticmethod
    def register_tool(tool_class: Tool):
        ToolFactory.TOOL_NAME_TO_CLASS[tool_class.NAME] = tool_class

    @staticmethod
    def create_tool(
        tool_name: str,
        **kwargs,
    ) -> Tool:
        """
        Create a tool by name.

        Parameters
        ----------
        tool_name : str
            The name of the tool to create.

        **kwargs
            The arguments for the tool.

        Returns
        -------
        tool : Tool
            The created tool.
        """
        try:
            tool_class = ToolFactory.TOOL_NAME_TO_CLASS[tool_name]
        except KeyError:
            raise ValueError(f"Unknown tool: {tool_name}")

        tool_instance = tool_class(**kwargs)
        return tool_instance
