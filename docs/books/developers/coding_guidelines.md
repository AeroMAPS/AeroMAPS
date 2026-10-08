# Coding Guidelines

In this page we will give a quick overview of the main coding good practices to be
applied to this project. 

## Writing Code

### Python coding style and formatting

The code shall be understandable by all contributors, therefore good coding practices
are mandatory. For coding style, [PEP8](https://peps.python.org/pep-0008/) should
apply as much as possible. The one global exception for this project is the usage of
line length up to 100 characters.

Code formatting and style (mostly) is enforced with 
[Ruff](https://docs.astral.sh/ruff/). 

The usage of type hints is strongly recommended. 

## Testing

New lines of code or modified lines should be covered by tests. We use 
[pytest](https://docs.pytest.org/en/latest/) as testing framework.

Unit tests are in the source folder of the project (`./aeromaps/`), other tests can
be found in `./tests/`.

### Running test

There are two main ways to run the tests:

1. From a terminal at the root of the project with the command:

```bash
uv run pytest
```

2. From your IDE's testing interface.


You can run the tests a get a html coverage report with:

```bash
uv run pytest --cov --cov-report=html
```

Similarly, this can also be done within your IDE's interface.

## Documentation

A good project is well documented. Make sure that any new feature added is properly
document.

Good documentation can take many different forms from having proper descriptive
docstrings to having dedicated usage examples pages.

We use [mkdocs](https://www.mkdocs.org/) for documenting.

The documentation lives in the folder `./docs/`. Here you will find the markdown (.md)
files which structure the pages of the documentation. In the root folder you will find 
the `mkdocs.yml` file, this file is the "instruction" file that mkdocs uses to structure
the documentation. Whenever you are a new page to the documentation, you need to add it
to this file too.


to compile the documentation use the command:

```bash
uv run mkdocs serve
```

This will compile the documentation in a local server which you can open in your own
browser. This will allow you to visualize the documentation and edit it live so that
you can monitor that the the documentation you write displays how you intend it to do.

## Packages upgrades

All dependencies of AeroMAPS and they allowed version ranges are defined in the `pyproject.yaml`.
When adding a new dependency to the project you must add it to the pyproject.yaml file
to the corresponding group (if applicable), define a range of allowed versions and
update the lock file (`uv.lock`) with 
```bash
uv lock
``` 

so that the new dependencies are considered.

The dependencies groups are:

- `test`: testing dependencies 
- `docs`: documentation dependencies
- `paper`: Scientific publications dependencies
- `lint`: linting dependencies

Any other dependency should be in the `dependencies` section, or `project.optional-dependencies`
if they are optional.
