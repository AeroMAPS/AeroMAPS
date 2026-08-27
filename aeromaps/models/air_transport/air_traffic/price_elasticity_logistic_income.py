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

import numpy as np
import pandas as pd
from numpy import divide, exp, log

from aeromaps.models.base import AeroMAPSModel
from aeromaps.models.air_transport.air_traffic.price_delay import (
    apply_price_delay,
)


def generalised_logistic_function(
    x, left_asymptote, capacity, growth_rate, logistic_nu, asymptote_coeff, x_lag
):
    y = left_asymptote + divide(
        capacity - left_asymptote,
        (asymptote_coeff + exp(-growth_rate * (x - x_lag))) ** (1.0 / logistic_nu),
    )

    return y


# Reference years for the COVID recovery calibration. These are observations, not
# scenario settings: 2019 is the pre-COVID per-capita traffic level, and 2024 is the
# year by which per-capita traffic is observed to have regained it. They are held
# fixed on purpose and are deliberately NOT tied to ``prospection_start_year`` -- a
# scenario's modelling window says nothing about when the pandemic happened.
COVID_REFERENCE_YEAR = 2019
COVID_RECOVERY_YEAR = 2024

# Year the price index is anchored on. The index is a *relative* response: demand reacts
# to how far the cost of flying has moved from a reference, so the reference has to be a
# cost the world actually had. Anchoring on the model's own cost in this year makes
# price_index == 1 there, so no demand response is attributed before the trajectory
# departs from observed conditions.
#
# The alternative -- a fixed `price_ref` constant carried from an older calibration --
# is only correct while that constant stays on the same basis as the computed
# doc_net_energy_per_rpk_mean. It had drifted: the index started around 0.70 in the
# first prospective year of every scenario, so roughly a 30% demand reduction was
# already booked before any scenario had done anything.
PRICE_REFERENCE_YEAR = 2024


class RPKLogisticIncomePriceElasticity(AeroMAPSModel):
    """
    Compute Revenue Passenger Kilometers (RPK) per capita using a generalised logistic
    function of GDP per capita (income trend), adjusted for price effects via a price index.

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

    MARKET_SCOPE = "cross_market"

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
            "price_reference_year": float(PRICE_REFERENCE_YEAR),
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
        """Effective price the demand model responds to.

        Filtered from the first year of the series rather than from the first
        projected one, so the recursion reaches the projection carrying its
        memory. See ``price_delay.apply_price_delay`` for why that matters.
        """
        return apply_price_delay(
            price,
            getattr(self, "price_delay", 0.0),
            self.historic_start_year,
            self.end_year,
        )

    def _price_reference(self, price, fallback: float, reference_year) -> float:
        """Cost per RPK the price index is measured against.

        Anchored on the model's own cost in ``reference_year``, so the index is 1
        there and demand responds only to movement away from that year. Because the
        index enters as ``(P/P_ref)**elast``, the reference is a pure scale factor:
        getting it wrong does not distort the *shape* of the response, but it shifts
        every scenario's demand level by a constant, and with it the headline "demand
        avoided" figure.

        Set ``price_reference_year`` to 0 to opt out and use the calibrated
        ``price_ref`` constant instead -- which is what scenarios published against the
        old behaviour should do, so their numbers do not move. The same fallback
        applies when the requested year lies outside the modelled horizon, or the cost
        there is not usable.
        """
        try:
            year = int(reference_year)
        except (TypeError, ValueError):
            return fallback
        if year <= 0:
            return fallback
        try:
            reference = float(price.loc[year])
        except (KeyError, IndexError, TypeError):
            return fallback
        if not np.isfinite(reference) or reference <= 0.0:
            return fallback
        return reference

    def _covid_shift(self, rpk_init, population_init, gdp_per_capita) -> float:
        """Income-axis shift calibrated on the observed COVID recovery.

        The pandemic left per-capita air travel below the level its income trend
        alone would imply. That gap is represented as a shift along the GDP-per-capita
        axis, calibrated so the logistic trend evaluated at :data:`COVID_RECOVERY_YEAR`
        income returns the :data:`COVID_REFERENCE_YEAR` per-capita traffic level --
        i.e. per-capita traffic recovers, but no more than recovers, its pre-COVID value.

        Both years are observations and are fixed, so the same shift is obtained
        whatever window a scenario models. The previous implementation instead zeroed
        the shift whenever ``prospection_start_year > covid_end_year``, which made a
        physical correction depend on an unrelated modelling choice.

        The generalised logistic is invertible, so this is closed-form. From
        ``y = L + (K - L) / (A + exp(-g (x - x_lag)))**(1/nu)``::

            x_lag = x + ln( ((K - L) / (y - L))**nu - A ) / g

        Returns 0.0 if the target is unreachable (outside the curve's range), leaving
        the uncorrected trend rather than raising.
        """
        try:
            target = float(rpk_init.loc[COVID_REFERENCE_YEAR]) / float(
                population_init.loc[COVID_REFERENCE_YEAR]
            )
            income = float(gdp_per_capita.loc[COVID_RECOVERY_YEAR])
        except (KeyError, IndexError, ZeroDivisionError):
            return 0.0

        span = self.capacity - self.left_asymptote
        offset = target - self.left_asymptote
        if offset <= 0.0 or span <= 0.0:
            return 0.0

        inner = (span / offset) ** self.logistic_nu - self.asymptote_coeff
        if inner <= 0.0:
            # Target sits above what the curve can produce at any income.
            return 0.0

        required_x_lag = income + log(inner) / self.growth_rate
        return required_x_lag - self.x_lag

    def compute(self, input_data: dict) -> dict:
        """Compute prospective RPK using a generalised logistic income trend adjusted for price.

        The global per-capita income trend is multiplied by the price index; the result is
        split across passenger markets by their last-historical-year RPK share, multiplied
        by each market's measures impact and summed into the total ``rpk``. Historic years
        are pinned to the exogenous ``rpk_init`` split.
        """
        rpk_init = input_data["rpk_init"]
        population = input_data["population"]
        gdp_per_capita = input_data["gdp_per_capita"]
        # (COVID handling lives in _covid_shift, below.)
        doc_net_energy_per_rpk_mean = input_data["doc_net_energy_per_rpk_mean"]
        gdp_per_capita_init = input_data["gdp_per_capita_init"]
        population_init = input_data["population_init"]

        price_ref_eur = self.price_ref * self.eur_usd_exchange_rate
        covid_shift = self._covid_shift(rpk_init, population_init, gdp_per_capita)
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
        price_index = (
            doc_net_energy_per_rpk_delayed
            / self._price_reference(
                doc_net_energy_per_rpk_delayed,
                price_ref_eur,
                input_data["price_reference_year"],
            )
        ) ** self.price_elast
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
