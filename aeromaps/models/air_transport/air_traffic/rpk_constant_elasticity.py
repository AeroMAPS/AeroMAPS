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
        population: pd.Series,
        gdp_per_capita: pd.Series,
        doc_energy_per_rpk: pd.Series,
        gdp_per_capita_2019: float,
        gdp_per_capita_covid_end: float,
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Compute prospective RPK from population, GDP per capita and energy cost per RPK.

        Parameters
        ----------
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

        Returns
        -------
        rpk
            Annual Revenue Passenger Kilometers [RPK].
        rpk_per_capita
            Annual RPKs per capita [RPK/capita].
        annual_growth_rate_rpk
            Year-on-year growth rate of total RPK [%/year].
        """
        # Convert price from EUR to USD to match the calibration currency
        price_usd = doc_energy_per_rpk / self.eur_usd_exchange_rate

        # COVID-19 lag: shift the effective GDP per capita back by the gap caused by COVID,
        # so that the demand curve reflects the post-COVID recovery trajectory
        covid_shift = gdp_per_capita_covid_end - gdp_per_capita_2019
        gdp_per_capita_shifted = gdp_per_capita - covid_shift

        rpk_per_capita = (
            self.sigma
            * (gdp_per_capita_shifted ** self.income_elast)
            * (price_usd ** self.price_elast)
        )
        rpk = population * rpk_per_capita

        annual_growth_rate_rpk = rpk.pct_change() * 100

        self.df.loc[:, "rpk_per_capita"] = rpk_per_capita
        self.df.loc[:, "rpk"] = rpk
        self.df.loc[:, "annual_growth_rate_rpk"] = annual_growth_rate_rpk

        return (
            rpk,
            rpk_per_capita,
            annual_growth_rate_rpk,
        )

