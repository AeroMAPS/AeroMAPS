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

To run processes on the JAX execution path (see below), install the `jax` extra:

``` {.bash}
poetry install -E jax
```

## The JAX execution path

`create_process(..., use_jax=True)` wraps every model that provides a
`jax_compute` method in a [gemseo-jax](https://gitlab.com/gemseo/dev/gemseo-jax)
discipline, which gives the MDA and the optimiser analytic derivatives by
automatic differentiation instead of finite differences. Models without a
`jax_compute` keep the regular pandas wrappers, so the two kinds of discipline
coexist in the same process, and the results are identical either way — this is
locked by `aeromaps/tests/core/test_jax_parity.py`, which compares
`vector_outputs`, `climate_outputs` and `float_outputs` between the two paths.

### Writing a `jax_compute`

`compute` is never modified: `jax_compute` is added next to it and must return
the same values.

* Keep the same signature as `compute` for `model_type="auto"` models, and the
  same `input_data` dict contract for `model_type="custom"` ones.
* Year-indexed quantities are flat `jax.numpy` arrays over the model's full year
  index. Where the pandas version leaves a cell unset, the JAX version must hold
  `NaN` — the parity test compares NaN patterns year by year, because NaN means
  "no value for this year" throughout AeroMAPS.
* `aeromaps/models/jax_helpers.py` holds the JAX counterparts of the pandas
  helpers (interpolation, levelling, COVID trajectories, per-vintage discounting
  windows, a differentiable scalar root find, …). Reuse them rather than
  re-deriving the conventions.
* Values that are loop bounds, window lengths or interpolation knots must be
  static: list them in `jax_static_input_names` and they are frozen at
  discipline-build time instead of being traced.
* For an `auto` model, `AutoJAXDiscipline` names the outputs by walking **every**
  `return` statement in the source of `jax_compute` — including those of nested
  functions — and each returned element must be a plain name. Put any helper
  with its own `return` at module level.
* GEMSEO passes scalar variables as plain floats when executing but as size-1
  arrays when linearizing; use `jax_scalar_value` where a model reads a scalar
  that may also be given per year.

Three class attributes on `AeroMAPSModel` declare what the wrapper cannot infer:

* `jax_climate_output_names` — outputs the pandas `compute` keeps in
  `df_climate` rather than `df`.
* `jax_extra_output_names` — intermediates the pandas `compute` writes straight
  into `self.df` without declaring them as GEMSEO variables.
* `jax_output_indexes` (a property) — outputs whose index is not the model year
  index.

### Models that stay on the pandas path

* `ClimateModel` and the life cycle assessment models delegate to external
  packages (AeroCM, brightway), so porting them belongs in those projects.
* The fleet-model-coupled disciplines (`FleetEvolution`, the `*Complex`
  efficiency and emission-index models, the manufacturer cost models,
  `FleetCarbonAbatementCosts`) read the bottom-up fleet object's dataframes
  rather than GEMSEO variables.

## Release process

The release process adopted is similar to [that used for FAST-OAD](https://github.com/fast-aircraft-design/FAST-OAD/wiki/Release-process).
Note that you also need to change the version name in the pyproject.toml file in the release branch.
