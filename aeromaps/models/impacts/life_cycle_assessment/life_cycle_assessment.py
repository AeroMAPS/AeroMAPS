"""
Model for Life Cycle Assessment (LCA) of air transportation systems
"""

from aeromaps.models.base import AeromapsModel, AeromapsInterpolationFunction
import pandas as pd
import numpy as np
import lca_algebraic as agb
from aeromaps.models.impacts.life_cycle_assessment.configuration import LCAProblemConfigurator
import os.path as pth
DATA_FOLDER = './data/lca_data'
CONFIGURATION_FILE = pth.join(DATA_FOLDER, 'configuration_methodo_ei391.yaml')
from typing import Tuple
KEY_YEAR = 'year'
KEY_AXIS = 'phase'
KEY_METHOD = 'method'


class LifeCycleAssessment(AeromapsModel):
    def __init__(self, name="life_cycle_assessment", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        _, model, methods = LCAProblemConfigurator(CONFIGURATION_FILE).generate()
        self.model = model
        self.methods = methods

        self.params_names = agb.all_params().keys()
        self.params_dict = dict()
        self.custom_inputs = [item for x in agb.all_params().keys() for item in
                              (x + '_reference_years', x + '_reference_years_values') if x not in [KEY_YEAR]]  # For gemseo inputs

    def compute(
            self,
            **kwargs
    ) -> Tuple[pd.Series, ...]:  # Python 3.9+: use builtins tuple instead of Tuple from typing lib

        # Parameters interpolation and assignment
        for name in self.params_names:
            if name == KEY_YEAR:
                self.params_dict[name] = [year for year in range(self.prospection_start_year, self.end_year + 1)]
            elif any(isinstance(elem, str) for elem in kwargs[f'{name}_reference_years_values']):
                # TODO: expand list of non-float values to match the length of interpolated years?
                self.params_dict[name] = kwargs[f'{name}_reference_years_values']
            else:
                param_values = AeromapsInterpolationFunction(
                    self,
                    kwargs[f'{name}_reference_years'],
                    kwargs[f'{name}_reference_years_values'],
                    model_name=self.name,
                )
                param_values = param_values[self.prospection_start_year - self.historic_start_year:]  # remove interpolated values before the start of prospective start year (these are NaNs)
                self.params_dict[name] = np.nan_to_num(param_values)

        # LCIA calculation
        multi_df_lca = pd.DataFrame()  # Create empty DataFrame to store the results for each impact method and year

        # Calculate impacts for each year
        # (this is a temporary solution waiting for lca_algebraic to handle both 'axis' and multi params simultaneously)
        for i, year in enumerate(self.params_dict[KEY_YEAR]):
            parameters_tmp = self.params_dict.copy()
            # Get the value of each parameter for the current year
            for key, val in parameters_tmp.items():
                if isinstance(val, (list, np.ndarray)):
                    parameters_tmp[key] = val[i]

            # Calculate impacts for the current year
            res = agb.compute_impacts(
                self.model,
                self.methods,
                axis=KEY_AXIS,
                **parameters_tmp,
            )

            # Buidl MultiIndex DataFrame by iterating over each method
            df_year = pd.DataFrame()  # DataFrame for the results of each impact method for the current year
            for method in res.columns:
                # Extract the results for the current method
                data = res[method]
                # Create a DataFrame with MultiIndex consisting of method and year
                df_year_method = pd.DataFrame(data.values, columns=[year],
                                              index=pd.MultiIndex.from_product([[method], data.index],
                                                                               names=[KEY_METHOD, KEY_AXIS]))
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

        return tuple(series_list)

    # def compute_old(
    #         self,
    #         share_efuel_reference_years: list = [],
    #         share_efuel_reference_years_values: list = [],
    #         #param_2: pd.Series = pd.Series(dtype="float64"),
    #         #param_3: pd.Series = pd.Series(dtype="float64"),
    # ) -> Tuple[pd.Series, ...]:  # Python 3.9+: use builtins tuple instead of Tuple from typing lib
    #
    #     # Parameters interpolation and assignment
    #     args = locals().copy()
    #     args.pop('self')
    #     for key, val in args.items():
    #         param_name = key.split('_reference')[0]
    #         if param_name in self.lca_params:
    #             continue
    #         # TODO: deal with enum params (not floats)
    #         param_values = AeromapsInterpolationFunction(
    #             self,
    #             args[f'{param_name}_reference_years'],
    #             args[f'{param_name}_reference_years_values'],
    #             model_name=self.name,
    #         )
    #         self.lca_params[param_name] = np.nan_to_num(param_values)  # replace NaNs by 0s
    #
    #     # LCIA calculation
    #     res = agb.compute_impacts(
    #         self.model,
    #         self.methods,
    #         **self.lca_params
    #     )
    #
    #     # Outputs
    #     outputs_list = list()
    #     for cat in res.columns:
    #         temporal_impacts = pd.Series(res.loc[:, cat].values, index=self.df.index)
    #         self.df.loc[:, cat] = temporal_impacts  # TODO: replace by df_lca
    #         outputs_list.append(temporal_impacts)
    #
    #     return outputs_list