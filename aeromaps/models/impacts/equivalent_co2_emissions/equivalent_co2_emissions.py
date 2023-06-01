from typing import Tuple
import numpy as np
import pandas as pd

from aeromaps.models.base import AeromapsModel


class EquivalentCO2Emissions(AeromapsModel):
    def __init__(self, name="equivalent_co2_emissions", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        total_erf: pd.Series = pd.Series(dtype="float64"),
        co2_erf: pd.Series = pd.Series(dtype="float64"),
        co2_emissions: pd.Series = pd.Series(dtype="float64"),
        erf_coefficient_co2: float = 0.0,
    ) -> Tuple[
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
    ]:
        """Equivalent CO2 emissions calculation using smoothed data and GWP* method."""

        # Smooth on 5 years (except for extrem values)

        self.df["total_erf_smooth"] = total_erf
        self.df["co2_erf_smooth"] = co2_erf
        self.df["co2_emissions_smooth"] = co2_emissions

        for k in range(self.historic_start_year + 2, self.end_year - 1):
            self.df.loc[k, "total_erf_smooth"] = (
                total_erf.loc[k - 2]
                + total_erf.loc[k - 1]
                + total_erf.loc[k]
                + total_erf.loc[k + 1]
                + total_erf.loc[k + 2]
            ) / 5
            self.df.loc[k, "co2_erf_smooth"] = (
                co2_erf.loc[k - 2]
                + co2_erf.loc[k - 1]
                + co2_erf.loc[k]
                + co2_erf.loc[k + 1]
                + co2_erf.loc[k + 2]
            ) / 5
            self.df.loc[k, "co2_emissions_smooth"] = (
                co2_emissions.loc[k - 2]
                + co2_emissions.loc[k - 1]
                + co2_emissions.loc[k]
                + co2_emissions.loc[k + 1]
                + co2_emissions.loc[k + 2]
            ) / 5

        # Cumulative CO2 smooth emissions(Gtwe)
        self.df.loc[self.prospection_start_year - 1, "cumulative_co2_emissions_smooth"] = 0.0
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "cumulative_co2_emissions_smooth"] = (
                self.df.loc[k - 1, "cumulative_co2_emissions_smooth"]
                + self.df.loc[k, "co2_emissions_smooth"] / 1000
            )

        total_erf_smooth = self.df["total_erf_smooth"]
        co2_erf_smooth = self.df["co2_erf_smooth"]
        co2_emissions_smooth = self.df["co2_emissions_smooth"]
        cumulative_co2_emissions_smooth = self.df["cumulative_co2_emissions_smooth"]

        # DeltaF/Deltat
        for k in range(self.historic_start_year, self.end_year + 1):
            self.df.loc[k, "non_co2_erf_smooth"] = (
                self.df.loc[k, "total_erf_smooth"] - self.df.loc[k, "co2_erf_smooth"]
            )
        gwpstar_variation_duration = 20
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "non_co2_erf_smooth_variation"] = (
                self.df.loc[k, "non_co2_erf_smooth"]
                - self.df.loc[k - gwpstar_variation_duration, "non_co2_erf_smooth"]
            ) / gwpstar_variation_duration
        non_co2_erf_smooth = self.df["non_co2_erf_smooth"]
        non_co2_erf_smooth_variation = self.df["non_co2_erf_smooth_variation"]

        # Non-CO2 equivalent emissions (Mtwe)
        climate_time_frame = 100
        co2_absolute_global_warming_potential = erf_coefficient_co2 * 100 / 1000
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "non_co2_equivalent_emissions"] = (
                self.df.loc[k, "non_co2_erf_smooth_variation"]
                * climate_time_frame
                / co2_absolute_global_warming_potential
            )
        non_co2_equivalent_emissions = self.df["non_co2_equivalent_emissions"]

        # Cumulative non-CO2 equivalent emissions (Gtwe)
        self.df.loc[
            self.prospection_start_year - 1, "cumulative_non_co2_equivalent_emissions"
        ] = 0.0
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "cumulative_non_co2_equivalent_emissions"] = (
                self.df.loc[k - 1, "cumulative_non_co2_equivalent_emissions"]
                + self.df.loc[k, "non_co2_equivalent_emissions"] / 1000
            )
        cumulative_non_co2_equivalent_emissions = self.df["cumulative_non_co2_equivalent_emissions"]

        # Equivalent emissions (Mtwe)
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "total_equivalent_emissions"] = (
                self.df.loc[k, "non_co2_equivalent_emissions"]
                + self.df.loc[k, "co2_emissions_smooth"]
            )
        total_equivalent_emissions = self.df["total_equivalent_emissions"]

        # Cumulative equivalent emissions (Gtwe)
        self.df.loc[self.prospection_start_year - 1, "cumulative_total_equivalent_emissions"] = 0.0
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "cumulative_total_equivalent_emissions"] = (
                self.df.loc[k - 1, "cumulative_total_equivalent_emissions"]
                + self.df.loc[k, "total_equivalent_emissions"] / 1000
            )
        cumulative_total_equivalent_emissions = self.df["cumulative_total_equivalent_emissions"]

        self.cumulative_total_equivalent_emissions_end_year = self.df.loc[
            self.end_year, "cumulative_total_equivalent_emissions"
        ]  # A voir avec Scott

        # Share CO2/non-CO2
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "total_co2_equivalent_emissions_ratio"] = (
                self.df.loc[k, "total_equivalent_emissions"]
                / self.df.loc[k, "co2_emissions_smooth"]
            )
        total_co2_equivalent_emissions_ratio = self.df["total_co2_equivalent_emissions_ratio"]

        co2_total_erf_ratio = co2_erf / total_erf * 100
        self.df.loc[:, "co2_total_erf_ratio"] = co2_total_erf_ratio

        return (
            total_erf_smooth,
            co2_erf_smooth,
            co2_emissions_smooth,
            cumulative_co2_emissions_smooth,
            non_co2_erf_smooth,
            non_co2_erf_smooth_variation,
            non_co2_equivalent_emissions,
            cumulative_non_co2_equivalent_emissions,
            total_equivalent_emissions,
            cumulative_total_equivalent_emissions,
            total_co2_equivalent_emissions_ratio,
            co2_total_erf_ratio,
        )
