"""
Model for Life Cycle Assessment (LCA) of air transportation systems
"""

from aeromaps.models.base import AeroMAPSModel, AeromapsInterpolationFunction
import pandas as pd
import numpy as np
import lca_algebraic as agb
from lca_modeller.io.configuration import LCAProblemConfigurator
from typing import Tuple

from aeromaps.core.process import default_parameters_path
from aeromaps.models.parameters import Parameters
from typing import Dict
import xarray as xr

KEY_YEAR = "year"
KEY_METHOD = "method"


class LifeCycleAssessment(AeroMAPSModel):
    def __init__(
        self,
        name: str = "life_cycle_assessment",
        configuration_file: str = None,
        split_by: str = None,
        *args,
        **kwargs,
    ):
        super().__init__(name=name, *args, **kwargs)

        # Get LCA model and LCIA methods
        if configuration_file is None:
            raise ValueError("Configuration file is missing.")
        _, model, methods = LCAProblemConfigurator(configuration_file).generate()
        self.model = model
        self.methods = methods
        self.axis = split_by
        self.params_names = agb.all_params().keys()
        self.params_dict = dict()
        self.xarray_lca = xr.DataArray()

        # Automatically add LCA parameters (except strings) as inputs of this AeroMAPSModel.
        # See gemseo.py for more details about addition of auto-generated inputs.
        self.auto_inputs = dict()
        json_file_parameters = Parameters()
        json_file_parameters.read_json(file_name=default_parameters_path)  # default json file (parameters.json)
        json_parameters_dict = json_file_parameters.to_dict()

        for x in self.params_names:
            # KEY_YEAR is a special parameter treated separately
            if x == KEY_YEAR:
                continue

            # Inputs provided in json file
            elif x in json_parameters_dict.keys():
                value = json_parameters_dict[x]
                self.auto_inputs[x] = type(value)

            # Parameters that should be interpolated from multiple values provided in json file
            # (reference years and corresponding values)
            elif x + "_reference_years" in json_parameters_dict.keys():
                self.auto_inputs[x + "_reference_years"] = type(
                    json_parameters_dict[x + "_reference_years"]
                )
                self.auto_inputs[x + "_reference_years_values"] = type(
                    json_parameters_dict[x + "_reference_years_values"]
                )

            # Parameters that are not in parameters.json are assumed to be outputs from other AeroMAPS models
            else:
                self.auto_inputs[x] = (
                    pd.Series
                )
                # TODO: is their a way to robustify this assumption about data type pd.Series?
                # Maybe by first running the other models and checking the data type of the outputs.

        # Dry run with lca_algebraic to build symbolic expressions of LCIA impacts
        print("Parametrizing LCIA impacts...", end=" ")
        self.lambdas = agb.lca._preMultiLCAAlgebric(self.model, self.methods, axis=self.axis)
        print("Done.")

        # Add the auto-generated outputs to the AeroMAPSModel
        # FIXME: this is a temporary solution. Not defining explicitly the output type cause issue since gemseo is expecting a np.ndarray or pd.Series as output type.
        self.auto_outputs = {"outputs_lca": xr.DataArray}

        # Alternative?
        # This doesn't work for now because the return value of compute() must be a tuple of explicit variables
        # self.auto_outputs = dict()
        # for i, method in enumerate(self.methods):
        #    if self.lambdas[0].axis_keys:
        #        for j, phase in enumerate(self.lambdas[0].axis_keys):
        #            self.auto_outputs[f"ImpactScore_Method_{i}_Axis_{j}"] = pd.Series
        #    else:
        #        self.auto_outputs[f"ImpactScore_Method_{i}"] = pd.Series

    def compute(
        self, **kwargs
    ) -> xr.DataArray:  # Python 3.9+: use builtins tuple instead of Tuple from typing lib
        # Assign values to parameters
        for name in self.params_names:
            # KEY_YEAR is a special parameter treated separately
            if name == KEY_YEAR:
                self.params_dict[name] = list(range(self.prospection_start_year, self.end_year + 1))
                # replace by self.data["years"]["prospective_years"] ?

            # String parameter
            elif isinstance(kwargs.get(name), str):
                self.params_dict[name] = kwargs[name]

            # Single float value
            elif isinstance(kwargs.get(name), float):
                self.params_dict[name] = kwargs[name]

            # Multiple values
            elif isinstance(kwargs.get(name), (list, np.ndarray, pd.Series)):
                param_values = kwargs[name].copy()
                # Check if the length of the parameter values is consistent with the years
                if len(param_values) > self.end_year - self.prospection_start_year + 1:
                    param_values = param_values[
                        -(self.end_year - self.prospection_start_year + 1) :
                    ]
                elif len(param_values) < self.end_year - self.prospection_start_year + 1:
                    raise ValueError(
                        f"Parameter '{name}' has not enough values for the simulation period."
                    )
                self.params_dict[name] = np.nan_to_num(param_values)

            # Parameters that should be interpolated from multiple values provided in json file
            # (reference years and corresponding values)
            elif name + "_reference_years" in kwargs and name + "_reference_years_values" in kwargs:
                param_values = AeromapsInterpolationFunction(
                    self,
                    kwargs[name + "_reference_years"],
                    kwargs[name + "_reference_years_values"],
                    model_name=self.name,
                )
                param_values = param_values.loc[self.prospection_start_year:self.end_year].values
                self.params_dict[name] = np.nan_to_num(param_values)

            # else: the parameter is not provided and will be set to its default value.
            else:
                raise UserWarning(f'Value for LCA parameter "{name}" is not provided. Default value will be used.')

        # Calculate impacts for all parameters at once
        res = self.multiLCAAlgebraicRaw(**self.params_dict)

        # Set the year as the 'x' axis and rename
        res["params"] = self.params_dict[KEY_YEAR]
        res = res.rename({"params": KEY_YEAR})

        # Store xarray to enable user to access data after process calculation
        self.xarray_lca = outputs_lca = res

        # Test: convert xarray to pd.Series to enable connection with other models.
        # Convert each (impact, axis) pair into a pd.Series
        # if self.lambdas[0].axis_keys:
        #    outputs_lca = tuple([
        #        res.sel(impacts=impact, axis=ax).to_series()
        #        for impact in res.coords["impacts"].values
        #        for ax in res.coords["axis"].values
        #    ])
        # else:
        #    outputs_lca = tuple([
        #        res.sel(impacts=impact).to_series() for impact in res.coords["impacts"].values
        #    ])
        # Issue to solve: how to set return with explicit variables? E.g. return tuple(outputs_lca) doesn't work.
        # It has to be for example return (my_var1, my_var2, my_var3, ..., my_var_n) with each variable being a pd.Series or ndarray.

        return outputs_lca

    def multiLCAAlgebraicRaw(self, **params):
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

    def compute_impacts_from_lambdas(
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
