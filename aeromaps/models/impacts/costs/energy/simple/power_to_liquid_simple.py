# @Time : 22/02/2023 16:01
# @Author : a.salgas
# @File : biofuel.py
# @Software: PyCharm
from typing import Tuple

import pandas as pd
from aeromaps.models.base import AeroMAPSModel, AeromapsInterpolationFunction


class ElectrofuelCostSimple(AeroMAPSModel):
    def __init__(self, name="electrofuel_cost_simple", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        energy_consumption_electrofuel: pd.Series,
        electrofuel_emission_factor: pd.Series,
        electrofuel_mean_mfsp_litre: pd.Series,
        carbon_tax: pd.Series,
        lhv_electrofuel: float,
        density_electrofuel: float,
    ) -> Tuple[
        pd.Series,
        pd.Series,
        pd.Series,
    ]:
        electrofuel_total_cost = (
            electrofuel_mean_mfsp_litre
            / density_electrofuel
            / lhv_electrofuel
            * energy_consumption_electrofuel
            / 1e6
        )
        self.df.loc[:, "electrofuel_total_cost"] = electrofuel_total_cost

        electrofuel_carbon_tax = (
            energy_consumption_electrofuel
            * electrofuel_emission_factor
            / 1000000
            * carbon_tax
            / 1000000
        )
        self.df.loc[:, "electrofuel_carbon_tax"] = electrofuel_carbon_tax

        electrofuel_mfsp_carbon_tax_supplement = (
            carbon_tax
            * electrofuel_emission_factor
            / 1000000
            * lhv_electrofuel
            * density_electrofuel
        )
        self.df.loc[:, "electrofuel_mfsp_carbon_tax_supplement"] = (
            electrofuel_mfsp_carbon_tax_supplement
        )

        return (
            electrofuel_total_cost,
            electrofuel_carbon_tax,
            electrofuel_mfsp_carbon_tax_supplement,
        )


class ElectrofuelMfspSimple(AeroMAPSModel):
    def __init__(self, name="electrofuel_mfsp_simple", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        electrofuel_mfsp_simple_reference_years: list,
        electrofuel_mfsp_simple_reference_years_values: list,
    ) -> pd.Series:
        """Electrofuel MFSP (Minimal fuel selling price) estimates"""

        electrofuel_mean_mfsp_litre = AeromapsInterpolationFunction(
            self,
            electrofuel_mfsp_simple_reference_years,
            electrofuel_mfsp_simple_reference_years_values,
            model_name=self.name,
        )

        self.df.loc[:, "electrofuel_mean_mfsp_litre"] = electrofuel_mean_mfsp_litre

        return electrofuel_mean_mfsp_litre
