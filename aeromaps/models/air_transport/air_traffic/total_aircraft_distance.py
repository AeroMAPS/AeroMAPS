import pandas as pd
from pandas import read_csv
import os.path as pth

from aeromaps.models.base import AeromapsModel
from aeromaps.resources import data


class TotalAircraftDistance(AeromapsModel):
    def __init__(self, name="total_aircraft_distance", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        # Load dataset
        historical_dataset_path = pth.join(data.__path__[0], "temperature_historical_dataset.csv")
        historical_dataset_df = read_csv(historical_dataset_path, delimiter=";")
        self.historical_dataset = historical_dataset_df.values

    def compute(
        self,
        rpk: pd.Series = pd.Series(dtype="float64"),
        total_aircraft_distance_init: pd.Series = pd.Series(dtype="float64"),
    ) -> pd.Series:
        """Total aircraft distance calculation."""

        historical_distance_for_temperature = self.historical_dataset[:, 6]

        for k in range(self.climate_historic_start_year, self.historical_dataset):
            self.df_climate.loc[k, "total_aircraft_distance"] = historical_distance_for_temperature[
                k - self.climate_historic_start_year
            ]

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df_climate.loc[k, "total_aircraft_distance"] = total_aircraft_distance_init.loc[k]

        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df_climate.loc[k, "total_aircraft_distance"] = (
                rpk.loc[k]
                / rpk.loc[self.prospection_start_year - 1]
                * self.df_climate.loc[self.prospection_start_year - 1, "total_aircraft_distance"]
            )

        total_aircraft_distance = self.df_climate["total_aircraft_distance"]

        return total_aircraft_distance
