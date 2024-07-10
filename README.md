# Pythoneer AI Agent 

Agentic developer tools for codebase-wide changes. For example, porting a Python 2 codebase to Python 3, converting TensorFlow to PyTorch (and vice versa), etc. 

### Capabilities

* Porting Python 2 to Python 3
* Converting PyTorch codebases to TensorFlow
* Converting TensorFlow codebases to PyTorch 

## Getting Started 

### Prerequisites 

* [Docker](https://docs.docker.com/) 🐋 - used by the agent to run Python scripts in isolated, pre-defined environments. See [Get Docker](https://docs.docker.com/get-docker/) for installation instructions.
*  Run `docker-compose build` to build the required images.
*  Create a `.env` file at the project root, and add an entry for your `ANTHROPIC_API_KEY`

### Running

* Run `run.py`, with arguments for your config file, codebase path and workspace path. 
