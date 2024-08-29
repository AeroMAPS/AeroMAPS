from typing import Tuple
import pandas as pd

from aeromaps.models.base import AeroMAPSModel, AbsoluteGlobalWarmingPotentialCO2Function


class SimplifiedERFCo2(AeroMAPSModel):
    def __init__(self, name="simplified_effective_radiative_forcing_co2", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        co2_emissions: pd.Series,
    ) -> Tuple[
        pd.Series,
        pd.Series,
    ]:
        """ERF calculation for CO2 emissions with a simplified method."""

        # CO2
        h = 100  # Climate time horizon
        for k in range(self.climate_historic_start_year, self.end_year + 1):
            self.df_climate.loc[k, "annual_co2_erf"] = (
                co2_emissions.loc[k] * AbsoluteGlobalWarmingPotentialCO2Function(h) / h
            )
        self.df_climate.loc[self.climate_historic_start_year, "co2_erf"] = self.df_climate.loc[
            self.climate_historic_start_year, "annual_co2_erf"
        ]
        for k in range(self.climate_historic_start_year + 1, self.end_year + 1):
            self.df_climate.loc[k, "co2_erf"] = (
                self.df_climate.loc[k - 1, "co2_erf"] + self.df_climate.loc[k, "annual_co2_erf"]
            )
        annual_co2_erf = self.df_climate["annual_co2_erf"]
        co2_erf = self.df_climate["co2_erf"]

        return (
            annual_co2_erf,
            co2_erf,
        )


class SimplifiedERFNox(AeroMAPSModel):
    def __init__(self, name="simplified_effective_radiative_forcing_nox", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        nox_emissions: pd.Series,
        erf_coefficient_nox: float,
    ) -> pd.Series:
        """ERF calculation for NOx emissions with a simplified method."""

        # NOx
        n_emissions = nox_emissions * 14 / 46
        self.df_climate["nox_erf"] = n_emissions * erf_coefficient_nox
        nox_erf = self.df_climate["nox_erf"]

        return nox_erf


class ERFNox(AeroMAPSModel):
    def __init__(self, name="effective_radiative_forcing_nox", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        nox_emissions: pd.Series,
        erf_coefficient_nox_short_term_o3_increase: float,
        erf_coefficient_nox_long_term_o3_decrease: float,
        erf_coefficient_nox_ch4_decrease: float,
        erf_coefficient_nox_stratospheric_water_vapor_decrease: float,
    ) -> Tuple[
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
    ]:
        """ERF calculation for NOx emissions."""

        # NOx
        n_emissions = nox_emissions * 14 / 46  # Molar masses of N and NOx
        self.df_climate["nox_short_term_o3_increase_erf"] = (
            n_emissions * erf_coefficient_nox_short_term_o3_increase
        )
        self.df_climate["nox_long_term_o3_decrease_erf"] = (
            n_emissions * erf_coefficient_nox_long_term_o3_decrease
        )
        self.df_climate["nox_ch4_decrease_erf"] = n_emissions * erf_coefficient_nox_ch4_decrease
        self.df_climate["nox_stratospheric_water_vapor_decrease_erf"] = (
            n_emissions * erf_coefficient_nox_stratospheric_water_vapor_decrease
        )
        nox_short_term_o3_increase_erf = self.df_climate["nox_short_term_o3_increase_erf"]
        nox_long_term_o3_decrease_erf = self.df_climate["nox_long_term_o3_decrease_erf"]
        nox_ch4_decrease_erf = self.df_climate["nox_ch4_decrease_erf"]
        nox_stratospheric_water_vapor_decrease_erf = self.df_climate[
            "nox_stratospheric_water_vapor_decrease_erf"
        ]
        nox_erf = (
            nox_short_term_o3_increase_erf
            + nox_long_term_o3_decrease_erf
            + nox_ch4_decrease_erf
            + nox_stratospheric_water_vapor_decrease_erf
        )
        self.df_climate["nox_erf"] = nox_erf

        return (
            nox_short_term_o3_increase_erf,
            nox_long_term_o3_decrease_erf,
            nox_ch4_decrease_erf,
            nox_stratospheric_water_vapor_decrease_erf,
            nox_erf,
        )


class ERFOthers(AeroMAPSModel):
    def __init__(self, name="effective_radiative_forcing_others", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        soot_emissions: pd.Series,
        h2o_emissions: pd.Series,
        sulfur_emissions: pd.Series,
        erf_coefficient_contrails: float,
        erf_coefficient_soot: float,
        erf_coefficient_h2o: float,
        erf_coefficient_sulfur: float,
        total_aircraft_distance: pd.Series,
        operations_contrails_gain: pd.Series,
        fuel_effect_correction_contrails: pd.Series,
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
        """ERF calculation for the other climate impacts of aviation."""

        # Contrails
        for k in range(self.climate_historic_start_year, self.end_year + 1):
            self.df_climate.loc[k, "contrails_erf"] = (
                total_aircraft_distance.loc[k] * erf_coefficient_contrails
            )
        for k in range(self.historic_start_year, self.end_year + 1):
            self.df_climate.loc[k, "contrails_erf"] = (
                total_aircraft_distance.loc[k]
                * erf_coefficient_contrails
                * (1 - operations_contrails_gain.loc[k] / 100)
                * fuel_effect_correction_contrails.loc[k]
            )
        contrails_erf = self.df_climate["contrails_erf"]

        # Others
        self.df_climate["soot_erf"] = soot_emissions * erf_coefficient_soot
        self.df_climate["h2o_erf"] = h2o_emissions * erf_coefficient_h2o
        self.df_climate["sulfur_erf"] = sulfur_emissions * erf_coefficient_sulfur
        soot_erf = self.df_climate["soot_erf"]
        h2o_erf = self.df_climate["h2o_erf"]
        sulfur_erf = self.df_climate["sulfur_erf"]
        self.df_climate["aerosol_erf"] = soot_erf + sulfur_erf
        aerosol_erf = self.df_climate["aerosol_erf"]

        return (
            contrails_erf,
            soot_erf,
            h2o_erf,
            sulfur_erf,
            aerosol_erf,
        )


class ERFTotal(AeroMAPSModel):
    def __init__(self, name="effective_radiative_forcing_total", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        co2_erf: pd.Series,
        contrails_erf: pd.Series,
        h2o_erf: pd.Series,
        nox_erf: pd.Series,
        soot_erf: pd.Series,
        sulfur_erf: pd.Series,
    ) -> pd.Series:
        """ERF calculation for the total climate impact of aviation."""

        self.df_climate["total_erf"] = (
            co2_erf + contrails_erf + h2o_erf + nox_erf + soot_erf + sulfur_erf
        )
        total_erf = self.df_climate["total_erf"]

        return total_erf


class ERFDetailed(AeroMAPSModel):
    def __init__(self, name="effective_radiative_forcing_detailed", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        co2_erf: pd.Series,
        contrails_erf: pd.Series,
        h2o_erf: pd.Series,
        nox_erf: pd.Series,
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """ERF calculation for helping plot display."""

        self.df_climate["co2_h2o_erf"] = co2_erf + h2o_erf
        self.df_climate["co2_h2o_nox_erf"] = co2_erf + h2o_erf + nox_erf
        self.df_climate["co2_h2o_nox_contrails_erf"] = co2_erf + h2o_erf + nox_erf + contrails_erf

        co2_h2o_erf = self.df_climate["co2_h2o_erf"]
        co2_h2o_nox_erf = self.df_climate["co2_h2o_nox_erf"]
        co2_h2o_nox_contrails_erf = self.df_climate["co2_h2o_nox_contrails_erf"]

        return co2_h2o_erf, co2_h2o_nox_erf, co2_h2o_nox_contrails_erf
