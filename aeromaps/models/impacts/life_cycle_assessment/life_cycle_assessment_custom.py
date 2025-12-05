"""
Custom model for Life Cycle Assessment (LCA) of air transportation systems
"""

# Standard library imports
import warnings
import pandas as pd
import numpy as np
from typing import Dict
import xarray as xr

try:
    import lca_algebraic as agb
    from lca_modeller.io.configuration import LCAProblemConfigurator
    import brightway2 as bw
except ImportError as e:
    raise ImportError(
        "Required libraries for Custom Life Cycle Assessment module are not installed. "
        "Please run 'pip install --upgrade aeromaps[lca]' to install them."
    ) from e

# AeroMAPS imports
from aeromaps.models.base import AeroMAPSModel, aeromaps_interpolation_function
from aeromaps.models.impacts.life_cycle_assessment.utils.functions import (
    tuple_to_varname,
    is_not_nan,
    compute_param_length
)

# Constants
KEY_YEAR = "year"
KEY_METHOD = "method"

# suppress warnings from woosh (to be resolved in future versions of lca-modeller?)
warnings.filterwarnings("ignore", category=SyntaxWarning)


class LifeCycleAssessmentCustom(AeroMAPSModel):
    """ Life Cycle Assessment (LCA) model to compute multiple environmental impacts beyond climate change.

        This model requires a valid ecoinvent license stored in a private '.env' file (that you will not share /commit)
        in the notebooks or project root folder, containing the following variables:
            ECOINVENT_LOGIN=<your_login>
            ECOINVENT_PASSWORD=<your_password>

        This model uses the lca_modeller library to build a parametric LCA model from a user-provided configuration file,
        and the lca_algebraic library (a layer on top of brightway) to compute LCA results efficiently for multiple years.
        The life cycle inventory relies on the ecoinvent database, projected to future years using the premise library.

        Parameters
        ----------
        name : str
            Name of the model instance.
        configuration_file : str
            Path to the LCA configuration file defining the model and LCIA methods.
        split_by : str, optional
            Axis to split impacts by (typically, "phase").
            Should match an axis defined in the configuration file through the "attribute" field.

        Attributes
        ----------
        model : agb.Activity
            The parametric LCA model representative of air transport, generated from the configuration file.
        methods : list
            List of LCIA methods to compute.
        axis : str
            Optional axis to get contributors to impacts (typically, "phase").
        params_names : list
            List of LCA parameter names used in the model, generated automatically from the LCA model definition.
        xarray_lca : xr.DataArray
            The full LCA results stored as an xarray DataArray after computation.
        lambdas : list
            List of symbolic expressions for LCIA impacts, precomputed for efficiency.

        """
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
            *args,
            **kwargs,
        )

        # Get LCA model and LCIA methods
        if configuration_file is None:
            raise ValueError("Configuration file is missing.")

        print("===== LCA Custom Model Initialization =====")
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
        print("===========================================")

        # --- Add LCA impact categories the outputs to the AeroMAPSModel ---
        self.axis_keys = getattr(self.lambdas[0], "axis_keys", None)
        if self.axis_keys:
            self.axis_keys = list(self.axis_keys)
            for method in self.methods:
                for phase in self.axis_keys:
                    method_with_axis = method + (phase,)
                    self.output_names.append(tuple_to_varname(method_with_axis))
        else:
            for method in self.methods:
                self.output_names.append(tuple_to_varname(method))

    def compute(self, input_data) -> dict:
        """
        Compute LCA impacts for the given input parameters.

        Parameters
        ----------
        input_data : dict
            Dictionary containing values for LCA parameters.

        Returns
        -------
        dict
            Dictionary containing computed LCA impacts as pd.Series (one per impact category).
        """
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
        and interpolation from reference years/values if needed.

        Parameters
        ----------
        input_data : dict
            Dictionary containing values for LCA parameters.

        Returns
        -------
        dict
            Dictionary of parameter names (LCA-compliant) and their corresponding values for the simulation period.
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
                    f'Both direct value and reference years/values provided for parameter "{name}". '
                    f'Direct value will be used.'
                )

        return params_dict

    def _multi_lca_algebraic_raw(self, **params):
        """
        Main parametric LCIA method, adapted from lca_algebraic.
        Computes impacts from the compiled LCIA expressions (lambdas) and the provided parameters values.
        Compared to the compute_impacts method from lca_algebraic, this version can handle simultaneously
        lists of parameters and subdivision by axis.

        Parameters
        ----------
        params : Dict[str,ListOrScalar]
                 Dictionary of name: values of all the parameters declared in the model.
                 Values can be single value or list of values (in this case, all of the same size)

        Returns
        ------
        xr.DataArray
            3 dimension xarray of lca results, with dims=("systems", "impacts", "params"]
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

        param_length = compute_param_length(params)
        out = np.full((len(models.keys()), len(methods), param_length), np.nan, float)
        axis_keys = self.axis_keys

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

                if self.axis_keys:
                    # Reshape array to add dimension corresponding to axis keys
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

        # Add units in metadata
        units_attr = res.coords["impacts"].attrs.get("units", {})
        for imethod, method in enumerate(methods):
            units_attr[method] = unit = bw.Method(method).metadata.get("unit", None)
        res.coords["impacts"].attrs["units"] = units_attr

        return res

    def _compute_impacts_from_lambdas(
        self,
        **params: Dict[str, agb.SingleOrMultipleFloat],
    ):
        """
        Modified version of compute_impacts from lca_algebraic to compute impacts from precomputed lambdas.
        More like a wrapper of _postLCAAlgebraic, to avoid calling _preLCAAlgebraic which is unecessarily
        time consuming when lambdas have already been calculated and doesn't have to be updated.
        This version does not handle simultaneously lists of parameters and subdivision by axis.
        Will probably be deprecated in future versions.

        Parameters
        ----------
        params : Dict[str,ListOrScalar]
                 Dictionary of name: values of all the parameters declared in the model.
                 Values can be single value or list of values (in this case, all of the same size)

        Returns
        ------
        pd.DataFrame
            DataFrame of lca results, indexed by axis or parameter values if applicable.

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
                df[self.axis] = self.axis_keys
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

        Parameters
        ----------
        res : xr.DataArray
            The xarray DataArray containing LCA results.

        Returns
        -------
        dict
            Dictionary of pd.Series for each impact category.
        """
        output_data = {}

        if self.axis_keys:
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
