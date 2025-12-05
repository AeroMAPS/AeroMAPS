"""
Default model for Life Cycle Assessment (LCA) of air transportation systems
"""

# Standard library imports
import warnings
import pandas as pd
import numpy as np
import ast
from typing import Dict
import xarray as xr

# AeroMAPS imports
from aeromaps.models.base import AeroMAPSModel, aeromaps_interpolation_function
from aeromaps.models.impacts.life_cycle_assessment.io.common import Model, TOTAL_AXIS_KEY
from aeromaps.models.impacts.life_cycle_assessment.utils.functions import (
    tuple_to_varname,
    is_not_nan,
    compute_param_length
)

# Constants
KEY_YEAR = "year"
KEY_METHOD = "method"
KEY_MODEL = "model"


class LifeCycleAssessmentDefault(AeroMAPSModel):
    """
    Model to load LCA pre-compiled expressions from a JSON file.
    Compared to the LifeCycleAssessmentCustom model, this model does not require the user to install LCA-specific
    packages and is disconnected from the ecoinvent database. It is therefore easier to use and deploy, but less
    flexible as the user cannot modify the LCA model structure.

    Parameters
    ----------
    name : str, optional
        Name of the model instance.
    json_file : str
        Path to the JSON file containing the pre-compiled LCA model.
    split_by : str, optional
        Axis to split the results by (e.g., "phase"). If None, total results are provided.

    Attributes
    ----------
    model : Model
        The LCA model loaded from the JSON file.
    methods : List[tuple]
        List of impact assessment methods available in the model.
    axis_keys : List[str] or None
        List of keys for the specified axis, if applicable.
    params_names : List[str]
        List of parameter names required by the LCA model.
    xarray_lca : xr.DataArray
        Xarray DataArray storing the LCA results after computation.
    """

    def __init__(
        self,
        name: str = "life_cycle_assessment_default",
        json_file: str = None,
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

        # Instantiate LCA model from JSON file
        if json_file is None:
            raise ValueError("JSON file is missing.")

        # Get methods names, axis keys, and parameters names
        self.axis = split_by if split_by else TOTAL_AXIS_KEY

        print("===== LCA Default Model Import =====")
        self.model = Model.from_file(json_file, axis=self.axis, progress_bar=True)
        self.methods = [ast.literal_eval(s) for s in self.model.impacts.keys()]
        self.axis_keys = None
        expr = self.model.expressions[self.axis][str(self.methods[0])].expr
        if isinstance(expr, dict):
            self.axis_keys = list(expr.keys())
        self.params_names = list(self.model.params.keys())
        print("====================================")

        # Initialize empty xarray to store results after compute
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

        # --- Add LCA impact categories the outputs to the AeroMAPSModel ---
        if self.axis_keys:
            for method in self.methods:
                for phase in self.axis_keys:
                    method_with_axis = method + (phase,)
                    self.output_names.append(tuple_to_varname(method_with_axis))
        else:
            for method in self.methods:
                self.output_names.append(tuple_to_varname(method))

    def compute(self, input_data) -> dict:
        """
        Main compute method for the LCA model.

        Parameters
        ----------
        input_data : dict
            Dictionary containing input parameter values.

        Returns
        -------
        output_data : dict
            Dictionary containing LCA results as pd.Series for each impact category.
        """
        # --- Assign values to parameters ---
        params_dict = self._get_param_values(input_data)

        # --- Calculate impacts for all parameters at once ---
        res = self._multi_lca_algebraic_json(**params_dict)

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
                            input_value = input_value[-len(self.years):]
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

            # --- Parameter value not provided, use default value from LCA model ---
            else:
                default_val = self.model.params[name].default
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

    def _multi_lca_algebraic_json(self, **params):
        """
        Main parametric LCIA method using pre-compiled expressions from JSON file.

        Parameters
        ----------
        params : Dict[str,ListOrScalar]
                 You should provide named values of all the parameters declared
                 in the model. Values can be single value or list of samples, all of the same size

        Return
        ------
        lca : 3 or 4 dimension xarray of lca results, with dims=("systems", "impacts", "axis" (optional), "params"]
        """

        models = {KEY_MODEL: self.model}
        methods = self.methods
        param_length = compute_param_length(params)
        out = np.empty((len(models), len(methods), param_length))
        axis = self.axis
        axis_keys = self.axis_keys

        for imodel, (model_name, model) in enumerate(models.items()):
            expr = model.expressions[axis][str(methods[0])].expr
            if isinstance(expr, dict):
                axis_keys = expr.keys()
                out = np.expand_dims(out, axis=-2)
                out = np.repeat(out, len(axis_keys), axis=-2)
            for imethod, method in enumerate(methods):
                result_dict, _ = model.evaluate(str(method), axis=axis, **params)
                if isinstance(result_dict, dict):
                    # result_dict = normalize_result_dict(result_dict, param_length)
                    for iaxis, ax in enumerate(axis_keys):
                        out[imodel, imethod, iaxis, :] = result_dict[ax]  # np.array(list(result_dict.values()), dtype=float)
                else:
                    out[imodel, imethod, :] = result_dict

        if axis_keys:
            res = xr.DataArray(
                out,
                name="lca",
                coords=[
                    ("systems", np.fromiter((m for m in models.keys()), dtype="O")),
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
                    ("systems", np.fromiter((m for m in models.keys()), dtype="O")),
                    ("impacts", np.fromiter(methods, dtype="O")),
                    ("params", list(range(param_length))),
                ],
            )

        # Add units in metadata
        units_attr = res.coords["impacts"].attrs.get("units", {})
        for imethod, method in enumerate(methods):
            units_attr[method] = self.model.impacts[str(method)].unit
        res.coords["impacts"].attrs["units"] = units_attr

        return res

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
                    value = res.sel(systems=KEY_MODEL, impacts=method, axis=phase).to_series()
                    value = value.reindex(range(self.historic_start_year, self.end_year + 1))
                    output_data[tuple_to_varname(method_with_axis)] = value
        else:
            for method in res.coords["impacts"].values:
                value = res.sel(systems=KEY_MODEL, impacts=method).to_series()
                value = value.reindex(range(self.historic_start_year, self.end_year + 1))
                output_data[tuple_to_varname(method)] = value

        return output_data