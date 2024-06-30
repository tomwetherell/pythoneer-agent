"""Base class for tools that agents can use."""

from __future__ import annotations
from typing import TYPE_CHECKING

from dataclasses import dataclass
from abc import ABC, abstractmethod

from loguru import logger

from pythoneer.tools.observations import Observation

if TYPE_CHECKING:
    from pythoneer.agent import Agent


@dataclass
class Parameter:
    """A parameter for a tool."""

    name: str
    type: str
    description: str
    required: bool = True


class Tool(ABC):
    """
    Base class defining a tool.

    This class should be subclassed to create new tools.
    """

    NAME: str | None = None
    DESCRIPTION: str | None = None
    PARAMETERS: list[Parameter] | None = None
    """Tool descriptors. These should be overridden in each subclass."""

    def __init__(self, **kwargs):
        """
        Initialise the tool.

        Parameters
        ----------

        **kwargs
            The arguments for the tool. The keys should match the parameter names
            in the `parameters` property of the tool.
        """
        if self.NAME is None or self.DESCRIPTION is None or self.PARAMETERS is None:
            raise NotImplementedError(
                "Tool subclass must define NAME, DESCRIPTION, and PARAMETERS class attributes."
            )

        self.arguments = kwargs

    def validate_arguments(self, agent: Agent):
        """Validate the provided arguments."""
        self._validate_all_parameters_present()
        self._validate_argument_values(agent)
        self._validate_argument_types()
        self._warn_unused_arguments()

    def use(self, agent: Agent) -> Observation:
        """
        Use the tool.

        Parameters
        ----------
        agent : Agent
            The agent using the tool.

        Returns
        -------
        observation : Observation
            An observation after using the tool.

        Raises
        ------
        ValueError
            If the arguments are invalid (e.g., missing, wrong type, etc.)
        """
        try:
            self.self.validate_arguments()
        except ValueError as exc:
            # TODO: Create ErrorObservation for this.
            observation = Observation(step=self.step, description=str(exc))
        else:
            observation = self._use(agent)

        return observation

    @abstractmethod
    def _use(self, agent) -> Observation:
        """
        Use the tool.

        Parameters
        ----------
        agent : Agent
            The agent using the tool.

        Returns
        -------
        observation : Observation
            An observation after using the tool.
        """
        pass

    @classmethod
    def json_description(cls) -> dict:
        """
        The JSON-format description for the tool.

        This is provided to the large language model. Currently, the returned
        schema is suitable only for Anthropic's LM API.
        """
        properties = {}
        for parameter in cls.PARAMETERS:
            properties[parameter.name] = {
                "type": parameter.type,
                "description": parameter.description,
            }

        required = [parameter.name for parameter in cls.PARAMETERS if parameter.required]

        description = {
            "name": cls.NAME,
            "description": cls.DESCRIPTION,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }

        return description

    def _validate_argument_values(self, agent: Agent):
        """
        Validate the values of the arguments.

        This method can be overridden by subclasses to provide custom validation.

        Parameters
        ----------
        agent : Agent
            The agent using the tool.

        Raises
        ------
        ValueError
            If the arguments are invalid. The message should contain enough information
            to help the agent correct the issue.
        """
        pass

    def _validate_all_parameters_present(self):
        """Validate that all required parameters are present."""
        for parameter in self.PARAMETERS:
            if parameter.required and parameter.name not in self.arguments:
                raise ValueError(
                    f"Tool {type(self).__name__} is missing required argument: {parameter.name}"
                )

    def _validate_argument_types(self):
        """Validate that the provided arguments have the correct types."""
        for parameter in self.PARAMETERS:
            if parameter.name in self.arguments:
                expected_type = parameter.type
                if expected_type == "string":
                    expected_type = "str"
                actual_type = type(self.arguments[parameter.name]).__name__
                if actual_type != expected_type:
                    raise ValueError(
                        f"Invalid argument type for {parameter.name}. "
                        f"Expected {expected_type}, got {actual_type}."
                    )

    def _warn_unused_arguments(self):
        """Warn if any arguments are not used."""
        for argument in self.arguments:
            if argument not in [parameter.name for parameter in self.PARAMETERS]:
                logger.warning(f"Unused argument: '{argument}' provided to '{self.NAME}' tool.")
