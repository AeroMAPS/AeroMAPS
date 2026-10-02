# Contribution and development

As a contributor please read the [developer guide](#developer-guide) and the [coding guidelines and best practices]().

## Quick Start

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


## Developer Guide




### Git

### Testing

### Documentation

### Versioning

### Configure your IDE

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
