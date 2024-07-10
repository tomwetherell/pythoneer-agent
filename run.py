"""Run the agent."""

from argparse import ArgumentParser

from pythoneer.agent import Agent


def parse_args():
    """Parse command-line arguments."""
    parser = ArgumentParser(description="Runs the agent with a task.")
    parser.add_argument(
        "--config_file",
        type=str,
        required=True,
        help=(
            "Path to the config file. The config file defines the task and the agent's parameters. "
            "See `pythoneer/config` for examples."
        ),
    )
    parser.add_argument(
        "--codebase_path",
        type=str,
        required=True,
        help="Path to the codebase for the agent to work on.",
    )
    parser.add_argument(
        "--workspace_path",
        type=str,
        required=True,
        help=(
            "Path to the agent's workspace directory. "
            "This is where the agent will save the modified codebase."
        ),
    )

    args = parser.parse_args()

    return args


def main():
    """Run the agent."""
    args = parse_args()
    agent = Agent(
        config_file=args.config_file,
        codebase_path=args.codebase_path,
        workspace_path=args.workspace_path,
    )
    agent.run()


if __name__ == "__main__":
    main()
