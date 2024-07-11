"""
Model for Life Cycle Assessment (LCA) of air transportation systems
"""

from aeromaps.models.base import AeroMAPSModel, AeromapsInterpolationFunction
import pandas as pd
import numpy as np
import lca_algebraic as agb
#from aeromaps.models.impacts.life_cycle_assessment.configuration import LCAProblemConfigurator
from lcav.io.configuration import LCAProblemConfigurator
import os.path as pth
DATA_FOLDER = './data/lca_data'
CONFIGURATION_FILE = pth.join(DATA_FOLDER, 'configuration_methodo_ei391.yaml')
from typing import Tuple
KEY_YEAR = 'year'
KEY_METHOD = 'method'
from aeromaps.core.process import default_parameters_path
from aeromaps.models.parameters import Parameters
from typing import Dict


class LifeCycleAssessment(AeroMAPSModel):
    def __init__(self, name="life_cycle_assessment", reset: bool = False, *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

        # Get LCA model and LCIA methods
        _, model, methods = LCAProblemConfigurator(CONFIGURATION_FILE).generate(reset=reset)
        self.model = model
        self.methods = methods
        self.axis = 'phase'
        self.params_names = agb.all_params().keys()
        self.params_dict = dict()

        # Automatically add LCA parameters as inputs of this AeroMAPSModel. See gemseo.py for more details.
        self.custom_inputs = list()
        json_file_parameters = Parameters()
        json_file_parameters.read_json(file_name=default_parameters_path)
        for x in agb.all_params().keys():
            if x == KEY_YEAR:
                continue
            if x + '_reference_years' in json_file_parameters.to_dict().keys():
                self.custom_inputs += [x + '_reference_years', x + '_reference_years_values']
            else:
                self.custom_inputs += [x]

        # Dry run with lca_algebraic to build symbolic expressions of LCIA impacts
        print('Parametrizing LCIA impacts...', end=' ')
        self.lambdas = agb.lca._preMultiLCAAlgebric(self.model, self.methods, axis=self.axis)
        print('Done.')

    def compute(
            self,
            **kwargs
    ) -> Tuple[pd.Series, ...]:  # Python 3.9+: use builtins tuple instead of Tuple from typing lib

        # Parameters interpolation and assignment
        for name in self.params_names:
            if name == KEY_YEAR:  # temporal parameter
                self.params_dict[name] = list(range(self.prospection_start_year, self.end_year + 1))  # replace by self.data["years"]["prospective_years"] ?

            # Single float value (constant)
            elif isinstance(kwargs.get(f'{name}_reference_years_values', []), float):  # single float
                self.params_dict[name] = kwargs[f'{name}_reference_years_values']

            # TODO: better handling of non-float parameters?
            # String parameters
            elif any(isinstance(elem, str) for elem in kwargs.get(f'{name}_reference_years_values', [])):
                self.params_dict[name] = kwargs[f'{name}_reference_years_values']

            # Multiple float values (--> interpolate)
            else:
                # Input data provided in parameters.json
                if f'{name}_reference_years' in kwargs and f'{name}_reference_years_values' in kwargs:
                    param_values = AeromapsInterpolationFunction(
                        self,
                        kwargs[f'{name}_reference_years'],
                        kwargs[f'{name}_reference_years_values'],
                        model_name=self.name,
                    )  # pd.Series of interpolated values
                    param_values = param_values.loc[self.prospection_start_year: self.end_year].values
                # Output from previous AeroMAPS models
                else:
                    param_values = kwargs[name]
                # Check if the length of the parameter values is consistent with the years
                if isinstance(param_values, (list, np.ndarray)):
                    if len(param_values) != self.end_year - self.prospection_start_year + 1:
                        param_values = param_values[self.prospection_start_year - self.historic_start_year:]
                param_values = np.nan_to_num(param_values)
                self.params_dict[name] = param_values

        #print(self.params_dict)

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
            #res = agb.compute_impacts(
            #    self.model,
            #    self.methods,
            #    axis=self.axis,
            #    **parameters_tmp,
            #)
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
        # (*series_list,)

        # TODO: replace by xplicit names of each impact cat to enable auto connection with other models (c.f. gemseo.py)
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