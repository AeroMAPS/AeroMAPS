from typing import Tuple
import numpy as np
import pandas as pd

from aeromaps.models.base import AeromapsModel


class ERF(AeromapsModel):
    def __init__(self, name="effective_radiative_forcing", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        soot_emissions: pd.Series = pd.Series(dtype="float64"),
        co2_emissions: pd.Series = pd.Series(dtype="float64"),
        h2o_emissions: pd.Series = pd.Series(dtype="float64"),
        nox_emissions: pd.Series = pd.Series(dtype="float64"),
        sulfur_emissions: pd.Series = pd.Series(dtype="float64"),
        direct_co2_erf_2018_reference: float = 0.0,
        kerosene_emission_factor_2019: float = 0.0,
        erf_coefficient_soot: float = 0.0,
        erf_coefficient_co2: float = 0.0,
        erf_coefficient_contrails: float = 0.0,
        erf_coefficient_h2o: float = 0.0,
        erf_coefficient_nox: float = 0.0,
        erf_coefficient_sulfur: float = 0.0,
        total_aircraft_distance: pd.Series = pd.Series(dtype="float64"),
        operations_contrails_gain: pd.Series = pd.Series(dtype="float64"),
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
    ]:
        """ERF calculation for the different climate impacts of aviation."""

        # CO2
        self.df["annual_co2_erf"] = co2_emissions * erf_coefficient_co2 / 1000

        # To improve
        reference_year = 2018
        co2_erf_2018_reference = (
            direct_co2_erf_2018_reference * kerosene_emission_factor_2019 / 73.2
        )

        self.df.loc[reference_year, "co2_erf"] = co2_erf_2018_reference
        for k in range(self.historic_start_year, reference_year):
            self.df.loc[self.historic_start_year + reference_year - 1 - k, "co2_erf"] = (
                self.df.loc[self.historic_start_year + reference_year - k, "co2_erf"]
                - self.df.loc[self.historic_start_year + reference_year - 1 - k, "annual_co2_erf"]
            )
        for k in range(reference_year + 1, self.end_year + 1):
            self.df.loc[k, "co2_erf"] = (
                self.df.loc[k - 1, "co2_erf"] + self.df.loc[k, "annual_co2_erf"]
            )

        annual_co2_erf = self.df["annual_co2_erf"]
        co2_erf = self.df["co2_erf"]

        # Contrails
        self.df["contrails_erf"] = (
            total_aircraft_distance
            * erf_coefficient_contrails
            * (1 - operations_contrails_gain / 100)
        )
        contrails_erf = self.df["contrails_erf"]

        # Others
        self.df["soot_erf"] = soot_emissions * erf_coefficient_soot
        self.df["h2o_erf"] = h2o_emissions * erf_coefficient_h2o
        self.df["nox_erf"] = nox_emissions * erf_coefficient_nox
        self.df["sulfur_erf"] = sulfur_emissions * erf_coefficient_sulfur
        soot_erf = self.df["soot_erf"]
        h2o_erf = self.df["h2o_erf"]
        nox_erf = self.df["nox_erf"]
        sulfur_erf = self.df["sulfur_erf"]

        # Total
        self.df["aerosol_erf"] = soot_erf + sulfur_erf
        self.df["total_erf"] = co2_erf + contrails_erf + h2o_erf + nox_erf + soot_erf + sulfur_erf
        aerosol_erf = self.df["aerosol_erf"]
        total_erf = self.df["total_erf"]

        return (
            annual_co2_erf,
            co2_erf,
            contrails_erf,
            soot_erf,
            h2o_erf,
            nox_erf,
            sulfur_erf,
            aerosol_erf,
            total_erf,
        )


class DetailedERF(AeromapsModel):
    def __init__(self, name="detailed_erf", *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def compute(
        self,
        co2_erf: pd.Series = pd.Series(dtype="float64"),
        contrails_erf: pd.Series = pd.Series(dtype="float64"),
        h2o_erf: pd.Series = pd.Series(dtype="float64"),
        nox_erf: pd.Series = pd.Series(dtype="float64"),
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """ERF calculation for helping plot display."""

        self.df["co2_h2o_erf"] = co2_erf + h2o_erf
        self.df["co2_h2o_nox_erf"] = co2_erf + h2o_erf + nox_erf
        self.df["co2_h2o_nox_contrails_erf"] = co2_erf + h2o_erf + nox_erf + contrails_erf

        co2_h2o_erf = self.df["co2_h2o_erf"]
        co2_h2o_nox_erf = self.df["co2_h2o_nox_erf"]
        co2_h2o_nox_contrails_erf = self.df["co2_h2o_nox_contrails_erf"]

        return co2_h2o_erf, co2_h2o_nox_erf, co2_h2o_nox_contrails_erf
