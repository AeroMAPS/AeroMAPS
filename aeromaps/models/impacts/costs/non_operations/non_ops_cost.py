from typing import Tuple

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from aeromaps.models.base import AeromapsModel


class PassengerAircraftNocCarbonOffset(AeromapsModel):
    def __init__(
        self, name="passenger_aircraft_noc_carbon_offset", fleet_model=None, *args, **kwargs
    ):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        carbon_offset: pd.Series = pd.Series(dtype="float64"),
        ask: pd.Series = pd.Series(dtype="float64"),
        carbon_offset_price_reference_years: list = [],
        carbon_offset_price_reference_years_values: list = [],
    ) -> Tuple[pd.Series, pd.Series]:

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "carbon_offset_price"] = 0.0

        if len(carbon_offset_price_reference_years) == 0:
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[k, "carbon_offset_price"] = carbon_offset_price_reference_years_values
        else:
            carbon_offset_price_function = interp1d(
                carbon_offset_price_reference_years,
                carbon_offset_price_reference_years_values,
                kind="linear",
            )
            for k in range(self.prospection_start_year, self.end_year + 1):
                self.df.loc[k, "carbon_offset_price"] = carbon_offset_price_function(k)

        carbon_offset_price = self.df["carbon_offset_price"]

        noc_carbon_offset_per_ask = carbon_offset * carbon_offset_price * 10**6 / ask

        self.df.loc[:, "noc_carbon_offset_per_ask"] = noc_carbon_offset_per_ask

        return (carbon_offset_price, noc_carbon_offset_per_ask)
