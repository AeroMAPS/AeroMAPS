# Project setup

## UV

We use [uv](https://docs.astral.sh/uv/) to handle all development tasks such as 
dependencies management, packaging, testing, checking, managing development environments. 
Follow uv's [installation guide](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer) to start.

With uv installed there's no need to install a specific python version as uv handles it.

## Development environment

Clone the project with: 
```bash
git clone https://github.com/AeroMAPS/AeroMAPS.git
```

From the root repository of the project (where you can find the uv.lock file) open a 
terminal and create a python virtual environment (venv) with:

```bash
uv venv
```

you can chose the python version with the flag `--python` followed by the version, eg:

```bash
uv venv --python 3.11
```

You can find more information about uv venv [here](https://docs.astral.sh/uv/pip/environments/).


With the development environment created, you can install the package and its requirements with:

```bash
uv sync
```

This will install AeroMAPS in editable mode which means the package will be 
installed in the development environment while it still being visible and editable 
from the repository tree.

While activating the environment is not necessary to code within the project, it can be 
useful to investigate the code when needed.

To activate the environment within the terminal use:

- On linux and MacOS:
    ```bash
    source .venv/bin/activate
    ```
- On Windows:
    ```bash
    .venv\bin\activate.bat
    ```

Pointing to the development environment's python interpreter within your IDE can be 
useful to execute code, debug, run tests, etc from your IDE graphical interface. 

## Setup pre-commit

While [pre-commit](https://pre-commit.com/) is a project dependency, we recommend 
installing pre-commit globally as a development tool. That can be done with:

```bash
uv tool install pre-commit --with pre-commit-uv   
```

Install pre-commit hooks with

```bash
pre-commit install
```

Pre-commit uses Ruff as a tool for analyzing and formatting code. We recommend 
automating the usage of the tool by installing the Ruff Extension on your IDE when
you configure your IDE and installing the tool in your 
environment with:

```bash
uv tool install ruff
``` 