from typing import Tuple

import pandas as pd

from aeromaps.models.base import AeromapsModel, AeromapsInterpolationFunction


class PassengerAircraftNocCarbonOffset(AeromapsModel):
    def __init__(self, name="passenger_aircraft_noc_carbon_offset", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        carbon_offset: pd.Series = pd.Series(dtype="float64"),
        ask: pd.Series = pd.Series(dtype="float64"),
        carbon_offset_price_reference_years: list = [],
        carbon_offset_price_reference_years_values: list = [],
    ) -> Tuple[pd.Series, pd.Series]:

        carbon_offset_price_prospective = AeromapsInterpolationFunction(
            self,
            carbon_offset_price_reference_years,
            carbon_offset_price_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "carbon_offset_price"] = carbon_offset_price_prospective
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "carbon_offset_price"] = 0.0
        carbon_offset_price = self.df["carbon_offset_price"]

        noc_carbon_offset_per_ask = carbon_offset * carbon_offset_price * 10**6 / ask

        self.df.loc[:, "noc_carbon_offset_per_ask"] = noc_carbon_offset_per_ask

        return (carbon_offset_price, noc_carbon_offset_per_ask)
