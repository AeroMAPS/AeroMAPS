from typing import Tuple
import numpy as np
import pandas as pd

from aeromaps.models.base import AeromapsModel


class Temperature(AeromapsModel):
    def __init__(self, name="temperature", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        TCRE: float = 0.0,
        temperature_increase_from_aviation_init: pd.Series = pd.Series(dtype="float64"),
        cumulative_total_equivalent_emissions: pd.Series = pd.Series(dtype="float64"),
        cumulative_co2_emissions: pd.Series = pd.Series(dtype="float64"),
        co2_emissions: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Temperature calculation using equivalent emissions."""

        # Total temperature

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[
                k, "temperature_increase_from_aviation"
            ] = temperature_increase_from_aviation_init.loc[k]

        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "temperature_increase_from_aviation"] = (
                temperature_increase_from_aviation_init.loc[2019]
                + TCRE * cumulative_total_equivalent_emissions.loc[k]
            )

        temperature_increase_from_aviation = self.df["temperature_increase_from_aviation"]

        # Temperature due to CO2 emissions - Assumption of a third of temperature increase due to CO2

        self.df.loc[2019, "temperature_increase_from_co2_from_aviation"] = (
            temperature_increase_from_aviation_init.loc[2019] / 3
        )

        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "temperature_increase_from_co2_from_aviation"] = (
                self.df.loc[2019, "temperature_increase_from_co2_from_aviation"]
                + TCRE * cumulative_co2_emissions.loc[k]
            )

        for k in reversed(range(self.historic_start_year, self.prospection_start_year - 1)):
            self.df.loc[k, "temperature_increase_from_co2_from_aviation"] = (
                self.df.loc[k + 1, "temperature_increase_from_co2_from_aviation"]
                - TCRE * co2_emissions.loc[k] / 1000
            )

        temperature_increase_from_co2_from_aviation = self.df[
            "temperature_increase_from_co2_from_aviation"
        ]

        # Temperature due to non-CO2 effects

        temperature_increase_from_nonco2_from_aviation = (
            temperature_increase_from_aviation - temperature_increase_from_co2_from_aviation
        )

        self.df.loc[
            :, "temperature_increase_from_nonco2_from_aviation"
        ] = temperature_increase_from_nonco2_from_aviation

        return (
            temperature_increase_from_aviation,
            temperature_increase_from_co2_from_aviation,
            temperature_increase_from_nonco2_from_aviation,
        )
