"""
price_and_income_elasticity
===========================

Module for computing air traffic (RPK) with a constant-elasticity demand model.

Adapted from the original (hard-coded short/medium/long range) model so it works
with the generic market structure: the global per-capita demand is unchanged,
only the per-segment split now iterates over the registry's passenger markets.
Selected via ``global.demand.model: constant_elasticity`` in ``markets.yaml``.
"""

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class RPKPriceIncomeElasticity(AeroMAPSModel):
    """
    Compute Revenue Passenger Kilometers (RPK) using a constant-elasticity demand model.

    RPK per capita is modelled as:
        rpk_per_capita = sigma * gdp_per_capita^income_elast * price^price_elast

    where ``sigma``, ``income_elast`` and ``price_elast`` are calibrated coefficients
    fixed at the class level.  The price input (``doc_net_energy_per_rpk_mean``) is expressed
    in EUR/RPK and is converted to USD before evaluation so that the units match the
    original calibration.

    The global per-capita demand is split across the registry's passenger markets by
    ``<mid>_rpk_share_last_historical_year`` and multiplied by each market's ``rpk_<mid>_measures_impact``.
    It reads ``doc_net_energy_per_rpk_mean`` to close the cost <-> demand MDA cycle and
    aggregates the per-market reference trajectories into the total ``rpk_reference``.

    Unlike the traffic/efficiency models (one discipline instance per market), this is a
    single discipline spanning all passenger markets: the income trend and the
    price <-> demand MDA coupling are global, so per-market instances would duplicate
    the same global cycle N times.

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
        # Calibrated constant-elasticity parameters (fixed at class level)
        self.sigma: float = 0.0004016258667105296
        self.income_elast: float = 1.4207611236946205
        self.price_elast: float = -0.38053802791092983
        # Exchange rate used to convert doc_net_energy_per_rpk_mean from EUR to USD [EUR/USD]
        self.eur_usd_exchange_rate: float = 0.9
        # Calibrated price-response delay (first-order lag time constant) [yr]; 0.0 disables it.
        self.price_delay: float = 1.3312445030564617

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
        # Seed value for MDA coupling initialization: approximate 2019 all-energy cost per RPK
        self._coupling_defaults = {
            "doc_net_energy_per_rpk_mean": pd.Series(
                0.012,  # EUR/RPK
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
        a = float(np.exp(-1.0 / tau))  # annual step, dt = 1 year
        prev = float(price.loc[self.prospection_start_year])
        delayed.loc[self.prospection_start_year] = prev
        for year in range(self.prospection_start_year + 1, self.end_year + 1):
            prev = a * prev + (1.0 - a) * float(price.loc[year])
            delayed.loc[year] = prev
        return delayed

    def compute(self, input_data: dict) -> dict:
        """Compute prospective RPK from population, GDP per capita and energy cost per RPK.

        The global per-capita demand uses the constant-elasticity model; it is then
        split across passenger markets by their last-historical-year RPK share, multiplied
        by each market's measures impact and summed into the total ``rpk``. Historic years
        are pinned to the exogenous ``rpk_init`` split.
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

        doc_net_energy_per_rpk_delayed = self._apply_price_delay(doc_net_energy_per_rpk_mean)
        price_usd = doc_net_energy_per_rpk_delayed / self.eur_usd_exchange_rate
        covid_end_year = int(input_data["covid_end_year_passenger"])
        # When the prospective window starts after COVID (prospection_start_year >
        # covid_end_year), the GDP series already reflects the post-COVID level, so
        # re-applying covid_shift would double-count the COVID dampening.
        if self.prospection_start_year > covid_end_year:
            covid_shift = 0.0
        else:
            covid_shift = gdp_per_capita_covid_end - gdp_per_capita_last_historical_year
        hist_slice = slice(self.historic_start_year, self.prospection_start_year - 1)

        # --- Per-capita RPK (with and without COVID lag) ---
        rpk_per_capita = (
            self.sigma
            * ((gdp_per_capita - covid_shift) ** self.income_elast)
            * (price_usd**self.price_elast)
        )
        rpk_per_capita_no_covid = (
            self.sigma * (gdp_per_capita**self.income_elast) * (price_usd**self.price_elast)
        )
        rpk_per_capita_no_covid_hist = self.sigma * (gdp_per_capita_init**self.income_elast)

        # --- RPK without price elasticity (income-driven only) ---
        rpk_per_capita_no_price = self.sigma * ((gdp_per_capita - covid_shift) ** self.income_elast)

        # --- Total RPK (model, no measures yet) ---
        rpk_model_total = population * rpk_per_capita
        rpk_no_price_total = population * rpk_per_capita_no_price

        # --- Build rpk_model_without_covid (historic from gdp_init/pop_init, no price adj.) ---
        rpk_model_without_covid_raw = population * rpk_per_capita_no_covid
        rpk_model_without_covid_raw.loc[hist_slice] = (
            population_init * rpk_per_capita_no_covid_hist
        ).loc[hist_slice]

        # --- Per-market split (historic uses rpk_init * share), measures, and totals ---
        n = self.end_year - self.prospection_start_year
        base_year = self.prospection_start_year - 1
        output_data = {}
        rpk = pd.Series(0.0, index=self.df.index)
        rpk_reference = pd.Series(0.0, index=self.df.index)
        # Sum of share_m * measures_m: aggregate-only outputs are rebuilt from this
        # single weighting after the loop instead of being recomputed per market.
        weighted_measures = pd.Series(0.0, index=self.df.index)

        for mid in self.passenger_market_ids:
            share = float(input_data[f"{mid}_rpk_share_last_historical_year"]) / 100
            measures_impact = self._full_series(input_data[f"rpk_{mid}_measures_impact"], 1.0)
            weighted_measures += share * measures_impact

            rpk_m = rpk_model_total * share
            rpk_m.loc[hist_slice] = rpk_init.loc[hist_slice] * share
            rpk_m = rpk_m * measures_impact

            rpk += rpk_m
            rpk_reference += self._full_series(input_data[f"rpk_reference_{mid}"], 0.0)

            output_data[f"rpk_{mid}"] = rpk_m
            output_data[f"annual_growth_rate_rpk_{mid}"] = rpk_m.pct_change() * 100
            output_data[f"cagr_rpk_{mid}"] = 100 * (
                (rpk_m.loc[self.end_year] / rpk_m.loc[base_year]) ** (1 / n) - 1
            )
            output_data[f"prospective_evolution_rpk_{mid}"] = 100 * (
                rpk_m.loc[self.end_year] / rpk_m.loc[base_year] - 1
            )

        # --- Aggregate-only series (no per-market output), built once from the weighting ---
        rpk_no_elasticity = rpk_no_price_total.copy()
        rpk_no_elasticity.loc[hist_slice] = rpk_init.loc[hist_slice]
        rpk_no_elasticity = rpk_no_elasticity * weighted_measures
        rpk_model_without_covid = rpk_model_without_covid_raw * weighted_measures

        # --- Totals ---
        reference_growth = pd.Series(np.nan, index=self.df.index)
        proj = slice(self.prospection_start_year + 1, self.end_year)
        reference_growth.loc[proj] = (rpk_reference.pct_change() * 100).loc[proj]

        output_data["rpk"] = rpk
        output_data["rpk_no_elasticity"] = rpk_no_elasticity
        output_data["rpk_per_capita"] = rpk_per_capita
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
