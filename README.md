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

* Install [Docker](https://docs.docker.com/) 🐋. Docker is used by the agent to run Python scripts in isolated, pre-defined environments. See [Get Docker](https://docs.docker.com/get-docker/) for installation instructions.
*  Run `docker-compose build` to build the required images.
*  Create a `.env` file at the project root, and add an entry for your `ANTHROPIC_API_KEY`. 
*  Create a virtual environment and run `pip install .` to install the package and the dependencies. 

### Use

* Create a config file, or use one of the existing configs in `/config`. The config file defines the task, and the tools that the agent has access to. 
* Run the agent:

```
export CONFIG_FILE=<path to config file>
export CODEBASE_PATH=<path to codebase to edit>
export WORKSPACE_PATH=<path to directory to save outputs to>

run.py \
--config_file $CONFIG_FILE \
--codebase_path $CODEBASE_PATH \
--workspace_path $WORKSPACE_PATH
```
