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

## Units and variable metadata

Every variable exchanged between AeroMAPS models (inputs, outputs, climate
outputs) carries a unit and a description. The metadata lives on the GEMSEO
grammars of the disciplines: when a model is wrapped, its unit is validated
against the vocabulary and attached to the discipline, and the description is
stored in the grammar. The test suite fails if a variable of one of the tested
configurations has neither, so documenting a variable is part of adding a model.

### Declaring metadata in the model

The preferred place is the model itself, because the model that generates a
family of names (one per market, one per pathway) knows their unit once.

- Custom models declare their I/O with `declare_input` and `declare_output`
  instead of filling `input_names` and `output_names` by hand:

  ```python
  self.declare_output(
      f"energy_per_ask_{market.id}_{energy_type}",
      pd.Series([0.0]),
      unit="MJ/ASK",
      description=f"Energy per ASK of the {market.id} market",
  )
  ```

- Auto models declare units in the class-level `UNITS` mapping; descriptions
  are parsed by GEMSEO from the docstring of `compute`:

  ```python
  class ManualCarbonOffset(AeroMAPSModel):
      UNITS = {"manual_carbon_offset": "MtCO2"}
  ```

Wrong units fail when the discipline is built, and a coupling variable
produced in one unit and consumed in another (even a commensurable one, MJ
against EJ) fails when the process assembles its disciplines. Values are
passed between models without conversion, so identical units are required.
`process.list_registry_resolved_variables()` lists the variables whose unit
still comes from the registry described below; the list is meant to shrink.

### The metadata registry

Variables not declared by a model fall back to
[`aeromaps/resources/data/data_information.yaml`](https://github.com/AeroMAPS/AeroMAPS/blob/main/aeromaps/resources/data/data_information.yaml).
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

Prefer a pattern whenever the variable name embeds something the user chooses —
an energy pathway, a resource, or a **market id**. Market ids come from the
markets yaml file, so market-scoped variables (`<market_id>_covid_end_year`,
`cagr_rpk_<market_id>`, ...) can never be enumerated exhaustively and are
documented by the rules of the *Market-scoped* sections of
`data_information.yaml`. Adding a market to a scenario then requires no change
to the metadata file.

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
process with `process.get_variable_information("co2_emissions")`; what the
model declares wins over the registry, the source always comes from the
registry.

### Exporting the variable schemas

The inputs and outputs of a configured process can be exported as two JSON
Schema files (draft-07), derived from the discipline grammars:

```bash
aeromaps schema --config my_config.yaml --output-dir schema/ --compute
```

`inputs_schema.json` lists every variable read by a model and produced by
none, with its JSON type, `unit`, `description`, `source`, default value and
the models consuming it (`x-consumers`). `outputs_schema.json` lists every
variable produced by a model, with its producer (`x-producer`). Auto models do
not annotate their outputs one by one, so those outputs are untyped unless the
process has run (`--compute`, or `process.compute()` before
`process.export_schema()`). Downstream tools such as the web application
should read units and descriptions from these files rather than duplicating
them.

## Release process

The release process adopted is similar to [that used for FAST-OAD](https://github.com/fast-aircraft-design/FAST-OAD/wiki/Release-process).
Note that you also need to change the version name in the pyproject.toml file in the release branch.
