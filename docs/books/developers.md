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

## Units and variable metadata

Every variable exchanged between AeroMAPS models (inputs, outputs, climate
outputs) is documented — unit, description, optional source — in a single
file: [`aeromaps/resources/data/data_information.yaml`](https://github.com/AeroMAPS/AeroMAPS/blob/main/aeromaps/resources/data/data_information.yaml).
The test suite fails if a variable produced by one of the tested configurations
is missing from it, so keeping it up to date is part of adding a model.

### Documenting a new variable

Two options, in order of precedence:

1. **Exact entry** in the `variables` section, keyed by the variable name:

   ```yaml
   variables:
     my_new_output:
       unit: "MtCO2"
       description: "Annual CO2 emissions of my new model"
       source: "Optional reference for the default value"
   ```

2. **Pattern rule** in the `patterns` section, for families of variables whose
   names are generated dynamically (e.g. one per energy pathway). Rules are
   evaluated in file order and the first match wins; `{prefix}` in the
   description is replaced by the text matched by the first `*`:

   ```yaml
   patterns:
     - match: "*_energy_consumption"
       unit: "MJ"
       description: "Energy consumption of `{prefix}`"
   ```

The special unit `N/A` marks variables whose unit cannot be expressed
statically (e.g. LCA impacts, whose unit depends on the LCIA method).

### The unit vocabulary

Unit strings are validated when the file is loaded, against the controlled
vocabulary defined in `aeromaps/utils/units.py`. Units are composed from
atomic symbols (`MJ`, `yr`, `€`, `ASK`, `gCO2`, `kg_NOx`, ...) with `*`, `/`
and parentheses, e.g. `gCO2/MJ` or `€/(MJ/yr)`. Species-tagged masses (CO2,
CO2e, NOx, ...) are dimensionally distinct so they cannot be mixed by mistake.
To introduce a new atomic symbol, add it to `ATOMIC_UNITS` (or `UNIT_ALIASES`
for an alternative spelling) in `aeromaps/utils/units.py`.

The module also provides validated conversions for use in models or
post-processing:

```python
from aeromaps.utils.units import convert

energy_ej = convert(energy_mj, "MJ", "EJ")  # works on scalars, arrays, Series
```

`convert` raises a `UnitError` if the two units are not commensurable, which
catches unit mistakes early. Metadata of a variable can be queried from a
process with `process.get_variable_information("co2_emissions")`.

## Release process

The release process adopted is similar to [that used for FAST-OAD](https://github.com/fast-aircraft-design/FAST-OAD/wiki/Release-process).
Note that you also need to change the version name in the pyproject.toml file in the release branch.
