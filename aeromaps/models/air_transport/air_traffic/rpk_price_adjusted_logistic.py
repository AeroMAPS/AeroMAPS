from typing import Tuple

import pandas as pd
from numpy import divide
from numpy import exp

from aeromaps.models.base import AeroMAPSModel


def generalised_logistic_function(
    x, left_asymptote, capacity, growth_rate, logistic_nu, asymptote_coeff, x_lag
):
    y = left_asymptote + divide(
        capacity - left_asymptote,
        (asymptote_coeff + exp(
            -growth_rate * (x - x_lag)
        )) ** (1.0 / logistic_nu),
    )

    return y

def per_capita_logistic_price(
    population, gdp_per_capita, price,
    left_asymptote, capacity, growth_rate, logistic_nu, asymptote_coeff, x_lag,
    price_ref, price_elast
):
    rpk_per_capita_trend = generalised_logistic_function(
        x=gdp_per_capita,
        left_asymptote=left_asymptote,
        capacity=capacity,
        growth_rate=growth_rate,
        logistic_nu=logistic_nu,
        asymptote_coeff=asymptote_coeff,
        x_lag=x_lag,
    )
    price_index = (price / price_ref) ** price_elast
    rpk_per_capita = rpk_per_capita_trend * price_index
    rpk = population * rpk_per_capita
    return rpk, rpk_per_capita, rpk_per_capita_trend, price_index


class RPKPriceAdjustedLogistic(AeroMAPSModel):
    """
    Class to compute Revenue Passenger Kilometers (RPK) per capita using a generalised logistic function adjusted for price effects.

    Parameters
    ----------
    name : str
        Name of the model instance ('rpk_price_adjusted_logistic' by default).
    """

    def __init__(self, name="rpk_price_adjusted_logistic", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        # Calibrated logistic parameters (fixed at class level)
        self.left_asymptote: float = 0.0
        self.capacity: float = 11107.928628672116
        self.growth_rate: float = 0.00010075258175566807
        self.logistic_nu: float = 0.168484473
        self.asymptote_coeff: float = 1.148428926
        self.x_lag: float = 0.0
        self.price_elast: float = -0.26608795863374457
        # Reference energy cost per RPK from calibration [USD/RPK]
        self.price_ref: float = 0.012613517478578513
        # Exchange rate used to convert price_ref from USD to EUR [EUR/USD]
        self.eur_usd_exchange_rate: float = 0.9

    def compute(
        self,
        population: pd.Series,
        gdp_per_capita: pd.Series,
        doc_energy_per_rpk: pd.Series,
        gdp_per_capita_2019: float,
        gdp_per_capita_covid_end: float,
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
        """
        Execute the computation of RPK per capita using a generalised logistic function adjusted for price effects.

        Parameters
        ----------
        population
            Annual population [people].
        gdp_per_capita
            Annual GDP per capita [USD/capita].
        doc_energy_per_rpk
            Direct operating cost attributable to energy expenses per Revenue Passenger Kilometer [€/RPK].
        gdp_per_capita_2019
            GDP per capita at 2019 [USD/capita].
        gdp_per_capita_covid_end
            GDP per capita at end of covid [USD/capita].

        Returns
        -------
        rpk
            Annual RPKs [RPK].
        rpk_per_capita
            Annual RPKs per capita [RPK/capita].
        rpk_per_capita_trend
            RPK per capita trend from the logistic function without price adjustment [RPK/capita].
        price_index
            Price index applied to adjust RPK per capita based on energy cost per RPK.
        annual_growth_rate_rpk
            Year-on-year growth rate of total RPK [%/year].
        """
        # Convert reference price from USD to EUR so it is in the same currency as doc_energy_per_rpk
        price_ref_eur = self.price_ref * self.eur_usd_exchange_rate

        # COVID-19 horizontal shift: align the logistic curve to post-COVID GDP trajectory
        covid_shift = gdp_per_capita_covid_end - gdp_per_capita_2019

        rpk_per_capita_trend = generalised_logistic_function(
            x=gdp_per_capita,
            left_asymptote=self.left_asymptote,
            capacity=self.capacity,
            growth_rate=self.growth_rate,
            logistic_nu=self.logistic_nu,
            asymptote_coeff=self.asymptote_coeff,
            x_lag=self.x_lag + covid_shift,
        )

        price_index = (doc_energy_per_rpk / price_ref_eur) ** self.price_elast
        rpk_per_capita = rpk_per_capita_trend * price_index
        rpk = population * rpk_per_capita

        annual_growth_rate_rpk = rpk.pct_change() * 100

        self.df.loc[:, "rpk_per_capita_trend"] = rpk_per_capita_trend
        self.df.loc[:, "price_index"] = price_index
        self.df.loc[:, "rpk_per_capita"] = rpk_per_capita
        self.df.loc[:, "rpk"] = rpk
        self.df.loc[:, "annual_growth_rate_rpk"] = annual_growth_rate_rpk

        return (
            rpk,
            rpk_per_capita,
            rpk_per_capita_trend,
            price_index,
            annual_growth_rate_rpk,
        )
