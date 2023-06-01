from typing import Tuple

import pandas as pd


from aeromaps.models.base import AeromapsModel


class TotalAircraftDistance(AeromapsModel):
    def __init__(self, name="total_aircraft_distance", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        rpk: pd.Series = pd.Series(dtype="float64"),
        total_aircraft_distance_init: pd.Series = pd.Series(dtype="float64"),
    ) -> pd.Series:
        """Total aircraft distance calculation."""

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "total_aircraft_distance"] = total_aircraft_distance_init.loc[k]

        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "total_aircraft_distance"] = (
                rpk.loc[k]
                / rpk.loc[self.prospection_start_year - 1]
                * self.df.loc[self.prospection_start_year - 1, "total_aircraft_distance"]
            )

        total_aircraft_distance = self.df["total_aircraft_distance"]

        return total_aircraft_distance
