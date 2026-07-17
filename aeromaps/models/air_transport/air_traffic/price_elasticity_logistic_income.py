"""
price_elasticity_logistic_income
================================

Module for computing air traffic (RPK) with a generalised logistic income trend
adjusted for price effects.

Adapted from the original (hard-coded short/medium/long range) model so it works
with the generic market structure: the global per-capita demand is unchanged,
only the per-segment split now iterates over the registry's passenger markets.
Selected via ``global.demand.model: logistic_income`` in ``markets.yaml``.
"""

import pandas as pd
from numpy import divide, exp

from aeromaps.models.base import AeroMAPSModel


def generalised_logistic_function(
    x, left_asymptote, capacity, growth_rate, logistic_nu, asymptote_coeff, x_lag
):
    y = left_asymptote + divide(
        capacity - left_asymptote,
        (asymptote_coeff + exp(-growth_rate * (x - x_lag))) ** (1.0 / logistic_nu),
    )

    return y


class RPKLogisticIncomePriceElasticity(AeroMAPSModel):
    """
    Compute Revenue Passenger Kilometers (RPK) per capita using a generalised logistic
    function of GDP per capita (income trend), adjusted for price effects via a price index.

    The global per-capita demand is split across the registry's passenger markets by
    ``<mid>_rpk_share_last_historical_year`` and multiplied by each market's ``rpk_<mid>_measures_impact``.
    It reads ``doc_net_energy_per_rpk_mean`` to close the cost <-> demand MDA cycle and
    aggregates the per-market reference trajectories into the total ``rpk_reference``.

    Parameters
    ----------
    name : str
        Discipline name.
    passenger_market_ids : list of str
        Ordered list of passenger market ids.
    """

    def __init__(self, name: str, passenger_market_ids: list, *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.passenger_market_ids = list(passenger_market_ids)
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

        self.input_names = {
            "rpk_init": pd.Series([0.0]),
            "population": pd.Series([0.0]),
            "gdp_per_capita": pd.Series([0.0]),
            "doc_net_energy_per_rpk_mean": pd.Series([0.0]),
            "gdp_per_capita_last_historical_year": 0.0,
            "gdp_per_capita_covid_end": 0.0,
            "covid_end_year_passenger": 0.0,
            "gdp_per_capita_init": pd.Series([0.0]),
            "population_init": pd.Series([0.0]),
        }
        for mid in self.passenger_market_ids:
            self.input_names[f"{mid}_rpk_share_last_historical_year"] = 0.0
            self.input_names[f"rpk_{mid}_measures_impact"] = pd.Series([0.0])
            self.input_names[f"rpk_reference_{mid}"] = pd.Series([0.0])

        self.output_names = {
            "rpk": pd.Series([0.0]),
            "rpk_no_elasticity": pd.Series([0.0]),
            "rpk_per_capita": pd.Series([0.0]),
            "rpk_per_capita_trend": pd.Series([0.0]),
            "price_index": pd.Series([0.0]),
            "doc_net_energy_per_rpk_delayed": pd.Series([0.0]),
            "rpk_model_without_covid": pd.Series([0.0]),
            "annual_growth_rate_passenger": pd.Series([0.0]),
            "cagr_rpk": 0.0,
            "prospective_evolution_rpk": 0.0,
            "rpk_reference": pd.Series([0.0]),
            "reference_annual_growth_rate_passenger": pd.Series([0.0]),
        }
        for mid in self.passenger_market_ids:
            self.output_names[f"rpk_{mid}"] = pd.Series([0.0])
            self.output_names[f"annual_growth_rate_rpk_{mid}"] = pd.Series([0.0])
            self.output_names[f"cagr_rpk_{mid}"] = 0.0
            self.output_names[f"prospective_evolution_rpk_{mid}"] = 0.0

    def _initialize_df(self):
        super()._initialize_df()
        # Seed value for MDA coupling initialization: reference all-energy cost per RPK in EUR
        self._coupling_defaults = {
            "doc_net_energy_per_rpk_mean": pd.Series(
                self.price_ref * self.eur_usd_exchange_rate,  # EUR/RPK
                index=range(self.historic_start_year, self.end_year + 1),
            )
        }

    def _full_series(self, value, fill: float) -> pd.Series:
        """Return ``value`` if it is a full-horizon series, else a constant ``fill`` series.

        Guards against the length-1 grammar placeholder GEMSEO supplies when no
        upstream discipline produces a coupling input (1.0 for a measures
        multiplier, 0.0 for a missing reference).
        """
        if isinstance(value, pd.Series) and len(value) == len(self.df.index):
            return value
        return pd.Series(fill, index=self.df.index)

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

    def compute(self, input_data: dict) -> dict:
        """Compute prospective RPK using a generalised logistic income trend adjusted for price.

        The global per-capita income trend is multiplied by the price index; the result is
        split across passenger markets by their 2019 RPK share, multiplied by each market's
        measures impact and summed into the total ``rpk``. Historic years are pinned to the
        exogenous ``rpk_init`` split.
        """
        rpk_init = input_data["rpk_init"]
        population = input_data["population"]
        gdp_per_capita = input_data["gdp_per_capita"]
        doc_net_energy_per_rpk_mean = input_data["doc_net_energy_per_rpk_mean"]
        gdp_per_capita_last_historical_year = float(
            input_data["gdp_per_capita_last_historical_year"]
        )
        gdp_per_capita_covid_end = float(input_data["gdp_per_capita_covid_end"])
        gdp_per_capita_init = input_data["gdp_per_capita_init"]
        population_init = input_data["population_init"]

        price_ref_eur = self.price_ref * self.eur_usd_exchange_rate
        covid_end_year = int(input_data["covid_end_year_passenger"])
        # When the prospective window starts after COVID (prospection_start_year >
        # covid_end_year), the GDP series already reflects the post-COVID level, so
        # re-applying covid_shift would double-count the COVID dampening.
        if self.prospection_start_year > covid_end_year:
            covid_shift = 0.0
        else:
            covid_shift = gdp_per_capita_covid_end - gdp_per_capita_last_historical_year
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
        # RPK without price elasticity (logistic trend only)
        rpk_no_price_total = population * rpk_per_capita_trend

        # --- Build rpk_model_without_covid (historic from gdp_init/pop_init, no price adj.) ---
        rpk_model_without_covid_raw = population * (rpk_per_capita_trend_no_covid * price_index)
        rpk_model_without_covid_raw.loc[hist_slice] = (
            population_init * rpk_per_capita_trend_hist
        ).loc[hist_slice]

        # --- Per-market split (historic uses rpk_init * share), measures, and totals ---
        n = self.end_year - self.prospection_start_year
        base_year = self.prospection_start_year - 1
        output_data = {}
        rpk = rpk_no_elasticity = rpk_model_without_covid = rpk_reference = None

        for mid in self.passenger_market_ids:
            share = float(input_data[f"{mid}_rpk_share_last_historical_year"]) / 100
            measures_impact = self._full_series(input_data[f"rpk_{mid}_measures_impact"], 1.0)

            rpk_m = rpk_model_total * share
            rpk_m.loc[hist_slice] = rpk_init.loc[hist_slice] * share
            rpk_m = rpk_m * measures_impact

            rpk_m_no_elast = rpk_no_price_total * share
            rpk_m_no_elast.loc[hist_slice] = rpk_init.loc[hist_slice] * share
            rpk_m_no_elast = rpk_m_no_elast * measures_impact

            rpk_m_wc = rpk_model_without_covid_raw * share * measures_impact

            rpk = rpk_m if rpk is None else rpk + rpk_m
            rpk_no_elasticity = (
                rpk_m_no_elast if rpk_no_elasticity is None else rpk_no_elasticity + rpk_m_no_elast
            )
            rpk_model_without_covid = (
                rpk_m_wc if rpk_model_without_covid is None else rpk_model_without_covid + rpk_m_wc
            )
            rpk_reference_m = self._full_series(input_data[f"rpk_reference_{mid}"], 0.0)
            rpk_reference = (
                rpk_reference_m if rpk_reference is None else rpk_reference + rpk_reference_m
            )

            output_data[f"rpk_{mid}"] = rpk_m
            output_data[f"annual_growth_rate_rpk_{mid}"] = rpk_m.pct_change() * 100
            output_data[f"cagr_rpk_{mid}"] = 100 * (
                (rpk_m.loc[self.end_year] / rpk_m.loc[base_year]) ** (1 / n) - 1
            )
            output_data[f"prospective_evolution_rpk_{mid}"] = 100 * (
                rpk_m.loc[self.end_year] / rpk_m.loc[base_year] - 1
            )

        # --- Totals ---
        reference_growth = pd.Series(float("nan"), index=self.df.index)
        proj = slice(self.prospection_start_year + 1, self.end_year)
        reference_growth.loc[proj] = (rpk_reference.pct_change() * 100).loc[proj]

        output_data["rpk"] = rpk
        output_data["rpk_no_elasticity"] = rpk_no_elasticity
        output_data["rpk_per_capita"] = rpk_per_capita
        output_data["rpk_per_capita_trend"] = rpk_per_capita_trend
        output_data["price_index"] = price_index
        output_data["rpk_model_without_covid"] = rpk_model_without_covid
        output_data["rpk_reference"] = rpk_reference
        output_data["doc_net_energy_per_rpk_delayed"] = doc_net_energy_per_rpk_delayed
        output_data["annual_growth_rate_passenger"] = rpk.pct_change() * 100
        output_data["reference_annual_growth_rate_passenger"] = reference_growth
        output_data["cagr_rpk"] = 100 * (
            (rpk.loc[self.end_year] / rpk.loc[base_year]) ** (1 / n) - 1
        )
        output_data["prospective_evolution_rpk"] = 100 * (
            rpk.loc[self.end_year] / rpk.loc[base_year] - 1
        )

        self._store_outputs(output_data)
        return output_data
