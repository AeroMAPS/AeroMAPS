from typing import Tuple
from numbers import Number

import pandas as pd
from numpy import divide
from numpy import exp
from scipy.interpolate import interp1d

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

class RPKLogisticIncomePriceElasticity(AeroMAPSModel):
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
        self.capacity: float = 10567.171437822739
        self.growth_rate: float = 0.00011537900000000001
        self.logistic_nu: float = 0.168484473
        self.asymptote_coeff: float = 1.148428926
        self.x_lag: float = 0.0
        self.price_elast: float = -0.34504782729982275
        # Reference all-energy cost per RPK from calibration [USD/RPK]
        self.price_ref: float = 0.00947670537084349
        # Calibrated price-response delay (first-order lag time constant) [yr]; 0.0 disables it.
        self.price_delay: float = 1.2562195408290782
        # Exchange rate used to convert price_ref from USD to EUR [EUR/USD]
        self.eur_usd_exchange_rate: float = 0.9

    def _initialize_df(self):
        super()._initialize_df()
        # Seed value for MDA coupling initialization: reference all-energy cost per RPK in EUR
        self._coupling_defaults = {
            "doc_net_energy_per_rpk_mean": pd.Series(
                self.price_ref * self.eur_usd_exchange_rate,  # EUR/RPK
                index=range(self.historic_start_year, self.end_year + 1),
            )
        }

    def _apply_price_delay(self, price):
        delayed = price.copy()
        tau = getattr(self, "price_delay", 0.0)
        if not tau or tau <= 0.0:
            return delayed
        a = float(exp(-1.0 / tau))  # annual step, dt = 1 year
        prev = float(price.loc[self.prospection_start_year])
        delayed.loc[self.prospection_start_year] = prev
        for year in range(self.prospection_start_year + 1, self.end_year + 1):
            prev = a * prev + (1.0 - a) * float(price.loc[year])
            delayed.loc[year] = prev
        return delayed

    def compute(
        self,
        rpk_init: pd.Series,
        population: pd.Series,
        gdp_per_capita: pd.Series,
        doc_net_energy_per_rpk_mean: pd.Series,
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
        covid_start_year: Number,
        covid_rpk_drop_start_year: float,
        covid_end_year_passenger: Number,
        covid_end_year_reference_rpk_ratio: float,
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
        pd.Series,
        pd.Series,
    ]:
        """
        Execute the computation of RPK per capita using a generalised logistic function adjusted for price effects.

        Parameters
        ----------
        rpk_init
            Historical number of Revenue Passenger Kilometer (RPK) over 2000-2019 [RPK].
        population
            Annual population [people].
        gdp_per_capita
            Annual GDP per capita [USD/capita].
        doc_net_energy_per_rpk_mean
            Total energy-related direct operating cost (energy + carbon tax - subsidy + energy tax) per Revenue Passenger Kilometer [€/RPK].
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
        covid_start_year
            Start year of the COVID period for override [year].
        covid_rpk_drop_start_year
            RPK reduction at the start of the COVID period for override [%].
        covid_end_year_passenger
            End year of the COVID period for passenger RPK recovery override [year].
        covid_end_year_reference_rpk_ratio
            RPK ratio at the end of the COVID period for override (relative to 2019) [%].

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
        rpk_no_elasticity
            RPKs without considering price elasticity (logistic trend only) [RPK].
        rpk_per_capita
            Annual RPKs per capita [RPK/capita].
        rpk_per_capita_trend
            RPK per capita trend from the logistic function without price adjustment [RPK/capita].
        price_index
            Price index applied to adjust RPK per capita based on energy cost per RPK.
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
            Annual RPKs from the model without the COVID lag correction. Historic years are
            estimated from the logistic model using gdp_per_capita_init and population_init
            (at reference price); prospective years use the projected inputs without the
            COVID shift [RPK].
        doc_net_energy_per_rpk_delayed
            Energy cost per RPK after applying the first-order price-response lag, i.e. the
            consumer-perceived price that drives the price index [€/RPK].
        """
        price_ref_eur = self.price_ref * self.eur_usd_exchange_rate
        covid_shift = gdp_per_capita_covid_end - gdp_per_capita_2019
        hist_slice = slice(self.historic_start_year, self.prospection_start_year - 1)

        # --- Logistic trends ---
        rpk_per_capita_trend = generalised_logistic_function(
            x=gdp_per_capita,
            left_asymptote=self.left_asymptote,
            capacity=self.capacity,
            growth_rate=self.growth_rate,
            logistic_nu=self.logistic_nu,
            asymptote_coeff=self.asymptote_coeff,
            x_lag=self.x_lag + covid_shift,
        )
        rpk_per_capita_trend_no_covid = generalised_logistic_function(
            x=gdp_per_capita,
            left_asymptote=self.left_asymptote,
            capacity=self.capacity,
            growth_rate=self.growth_rate,
            logistic_nu=self.logistic_nu,
            asymptote_coeff=self.asymptote_coeff,
            x_lag=self.x_lag,
        )
        rpk_per_capita_trend_hist = generalised_logistic_function(
            x=gdp_per_capita_init,
            left_asymptote=self.left_asymptote,
            capacity=self.capacity,
            growth_rate=self.growth_rate,
            logistic_nu=self.logistic_nu,
            asymptote_coeff=self.asymptote_coeff,
            x_lag=self.x_lag,
        )

        doc_net_energy_per_rpk_delayed = self._apply_price_delay(doc_net_energy_per_rpk_mean)
        price_index = (doc_net_energy_per_rpk_delayed / price_ref_eur) ** self.price_elast
        rpk_per_capita = rpk_per_capita_trend * price_index

        # --- Total RPK (model, no measures yet) ---
        rpk_model_total = population * rpk_per_capita

        # --- Build rpk_model_without_covid (historic from gdp_init/pop_init, no price adj.) ---
        rpk_model_without_covid_raw = population * (rpk_per_capita_trend_no_covid * price_index)
        rpk_model_without_covid_raw.loc[hist_slice] = (
            population_init * rpk_per_capita_trend_hist
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

        # --- RPK without price elasticity (logistic trend only) ---
        rpk_no_price_total = population * rpk_per_capita_trend

        rpk_no_elast_short = rpk_no_price_total * short_range_rpk_share_2019 / 100
        rpk_no_elast_medium = rpk_no_price_total * medium_range_rpk_share_2019 / 100
        rpk_no_elast_long = rpk_no_price_total * long_range_rpk_share_2019 / 100

        rpk_no_elast_short.loc[hist_slice] = rpk_init.loc[hist_slice] * short_range_rpk_share_2019 / 100
        rpk_no_elast_medium.loc[hist_slice] = rpk_init.loc[hist_slice] * medium_range_rpk_share_2019 / 100
        rpk_no_elast_long.loc[hist_slice] = rpk_init.loc[hist_slice] * long_range_rpk_share_2019 / 100

        rpk_no_elast_short = rpk_no_elast_short * rpk_short_range_measures_impact
        rpk_no_elast_medium = rpk_no_elast_medium * rpk_medium_range_measures_impact
        rpk_no_elast_long = rpk_no_elast_long * rpk_long_range_measures_impact

        rpk_no_elasticity = rpk_no_elast_short + rpk_no_elast_medium + rpk_no_elast_long

        # --- rpk_model_without_covid: apply measures to segment split ---
        rpk_wc_short = rpk_model_without_covid_raw * short_range_rpk_share_2019 / 100 * rpk_short_range_measures_impact
        rpk_wc_medium = rpk_model_without_covid_raw * medium_range_rpk_share_2019 / 100 * rpk_medium_range_measures_impact
        rpk_wc_long = rpk_model_without_covid_raw * long_range_rpk_share_2019 / 100 * rpk_long_range_measures_impact
        rpk_model_without_covid = rpk_wc_short + rpk_wc_medium + rpk_wc_long

        # --- Override covid period with actual observed values (ATAG S1 preset) ---
        # TODO: find a better way to do this value reset after change of start_year
        _cov_s = int(covid_start_year)
        _cov_e = int(covid_end_year_passenger)
        _ref_rpk = rpk_init.loc[self.prospection_start_year - 1]
        _ov_years = list(range(_cov_s, _cov_e + 1))
        _cov_fn = interp1d(
            [_cov_s, _cov_e],
            [1.0 - covid_rpk_drop_start_year / 100.0, covid_end_year_reference_rpk_ratio / 100.0],
            kind="linear",
        )
        _covid_factors = pd.Series(
            [float(_cov_fn(k)) for k in _ov_years], index=_ov_years, dtype=float
        )
        rpk_short_range.loc[_ov_years] = (
            _ref_rpk * short_range_rpk_share_2019 / 100
            * _covid_factors
            * rpk_short_range_measures_impact.loc[_ov_years]
        )
        rpk_medium_range.loc[_ov_years] = (
            _ref_rpk * medium_range_rpk_share_2019 / 100
            * _covid_factors
            * rpk_medium_range_measures_impact.loc[_ov_years]
        )
        rpk_long_range.loc[_ov_years] = (
            _ref_rpk * long_range_rpk_share_2019 / 100
            * _covid_factors
            * rpk_long_range_measures_impact.loc[_ov_years]
        )
        rpk.loc[_ov_years] = (
            rpk_short_range.loc[_ov_years]
            + rpk_medium_range.loc[_ov_years]
            + rpk_long_range.loc[_ov_years]
        )

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
        self.df.loc[:, "rpk_no_elasticity"] = rpk_no_elasticity
        self.df.loc[:, "rpk_per_capita_trend"] = rpk_per_capita_trend
        self.df.loc[:, "price_index"] = price_index
        self.df.loc[:, "doc_net_energy_per_rpk_delayed"] = doc_net_energy_per_rpk_delayed
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
            rpk_no_elasticity,
            rpk_per_capita,
            rpk_per_capita_trend,
            price_index,
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
            doc_net_energy_per_rpk_delayed,
        )
