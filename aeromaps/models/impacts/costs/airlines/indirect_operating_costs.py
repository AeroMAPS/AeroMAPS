# @Time : 04/01/2024 15:20
# @Author : a.salgas
# @File : indirect_operating_costs.py
# @Software: PyCharm

from typing import Tuple
import pandas as pd
from aeromaps.models.base import AeromapsModel, AeromapsInterpolationFunction



class PassengerAircraftIndirectOpCosts(AeromapsModel):
    def __init__(self, name="passenger_aircraft_ioc", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
            self,
            ioc_reference_years: list = [],
            ioc_reference_years_values: list = [],
    ) -> Tuple[pd.Series]:
        # Simple computation of airline non-operating costs (NOC)

        # TODO calibrate IOC values in parameters.json
        ioc_prospective = AeromapsInterpolationFunction(
            self,
            ioc_reference_years,
            ioc_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "indirect_operating_cost_per_ask"] = ioc_prospective
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "indirect_operating_cost_per_ask"] = self.df.loc[
                self.prospection_start_year, "indirect_operating_cost_per_ask"
            ]
        indirect_operating_cost_per_ask = self.df["indirect_operating_cost_per_ask"]
        return indirect_operating_cost_per_ask


