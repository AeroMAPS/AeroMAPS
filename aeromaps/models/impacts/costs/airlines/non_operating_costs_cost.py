from typing import Tuple

import pandas as pd

from aeromaps.models.base import AeromapsModel, AeromapsInterpolationFunction


class PassengerAircraftNocCarbonOffset(AeromapsModel):
    # TODO move into Indirect Operating Costs (IOC)?
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

        noc_carbon_offset_per_ask = carbon_offset * carbon_offset_price * 10 ** 6 / ask

        self.df.loc[:, "noc_carbon_offset_per_ask"] = noc_carbon_offset_per_ask

        return (carbon_offset_price, noc_carbon_offset_per_ask)


class PassengerAircraftNonOpCosts(AeromapsModel):
    def __init__(self, name="passenger_aircraft_noc", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
            self,
            noc_reference_years: list = [],
            noc_reference_years_values: list = [],
    ) -> Tuple[pd.Series]:
        # Simple computation of airline non-operating costs (NOC)

        # TODO calibrate NOC values in parameters.json
        noc_prospective = AeromapsInterpolationFunction(
            self,
            noc_reference_years,
            noc_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "non_operating_cost_per_ask"] = noc_prospective
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "non_operating_cost_per_ask"] = self.df.loc[
                self.prospection_start_year, "non_operating_cost_per_ask"
            ]
        non_operating_cost_per_ask = self.df["non_operating_cost_per_ask"]
        return non_operating_cost_per_ask
