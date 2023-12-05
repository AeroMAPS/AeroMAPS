from typing import Tuple
import numpy as np
import pandas as pd

from aeromaps.models.base import AeromapsModel, AeromapsEquivalentEmissionsFunction


class EquivalentCO2Emissions(AeromapsModel):
    def __init__(self, name="equivalent_co2_emissions", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        contrails_erf: pd.Series = pd.Series(dtype="float64"),
        nox_short_term_o3_increase_erf: pd.Series = pd.Series(dtype="float64"),
        nox_long_term_o3_decrease_erf: pd.Series = pd.Series(dtype="float64"),
        nox_ch4_decrease_erf: pd.Series = pd.Series(dtype="float64"),
        nox_stratospheric_water_vapor_decrease_erf: pd.Series = pd.Series(dtype="float64"),
        soot_erf: pd.Series = pd.Series(dtype="float64"),
        h2o_erf: pd.Series = pd.Series(dtype="float64"),
        sulfur_erf: pd.Series = pd.Series(dtype="float64"),
        co2_erf: pd.Series = pd.Series(dtype="float64"),
        total_erf: pd.Series = pd.Series(dtype="float64"),
        erf_coefficient_co2: float = 0.0,
        co2_emissions: pd.Series = pd.Series(dtype="float64"),
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
        pd.Series,
        pd.Series,
    ]:
        """Equivalent CO2 emissions calculation using GWP* method."""

        # Contrails
        contrails_equivalent_emissions = AeromapsEquivalentEmissionsFunction(
            self,
            emissions_erf=contrails_erf,
            gwpstar_variation_duration=1.0,
            alpha_coefficient=0.0,
            erf_coefficient_co2=erf_coefficient_co2,
        )
        self.df["contrails_equivalent_emissions"] = contrails_equivalent_emissions

        # NOx short-term O3 increase
        nox_short_term_o3_increase_equivalent_emissions = AeromapsEquivalentEmissionsFunction(
            self,
            emissions_erf=nox_short_term_o3_increase_erf,
            gwpstar_variation_duration=1.0,
            alpha_coefficient=0.0,
            erf_coefficient_co2=erf_coefficient_co2,
        )
        self.df[
            "nox_short_term_o3_increase_equivalent_emissions"
        ] = nox_short_term_o3_increase_equivalent_emissions

        # NOx long-term O3 decrease
        nox_long_term_o3_decrease_equivalent_emissions = AeromapsEquivalentEmissionsFunction(
            self,
            emissions_erf=nox_long_term_o3_decrease_erf,
            gwpstar_variation_duration=20.0,
            alpha_coefficient=0.0,
            erf_coefficient_co2=erf_coefficient_co2,
        )
        self.df[
            "nox_long_term_o3_decrease_equivalent_emissions"
        ] = nox_long_term_o3_decrease_equivalent_emissions

        # NOx CH4 decrease
        nox_ch4_decrease_equivalent_emissions = AeromapsEquivalentEmissionsFunction(
            self,
            emissions_erf=nox_ch4_decrease_erf,
            gwpstar_variation_duration=20.0,
            alpha_coefficient=0.0,
            erf_coefficient_co2=erf_coefficient_co2,
        )
        self.df["nox_ch4_decrease_equivalent_emissions"] = nox_ch4_decrease_equivalent_emissions

        # NOx stratospheric water vapor decrease
        nox_stratospheric_water_vapor_decrease_equivalent_emissions = (
            AeromapsEquivalentEmissionsFunction(
                self,
                emissions_erf=nox_stratospheric_water_vapor_decrease_erf,
                gwpstar_variation_duration=20.0,
                alpha_coefficient=0.0,
                erf_coefficient_co2=erf_coefficient_co2,
            )
        )
        self.df[
            "nox_stratospheric_water_vapor_decrease_equivalent_emissions"
        ] = nox_stratospheric_water_vapor_decrease_equivalent_emissions

        # Soot
        soot_equivalent_emissions = AeromapsEquivalentEmissionsFunction(
            self,
            emissions_erf=soot_erf,
            gwpstar_variation_duration=1.0,
            alpha_coefficient=0.0,
            erf_coefficient_co2=erf_coefficient_co2,
        )
        self.df["soot_equivalent_emissions"] = soot_equivalent_emissions

        # H2O
        h2o_equivalent_emissions = AeromapsEquivalentEmissionsFunction(
            self,
            emissions_erf=h2o_erf,
            gwpstar_variation_duration=20.0,
            alpha_coefficient=0.0,
            erf_coefficient_co2=erf_coefficient_co2,
        )
        self.df["h2o_equivalent_emissions"] = h2o_equivalent_emissions

        # Sulfur
        sulfur_equivalent_emissions = AeromapsEquivalentEmissionsFunction(
            self,
            emissions_erf=sulfur_erf,
            gwpstar_variation_duration=1.0,
            alpha_coefficient=0.0,
            erf_coefficient_co2=erf_coefficient_co2,
        )
        self.df["sulfur_equivalent_emissions"] = sulfur_equivalent_emissions

        # Total
        non_co2_equivalent_emissions = (
            contrails_equivalent_emissions
            + nox_short_term_o3_increase_equivalent_emissions
            + nox_long_term_o3_decrease_equivalent_emissions
            + nox_ch4_decrease_equivalent_emissions
            + nox_stratospheric_water_vapor_decrease_equivalent_emissions
            + soot_equivalent_emissions
            + h2o_equivalent_emissions
            + sulfur_equivalent_emissions
        )
        total_equivalent_emissions = co2_emissions + non_co2_equivalent_emissions
        self.df["non_co2_equivalent_emissions"] = non_co2_equivalent_emissions
        self.df["total_equivalent_emissions"] = total_equivalent_emissions

        # Cumulative non-CO2 and total equivalent emissions (Gtwe)
        self.df.loc[
            self.prospection_start_year - 1, "cumulative_non_co2_equivalent_emissions"
        ] = 0.0
        self.df.loc[self.prospection_start_year - 1, "cumulative_total_equivalent_emissions"] = 0.0
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "cumulative_non_co2_equivalent_emissions"] = (
                self.df.loc[k - 1, "cumulative_non_co2_equivalent_emissions"]
                + self.df.loc[k, "non_co2_equivalent_emissions"] / 1000
            )
            self.df.loc[k, "cumulative_total_equivalent_emissions"] = (
                self.df.loc[k - 1, "cumulative_total_equivalent_emissions"]
                + self.df.loc[k, "total_equivalent_emissions"] / 1000
            )
        cumulative_non_co2_equivalent_emissions = self.df["cumulative_non_co2_equivalent_emissions"]
        cumulative_total_equivalent_emissions = self.df["cumulative_total_equivalent_emissions"]

        # Share CO2/non-CO2
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "total_co2_equivalent_emissions_ratio"] = (
                total_equivalent_emissions.loc[k] / co2_emissions.loc[k]
            )
        total_co2_equivalent_emissions_ratio = self.df["total_co2_equivalent_emissions_ratio"]

        co2_total_erf_ratio = co2_erf / total_erf * 100
        self.df.loc[:, "co2_total_erf_ratio"] = co2_total_erf_ratio

        return (
            contrails_equivalent_emissions,
            nox_short_term_o3_increase_equivalent_emissions,
            nox_long_term_o3_decrease_equivalent_emissions,
            nox_ch4_decrease_equivalent_emissions,
            nox_stratospheric_water_vapor_decrease_equivalent_emissions,
            soot_equivalent_emissions,
            h2o_equivalent_emissions,
            sulfur_equivalent_emissions,
            non_co2_equivalent_emissions,
            cumulative_non_co2_equivalent_emissions,
            total_equivalent_emissions,
            cumulative_total_equivalent_emissions,
            total_co2_equivalent_emissions_ratio,
            co2_total_erf_ratio,
        )


class EquivalentCO2EmissionsSimplifiedGWPStar(AeromapsModel):
    def __init__(self, name="equivalent_co2_emissions_simplified_gwpstar", *args, **kwargs):
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
        ]

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
