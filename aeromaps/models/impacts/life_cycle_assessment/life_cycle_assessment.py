"""
Model for Life Cycle Assessment (LCA) of air transportation systems
"""

from aeromaps.models.base import AeroMAPSModel, AeromapsInterpolationFunction
import pandas as pd
import numpy as np
import lca_algebraic as agb
from lcav.io.configuration import LCAProblemConfigurator
from typing import Tuple
KEY_YEAR = 'year'
KEY_METHOD = 'method'
from aeromaps.core.process import default_parameters_path
from aeromaps.models.parameters import Parameters
from typing import Dict


class LifeCycleAssessment(AeroMAPSModel):
    def __init__(self, name: str = "life_cycle_assessment", configuration_file: str = None, split_by: str = None, *args, **kwargs):
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

        # Automatically add LCA parameters (except strings) as inputs of this AeroMAPSModel.
        # See gemseo.py for more details about addition of auto-generated inputs.
        self.auto_inputs = dict()
        json_file_parameters = Parameters()
        json_file_parameters.read_json(file_name=default_parameters_path)
        json_parameters_dict = json_file_parameters.to_dict()

        for x in self.params_names:

            # KEY_YEAR is a special parameter treated separately
            if x == KEY_YEAR:
                continue

            # Inputs provided in parameters.json
            elif x in json_parameters_dict.keys():
                value = json_parameters_dict[x]

                # String inputs are directly stored in the params_dict
                if isinstance(value, str):
                    self.params_dict[x] = value
                elif isinstance(value, list) and any(isinstance(elem, str) for elem in value):
                    self.params_dict[x] = value

                # Float parameters are stored in the auto_inputs dict
                # to be automatically added as inputs of the AeroMAPSModel
                else:
                    self.auto_inputs[x] = type(value)

            # Parameters that should be interpolated from multiple values provided in parameters.json
            # (reference years and corresponding values)
            elif x + '_reference_years' in json_parameters_dict.keys():
                self.auto_inputs[x + '_reference_years'] = type(json_parameters_dict[x + '_reference_years'])
                self.auto_inputs[x + '_reference_years_values'] = type(json_parameters_dict[x + '_reference_years_values'])

            # Parameters that are not in parameters.json are assumed to be outputs from other AeroMAPS models
            else:
                self.auto_inputs[x] = pd.Series  # TODO: is their a way to robustify this assumption?

        # Dry run with lca_algebraic to build symbolic expressions of LCIA impacts
        print('Parametrizing LCIA impacts...', end=' ')
        self.lambdas = agb.lca._preMultiLCAAlgebric(self.model, self.methods, axis=self.axis)
        print('Done.')

        # Add the auto-generated outputs to the AeroMAPSModel
        self.auto_outputs = dict()
        self.auto_outputs["series_list"] = tuple

        # TODO: explicitly define the outputs (with their types, e.g. pd.Series) of the model
        #for i, method in enumerate(self.methods):
        #    if self.lambdas[0].axis_keys:
        #        for j, phase in enumerate(self.lambdas[0].axis_keys):
        #            self.auto_outputs[f"ImpactScore_Method_{i}_Phase_{j}"] = pd.Series
        #    else:
        #        self.auto_outputs[f"ImpactScore_Method_{i}"] = pd.Series
            #TODO: change names to be pythonic (no spaces, no special characters, etc.)

    def compute(
            self,
            **kwargs
    ) -> Tuple[pd.Series, ...]:  # Python 3.9+: use builtins tuple instead of Tuple from typing lib

        # Assign values to parameters
        for name in self.params_names:

            # KEY_YEAR is a special parameter treated separately
            if name == KEY_YEAR:
                self.params_dict[name] = list(range(self.prospection_start_year, self.end_year + 1))
                # replace by self.data["years"]["prospective_years"] ?

            # Single float value
            elif isinstance(kwargs.get(name), float):
                self.params_dict[name] = kwargs[name]

            # Multiple float values
            elif isinstance(kwargs.get(name), (list, np.ndarray, pd.Series)):
                param_values = kwargs[name].copy()
                # Check if the length of the parameter values is consistent with the years
                if len(param_values) > self.end_year - self.prospection_start_year + 1:
                    param_values = param_values[- (self.end_year - self.prospection_start_year + 1):]
                elif len(param_values) < self.end_year - self.prospection_start_year + 1:
                    raise ValueError(f"Parameter '{name}' has not enough values for the simulation period.")
                self.params_dict[name] = np.nan_to_num(param_values)
                # TODO: nan_to_num is a weird way to convert pd.Series to lists. Should be done in a more explicit way.

            # Parameters that should be interpolated from multiple values provided in parameters.json
            # (reference years and corresponding values)
            elif name + '_reference_years' in kwargs and name + '_reference_years_values' in kwargs:
                param_values = AeromapsInterpolationFunction(
                    self,
                    kwargs[name + '_reference_years'],
                    kwargs[name + '_reference_years_values'],
                    model_name=self.name,
                )
                param_values = param_values.loc[self.prospection_start_year: self.end_year].values
                self.params_dict[name] = np.nan_to_num(param_values)

            # else: the parameter is not provided and will be set to its default value.
            # This is typically the case for non-float parameters that are set in __init__

        # LCIA calculation
        multi_df_lca = pd.DataFrame()  # Create empty DataFrame to store the results for each impact method and year

        # Calculate impacts for each year
        # FIXME: this is a temporary solution waiting for lca_algebraic to handle 'axis' and multi params simultaneously
        parameters_tmp = self.params_dict.copy()
        for i, year in enumerate(self.params_dict[KEY_YEAR]):
            # Get the value of each parameter for the current year
            for key, val in self.params_dict.items():
                if isinstance(val, (list, np.ndarray)):
                    parameters_tmp[key] = val[i]

            # Calculate impacts for the current year
            res = self.compute_impacts_from_lambdas(**parameters_tmp)

            # Build MultiIndex DataFrame by iterating over each method
            df_year = pd.DataFrame()  # DataFrame for the results of each impact method for the current year
            for method in res.columns:
                # Extract the results for the current method
                data = res[method]
                # Create a DataFrame with MultiIndex consisting of method and year
                df_year_method = pd.DataFrame(data.values, columns=[year],
                                              index=pd.MultiIndex.from_product([[method], data.index],
                                                                               names=[KEY_METHOD, self.axis]))
                # Concatenate the new DataFrame with the existing DataFrame
                df_year = pd.concat([df_year, df_year_method], axis=0)

            # Concatenate the DataFrame with the final LCA DataFrame
            multi_df_lca = pd.concat([multi_df_lca, df_year], axis=1)

        # Outputs : convert the DataFrame to a list of Series
        self.multi_df_lca = multi_df_lca
        series_list = list()
        # Iterate over each row (method, phase) of the DataFrame
        for index, row in multi_df_lca.iterrows():
            # Convert the row to a Pandas Series
            series = row.squeeze()
            # Set the name of the series as the tuple index (method, phase)
            series.name = index
            # Append the series to the list
            series_list.append(series)

        series_list = tuple(series_list)  # convert list to tuple

        # TODO: replace by xplicit names of each impact cat to enable connection with other models (c.f. "auto_outputs")
        return series_list

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

            #lambdas = _preMultiLCAAlgebric(model, methods, alpha=alpha, axis=axis)  # <-- this is the time-consuming part

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