# @Time : 22/02/2023 16:01
# @Author : a.salgas
# @File : biofuel.py
# @Software: PyCharm
from typing import Tuple

import numpy as np
import pandas as pd
from pandas import Series

from aeromaps.models.base import AeroMAPSModel, AeromapsInterpolationFunction


class ElectrofuelCostSimple(AeroMAPSModel):
    def __init__(self, name="electrofuel_cost_simple", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        energy_consumption_electrofuel: pd.Series = pd.Series(dtype="float64"),
        electrofuel_emission_factor: pd.Series = pd.Series(dtype="float64"),
        electrofuel_mfsp: pd.Series = pd.Series(dtype="float64"),
        carbon_tax: pd.Series = pd.Series(dtype="float64"),
        lhv_electrofuel: float = 0.0,
        density_electrofuel: float = 0.0,
    ) -> tuple[
        Series,
        Series,
        Series,

    ]:
        ### HEFA FOG
        
        electrofuel_cost = electrofuel_mfsp * density_electrofuel / lhv_electrofuel * energy_consumption_electrofuel /1e6
        self.df.loc[:, "electrofuel_cost"] = electrofuel_cost

        electrofuel_carbon_tax = (
                energy_consumption_electrofuel
                * electrofuel_emission_factor
                / 1000000
                * carbon_tax
                / 1000000
        )
        self.df.loc[:, "electrofuel_carbon_tax"] = electrofuel_carbon_tax

        electrofuel_mfsp_carbon_tax_supplement = (
                carbon_tax * electrofuel_emission_factor / 1000000 * lhv_electrofuel * density_electrofuel
        )
        self.df.loc[
            :, "electrofuel_mfsp_carbon_tax_supplement"
        ] = electrofuel_mfsp_carbon_tax_supplement

        

        return (
            electrofuel_cost,
            electrofuel_carbon_tax,
            electrofuel_mfsp_carbon_tax_supplement,
        )



class ElectrofuelMfsp(AeroMAPSModel):
    def __init__(self, name="biofuel_mfsp", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        electrofuel_mfsp_reference_years: list = [],
        electrofuel_mfsp_reference_years_values: list = [],
    ) -> Tuple[pd.Series,]:
        """Electrofuel MFSP (Minimal fuel selling price) estimates"""

        # HEFA FOG
        electrofuel_mfsp = AeromapsInterpolationFunction(
            self,
            electrofuel_mfsp_reference_years,
            electrofuel_mfsp_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "electrofuel_mfsp"] = electrofuel_mfsp

       

        return (
            electrofuel_mfsp,
        )