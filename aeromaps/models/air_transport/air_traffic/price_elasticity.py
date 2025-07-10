from typing import Tuple
from numbers import Number

# import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from aeromaps.models.base import (
    AeroMAPSModel,
    aeromaps_leveling_function,
    # aeromaps_interpolation_function,
)


class RPKWithElasticity(AeroMAPSModel):
    def __init__(self, name="rpk_with_elasticity", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        rpk_init: pd.Series,
        short_range_rpk_share_2019: float,
        medium_range_rpk_share_2019: float,
        long_range_rpk_share_2019: float,
        covid_start_year: Number,
        covid_rpk_drop_start_year: float,
        covid_end_year_passenger: Number,
        covid_end_year_reference_rpk_ratio: float,
        cagr_passenger_short_range_reference_periods: list,
        cagr_passenger_short_range_reference_periods_values: list,
        cagr_passenger_medium_range_reference_periods: list,
        cagr_passenger_medium_range_reference_periods_values: list,
        cagr_passenger_long_range_reference_periods: list,
        cagr_passenger_long_range_reference_periods_values: list,
        rpk_short_range_measures_impact: pd.Series,
        rpk_medium_range_measures_impact: pd.Series,
        rpk_long_range_measures_impact: pd.Series,
        airfare_per_rpk: pd.Series,
        price_elasticity: float,
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
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
    ]:
        """Update RPK based on cost increase calculation."""

        hist_index = range(self.historic_start_year, self.prospection_start_year)
        covid_years = range(covid_start_year, covid_end_year_passenger + 1)
        proj_years = range(covid_end_year_passenger + 1, self.end_year + 1)
        # all_years = range(self.historic_start_year, self.end_year + 1)

        self.df.loc[hist_index, "rpk_short_range"] = (
            short_range_rpk_share_2019 / 100 * rpk_init.loc[hist_index]
        )
        self.df.loc[hist_index, "rpk_medium_range"] = (
            medium_range_rpk_share_2019 / 100 * rpk_init.loc[hist_index]
        )
        self.df.loc[hist_index, "rpk_long_range"] = (
            long_range_rpk_share_2019 / 100 * rpk_init.loc[hist_index]
        )

        # Covid functions
        reference_years = [covid_start_year, covid_end_year_passenger]
        reference_values_covid = [
            1 - covid_rpk_drop_start_year / 100,
            covid_end_year_reference_rpk_ratio / 100,
        ]
        covid_function = interp1d(reference_years, reference_values_covid, kind="linear")
        covid_factors = pd.Series([covid_function(k) for k in covid_years], index=covid_years)

        # CAGR function
        ## Short range
        annual_growth_rate_passenger_short_range_prospective = aeromaps_leveling_function(
            self,
            cagr_passenger_short_range_reference_periods,
            cagr_passenger_short_range_reference_periods_values,
            model_name=self.name,
        )
        self.df.loc[:, "annual_growth_rate_passenger_short_range"] = (
            annual_growth_rate_passenger_short_range_prospective
        )
        ## Medium range
        annual_growth_rate_passenger_medium_range_prospective = aeromaps_leveling_function(
            self,
            cagr_passenger_medium_range_reference_periods,
            cagr_passenger_medium_range_reference_periods_values,
            model_name=self.name,
        )
        self.df.loc[:, "annual_growth_rate_passenger_medium_range"] = (
            annual_growth_rate_passenger_medium_range_prospective
        )
        ## Long range
        annual_growth_rate_passenger_long_range_prospective = aeromaps_leveling_function(
            self,
            cagr_passenger_long_range_reference_periods,
            cagr_passenger_long_range_reference_periods_values,
            model_name=self.name,
        )
        self.df.loc[:, "annual_growth_rate_passenger_long_range"] = (
            annual_growth_rate_passenger_long_range_prospective
        )

        # Covid période vectorisée
        prev_short = self.df.loc[covid_start_year - 1, "rpk_short_range"]
        prev_medium = self.df.loc[covid_start_year - 1, "rpk_medium_range"]
        prev_long = self.df.loc[covid_start_year - 1, "rpk_long_range"]
        self.df.loc[covid_years, "rpk_short_range"] = prev_short * covid_factors
        self.df.loc[covid_years, "rpk_medium_range"] = prev_medium * covid_factors
        self.df.loc[covid_years, "rpk_long_range"] = prev_long * covid_factors

        # Prospective période vectorisée (hors covid)
        # Short
        growth_short = 1 + self.df.loc[proj_years, "annual_growth_rate_passenger_short_range"] / 100
        self.df.loc[proj_years, "rpk_short_range"] = (
            self.df.loc[covid_end_year_passenger, "rpk_short_range"] * growth_short.cumprod()
        )
        # Medium
        growth_medium = (
            1 + self.df.loc[proj_years, "annual_growth_rate_passenger_medium_range"] / 100
        )
        self.df.loc[proj_years, "rpk_medium_range"] = (
            self.df.loc[covid_end_year_passenger, "rpk_medium_range"] * growth_medium.cumprod()
        )
        # Long
        growth_long = 1 + self.df.loc[proj_years, "annual_growth_rate_passenger_long_range"] / 100
        self.df.loc[proj_years, "rpk_long_range"] = (
            self.df.loc[covid_end_year_passenger, "rpk_long_range"] * growth_long.cumprod()
        )

        rpk_short_range_no_elasticity = self.df["rpk_short_range"].copy()
        rpk_medium_range_no_elasticity = self.df["rpk_medium_range"].copy()
        rpk_long_range_no_elasticity = self.df["rpk_long_range"].copy()

        # rpk_no_elasticity
        self.df.loc[hist_index, "rpk_no_elasticity"] = rpk_init.loc[hist_index]
        self.df.loc[self.prospection_start_year : self.end_year, "rpk_no_elasticity"] = (
            self.df.loc[self.prospection_start_year : self.end_year, "rpk_short_range"].fillna(0)
            + self.df.loc[self.prospection_start_year : self.end_year, "rpk_medium_range"].fillna(0)
            + self.df.loc[self.prospection_start_year : self.end_year, "rpk_long_range"].fillna(0)
        )
        rpk_no_elasticity = self.df["rpk_no_elasticity"]

        self.df.loc[self.historic_start_year : covid_end_year_passenger, "rpk"] = (
            rpk_no_elasticity.loc[self.historic_start_year : covid_end_year_passenger]
        )

        airfare_init = 0.09236379319842411  # See total_airline_cost_and_airfare ==> IATA base value calibration

        #  airfare_init = pd.Series([
        # 0.09539189, 0.09571726, 0.09605239, 0.09639756, 0.09675307,
        # 0.09711924, 0.09749638, 0.09788483, 0.09828492, 0.09869701,
        # 0.09912144, 0.0995586 , 0.10000887, 0.10047264, 0.10095031,
        # 0.1014423 , 0.10194905, 0.10247099, 0.10300858, 0.10356229,
        # 0.10413261, 0.10472003, 0.10532506, 0.10594824, 0.10659012,
        # 0.10725124], index=range(2025, 2051))

        self.df.loc[covid_end_year_passenger + 1 : self.end_year, "rpk"] = (
            rpk_no_elasticity
            / (airfare_init**price_elasticity)
            * (
                airfare_per_rpk.loc[covid_end_year_passenger + 1 : self.end_year]
                ** price_elasticity
            )
        )

        # Répartition par segment vectorisée
        rpk_short_range = self.df["rpk_short_range"] * self.df["rpk"] / rpk_no_elasticity
        rpk_medium_range = self.df["rpk_medium_range"] * self.df["rpk"] / rpk_no_elasticity
        rpk_long_range = self.df["rpk_long_range"] * self.df["rpk"] / rpk_no_elasticity

        # TODO discuss if that should be considered for surplus destruction. I think so => not inlcluded in rpk_no_elasticity
        rpk_short_range = rpk_short_range * rpk_short_range_measures_impact
        rpk_medium_range = rpk_medium_range * rpk_medium_range_measures_impact
        rpk_long_range = rpk_long_range * rpk_long_range_measures_impact

        self.df.loc[:, "rpk_short_range"] = rpk_short_range
        self.df.loc[:, "rpk_medium_range"] = rpk_medium_range
        self.df.loc[:, "rpk_long_range"] = rpk_long_range

        # Total RPK vectorisé
        self.df.loc[hist_index, "rpk"] = rpk_init.loc[hist_index]
        self.df.loc[self.prospection_start_year : self.end_year, "rpk"] = (
            self.df.loc[self.prospection_start_year : self.end_year, "rpk_short_range"].fillna(0)
            + self.df.loc[self.prospection_start_year : self.end_year, "rpk_medium_range"].fillna(0)
            + self.df.loc[self.prospection_start_year : self.end_year, "rpk_long_range"].fillna(0)
        )
        rpk = self.df["rpk"]

        # Annual growth rates vectorisés
        idx_growth = range(self.historic_start_year + 1, self.end_year + 1)
        self.df.loc[idx_growth, "annual_growth_rate_passenger_short_range"] = (
            self.df["rpk_short_range"].loc[idx_growth].values
            / self.df["rpk_short_range"].shift(1).loc[idx_growth].values
            - 1
        ) * 100
        self.df.loc[idx_growth, "annual_growth_rate_passenger_medium_range"] = (
            self.df["rpk_medium_range"].loc[idx_growth].values
            / self.df["rpk_medium_range"].shift(1).loc[idx_growth].values
            - 1
        ) * 100
        self.df.loc[idx_growth, "annual_growth_rate_passenger_long_range"] = (
            self.df["rpk_long_range"].loc[idx_growth].values
            / self.df["rpk_long_range"].shift(1).loc[idx_growth].values
            - 1
        ) * 100
        self.df.loc[idx_growth, "annual_growth_rate_passenger"] = (
            self.df["rpk"].loc[idx_growth].values / self.df["rpk"].shift(1).loc[idx_growth].values
            - 1
        ) * 100

        annual_growth_rate_passenger_short_range = self.df[
            "annual_growth_rate_passenger_short_range"
        ]
        annual_growth_rate_passenger_medium_range = self.df[
            "annual_growth_rate_passenger_medium_range"
        ]
        annual_growth_rate_passenger_long_range = self.df["annual_growth_rate_passenger_long_range"]
        annual_growth_rate_passenger = self.df["annual_growth_rate_passenger"]

        # Compound Annual Growth Rate (CAGR)
        cagr_rpk_short_range = 100 * (
            (
                self.df.loc[self.end_year, "rpk_short_range"]
                / self.df.loc[self.prospection_start_year - 1, "rpk_short_range"]
            )
            ** (1 / (self.end_year - self.prospection_start_year))
            - 1
        )
        cagr_rpk_medium_range = 100 * (
            (
                self.df.loc[self.end_year, "rpk_medium_range"]
                / self.df.loc[self.prospection_start_year - 1, "rpk_medium_range"]
            )
            ** (1 / (self.end_year - self.prospection_start_year))
            - 1
        )
        cagr_rpk_long_range = 100 * (
            (
                self.df.loc[self.end_year, "rpk_long_range"]
                / self.df.loc[self.prospection_start_year - 1, "rpk_long_range"]
            )
            ** (1 / (self.end_year - self.prospection_start_year))
            - 1
        )
        cagr_rpk = 100 * (
            (
                self.df.loc[self.end_year, "rpk"]
                / self.df.loc[self.prospection_start_year - 1, "rpk"]
            )
            ** (1 / (self.end_year - self.prospection_start_year))
            - 1
        )

        # Prospective evolution of RPK (between prospection_start_year-1 and end_year)
        prospective_evolution_rpk_short_range = 100 * (
            self.df.loc[self.end_year, "rpk_short_range"]
            / self.df.loc[self.prospection_start_year - 1, "rpk_short_range"]
            - 1
        )
        prospective_evolution_rpk_medium_range = 100 * (
            self.df.loc[self.end_year, "rpk_medium_range"]
            / self.df.loc[self.prospection_start_year - 1, "rpk_medium_range"]
            - 1
        )
        prospective_evolution_rpk_long_range = 100 * (
            self.df.loc[self.end_year, "rpk_long_range"]
            / self.df.loc[self.prospection_start_year - 1, "rpk_long_range"]
            - 1
        )
        prospective_evolution_rpk = 100 * (
            self.df.loc[self.end_year, "rpk"] / self.df.loc[self.prospection_start_year - 1, "rpk"]
            - 1
        )

        self.float_outputs["cagr_rpk_short_range"] = cagr_rpk_short_range
        self.float_outputs["cagr_rpk_medium_range"] = cagr_rpk_medium_range
        self.float_outputs["cagr_rpk_long_range"] = cagr_rpk_long_range
        self.float_outputs["cagr_rpk"] = cagr_rpk
        self.float_outputs["prospective_evolution_rpk_short_range"] = (
            prospective_evolution_rpk_short_range
        )
        self.float_outputs["prospective_evolution_rpk_medium_range"] = (
            prospective_evolution_rpk_medium_range
        )
        self.float_outputs["prospective_evolution_rpk_long_range"] = (
            prospective_evolution_rpk_long_range
        )
        self.float_outputs["prospective_evolution_rpk"] = prospective_evolution_rpk

        return (
            rpk_short_range,
            rpk_medium_range,
            rpk_long_range,
            rpk,
            rpk_no_elasticity,
            rpk_short_range_no_elasticity,
            rpk_medium_range_no_elasticity,
            rpk_long_range_no_elasticity,
            annual_growth_rate_passenger_short_range,
            annual_growth_rate_passenger_medium_range,
            annual_growth_rate_passenger_long_range,
            annual_growth_rate_passenger,
            cagr_rpk_short_range,
            cagr_rpk_medium_range,
            cagr_rpk_long_range,
            cagr_rpk,
            prospective_evolution_rpk_short_range,
            prospective_evolution_rpk_medium_range,
            prospective_evolution_rpk_long_range,
            prospective_evolution_rpk,
        )
