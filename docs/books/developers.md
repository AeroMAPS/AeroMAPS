## Installation guide for developers
If you want to contribute to the development of AeroCM, you can clone the repository and install the package in a virtual environment using [Poetry](https://python-poetry.org/):

``` {.bash}
git clone https://github.com/AeroMAPS/AeroMAPS.git
cd aeromaps
poetry install
```

If you also want to run the custom life cycle assessment model (which requires a valid ecoinvent license), install 
the extra dependencies with this command:

``` {.bash}
poetry install -E lca
```

## Release process

The release process adopted is similar to [that used for FAST-OAD](https://github.com/fast-aircraft-design/FAST-OAD/wiki/Release-process).
Note that you also need to change the version name in the pyproject.toml file in the release branch.
