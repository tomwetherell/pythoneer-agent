# Pythoneer AI Agent 

Pythoneer AI is a tool to help developers make codebase-wide changes to their Python projects - giving them more time to focus on more enjoyable and rewarding problems.

The agent is provided with a codebase and a task, and takes iterative steps to complete it. Through the use of tools, the agent is able to open, edit and create files, and run tests and python scripts.

### Capabilities

* Porting Python 2 to Python 3
* Converting PyTorch codebases to TensorFlow
* Converting TensorFlow codebases to PyTorch

Check out the [website](https://pythoneer.ai/) for some demos!

## Getting Started 

### Prerequisites 

* [Docker](https://docs.docker.com/) 🐋 - used by the agent to run Python scripts in isolated, pre-defined environments. See [Get Docker](https://docs.docker.com/get-docker/) for installation instructions.
*  Run `docker-compose build` to build the required images.
*  Create a `.env` file at the project root, and add an entry for your `ANTHROPIC_API_KEY`
*  Create a virtual environment and run `pip install .` to install the package and the dependencies. 

### Running

* Run `run.py`, with arguments for your config file, codebase path and workspace path. 
