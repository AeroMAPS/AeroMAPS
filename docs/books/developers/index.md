# Contribution and development

As a contributor please read the [developer guide](/docs/books/developers/index.md) and the [coding guidelines and best practices](coding_guidelines.md).

## Quick Start

- Install [uv](project_setup.md#uv)

- Clone the repository:
    ```bash
    git clone https://github.com/AeroMAPS/AeroMAPS.git
    ```
- Move into the root of the git clone with:
    ```bash
    cd aeromaps
    ```
- create a [development environment](project_setup.md#development-environment):
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
### Versioning

### Configure your IDE

#### PyCharm

#### VSCode
