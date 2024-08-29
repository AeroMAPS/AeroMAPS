import pandas as pd

from aeromaps.models.base import AeroMAPSModel, AeromapsInterpolationFunction


class PassengerAircraftNonOpCosts(AeroMAPSModel):
    def __init__(self, name="passenger_aircraft_noc", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        noc_reference_years: list,
        noc_reference_years_values: list,
    ) -> pd.Series:
        # Simple computation of airline non-operating costs (NOC)
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


class PassengerAircraftPassengerTax(AeroMAPSModel):
    def __init__(self, name="passenger_aircraft_passenger_tax", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        passenger_tax_reference_years: list,
        passenger_tax_reference_years_values: list,
    ) -> pd.Series:
        # Simple computation of airline non-operating costs (NOC)

        passenger_tax_prospective = AeromapsInterpolationFunction(
            self,
            passenger_tax_reference_years,
            passenger_tax_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "passenger_tax_per_ask"] = passenger_tax_prospective
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "passenger_tax_per_ask"] = self.df.loc[
                self.prospection_start_year, "passenger_tax_per_ask"
            ]
        passenger_tax_per_ask = self.df["passenger_tax_per_ask"]
        return passenger_tax_per_ask
