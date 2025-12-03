"""
total_aircraft_distance
=========================
Module for computing total aircraft distance flown.
"""

from typing import Tuple
import pandas as pd
from aeromaps.models.base import AeroMAPSModel


class TotalAircraftDistance(AeroMAPSModel):
    """
    Class to compute total aircraft distance flown for all commercial air transport.

    Parameters
    ----------
    name : str
        Name of the model instance ('total_aircraft_distance' by default).
    """

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
        """
        Total aircraft distance calculation.

        Parameters
        ----------
        rtk
            Number of Revenue Tonne Kilometer (RTK) for freight air transport [RTK].
        ask
            Number of (ASK) for all commercial air transport [ASK].
        ask_dropin_fuel
            Number of (ASK) for drop-in fuel aircraft [ASK].
        ask_hydrogen
            Number of (ASK) for hydrogen aircraft [ASK].
        ask_electric
            Number of (ASK) for electric aircraft [ASK].
        total_aircraft_distance_init
            Historical total distance travelled by aircraft over 2000-2019 [km].

        Returns
        -------
        total_aircraft_distance
            Total distance flown by all aircraft [km].
        total_aircraft_distance_dropin_fuel
            Total aircraft distance flown by drop-in fuel aircraft [km].
        total_aircraft_distance_hydrogen
            Total aircraft distance flown by hydrogen aircraft [km].
        total_aircraft_distance_electric
            Total aircraft distance flown by electric aircraft [km].
        """

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
