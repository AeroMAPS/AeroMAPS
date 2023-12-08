from typing import Tuple
import pandas as pd
import numpy as np

from aeromaps.models.base import (
    AeromapsModel,
    GWPStarEquivalentEmissionsFunction,
    GWPStarEquivalentEmissionsArrayFunction,
    AbsoluteGlobalWarmingPotentialCO2Function,
)


class TemperatureGWPStar(AeromapsModel):
    def __init__(self, name="temperature_gwpstar", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        historical_co2_emissions_for_temperature: np.ndarray = np.array([]),
        historical_contrails_erf_for_temperature: np.ndarray = np.array([]),
        historical_nox_short_term_o3_increase_erf_for_temperature: np.ndarray = np.array([]),
        historical_nox_long_term_o3_decrease_erf_for_temperature: np.ndarray = np.array([]),
        historical_nox_ch4_decrease_erf_for_temperature: np.ndarray = np.array([]),
        historical_nox_stratospheric_water_vapor_decrease_erf_for_temperature: np.ndarray = np.array(
            []
        ),
        historical_soot_erf_for_temperature: np.ndarray = np.array([]),
        historical_h2o_erf_for_temperature: np.ndarray = np.array([]),
        historical_sulfur_erf_for_temperature: np.ndarray = np.array([]),
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
        co2_emissions: pd.Series = pd.Series(dtype="float64"),
        tcre_coefficient: float = 0.0,
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
        pd.Series,
        pd.Series,
        pd.Series,
    ]:
        """Temperature calculation using equivalent emissions (with GWP* method) and TCRE."""

        # EQUIVALENT EMISSIONS (HISTORICAL BEFORE 2000)

        ## Contrails
        historical_contrails_equivalent_emissions_for_temperature = (
            GWPStarEquivalentEmissionsArrayFunction(
                self,
                emissions_erf=historical_contrails_erf_for_temperature,
                gwpstar_variation_duration=1.0,
                alpha_coefficient=0.0,
            )
        )

        ## NOx short-term O3 increase
        historical_nox_short_term_o3_increase_equivalent_emissions_for_temperature = (
            GWPStarEquivalentEmissionsArrayFunction(
                self,
                emissions_erf=historical_nox_short_term_o3_increase_erf_for_temperature,
                gwpstar_variation_duration=1.0,
                alpha_coefficient=0.0,
            )
        )

        ## NOx long-term O3 decrease
        historical_nox_long_term_o3_decrease_equivalent_emissions_for_temperature = (
            GWPStarEquivalentEmissionsArrayFunction(
                self,
                emissions_erf=historical_nox_long_term_o3_decrease_erf_for_temperature,
                gwpstar_variation_duration=20.0,
                alpha_coefficient=0.0,
            )
        )

        ## NOx CH4 decrease
        historical_nox_ch4_decrease_equivalent_emissions_for_temperature = (
            GWPStarEquivalentEmissionsArrayFunction(
                self,
                emissions_erf=historical_nox_ch4_decrease_erf_for_temperature,
                gwpstar_variation_duration=20.0,
                alpha_coefficient=0.25,
            )
        )

        ## NOx stratospheric water vapor decrease
        historical_nox_stratospheric_water_vapor_decrease_equivalent_emissions_for_temperature = (
            GWPStarEquivalentEmissionsArrayFunction(
                self,
                emissions_erf=historical_nox_stratospheric_water_vapor_decrease_erf_for_temperature,
                gwpstar_variation_duration=20.0,
                alpha_coefficient=0.0,
            )
        )

        ## Soot
        historical_soot_equivalent_emissions_for_temperature = (
            GWPStarEquivalentEmissionsArrayFunction(
                self,
                emissions_erf=historical_soot_erf_for_temperature,
                gwpstar_variation_duration=1.0,
                alpha_coefficient=0.0,
            )
        )

        ## H2O
        historical_h2o_equivalent_emissions_for_temperature = (
            GWPStarEquivalentEmissionsArrayFunction(
                self,
                emissions_erf=historical_h2o_erf_for_temperature,
                gwpstar_variation_duration=20.0,
                alpha_coefficient=0.0,
            )
        )

        ## Sulfur
        historical_sulfur_equivalent_emissions_for_temperature = (
            GWPStarEquivalentEmissionsArrayFunction(
                self,
                emissions_erf=historical_sulfur_erf_for_temperature,
                gwpstar_variation_duration=1.0,
                alpha_coefficient=0.0,
            )
        )

        # Total
        historical_non_co2_equivalent_emissions_for_temperature = (
            historical_contrails_equivalent_emissions_for_temperature
            + historical_nox_short_term_o3_increase_equivalent_emissions_for_temperature
            + historical_nox_long_term_o3_decrease_equivalent_emissions_for_temperature
            + historical_nox_ch4_decrease_equivalent_emissions_for_temperature
            + historical_nox_stratospheric_water_vapor_decrease_equivalent_emissions_for_temperature
            + historical_soot_equivalent_emissions_for_temperature
            + historical_h2o_equivalent_emissions_for_temperature
            + historical_sulfur_equivalent_emissions_for_temperature
        )
        historical_total_equivalent_emissions_for_temperature = (
            historical_co2_emissions_for_temperature
            + historical_non_co2_equivalent_emissions_for_temperature
        )

        # Cumulative
        historical_cumulative_co2_emissions_for_temperature = np.zeros(
            len(historical_co2_emissions_for_temperature)
        )
        historical_cumulative_co2_emissions_for_temperature[0] = (
            historical_co2_emissions_for_temperature[0] / 1000
        )
        for k in range(1, len(historical_co2_emissions_for_temperature)):
            historical_cumulative_co2_emissions_for_temperature[k] = (
                historical_cumulative_co2_emissions_for_temperature[k - 1]
                + historical_co2_emissions_for_temperature[k] / 1000
            )
        historical_cumulative_non_co2_equivalent_emissions_for_temperature = np.zeros(
            len(historical_non_co2_equivalent_emissions_for_temperature)
        )
        historical_cumulative_non_co2_equivalent_emissions_for_temperature[0] = (
            historical_non_co2_equivalent_emissions_for_temperature[0] / 1000
        )
        for k in range(1, len(historical_co2_emissions_for_temperature)):
            historical_cumulative_non_co2_equivalent_emissions_for_temperature[k] = (
                historical_cumulative_non_co2_equivalent_emissions_for_temperature[k - 1]
                + historical_non_co2_equivalent_emissions_for_temperature[k] / 1000
            )
        historical_cumulative_total_equivalent_emissions_for_temperature = (
            historical_cumulative_co2_emissions_for_temperature
            + historical_cumulative_non_co2_equivalent_emissions_for_temperature
        )

        # EQUIVALENT EMISSIONS

        ## Contrails
        contrails_equivalent_emissions = GWPStarEquivalentEmissionsFunction(
            self,
            emissions_erf=contrails_erf,
            historical_emissions_erf=historical_contrails_erf_for_temperature,
            gwpstar_variation_duration=1.0,
            alpha_coefficient=0.0,
        )
        self.df["contrails_equivalent_emissions"] = contrails_equivalent_emissions

        ## NOx short-term O3 increase
        nox_short_term_o3_increase_equivalent_emissions = GWPStarEquivalentEmissionsFunction(
            self,
            emissions_erf=nox_short_term_o3_increase_erf,
            historical_emissions_erf=historical_nox_short_term_o3_increase_erf_for_temperature,
            gwpstar_variation_duration=1.0,
            alpha_coefficient=0.0,
        )
        self.df[
            "nox_short_term_o3_increase_equivalent_emissions"
        ] = nox_short_term_o3_increase_equivalent_emissions

        ## NOx long-term O3 decrease
        nox_long_term_o3_decrease_equivalent_emissions = GWPStarEquivalentEmissionsFunction(
            self,
            emissions_erf=nox_long_term_o3_decrease_erf,
            historical_emissions_erf=historical_nox_long_term_o3_decrease_erf_for_temperature,
            gwpstar_variation_duration=20.0,
            alpha_coefficient=0.0,
        )
        self.df[
            "nox_long_term_o3_decrease_equivalent_emissions"
        ] = nox_long_term_o3_decrease_equivalent_emissions

        ## NOx CH4 decrease
        nox_ch4_decrease_equivalent_emissions = GWPStarEquivalentEmissionsFunction(
            self,
            emissions_erf=nox_ch4_decrease_erf,
            historical_emissions_erf=historical_nox_ch4_decrease_erf_for_temperature,
            gwpstar_variation_duration=20.0,
            alpha_coefficient=0.25,
        )
        self.df["nox_ch4_decrease_equivalent_emissions"] = nox_ch4_decrease_equivalent_emissions

        ## NOx stratospheric water vapor decrease
        nox_stratospheric_water_vapor_decrease_equivalent_emissions = GWPStarEquivalentEmissionsFunction(
            self,
            emissions_erf=nox_stratospheric_water_vapor_decrease_erf,
            historical_emissions_erf=historical_nox_stratospheric_water_vapor_decrease_erf_for_temperature,
            gwpstar_variation_duration=20.0,
            alpha_coefficient=0.0,
        )
        self.df[
            "nox_stratospheric_water_vapor_decrease_equivalent_emissions"
        ] = nox_stratospheric_water_vapor_decrease_equivalent_emissions

        ## Soot
        soot_equivalent_emissions = GWPStarEquivalentEmissionsFunction(
            self,
            emissions_erf=soot_erf,
            historical_emissions_erf=historical_soot_erf_for_temperature,
            gwpstar_variation_duration=1.0,
            alpha_coefficient=0.0,
        )
        self.df["soot_equivalent_emissions"] = soot_equivalent_emissions

        ## H2O
        h2o_equivalent_emissions = GWPStarEquivalentEmissionsFunction(
            self,
            emissions_erf=h2o_erf,
            historical_emissions_erf=historical_h2o_erf_for_temperature,
            gwpstar_variation_duration=20.0,
            alpha_coefficient=0.0,
        )
        self.df["h2o_equivalent_emissions"] = h2o_equivalent_emissions

        ## Sulfur
        sulfur_equivalent_emissions = GWPStarEquivalentEmissionsFunction(
            self,
            emissions_erf=sulfur_erf,
            historical_emissions_erf=historical_sulfur_erf_for_temperature,
            gwpstar_variation_duration=1.0,
            alpha_coefficient=0.0,
        )
        self.df["sulfur_equivalent_emissions"] = sulfur_equivalent_emissions

        ## Total
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

        ## Cumulative non-CO2 and total equivalent emissions (Gtwe)

        ### From 1940
        self.df.loc[
            self.historic_start_year, "historical_cumulative_co2_emissions"
        ] = historical_cumulative_co2_emissions_for_temperature[-1]
        self.df.loc[
            self.historic_start_year, "historical_cumulative_non_co2_equivalent_emissions"
        ] = historical_cumulative_non_co2_equivalent_emissions_for_temperature[-1]
        for k in range(self.historic_start_year + 1, self.end_year + 1):
            self.df.loc[k, "historical_cumulative_co2_emissions"] = (
                self.df.loc[k - 1, "historical_cumulative_co2_emissions"]
                + co2_emissions.loc[k] / 1000
            )
            self.df.loc[k, "historical_cumulative_non_co2_equivalent_emissions"] = (
                self.df.loc[k - 1, "historical_cumulative_non_co2_equivalent_emissions"]
                + non_co2_equivalent_emissions.loc[k] / 1000
            )
        historical_cumulative_co2_emissions = self.df["historical_cumulative_co2_emissions"]
        historical_cumulative_non_co2_equivalent_emissions = self.df[
            "historical_cumulative_non_co2_equivalent_emissions"
        ]
        historical_cumulative_total_equivalent_emissions = (
            historical_cumulative_co2_emissions + historical_cumulative_non_co2_equivalent_emissions
        )
        self.df[
            "cumulative_total_equivalent_emissions"
        ] = historical_cumulative_total_equivalent_emissions

        ### From 2020
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

        ## Share CO2/non-CO2
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "total_co2_equivalent_emissions_ratio"] = (
                total_equivalent_emissions.loc[k] / co2_emissions.loc[k]
            )
        total_co2_equivalent_emissions_ratio = self.df["total_co2_equivalent_emissions_ratio"]

        co2_total_erf_ratio = co2_erf / total_erf * 100
        self.df.loc[:, "co2_total_erf_ratio"] = co2_total_erf_ratio

        # TEMPERATURE

        ## Historical estimation before 2000

        historical_temperature_increase_from_co2_from_aviation = np.zeros(
            len(historical_cumulative_co2_emissions_for_temperature)
        )
        historical_temperature_increase_from_non_co2_from_aviation = np.zeros(
            len(historical_cumulative_non_co2_equivalent_emissions_for_temperature)
        )
        for k in range(0, len(historical_temperature_increase_from_co2_from_aviation)):
            historical_temperature_increase_from_co2_from_aviation[k] = (
                tcre_coefficient * historical_cumulative_co2_emissions_for_temperature[k]
            )
            historical_temperature_increase_from_non_co2_from_aviation[k] = (
                tcre_coefficient
                * historical_cumulative_non_co2_equivalent_emissions_for_temperature[k]
            )
        historical_temperature_increase_from_aviation = (
            historical_temperature_increase_from_co2_from_aviation
            + historical_temperature_increase_from_non_co2_from_aviation
        )
        self.historical_temperature_increase_from_aviation = (
            historical_temperature_increase_from_aviation
        )
        self.historical_temperature_increase_from_non_co2_from_aviation = (
            historical_temperature_increase_from_non_co2_from_aviation
        )
        self.historical_temperature_increase_from_co2_from_aviation = (
            historical_temperature_increase_from_co2_from_aviation
        )

        ## Historical estimation after 2000 and prospective

        self.df.loc[
            self.historic_start_year, "temperature_increase_from_co2_from_aviation"
        ] = historical_temperature_increase_from_co2_from_aviation[-1]
        self.df.loc[
            self.historic_start_year, "temperature_increase_from_non_co2_from_aviation"
        ] = historical_temperature_increase_from_non_co2_from_aviation[-1]
        for k in range(self.historic_start_year + 1, self.end_year + 1):
            self.df.loc[k, "temperature_increase_from_co2_from_aviation"] = (
                tcre_coefficient * historical_cumulative_co2_emissions.loc[k]
            )
            self.df.loc[k, "temperature_increase_from_non_co2_from_aviation"] = (
                tcre_coefficient * historical_cumulative_non_co2_equivalent_emissions.loc[k]
            )
        temperature_increase_from_co2_from_aviation = self.df[
            "temperature_increase_from_co2_from_aviation"
        ]
        temperature_increase_from_non_co2_from_aviation = self.df[
            "temperature_increase_from_non_co2_from_aviation"
        ]

        temperature_increase_from_aviation = (
            temperature_increase_from_co2_from_aviation
            + temperature_increase_from_non_co2_from_aviation
        )
        self.df["temperature_increase_from_aviation"] = temperature_increase_from_aviation

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
            temperature_increase_from_aviation,
            temperature_increase_from_co2_from_aviation,
            temperature_increase_from_non_co2_from_aviation,
        )


class TemperatureSimpleGWPStar(AeromapsModel):
    def __init__(self, name="temperature_simple_gwpstar", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        total_erf: pd.Series = pd.Series(dtype="float64"),
        co2_erf: pd.Series = pd.Series(dtype="float64"),
        co2_emissions: pd.Series = pd.Series(dtype="float64"),
        tcre_coefficient: float = 0.0,
        temperature_increase_from_aviation_init: pd.Series = pd.Series(dtype="float64"),
        cumulative_co2_emissions: pd.Series = pd.Series(dtype="float64"),
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
        pd.Series,
    ]:
        """Temperature calculation using equivalent emissions (with simple and smooth GWP* method) and TCRE."""

        # EQUIVALENT EMISSIONS

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

        # Global
        climate_time_horizon = 100
        co2_agwp_h = AbsoluteGlobalWarmingPotentialCO2Function(climate_time_horizon)

        # Non-CO2 equivalent emissions (Mtwe)
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "non_co2_equivalent_emissions"] = (
                self.df.loc[k, "non_co2_erf_smooth_variation"] * climate_time_horizon / co2_agwp_h
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

        # TEMPERATURE

        # Total temperature

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[
                k, "temperature_increase_from_aviation"
            ] = temperature_increase_from_aviation_init.loc[k]

        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "temperature_increase_from_aviation"] = (
                temperature_increase_from_aviation_init.loc[2019]
                + tcre_coefficient * cumulative_total_equivalent_emissions.loc[k]
            )

        temperature_increase_from_aviation = self.df["temperature_increase_from_aviation"]

        # Temperature due to CO2 emissions - Assumption of a third of temperature increase due to CO2

        self.df.loc[2019, "temperature_increase_from_co2_from_aviation"] = (
            temperature_increase_from_aviation_init.loc[2019] / 3
        )

        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "temperature_increase_from_co2_from_aviation"] = (
                self.df.loc[2019, "temperature_increase_from_co2_from_aviation"]
                + tcre_coefficient * cumulative_co2_emissions.loc[k]
            )

        for k in reversed(range(self.historic_start_year, self.prospection_start_year - 1)):
            self.df.loc[k, "temperature_increase_from_co2_from_aviation"] = (
                self.df.loc[k + 1, "temperature_increase_from_co2_from_aviation"]
                - tcre_coefficient * co2_emissions.loc[k] / 1000
            )

        temperature_increase_from_co2_from_aviation = self.df[
            "temperature_increase_from_co2_from_aviation"
        ]

        # Temperature due to non-CO2 effects

        temperature_increase_from_non_co2_from_aviation = (
            temperature_increase_from_aviation - temperature_increase_from_co2_from_aviation
        )

        self.df.loc[
            :, "temperature_increase_from_non_co2_from_aviation"
        ] = temperature_increase_from_non_co2_from_aviation

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
            temperature_increase_from_aviation,
            temperature_increase_from_co2_from_aviation,
            temperature_increase_from_non_co2_from_aviation,
        )


class TemperatureFaIR(AeromapsModel):
    def __init__(self, name="temperature_fair", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        tcre_coefficient: float = 0.0,
        temperature_increase_from_aviation_init: pd.Series = pd.Series(dtype="float64"),
        cumulative_total_equivalent_emissions: pd.Series = pd.Series(dtype="float64"),
        cumulative_co2_emissions: pd.Series = pd.Series(dtype="float64"),
        co2_emissions: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Temperature calculation using FaIR."""

        # Total temperature

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[
                k, "temperature_increase_from_aviation"
            ] = temperature_increase_from_aviation_init.loc[k]

        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "temperature_increase_from_aviation"] = (
                temperature_increase_from_aviation_init.loc[2019]
                + tcre_coefficient * cumulative_total_equivalent_emissions.loc[k]
            )

        temperature_increase_from_aviation = self.df["temperature_increase_from_aviation"]

        # Temperature due to CO2 emissions - Assumption of a third of temperature increase due to CO2

        self.df.loc[2019, "temperature_increase_from_co2_from_aviation"] = (
            temperature_increase_from_aviation_init.loc[2019] / 3
        )

        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "temperature_increase_from_co2_from_aviation"] = (
                self.df.loc[2019, "temperature_increase_from_co2_from_aviation"]
                + tcre_coefficient * cumulative_co2_emissions.loc[k]
            )

        for k in reversed(range(self.historic_start_year, self.prospection_start_year - 1)):
            self.df.loc[k, "temperature_increase_from_co2_from_aviation"] = (
                self.df.loc[k + 1, "temperature_increase_from_co2_from_aviation"]
                - tcre_coefficient * co2_emissions.loc[k] / 1000
            )

        temperature_increase_from_co2_from_aviation = self.df[
            "temperature_increase_from_co2_from_aviation"
        ]

        # Temperature due to non-CO2 effects

        temperature_increase_from_non_co2_from_aviation = (
            temperature_increase_from_aviation - temperature_increase_from_co2_from_aviation
        )

        self.df.loc[
            :, "temperature_increase_from_non_co2_from_aviation"
        ] = temperature_increase_from_non_co2_from_aviation

        return (
            temperature_increase_from_aviation,
            temperature_increase_from_co2_from_aviation,
            temperature_increase_from_non_co2_from_aviation,
        )
