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


class LifeCycleAssessment(AeromapsModel):
    def __init__(self, name="life_cycle_assessment", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        _, model, methods = LCAProblemConfigurator(CONFIGURATION_FILE).generate()
        # TODO: preLCAALgebraic here to pre-compute LCIA functions
        # TODO : list_parameters() here to get all LCA parameters and set them as inputs of compute() method
        self.model = model
        self.methods = methods
        # self.lca_params = dict()

        self.params_dict = agb.all_params()
        self.custom_inputs = [item for x in agb.all_params().keys() for item in
                              (x + '_reference_years', x + '_reference_years_values')]  # For gemseo inputs

    def compute(
            self,
            **kwargs
    ) -> Tuple[pd.Series, ...]:  # Python 3.9+: use builtins tuple instead of Tuple from typing lib

        params_dict = {}

        # Parameters interpolation and assignment
        for name in self.params_dict.keys():
            if any(isinstance(elem, str) for elem in kwargs[f'{name}_reference_years_values']):
                # TODO: expand list of values to match the length of interpolated years
                self.params_dict[name] = kwargs[f'{name}_reference_years_values']
            else:
                param_values = AeromapsInterpolationFunction(
                    self,
                    kwargs[f'{name}_reference_years'],
                    kwargs[f'{name}_reference_years_values'],
                    model_name=self.name,
                )
                self.params_dict[name] = np.nan_to_num(param_values)  # replace NaNs by 0s

        # LCIA calculation
        res = agb.compute_impacts(
            self.model,
            self.methods,
            **self.params_dict
        )

        # Outputs
        outputs_list = list()
        for cat in res.columns:
            temporal_impacts = pd.Series(res.loc[:, cat].values, index=self.df.index)
            self.df.loc[:, cat] = temporal_impacts  # TODO: replace by df_lca
            outputs_list.append(temporal_impacts)

        return outputs_list

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