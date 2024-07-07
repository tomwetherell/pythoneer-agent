"""Module containing classes to represent observations from tool use."""


# TODO: Should this be a base class instead? Could have an observation type for each type of
# tool. Then, the logic for summarising the observation could be in the observation subclass.
# TODO: This could be a dataclass.
class Observation:
    """Class to represent an observation from tool use."""

    def __init__(
        self,
        observation_description: str,
        summarised_observation_description: str,
        terminal_output: bool = False,
        terminal_content: str | None = None,
        file_viewer_changed: bool = False,
        file_viewer_new_content: str | None = None,
        review_comment: str | None = None,
    ):
        """
        Initalise the Observation object.

        Parameters
        ----------
        observation_description : str
            A description of the observation.

        summarised_observation_description : str
            A summarised version of the observation description.

        terminal_output : bool
            Whether the observation relates to a terminal output.

        terminal_content : str
            The content of the terminal output, if applicable.

        file_viewer_changed : bool
            Whether the observation relates to a change in the contents of the file viewer.

        file_viewer_new_content : str
            The new contents of the file viewer, if applicable.

        review_comment : str | None
            A comment from the reviewer about the observation.
        """
        self.observation_description = observation_description
        self.summarised_observation_description = summarised_observation_description

        self.terminal_output = terminal_output
        self.terminal_content = terminal_content

        self.file_viewer_changed = file_viewer_changed
        self.file_viewer_new_content = file_viewer_new_content

        self.review_comment = review_comment
