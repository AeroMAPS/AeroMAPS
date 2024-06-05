from typing import Tuple
import pandas as pd
from aeromaps.models.base import AeroMAPSModel


class TotalAircraftDistance(AeroMAPSModel):
    def __init__(self, name="total_aircraft_distance", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        self.climate_historical_data = None

    def compute(
        self,
        rtk: pd.Series,
        ask: pd.Series,
        ask_dropin_fuel: pd.Series,
        ask_hydrogen: pd.Series,
        ask_electric: pd.Series,
        total_aircraft_distance_init: pd.Series,
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
        """Total aircraft distance calculation."""

        historical_distance_for_temperature = self.climate_historical_data[:, 6]

        for k in range(self.climate_historic_start_year, self.historic_start_year):
            self.df_climate.loc[k, "total_aircraft_distance"] = historical_distance_for_temperature[
                k - self.climate_historic_start_year
            ]

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df_climate.loc[k, "total_aircraft_distance"] = total_aircraft_distance_init.loc[k]

        # Assumption: 1 RTK = 10 ASK
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df_climate.loc[k, "total_aircraft_distance"] = (
                (ask.loc[k] + 10 * rtk.loc[k])
                / (
                    ask.loc[self.prospection_start_year - 1]
                    + 10 * rtk.loc[self.prospection_start_year - 1]
                )
                * self.df_climate.loc[self.prospection_start_year - 1, "total_aircraft_distance"]
            )

        total_aircraft_distance = self.df_climate["total_aircraft_distance"]

        # Assumption: distribution proportional to ASK
        total_aircraft_distance_dropin_fuel = total_aircraft_distance * ask_dropin_fuel / ask
        total_aircraft_distance_hydrogen = total_aircraft_distance * ask_hydrogen / ask
        total_aircraft_distance_electric = total_aircraft_distance * ask_electric / ask
        self.df.loc[:, "total_aircraft_distance_dropin_fuel"] = total_aircraft_distance_dropin_fuel
        self.df.loc[:, "total_aircraft_distance_hydrogen"] = total_aircraft_distance_hydrogen
        self.df.loc[:, "total_aircraft_distance_electric"] = total_aircraft_distance_electric

        return (
            total_aircraft_distance,
            total_aircraft_distance_dropin_fuel,
            total_aircraft_distance_hydrogen,
            total_aircraft_distance_electric,
        )
