from typing import Tuple

import pandas as pd
from scipy.interpolate import interp1d

from aeromaps.models.base import AeroMAPSModel, AeromapsLevelingFunction


class RTK(AeroMAPSModel):
    def __init__(self, name="rtk", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        rtk_init: pd.Series,
        covid_start_year: int,
        covid_rtk_drop_start_year: float,
        covid_end_year_freight: int,
        covid_end_year_reference_rtk_ratio: float,
        cagr_freight_reference_periods: list,
        cagr_freight_reference_periods_values: list,
    ) -> Tuple[pd.Series, pd.Series, float, float]:
        """RTK calculation."""

        # Initialization
        self.df.loc[self.prospection_start_year - 1, "rtk"] = rtk_init.loc[
            self.prospection_start_year - 1
        ]

        # Covid functions
        reference_years = [covid_start_year, covid_end_year_freight]
        reference_values_covid = [
            1 - covid_rtk_drop_start_year / 100,
            covid_end_year_reference_rtk_ratio / 100,
        ]
        covid_function = interp1d(reference_years, reference_values_covid, kind="linear")

        # CAGR function
        annual_growth_rate_freight_prospective = AeromapsLevelingFunction(
            self,
            cagr_freight_reference_periods,
            cagr_freight_reference_periods_values,
            model_name=self.name,
        )
        self.df.loc[:, "annual_growth_rate_freight"] = annual_growth_rate_freight_prospective

        # Main
        for k in range(covid_start_year, covid_end_year_freight + 1):
            self.df.loc[k, "rtk"] = self.df.loc[covid_start_year - 1, "rtk"] * covid_function(k)
        for k in range(covid_end_year_freight + 1, self.end_year + 1):
            self.df.loc[k, "rtk"] = self.df.loc[k - 1, "rtk"] * (
                1 + self.df.loc[k, "annual_growth_rate_freight"] / 100
            )

        # Historic values
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "rtk"] = rtk_init.loc[k]
        for k in range(self.historic_start_year + 1, self.prospection_start_year):
            self.df.loc[k, "annual_growth_rate_freight"] = (
                self.df.loc[k, "rtk"] / self.df.loc[k - 1, "rtk"] - 1
            ) * 100
        rtk = self.df["rtk"]
        annual_growth_rate_freight = self.df["annual_growth_rate_freight"]

        # Compound Annual Growth Rate (CAGR)
        cagr_rtk = 100 * (
            (
                self.df.loc[self.end_year, "rtk"]
                / self.df.loc[self.prospection_start_year - 1, "rtk"]
            )
            ** (1 / (self.end_year - self.prospection_start_year))
            - 1
        )

        # Prospective evolution of RTK (between prospection_start_year-1 and end_year)
        prospective_evolution_rtk = 100 * (
            self.df.loc[self.end_year, "rtk"] / self.df.loc[self.prospection_start_year - 1, "rtk"]
            - 1
        )

        self.float_outputs["cagr_rtk"] = cagr_rtk
        self.float_outputs["prospective_evolution_rtk"] = prospective_evolution_rtk

        return (
            rtk,
            annual_growth_rate_freight,
            cagr_rtk,
            prospective_evolution_rtk,
        )


class RTKReference(AeroMAPSModel):
    def __init__(self, name="rtk_reference", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        rtk: pd.Series,
        reference_cagr_freight_reference_periods: list,
        reference_cagr_freight_reference_periods_values: list,
        covid_start_year: int,
        covid_rtk_drop_start_year: float,
        covid_end_year_freight: int,
        covid_end_year_reference_rtk_ratio: float,
    ) -> Tuple[pd.Series, pd.Series]:
        """RTK reference calculation."""

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "rtk_reference"] = rtk.loc[k]

        covid_start_year = int(covid_start_year)
        covid_rtk_drop_start_year = int(covid_rtk_drop_start_year)
        covid_end_year_freight = int(covid_end_year_freight)
        covid_end_year_reference_rtk_ratio = int(covid_end_year_reference_rtk_ratio)

        self.df.loc[covid_start_year - 1, "rtk_reference"] = rtk.loc[covid_start_year - 1]

        # Covid functions
        reference_years = [covid_start_year, covid_end_year_freight]
        reference_values_covid = [
            1 - covid_rtk_drop_start_year / 100,
            covid_end_year_reference_rtk_ratio / 100,
        ]
        covid_function = interp1d(reference_years, reference_values_covid, kind="linear")

        # CAGR function
        reference_annual_growth_rate_freight = AeromapsLevelingFunction(
            self,
            reference_cagr_freight_reference_periods,
            reference_cagr_freight_reference_periods_values,
            model_name=self.name,
        )
        self.df.loc[:, "reference_annual_growth_rate_freight"] = (
            reference_annual_growth_rate_freight
        )

        # Main
        for k in range(covid_start_year, covid_end_year_freight + 1):
            self.df.loc[k, "rtk_reference"] = self.df.loc[
                covid_start_year - 1, "rtk_reference"
            ] * covid_function(k)
        for k in range(covid_end_year_freight + 1, self.end_year + 1):
            self.df.loc[k, "rtk_reference"] = self.df.loc[k - 1, "rtk_reference"] * (
                1 + self.df.loc[k, "reference_annual_growth_rate_freight"] / 100
            )

        rtk_reference = self.df["rtk_reference"]

        return (rtk_reference, reference_annual_growth_rate_freight)
