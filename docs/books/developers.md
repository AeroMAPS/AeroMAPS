# Contribution and development

As a contributor please read the [developer guide](#developer-guide) and the [coding guidelines and best practices]().

## Developer Guide

#### Quick Start

- Install [uv](#uv)

- Clone the repository:
    ```bash
    git clone https://github.com/AeroMAPS/AeroMAPS.git
    ```
- Move into the root of the git clone with:
    ```bash
    cd aeromaps
    ```
- create a [develompent environment](#development-environment):
    ```bash
    uv venv
    ```
- Install the dependencies:
    ```bash
    uv sync
    ```
- Install pre-commit hooks with:
    ```bash
    pre-commit install
    ```
- Configure your [IDE](#configuring-your-ide)

If you also want to run the custom life cycle assessment model (which requires a valid ecoinvent license), install the extra dependencies with this command:

```bash
uv sync --extra lca
```


### Environments

#### UV

We use [uv](https://docs.astral.sh/uv/) to handle all development tasks such as dependencies management, packaging, testing, checking, managing development enviroments. Follow uv's [installation guide](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer) to start.

With uv installed there's no need to install a specific python version as uv handles it.

#### Development environment

From the root repository of the project (where you can find the uv.lock file) open a terminal and create a python virtual environment (venv) with:

```bash
uv venv
```

you can chose the python version with the flag `--python` followed by the version, eg:

```bash
uv venv --python 3.11
```

You can find more information about uv venv [here](https://docs.astral.sh/uv/pip/environments/).


With



### Git

### Testing

### Documentation

### Versioning

### Configuring your IDE

#### PyCharm

#### VSCode

## Installation guide for developers
If you want to contribute to the development of AeroCM, you can clone the repository and install the package in a virtual environment using [uv](https://docs.astral.sh/uv/):

``` {.bash}
git clone https://github.com/AeroMAPS/AeroMAPS.git
cd aeromaps
uv sync
```

If you also want to run the custom life cycle assessment model (which requires a valid ecoinvent license), install 
the extra dependencies with this command:

``` {.bash}
uv sync --extra lca
```

## Release process

The release process adopted is similar to [that used for FAST-OAD](https://github.com/fast-aircraft-design/FAST-OAD/wiki/Release-process).
Note that you also need to change the version name in the pyproject.toml file in the release branch.
