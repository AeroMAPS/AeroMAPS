"""
Model for Life Cycle Assessment (LCA) of air transportation systems
"""

from aeromaps.models.base import AeroMAPSModel, AeromapsInterpolationFunction
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
from aeromaps.core.process import default_parameters_path
from aeromaps.models.parameters import Parameters


class LifeCycleAssessment(AeroMAPSModel):
    def __init__(self, name="life_cycle_assessment", reset: bool = False, *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        _, model, methods = LCAProblemConfigurator(CONFIGURATION_FILE).generate(reset=reset)
        self.model = model
        self.methods = methods

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


        #    [item for x in agb.all_params().keys() for item in
        #                      (x + '_reference_years', x + '_reference_years_values') if x not in [KEY_YEAR]]

    def compute(
            self,
            **kwargs
    ) -> Tuple[pd.Series, ...]:  # Python 3.9+: use builtins tuple instead of Tuple from typing lib

        # Parameters interpolation and assignment
        for name in self.params_names:
            if name == KEY_YEAR:  # temporal parameter
                self.params_dict[name] = list(range(self.prospection_start_year, self.end_year + 1))  # replace by self.data["years"]["prospective_years"] ?

            # TODO: better handling of non-float parameters
            elif any(isinstance(elem, str) for elem in kwargs.get(f'{name}_reference_years_values', [])):  # non-float parameters
                self.params_dict[name] = kwargs[f'{name}_reference_years_values']

            else:
                if f'{name}_reference_years' in kwargs and f'{name}_reference_years_values' in kwargs:  # input data provided in parameters.json
                    param_values = AeromapsInterpolationFunction(
                        self,
                        kwargs[f'{name}_reference_years'],
                        kwargs[f'{name}_reference_years_values'],
                        model_name=self.name,
                    )
                    # param_values = param_values[self.prospection_start_year - self.historic_start_year:]  # remove interpolated values before the start of prospective start year (these are NaNs)
                    # self.params_dict[name] = np.nan_to_num(param_values)
                else:  # data calculated by previous AeroMAPS models
                    param_values = kwargs[name]
                if len(param_values) != self.end_year - self.prospection_start_year + 1:
                    param_values = param_values[self.prospection_start_year - self.historic_start_year:]
                param_values = np.nan_to_num(param_values)
                self.params_dict[name] = param_values

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

        series_list = tuple(series_list)  # convert list to tuple
        # (*series_list,)

        return series_list  # TODO: replace by explicit names of each impact category to enable automatic connection with other disciplines (c.f. gemseo.py)