from typing import Tuple
import pandas as pd

from aeromaps.models.base import (
    AeromapsModel,
    GWPStarEquivalentEmissionsFunction,
    AbsoluteGlobalWarmingPotentialCO2Function,
)


class TemperatureGWPStar(AeromapsModel):
    def __init__(self, name="temperature_gwpstar", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

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

        # EQUIVALENT EMISSIONS

        ## Contrails
        contrails_equivalent_emissions = GWPStarEquivalentEmissionsFunction(
            self,
            emissions_erf=contrails_erf,
            gwpstar_variation_duration=1.0,
            alpha_coefficient=0.0,
        )
        self.df_climate["contrails_equivalent_emissions"] = contrails_equivalent_emissions

        ## NOx short-term O3 increase
        nox_short_term_o3_increase_equivalent_emissions = GWPStarEquivalentEmissionsFunction(
            self,
            emissions_erf=nox_short_term_o3_increase_erf,
            gwpstar_variation_duration=1.0,
            alpha_coefficient=0.0,
        )
        self.df_climate[
            "nox_short_term_o3_increase_equivalent_emissions"
        ] = nox_short_term_o3_increase_equivalent_emissions

        ## NOx long-term O3 decrease
        nox_long_term_o3_decrease_equivalent_emissions = GWPStarEquivalentEmissionsFunction(
            self,
            emissions_erf=nox_long_term_o3_decrease_erf,
            gwpstar_variation_duration=20.0,
            alpha_coefficient=0.0,
        )
        self.df_climate[
            "nox_long_term_o3_decrease_equivalent_emissions"
        ] = nox_long_term_o3_decrease_equivalent_emissions

        ## NOx CH4 decrease
        nox_ch4_decrease_equivalent_emissions = GWPStarEquivalentEmissionsFunction(
            self,
            emissions_erf=nox_ch4_decrease_erf,
            gwpstar_variation_duration=20.0,
            alpha_coefficient=0.25,
        )
        self.df_climate[
            "nox_ch4_decrease_equivalent_emissions"
        ] = nox_ch4_decrease_equivalent_emissions

        ## NOx stratospheric water vapor decrease
        nox_stratospheric_water_vapor_decrease_equivalent_emissions = (
            GWPStarEquivalentEmissionsFunction(
                self,
                emissions_erf=nox_stratospheric_water_vapor_decrease_erf,
                gwpstar_variation_duration=20.0,
                alpha_coefficient=0.0,
            )
        )
        self.df_climate[
            "nox_stratospheric_water_vapor_decrease_equivalent_emissions"
        ] = nox_stratospheric_water_vapor_decrease_equivalent_emissions

        ## Soot
        soot_equivalent_emissions = GWPStarEquivalentEmissionsFunction(
            self,
            emissions_erf=soot_erf,
            gwpstar_variation_duration=1.0,
            alpha_coefficient=0.0,
        )
        self.df_climate["soot_equivalent_emissions"] = soot_equivalent_emissions

        ## H2O
        h2o_equivalent_emissions = GWPStarEquivalentEmissionsFunction(
            self,
            emissions_erf=h2o_erf,
            gwpstar_variation_duration=20.0,
            alpha_coefficient=0.0,
        )
        self.df_climate["h2o_equivalent_emissions"] = h2o_equivalent_emissions

        ## Sulfur
        sulfur_equivalent_emissions = GWPStarEquivalentEmissionsFunction(
            self,
            emissions_erf=sulfur_erf,
            gwpstar_variation_duration=1.0,
            alpha_coefficient=0.0,
        )
        self.df_climate["sulfur_equivalent_emissions"] = sulfur_equivalent_emissions

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
        self.df_climate["non_co2_equivalent_emissions"] = non_co2_equivalent_emissions
        self.df_climate["total_equivalent_emissions"] = total_equivalent_emissions

        ## Cumulative CO2, non-CO2 and total equivalent emissions (Gtwe)

        ### From 1940
        self.df_climate.loc[
            self.climate_historic_start_year, "historical_cumulative_co2_emissions"
        ] = (co2_emissions.loc[self.climate_historic_start_year] / 1000)
        self.df_climate.loc[
            self.climate_historic_start_year, "historical_cumulative_non_co2_equivalent_emissions"
        ] = (non_co2_equivalent_emissions[self.climate_historic_start_year] / 1000)
        for k in range(self.climate_historic_start_year + 1, self.end_year + 1):
            self.df_climate.loc[k, "historical_cumulative_co2_emissions"] = (
                self.df_climate.loc[k - 1, "historical_cumulative_co2_emissions"]
                + co2_emissions.loc[k] / 1000
            )
            self.df_climate.loc[k, "historical_cumulative_non_co2_equivalent_emissions"] = (
                self.df_climate.loc[k - 1, "historical_cumulative_non_co2_equivalent_emissions"]
                + non_co2_equivalent_emissions.loc[k] / 1000
            )
        historical_cumulative_co2_emissions = self.df_climate["historical_cumulative_co2_emissions"]
        historical_cumulative_non_co2_equivalent_emissions = self.df_climate[
            "historical_cumulative_non_co2_equivalent_emissions"
        ]
        historical_cumulative_total_equivalent_emissions = (
            historical_cumulative_co2_emissions + historical_cumulative_non_co2_equivalent_emissions
        )
        self.df_climate[
            "cumulative_total_equivalent_emissions"
        ] = historical_cumulative_total_equivalent_emissions

        ### From 2020
        self.df_climate.loc[
            self.prospection_start_year - 1, "cumulative_non_co2_equivalent_emissions"
        ] = 0.0
        self.df_climate.loc[
            self.prospection_start_year - 1, "cumulative_total_equivalent_emissions"
        ] = 0.0
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df_climate.loc[k, "cumulative_non_co2_equivalent_emissions"] = (
                self.df_climate.loc[k - 1, "cumulative_non_co2_equivalent_emissions"]
                + non_co2_equivalent_emissions.loc[k] / 1000
            )
            self.df_climate.loc[k, "cumulative_total_equivalent_emissions"] = (
                self.df_climate.loc[k - 1, "cumulative_total_equivalent_emissions"]
                + total_equivalent_emissions.loc[k] / 1000
            )
        cumulative_non_co2_equivalent_emissions = self.df_climate[
            "cumulative_non_co2_equivalent_emissions"
        ]
        cumulative_total_equivalent_emissions = self.df_climate[
            "cumulative_total_equivalent_emissions"
        ]

        ## Share CO2/non-CO2
        for k in range(self.climate_historic_start_year, self.end_year + 1):
            self.df_climate.loc[k, "total_co2_equivalent_emissions_ratio"] = (
                total_equivalent_emissions.loc[k] / co2_emissions.loc[k]
            )
        total_co2_equivalent_emissions_ratio = self.df_climate[
            "total_co2_equivalent_emissions_ratio"
        ]

        co2_total_erf_ratio = co2_erf / total_erf * 100
        self.df_climate.loc[:, "co2_total_erf_ratio"] = co2_total_erf_ratio

        # TEMPERATURE

        for k in range(self.climate_historic_start_year, self.end_year + 1):
            self.df_climate.loc[k, "temperature_increase_from_co2_from_aviation"] = (
                tcre_coefficient * historical_cumulative_co2_emissions.loc[k]
            )
            self.df_climate.loc[k, "temperature_increase_from_non_co2_from_aviation"] = (
                tcre_coefficient * historical_cumulative_non_co2_equivalent_emissions.loc[k]
            )
        temperature_increase_from_co2_from_aviation = self.df_climate[
            "temperature_increase_from_co2_from_aviation"
        ]
        temperature_increase_from_non_co2_from_aviation = self.df_climate[
            "temperature_increase_from_non_co2_from_aviation"
        ]

        temperature_increase_from_aviation = (
            temperature_increase_from_co2_from_aviation
            + temperature_increase_from_non_co2_from_aviation
        )
        self.df_climate["temperature_increase_from_aviation"] = temperature_increase_from_aviation

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

        self.df_climate.loc[self.climate_historic_start_year, "total_erf_smooth"] = (
            total_erf.loc[self.climate_historic_start_year]
            + total_erf.loc[self.climate_historic_start_year + 1]
            + total_erf.loc[self.climate_historic_start_year + 2]
        ) / 3
        self.df_climate.loc[self.climate_historic_start_year, "co2_erf_smooth"] = (
            co2_erf.loc[self.climate_historic_start_year]
            + co2_erf.loc[self.climate_historic_start_year + 1]
            + co2_erf.loc[self.climate_historic_start_year + 2]
        ) / 3
        self.df_climate.loc[self.climate_historic_start_year, "co2_emissions_smooth"] = (
            co2_emissions.loc[self.climate_historic_start_year]
            + co2_emissions.loc[self.climate_historic_start_year + 1]
            + co2_emissions.loc[self.climate_historic_start_year + 2]
        ) / 3

        self.df_climate.loc[self.climate_historic_start_year + 1, "total_erf_smooth"] = (
            total_erf.loc[self.climate_historic_start_year]
            + total_erf.loc[self.climate_historic_start_year + 1]
            + total_erf.loc[self.climate_historic_start_year + 2]
            + total_erf.loc[self.climate_historic_start_year + 3]
        ) / 4
        self.df_climate.loc[self.climate_historic_start_year + 1, "co2_erf_smooth"] = (
            co2_erf.loc[self.climate_historic_start_year]
            + co2_erf.loc[self.climate_historic_start_year + 1]
            + co2_erf.loc[self.climate_historic_start_year + 2]
            + co2_erf.loc[self.climate_historic_start_year + 3]
        ) / 4
        self.df_climate.loc[self.climate_historic_start_year + 1, "co2_emissions_smooth"] = (
            co2_emissions.loc[self.climate_historic_start_year]
            + co2_emissions.loc[self.climate_historic_start_year + 1]
            + co2_emissions.loc[self.climate_historic_start_year + 2]
            + co2_emissions.loc[self.climate_historic_start_year + 3]
        ) / 4

        for k in range(self.climate_historic_start_year + 2, self.end_year - 1):
            self.df_climate.loc[k, "total_erf_smooth"] = (
                total_erf.loc[k - 2]
                + total_erf.loc[k - 1]
                + total_erf.loc[k]
                + total_erf.loc[k + 1]
                + total_erf.loc[k + 2]
            ) / 5
            self.df_climate.loc[k, "co2_erf_smooth"] = (
                co2_erf.loc[k - 2]
                + co2_erf.loc[k - 1]
                + co2_erf.loc[k]
                + co2_erf.loc[k + 1]
                + co2_erf.loc[k + 2]
            ) / 5
            self.df_climate.loc[k, "co2_emissions_smooth"] = (
                co2_emissions.loc[k - 2]
                + co2_emissions.loc[k - 1]
                + co2_emissions.loc[k]
                + co2_emissions.loc[k + 1]
                + co2_emissions.loc[k + 2]
            ) / 5

        self.df_climate.loc[self.end_year - 1, "total_erf_smooth"] = (
            total_erf.loc[self.end_year - 3]
            + total_erf.loc[self.end_year - 2]
            + total_erf.loc[self.end_year - 1]
            + total_erf.loc[self.end_year]
        ) / 4
        self.df_climate.loc[self.end_year - 1, "co2_erf_smooth"] = (
            co2_erf.loc[self.end_year - 3]
            + co2_erf.loc[self.end_year - 2]
            + co2_erf.loc[self.end_year - 1]
            + co2_erf.loc[self.end_year]
        ) / 4
        self.df_climate.loc[self.end_year - 1, "co2_emissions_smooth"] = (
            co2_emissions.loc[self.end_year - 3]
            + co2_emissions.loc[self.end_year - 2]
            + co2_emissions.loc[self.end_year - 1]
            + co2_emissions.loc[self.end_year]
        ) / 4

        self.df_climate.loc[self.end_year, "total_erf_smooth"] = (
            total_erf.loc[self.end_year - 2]
            + total_erf.loc[self.end_year - 1]
            + total_erf.loc[self.end_year]
        ) / 3
        self.df_climate.loc[self.end_year, "co2_erf_smooth"] = (
            co2_erf.loc[self.end_year - 2]
            + co2_erf.loc[self.end_year - 1]
            + co2_erf.loc[self.end_year]
        ) / 3
        self.df_climate.loc[self.end_year, "co2_emissions_smooth"] = (
            co2_emissions.loc[self.end_year - 2]
            + co2_emissions.loc[self.end_year - 1]
            + co2_emissions.loc[self.end_year]
        ) / 3

        for k in range(self.climate_historic_start_year, self.end_year + 1):
            self.df_climate.loc[k, "non_co2_erf_smooth"] = (
                self.df_climate.loc[k, "total_erf_smooth"]
                - self.df_climate.loc[k, "co2_erf_smooth"]
            )

        total_erf_smooth = self.df_climate["total_erf_smooth"]
        co2_erf_smooth = self.df_climate["co2_erf_smooth"]
        co2_emissions_smooth = self.df_climate["co2_emissions_smooth"]
        non_co2_erf_smooth = self.df_climate["non_co2_erf_smooth"]

        # Equivalent emissions (Mtwe)

        ## DeltaF/Deltat
        gwpstar_variation_duration = 20
        for k in range(self.climate_historic_start_year, self.end_year + 1):
            if k - self.climate_historic_start_year >= gwpstar_variation_duration:
                self.df_climate.loc[k, "non_co2_erf_smooth_variation"] = (
                    self.df_climate.loc[k, "non_co2_erf_smooth"]
                    - self.df_climate.loc[k - gwpstar_variation_duration, "non_co2_erf_smooth"]
                ) / gwpstar_variation_duration
            else:
                self.df_climate.loc[k, "non_co2_erf_smooth_variation"] = (
                    self.df_climate.loc[k, "non_co2_erf_smooth"] / gwpstar_variation_duration
                )
        non_co2_erf_smooth_variation = self.df_climate["non_co2_erf_smooth_variation"]

        ## Non-CO2 equivalent emissions
        climate_time_horizon = 100
        co2_agwp_h = AbsoluteGlobalWarmingPotentialCO2Function(climate_time_horizon)
        for k in range(self.climate_historic_start_year, self.end_year + 1):
            self.df_climate.loc[k, "non_co2_equivalent_emissions"] = (
                self.df_climate.loc[k, "non_co2_erf_smooth_variation"]
                * climate_time_horizon
                / co2_agwp_h
            )
        non_co2_equivalent_emissions = self.df_climate["non_co2_equivalent_emissions"]

        ## Total equivalent emissions
        for k in range(self.climate_historic_start_year, self.end_year + 1):
            self.df_climate.loc[k, "total_equivalent_emissions"] = (
                self.df_climate.loc[k, "non_co2_equivalent_emissions"]
                + self.df_climate.loc[k, "co2_emissions_smooth"]
            )
        total_equivalent_emissions = self.df_climate["total_equivalent_emissions"]

        ## Cumulative smooth CO2, non-CO2 and total equivalent emissions (Gtwe)

        ### From 1940
        self.df_climate.loc[
            self.climate_historic_start_year, "historical_cumulative_co2_emissions_smooth"
        ] = (co2_emissions_smooth.loc[self.climate_historic_start_year] / 1000)
        self.df_climate.loc[
            self.climate_historic_start_year, "historical_cumulative_non_co2_equivalent_emissions"
        ] = (non_co2_equivalent_emissions[self.climate_historic_start_year] / 1000)
        for k in range(self.climate_historic_start_year + 1, self.end_year + 1):
            self.df_climate.loc[k, "historical_cumulative_co2_emissions_smooth"] = (
                self.df_climate.loc[k - 1, "historical_cumulative_co2_emissions_smooth"]
                + co2_emissions_smooth.loc[k] / 1000
            )
            self.df_climate.loc[k, "historical_cumulative_non_co2_equivalent_emissions"] = (
                self.df_climate.loc[k - 1, "historical_cumulative_non_co2_equivalent_emissions"]
                + non_co2_equivalent_emissions.loc[k] / 1000
            )
        historical_cumulative_co2_emissions_smooth = self.df_climate[
            "historical_cumulative_co2_emissions_smooth"
        ]
        historical_cumulative_non_co2_equivalent_emissions = self.df_climate[
            "historical_cumulative_non_co2_equivalent_emissions"
        ]
        historical_cumulative_total_equivalent_emissions = (
            historical_cumulative_co2_emissions_smooth
            + historical_cumulative_non_co2_equivalent_emissions
        )
        self.df_climate[
            "cumulative_total_equivalent_emissions"
        ] = historical_cumulative_total_equivalent_emissions

        ### From 2020
        self.df_climate.loc[
            self.prospection_start_year - 1, "cumulative_co2_emissions_smooth"
        ] = 0.0
        self.df_climate.loc[
            self.prospection_start_year - 1, "cumulative_non_co2_equivalent_emissions"
        ] = 0.0
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df_climate.loc[k, "cumulative_co2_emissions_smooth"] = (
                self.df_climate.loc[k - 1, "cumulative_co2_emissions_smooth"]
                + co2_emissions_smooth.loc[k] / 1000
            )
            self.df_climate.loc[k, "cumulative_non_co2_equivalent_emissions"] = (
                self.df_climate.loc[k - 1, "cumulative_non_co2_equivalent_emissions"]
                + non_co2_equivalent_emissions.loc[k] / 1000
            )
        cumulative_co2_emissions_smooth = self.df_climate["cumulative_co2_emissions_smooth"]
        cumulative_non_co2_equivalent_emissions = self.df_climate[
            "cumulative_non_co2_equivalent_emissions"
        ]
        cumulative_total_equivalent_emissions = (
            cumulative_co2_emissions_smooth + cumulative_non_co2_equivalent_emissions
        )
        self.df_climate[
            "cumulative_total_equivalent_emissions"
        ] = cumulative_total_equivalent_emissions

        ## Share CO2/non-CO2
        for k in range(self.climate_historic_start_year, self.end_year + 1):
            self.df_climate.loc[k, "total_co2_equivalent_emissions_ratio"] = (
                total_equivalent_emissions.loc[k] / co2_emissions.loc[k]
            )
        total_co2_equivalent_emissions_ratio = self.df_climate[
            "total_co2_equivalent_emissions_ratio"
        ]

        co2_total_erf_ratio = co2_erf / total_erf * 100
        self.df_climate.loc[:, "co2_total_erf_ratio"] = co2_total_erf_ratio

        # TEMPERATURE

        for k in range(self.climate_historic_start_year, self.end_year + 1):
            self.df_climate.loc[k, "temperature_increase_from_co2_from_aviation"] = (
                tcre_coefficient * historical_cumulative_co2_emissions_smooth.loc[k]
            )
            self.df_climate.loc[k, "temperature_increase_from_non_co2_from_aviation"] = (
                tcre_coefficient * historical_cumulative_non_co2_equivalent_emissions.loc[k]
            )
        temperature_increase_from_co2_from_aviation = self.df_climate[
            "temperature_increase_from_co2_from_aviation"
        ]
        temperature_increase_from_non_co2_from_aviation = self.df_climate[
            "temperature_increase_from_non_co2_from_aviation"
        ]

        temperature_increase_from_aviation = (
            temperature_increase_from_co2_from_aviation
            + temperature_increase_from_non_co2_from_aviation
        )
        self.df_climate["temperature_increase_from_aviation"] = temperature_increase_from_aviation

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
