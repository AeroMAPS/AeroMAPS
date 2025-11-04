"""
Model for Life Cycle Assessment (LCA) of air transportation systems
"""

import warnings
import re

from aeromaps.models.base import AeroMAPSModel, aeromaps_interpolation_function
import pandas as pd
import numpy as np
import lca_algebraic as agb
from lca_modeller.io.configuration import LCAProblemConfigurator

# from aeromaps.core.process import DEFAULT_PARAMETERS_PATH
# from aeromaps.models.parameters import Parameters
from typing import Dict
import xarray as xr

KEY_YEAR = "year"
KEY_METHOD = "method"


class LifeCycleAssessment(AeroMAPSModel):
    deepcopy_at_init = (
        False  # --> do not re-instantiate model at each process run since LCA model is heavy
    )
    # (see aeromaps/core/process.py)

    def __init__(
        self,
        name: str = "life_cycle_assessment",
        configuration_file: str = None,
        split_by: str = None,
        *args,
        **kwargs,
    ):
        super().__init__(
            name=name,
            model_type="custom",
            # inputs/outputs are defined in __init__ rather than auto generated from compute() signature
            *args,
            **kwargs,
        )

        # Get LCA model and LCIA methods
        if configuration_file is None:
            raise ValueError("Configuration file is missing.")
        _, model, methods = LCAProblemConfigurator(configuration_file).generate()
        self.model = model
        self.methods = methods
        self.axis = split_by
        self.params_names = agb.all_params().keys()
        self.xarray_lca = xr.DataArray()

        # --- Add LCA parameters as inputs of this AeroMAPSModel ---
        self._skip_data_type_validation = True  # see aeromaps/core/gemseo.py
        self.input_names = []
        self.output_names = []

        for x in self.params_names:
            # Years of simulation are directly taken from AeroMAPS timeline and not as an input parameter
            if x == KEY_YEAR:
                continue

            self.input_names.append(x)
            self.input_names.append(x + "_reference_years")
            self.input_names.append(x + "_reference_years_values")

            self.default_input_data[x] = np.nan
            self.default_input_data[x + "_reference_years"] = np.nan
            self.default_input_data[x + "_reference_years_values"] = np.nan

        # Dry run with lca_algebraic to build symbolic expressions of LCIA impacts
        print("Parametrizing LCIA impacts...", end=" ")
        self.lambdas = agb.lca._preMultiLCAAlgebric(self.model, self.methods, axis=self.axis)
        print("Done.")

        # --- Add LCA impact categories the outputs to the AeroMAPSModel ---
        if getattr(self.lambdas[0], "axis_keys", None):
            for method in self.methods:
                for phase in self.lambdas[0].axis_keys:
                    method_with_axis = method + (phase,)
                    self.output_names.append(tuple_to_varname(method_with_axis))
        else:
            for method in self.methods:
                self.output_names.append(tuple_to_varname(method))

    def compute(self, input_data) -> dict:
        # --- Assign values to parameters ---
        params_dict = self._get_param_values(input_data)

        # --- Calculate impacts for all parameters at once ---
        res = self._multi_lca_algebraic_raw(**params_dict)

        # --- Store xarray to enable user to access data after process calculation ---
        res["params"] = params_dict[KEY_YEAR]  # replace param index by actual years
        res = res.rename({"params": KEY_YEAR})  # rename 'params' dimension to 'year'
        self.xarray_lca = res

        # --- Convert xarray to pd.Series to enable connection with other models ---
        output_data = self._convert_xarray_to_series(res)
        self._store_outputs(output_data)

        return output_data

    def _get_param_values(self, input_data) -> dict:
        """
        Extract LCA parameter values from input_data, handling different formats
        """
        params_dict = {}

        for name in self.params_names:
            # --- Year parameter is obtained from AeroMAPS timeline ---
            if name == KEY_YEAR:
                # params_dict[name] = list(range(self.prospection_start_year, self.end_year + 1))
                # replace by self.data["years"]["prospective_years"] ?
                params_dict[name] = self.years
                continue

            # --- Parameter provided directly (either single value or list of values) ---
            if is_not_nan(input_data[name]):  # np.nan is the default value set in __init__
                input_value = input_data[name]

                # Single value
                if isinstance(input_value, str | float | int):
                    params_dict[name] = input_value

                # Multiple values
                elif isinstance(input_value, (list, np.ndarray, pd.Series)):
                    if len(input_data[name]) == 1:
                        params_dict[name] = input_value[0]

                    elif len(input_value) == len(self.years):
                        params_dict[name] = np.nan_to_num(input_value)

                    elif len(input_value) > len(self.years):
                        n = len(input_value) - len(self.years)

                        # If it's a pandas Series, try to align on the years index
                        if isinstance(input_value, pd.Series):
                            # Attempt to reindex on self.years, dropping missing values or filling with NaN
                            input_value = input_value.reindex(self.years)
                        else:
                            # If not a Series, fall back to slicing and warn user
                            input_value = input_value[-len(self.years) :]
                            warnings.warn(
                                f"Too many values for parameter {name}: first {n} values will be dropped."
                            )

                        # Finally, convert safely
                        params_dict[name] = np.nan_to_num(input_value)

                    else:
                        raise ValueError(
                            f"Parameter '{name}' has not enough values for the simulation period {self.historic_start_year} - {self.end_year}."
                        )

                else:
                    raise TypeError(f"Parameter '{name}' has unsupported type {type(input_value)}.")

            # --- Parameter value not provided directly, try to interpolate from parameters.json ---
            elif is_not_nan(input_data[name + "_reference_years"]) and is_not_nan(
                input_data[name + "_reference_years_values"]
            ):
                param_values = aeromaps_interpolation_function(
                    self,
                    input_data[name + "_reference_years"],
                    input_data[name + "_reference_years_values"],
                    model_name=self.name,
                )
                # param_values = param_values.loc[self.prospection_start_year:self.end_year].values
                params_dict[name] = np.nan_to_num(param_values)

            # --- Parameter value not provided, use default value from lca_modeller ---
            else:
                default_val = agb.all_params()[name].default
                warnings.warn(
                    f'Value for LCA parameter "{name}" is not provided. Default value {default_val} will be used.'
                )
                params_dict[name] = default_val

            # --- Warn if both direct value and reference years/values were provided ---
            if (
                is_not_nan(input_data[name])
                and is_not_nan(input_data[name + "_reference_years"])
                and is_not_nan(input_data[name + "_reference_years_values"])
            ):
                warnings.warn(
                    f'Both direct value and reference years/values provided for parameter "{name}". Direct value will be used.'
                )

        return params_dict

    def _multi_lca_algebraic_raw(self, **params):
        """
        Main parametric LCIA method : Computes LCA by expressing the foreground
        model as symbolic expression of background activities and parameters.
        Then, compute 'static' inventory of the referenced background activities.
        This enables a very fast recomputation of LCA with different parameters,
        useful for stochastic evaluation of parametrized model
        Parameters
        ----------
        models : List of Activities, or Dict of Activities: Lambdas if impacts exprs already calculated
        methods : List of methods, i.e. impacts to consider. Overriden by info from lambdas if provided with models.
        params : Dict[str,ListOrScalar]
                 You should provide named values of all the parameters declared
                 in the models. Values can be single value or list of samples, all of the same size
        axis : keyword to split impacts by phase. Overriden by info from lambdas if provided with models.
        Return
        ------
        lca : 3 dimension xarray of lca results, with dims=("systems", "impacts", "params"]
        """

        models = {self.model: self.lambdas}
        methods = self.methods
        axis = self.axis

        # if isinstance(models, list):
        #    def to_tuple(item):
        #        if isinstance(item, tuple):
        #            return item
        #        else:
        #            return (item, None)
        #    models = dict(to_tuple(item) for item in self.model)

        # elif not isinstance(models, dict):
        #    models = {models: None}

        param_length = agb.params._compute_param_length(params)
        out = np.full((len(models.keys()), len(methods), param_length), np.nan, float)
        axis_keys = None

        for imodel, (model, lambdas) in enumerate(models.items()):
            dbname = model.key[0]
            with agb.DbContext(dbname):
                # Check no params are passed for FixedParams
                for key in params:
                    if key in agb.params._fixed_params():
                        raise ValueError(
                            "Param '%s' is marked as FIXED, but passed in parameters : ignored"
                            % key
                        )

                if not lambdas or len(lambdas) != len(methods):
                    if lambdas:
                        print("Lambdas do not match with len of methods. Recompiling expressions.")
                    lambdas = agb.lca._preMultiLCAAlgebric(model, methods, axis=axis)

                if lambdas[0].has_axis:
                    # Reshape array to add dimension corresponding to axis keys
                    axis_keys = lambdas[0].axis_keys
                    out = np.expand_dims(out, axis=-2)
                    out = np.repeat(out, len(axis_keys), axis=-2)
                for imethod, lambd_with_params in enumerate(lambdas):
                    value = lambd_with_params.compute(**params).value
                    if isinstance(value, dict):
                        # axis values
                        # value = list(float(value[axis]) if axis in value else 0.0 for axis in lambd_with_params.axis_keys)
                        for iaxis, ax in enumerate(axis_keys):
                            out[imodel, imethod, iaxis, :] = np.float_(value[ax])
                    else:
                        out[imodel, imethod, :] = value
        if axis_keys:
            res = xr.DataArray(
                out,
                name="lca",
                coords=[
                    ("systems", np.fromiter((m.key for m in models.keys()), dtype="O")),
                    ("impacts", np.fromiter(methods, dtype="O")),
                    ("axis", np.fromiter(axis_keys, dtype="O")),
                    ("params", list(range(param_length))),
                ],
            )
        else:
            res = xr.DataArray(
                out,
                name="lca",
                coords=[
                    ("systems", np.fromiter((m.key for m in models.keys()), dtype="O")),
                    ("impacts", np.fromiter(methods, dtype="O")),
                    ("params", list(range(param_length))),
                ],
            )
        return res

    def _compute_impacts_from_lambdas(
        self,
        **params: Dict[str, agb.SingleOrMultipleFloat],
    ):
        """
        Modified version of compute_impacts from lca_algebraic.
        More like a wrapper of _postLCAAlgebraic, to avoid calling _preLCAAlgebraic which is unecessarily time consuming when lambdas have already been calculated and doesn't have to be updated.
        """
        dfs = dict()

        dbname = self.model.key[0]
        with agb.DbContext(dbname):
            # Check no params are passed for FixedParams
            for key in params:
                if key in agb.params._fixed_params():
                    print("Param '%s' is marked as FIXED, but passed in parameters : ignored" % key)

            # lambdas = _preMultiLCAAlgebric(model, methods, alpha=alpha, axis=axis)  # <-- this is the time-consuming part

            df = agb.lca._postMultiLCAAlgebric(self.methods, self.lambdas, **params)

            model_name = agb.base_utils._actName(self.model)
            while model_name in dfs:
                model_name += "'"

            # param with several values
            list_params = {k: vals for k, vals in params.items() if isinstance(vals, list)}

            # Shapes the output / index according to the axis or multi param entry
            if self.axis:
                df[self.axis] = self.lambdas[0].axis_keys
                df = df.set_index(self.axis)
                df.index.set_names([self.axis])

                # Filter out line with zero output
                df = df.loc[
                    df.apply(
                        lambda row: not (row.name is None and row.values[0] == 0.0),
                        axis=1,
                    )
                ]

                # Rename "None" to others
                df = df.rename(index={None: "_other_"})

                # Sort index
                df.sort_index(inplace=True)

                # Add "total" line
                df.loc["*sum*"] = df.sum(numeric_only=True)

            elif len(list_params) > 0:
                for k, vals in list_params.items():
                    df[k] = vals
                df = df.set_index(list(list_params.keys()))

            else:
                # Single output ? => give the single row the name of the model activity
                df = df.rename(index={0: model_name})

            dfs[model_name] = df

        if len(dfs) == 1:
            df = list(dfs.values())[0]
        else:
            # Concat several dataframes for several models
            df = pd.concat(list(dfs.values()))

        return df

    def _convert_xarray_to_series(self, res: xr.DataArray) -> dict:
        """
        Convert xarray DataArray to dictionary of pd.Series
        """
        output_data = {}

        if getattr(self.lambdas[0], "axis_keys", None):
            for method in res.coords["impacts"].values:
                for phase in res.coords["axis"].values:
                    method_with_axis = method + (phase,)
                    value = res.sel(systems=self.model.key, impacts=method, axis=phase).to_series()
                    value = value.reindex(range(self.historic_start_year, self.end_year + 1))
                    output_data[tuple_to_varname(method_with_axis)] = value
        else:
            for method in res.coords["impacts"].values:
                value = res.sel(systems=self.model.key, impacts=method).to_series()
                value = value.reindex(range(self.historic_start_year, self.end_year + 1))
                output_data[tuple_to_varname(method)] = value

        return output_data


def tuple_to_varname(items):
    """
    Convert a tuple or list of strings into a clean, Python-friendly variable name.
    """
    if isinstance(items, (list, tuple)):
        text = "__".join(items)  # join parts with double underscores
    else:
        text = str(items)

    # Lowercase everything
    text = text.lower()

    # Replace anything that’s not alphanumeric or underscore with underscore
    text = re.sub(r"[^0-9a-zA-Z_]+", "_", text)

    # Remove leading/trailing underscores and collapse multiple underscores
    text = re.sub(r"_+", "_", text).strip("_")

    # Add lca to variable
    text = "lca_" + text

    return text


def is_not_nan(x):
    """Return True if x is not NaN or None."""
    if x is None:
        return False
    if isinstance(x, (float, int, np.number)):
        return not pd.isna(x)
    if isinstance(x, (pd.Series, np.ndarray, list, tuple)):
        return pd.notna(np.asarray(x)).any()
    return True
