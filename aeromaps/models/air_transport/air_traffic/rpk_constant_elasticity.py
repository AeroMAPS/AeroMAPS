from typing import Tuple

import pandas as pd

from aeromaps.models.base import AeroMAPSModel


def constant_elasticity(
    population, gdp_per_capita, price,
    sigma, income_elast, price_elast
):
    rpk_per_capita = sigma * (gdp_per_capita ** income_elast) * (price ** price_elast)
    rpk = population * rpk_per_capita
    return rpk, rpk_per_capita


class RPKConstantElasticity(AeroMAPSModel):
    """
    Compute Revenue Passenger Kilometers (RPK) using a constant-elasticity demand model.

    RPK per capita is modelled as:
        rpk_per_capita = sigma * gdp_per_capita^income_elast * price^price_elast

    where ``sigma``, ``income_elast`` and ``price_elast`` are calibrated coefficients
    fixed at the class level.  The price input (``doc_energy_per_rpk``) is expressed
    in EUR/RPK and is converted to USD before evaluation so that the units match the
    original calibration.

    Parameters
    ----------
    name : str
        Name of the model instance ('rpk_constant_elasticity' by default).
    """

    def __init__(self, name="rpk_constant_elasticity", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        # Calibrated constant-elasticity parameters (fixed at class level)
        self.sigma: float = 0.0015018367707702585
        self.income_elast: float = 1.318374753418146
        self.price_elast: float = -0.2808214954796415
        # Exchange rate used to convert doc_energy_per_rpk from EUR to USD [EUR/USD]
        self.eur_usd_exchange_rate: float = 0.9

    def compute(
        self,
        rpk_init: pd.Series,
        population: pd.Series,
        gdp_per_capita: pd.Series,
        doc_energy_per_rpk: pd.Series,
        gdp_per_capita_2019: float,
        gdp_per_capita_covid_end: float,
        gdp_per_capita_init: pd.Series,
        population_init: pd.Series,
        short_range_rpk_share_2019: float,
        medium_range_rpk_share_2019: float,
        long_range_rpk_share_2019: float,
        rpk_short_range_measures_impact: pd.Series,
        rpk_medium_range_measures_impact: pd.Series,
        rpk_long_range_measures_impact: pd.Series,
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
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        float,
        pd.Series,
    ]:
        """
        Compute prospective RPK from population, GDP per capita and energy cost per RPK.

        Parameters
        ----------
        rpk_init
            Historical number of Revenue Passenger Kilometer (RPK) over 2000-2019 [RPK].
        population
            Annual world population [people].
        gdp_per_capita
            Annual GDP per capita [USD/capita].
        doc_energy_per_rpk
            Direct operating cost attributable to energy expenses per Revenue
            Passenger Kilometer [€/RPK].
        gdp_per_capita_2019
            GDP per capita at 2019 [USD/capita].
        gdp_per_capita_covid_end
            GDP per capita at end of covid [USD/capita].
        gdp_per_capita_init
            Historical GDP per capita over the historic period [USD/capita].
        population_init
            Historical world population over the historic period [people].
        short_range_rpk_share_2019
            Share of RPK from short-range market in 2019 [%].
        medium_range_rpk_share_2019
            Share of RPK from medium-range market in 2019 [%].
        long_range_rpk_share_2019
            Share of RPK from long-range market in 2019 [%].
        rpk_short_range_measures_impact
            Traffic reduction impact of specific measures for passenger short-range market [-].
        rpk_medium_range_measures_impact
            Traffic reduction impact of specific measures for passenger medium-range market [-].
        rpk_long_range_measures_impact
            Traffic reduction impact of specific measures for passenger long-range market [-].

        Returns
        -------
        rpk_short_range
            Number of RPK for passenger short-range market [RPK].
        rpk_medium_range
            Number of RPK for passenger medium-range market [RPK].
        rpk_long_range
            Number of RPK for passenger long-range market [RPK].
        rpk
            Number of RPK for total passenger air transport [RPK].
        rpk_per_capita
            Annual RPKs per capita [RPK/capita].
        annual_growth_rate_passenger_short_range
            Annual growth rate for short-range passengers [%/year].
        annual_growth_rate_passenger_medium_range
            Annual growth rate for medium-range passengers [%/year].
        annual_growth_rate_passenger_long_range
            Annual growth rate for long-range passengers [%/year].
        annual_growth_rate_passenger
            Annual growth rate for total passengers [%/year].
        cagr_rpk_short_range
            Air traffic CAGR over prospective years for passenger short-range market [%].
        cagr_rpk_medium_range
            Air traffic CAGR over prospective years for passenger medium-range market [%].
        cagr_rpk_long_range
            Air traffic CAGR over prospective years for passenger long-range market [%].
        cagr_rpk
            Air traffic CAGR over prospective years for total passenger market [%].
        prospective_evolution_rpk_short_range
            Evolution of RPK for short-range market between prospection_start_year and end_year [%].
        prospective_evolution_rpk_medium_range
            Evolution of RPK for medium-range market between prospection_start_year and end_year [%].
        prospective_evolution_rpk_long_range
            Evolution of RPK for long-range market between prospection_start_year and end_year [%].
        prospective_evolution_rpk
            Evolution of total RPK between prospection_start_year and end_year [%].
        rpk_model_without_covid
            Annual RPKs from the model without the COVID GDP lag. Historic years are estimated
            from the constant-elasticity model using gdp_per_capita_init and population_init
            (at reference price); prospective years use the projected inputs without the
            COVID shift [RPK].
        """
        price_usd = doc_energy_per_rpk / self.eur_usd_exchange_rate
        covid_shift = gdp_per_capita_covid_end - gdp_per_capita_2019
        hist_slice = slice(self.historic_start_year, self.prospection_start_year - 1)

        # --- Per-capita RPK (with and without COVID lag) ---
        rpk_per_capita = (
            self.sigma
            * ((gdp_per_capita - covid_shift) ** self.income_elast)
            * (price_usd ** self.price_elast)
        )
        rpk_per_capita_no_covid = (
            self.sigma
            * (gdp_per_capita ** self.income_elast)
            * (price_usd ** self.price_elast)
        )
        rpk_per_capita_no_covid_hist = self.sigma * (gdp_per_capita_init ** self.income_elast)

        # --- Total RPK (model, no measures yet) ---
        rpk_model_total = population * rpk_per_capita

        # --- Build rpk_model_without_covid (historic from gdp_init/pop_init, no price adj.) ---
        rpk_model_without_covid_raw = population * rpk_per_capita_no_covid
        rpk_model_without_covid_raw.loc[hist_slice] = (
            population_init * rpk_per_capita_no_covid_hist
        ).loc[hist_slice]

        # --- Per-segment split (historic uses rpk_init * share) ---
        rpk_short_range = rpk_model_total * short_range_rpk_share_2019 / 100
        rpk_medium_range = rpk_model_total * medium_range_rpk_share_2019 / 100
        rpk_long_range = rpk_model_total * long_range_rpk_share_2019 / 100

        rpk_short_range.loc[hist_slice] = rpk_init.loc[hist_slice] * short_range_rpk_share_2019 / 100
        rpk_medium_range.loc[hist_slice] = rpk_init.loc[hist_slice] * medium_range_rpk_share_2019 / 100
        rpk_long_range.loc[hist_slice] = rpk_init.loc[hist_slice] * long_range_rpk_share_2019 / 100

        # --- Apply measures ---
        rpk_short_range = rpk_short_range * rpk_short_range_measures_impact
        rpk_medium_range = rpk_medium_range * rpk_medium_range_measures_impact
        rpk_long_range = rpk_long_range * rpk_long_range_measures_impact

        rpk = rpk_short_range + rpk_medium_range + rpk_long_range

        # --- rpk_model_without_covid: apply measures to segment split ---
        rpk_wc_short = rpk_model_without_covid_raw * short_range_rpk_share_2019 / 100 * rpk_short_range_measures_impact
        rpk_wc_medium = rpk_model_without_covid_raw * medium_range_rpk_share_2019 / 100 * rpk_medium_range_measures_impact
        rpk_wc_long = rpk_model_without_covid_raw * long_range_rpk_share_2019 / 100 * rpk_long_range_measures_impact
        rpk_model_without_covid = rpk_wc_short + rpk_wc_medium + rpk_wc_long

        # --- Annual growth rates ---
        annual_growth_rate_passenger_short_range = rpk_short_range.pct_change() * 100
        annual_growth_rate_passenger_medium_range = rpk_medium_range.pct_change() * 100
        annual_growth_rate_passenger_long_range = rpk_long_range.pct_change() * 100
        annual_growth_rate_passenger = rpk.pct_change() * 100

        # --- CAGRs (prospective period) ---
        n = self.end_year - self.prospection_start_year
        cagr_rpk_short_range = 100 * (
            (rpk_short_range.loc[self.end_year] / rpk_short_range.loc[self.prospection_start_year - 1])
            ** (1 / n) - 1
        )
        cagr_rpk_medium_range = 100 * (
            (rpk_medium_range.loc[self.end_year] / rpk_medium_range.loc[self.prospection_start_year - 1])
            ** (1 / n) - 1
        )
        cagr_rpk_long_range = 100 * (
            (rpk_long_range.loc[self.end_year] / rpk_long_range.loc[self.prospection_start_year - 1])
            ** (1 / n) - 1
        )
        cagr_rpk = 100 * (
            (rpk.loc[self.end_year] / rpk.loc[self.prospection_start_year - 1])
            ** (1 / n) - 1
        )

        # --- Prospective evolutions ---
        prospective_evolution_rpk_short_range = 100 * (
            rpk_short_range.loc[self.end_year] / rpk_short_range.loc[self.prospection_start_year - 1] - 1
        )
        prospective_evolution_rpk_medium_range = 100 * (
            rpk_medium_range.loc[self.end_year] / rpk_medium_range.loc[self.prospection_start_year - 1] - 1
        )
        prospective_evolution_rpk_long_range = 100 * (
            rpk_long_range.loc[self.end_year] / rpk_long_range.loc[self.prospection_start_year - 1] - 1
        )
        prospective_evolution_rpk = 100 * (
            rpk.loc[self.end_year] / rpk.loc[self.prospection_start_year - 1] - 1
        )

        # --- Store ---
        self.df.loc[:, "rpk_short_range"] = rpk_short_range
        self.df.loc[:, "rpk_medium_range"] = rpk_medium_range
        self.df.loc[:, "rpk_long_range"] = rpk_long_range
        self.df.loc[:, "rpk"] = rpk
        self.df.loc[:, "rpk_per_capita"] = rpk_per_capita
        self.df.loc[:, "annual_growth_rate_passenger_short_range"] = annual_growth_rate_passenger_short_range
        self.df.loc[:, "annual_growth_rate_passenger_medium_range"] = annual_growth_rate_passenger_medium_range
        self.df.loc[:, "annual_growth_rate_passenger_long_range"] = annual_growth_rate_passenger_long_range
        self.df.loc[:, "annual_growth_rate_passenger"] = annual_growth_rate_passenger
        self.df.loc[:, "rpk_model_without_covid"] = rpk_model_without_covid

        self.float_outputs["cagr_rpk_short_range"] = cagr_rpk_short_range
        self.float_outputs["cagr_rpk_medium_range"] = cagr_rpk_medium_range
        self.float_outputs["cagr_rpk_long_range"] = cagr_rpk_long_range
        self.float_outputs["cagr_rpk"] = cagr_rpk
        self.float_outputs["prospective_evolution_rpk_short_range"] = prospective_evolution_rpk_short_range
        self.float_outputs["prospective_evolution_rpk_medium_range"] = prospective_evolution_rpk_medium_range
        self.float_outputs["prospective_evolution_rpk_long_range"] = prospective_evolution_rpk_long_range
        self.float_outputs["prospective_evolution_rpk"] = prospective_evolution_rpk

        return (
            rpk_short_range,
            rpk_medium_range,
            rpk_long_range,
            rpk,
            rpk_per_capita,
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
            rpk_model_without_covid,
        )
