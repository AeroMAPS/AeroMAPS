"""
load_factor
================
Module for computing aircraft load factor evolution.

``LoadFactorMarket``     — per-market load factor.
``LoadFactorAggregator`` — recombines per-market load factors into the global
                           ``load_factor`` consumed by downstream models
                           (CO2 emissions, airline costs, etc.).
"""

import warnings

import pandas as pd

from aeromaps.models.base import AeroMAPSModel, aeromaps_interpolation_function

# Horizon (years) at which the arrival-slope constraint was calibrated from
# historical load-factor data: 2050 - 2019 = 31.  The fitted linear trend
# for the slope crosses zero at x ≈ 32, so evaluating it beyond that point
# would impose a physically wrong (negative) slope.  This constant must NOT
# be changed to end_year - last_historical_year.
_LF_DERIV_CALIB_HORIZON = 31


def _parameters_load_factor_model(
    end_year, last_historical_year, load_factor_lhy, load_factor_end_year
):
    """Compute the parameters of the quadratic model for load factor evolution.

    Parameters
    ----------
    end_year
        Year at which the target load factor is reached [yr]
    last_historical_year
        Last historical year, used as the quadratic anchor (x = 0) [yr]
    load_factor_lhy
        Load factor in the last historical year [%]
    load_factor_end_year
        Target load factor in end_year [%]

    Returns
    -------
    a
        Second order parameter of the quadratic model
    b
        First order parameter of the quadratic model
    """
    horizon = end_year - last_historical_year
    derivative = 2 * (-5.62003082e-05) * _LF_DERIV_CALIB_HORIZON + 3.59670410e-03
    a = -(load_factor_end_year - load_factor_lhy - derivative * horizon) / horizon**2
    b = derivative - 2 * a * horizon
    return [a, b]


class LoadFactorMarket(AeroMAPSModel):
    """Per-market aircraft load factor projection.

    Reads per-market parameters flattened from ``markets.yaml`` by
    ``_initialize_markets()``:

    * ``<mid>_load_factor_end_year``    — target LF in ``end_year`` [%]
    * ``<mid>_covid_load_factor_2020``  — LF override for 2020 [%]

    Historical years use the global ``rpk_init`` / ``ask_init`` series, so
    every market shares the same historical LF (no per-market historic split
    exists — same convention as ``RPKMarket``).

    Parameters
    ----------
    name : str
        Discipline name.
    market_id : str
        Market identifier.
    """

    def __init__(self, name: str, market_id: str, *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        mid = market_id
        self.market_id = mid
        self.input_names = {
            f"{mid}_load_factor_end_year": 0.0,
            f"{mid}_covid_load_factor_2020": 0.0,
            "rpk_init": pd.Series([0.0]),
            "ask_init": pd.Series([0.0]),
        }
        self.output_names = {
            f"load_factor_{mid}": pd.Series([0.0]),
        }

    def compute(self, input_data: dict) -> dict:
        """Execute the computation of per-market aircraft load factor.

        Historical load factor values are computed from provided RPK and
        historical ASK, initializes the 2019 load factor as a baseline, then
        projects load factor forward to `end_year` using a quadratic model.
        The 2020 value is overwritten with a Covid-19-specific value.
        """
        mid = self.market_id
        end_year_value = float(input_data[f"{mid}_load_factor_end_year"])
        covid_2020 = float(input_data[f"{mid}_covid_load_factor_2020"])
        rpk_init = input_data["rpk_init"]
        ask_init = input_data["ask_init"]

        col = f"load_factor_{mid}"

        horizon = self.end_year - self.last_historical_year
        if horizon != _LF_DERIV_CALIB_HORIZON:
            warnings.warn(
                f"[LoadFactorMarket - {mid}] The quadratic load-factor model was calibrated "
                f"for a horizon of {_LF_DERIV_CALIB_HORIZON} years (end_year=2050, "
                f"last_historical_year=2019). The current scenario has a horizon of "
                f"{horizon} years (end_year={self.end_year}, "
                f"last_historical_year={self.last_historical_year}). The arrival-slope "
                f"constraint (≈ 0 %/yr at end_year) is applied unchanged. "
                f"For a model without this limitation, use LoadFactorMarketSimpleInterpolation "
                f"(set global.load_factor.model: simple_interpolation in markets.yaml).",
                UserWarning,
                stacklevel=2,
            )

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, col] = rpk_init.loc[k] / ask_init.loc[k] * 100

        # Initialization for load factor
        load_factor_lhy = self.df.loc[self.last_historical_year, col]

        # Parameters for the model
        a, b = _parameters_load_factor_model(
            self.end_year, self.last_historical_year, load_factor_lhy, end_year_value
        )

        lhy = self.last_historical_year
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, col] = a * (k - lhy) ** 2 + b * (k - lhy) + load_factor_lhy

        # Covid-19 : à refaire proprement. Only applied when 2020 is in the
        # prospective window; for prospection_start_year > 2020 the observed
        # 2020 drop is expected to be already baked into the historic init data.
        if self.prospection_start_year <= 2020:
            self.df.loc[2020, col] = covid_2020

        output_data = {col: self.df[col]}
        self._store_outputs(output_data)
        return output_data


class LoadFactorMarketSimpleInterpolation(AeroMAPSModel):
    """Per-market aircraft load factor projection via linear interpolation.

    Instead of fitting a quadratic curve anchored at the last historical year,
    this model projects the load factor by linearly interpolating the workbook
    reference waypoints (e.g. 2025 → 83 %, 2045 → 88 %, 2050 → 89 %) using
    the shared :func:`aeromaps_interpolation_function`.  The result is a
    piece-wise linear trajectory that hits every waypoint exactly, as opposed
    to the smoothed ``LoadFactorMarket`` quadratic which only honours the
    single ``load_factor_end_year`` target.

    Select this model via ``global.load_factor.model: simple_interpolation``
    in ``markets.yaml``; the default is ``quadratic`` (``LoadFactorMarket``).

    Reads per-market parameters flattened from ``markets.yaml``:

    * ``<mid>_load_factor_reference_years``        — list of reference years
    * ``<mid>_load_factor_reference_years_values`` — LF values at those years [%]
    * ``<mid>_covid_load_factor_2020``             — LF override for 2020 [%]

    Historical years are filled from ``rpk_init`` / ``ask_init``, identical to
    ``LoadFactorMarket``.

    Parameters
    ----------
    name : str
        Discipline name.
    market_id : str
        Market identifier.
    """

    def __init__(self, name: str, market_id: str, *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        mid = market_id
        self.market_id = mid
        self.input_names = {
            f"{mid}_load_factor_reference_years": [],
            f"{mid}_load_factor_reference_years_values": [0.0],
            f"{mid}_covid_load_factor_2020": 0.0,
            "rpk_init": pd.Series([0.0]),
            "ask_init": pd.Series([0.0]),
        }
        self.output_names = {
            f"load_factor_{mid}": pd.Series([0.0]),
        }

    def compute(self, input_data: dict) -> dict:
        """Execute the computation of per-market aircraft load factor via linear interpolation.

        Historical load factor values are computed from provided RPK and ASK.
        Prospective years are filled by linearly interpolating the reference
        waypoints supplied in the workbook, using the shared
        ``aeromaps_interpolation_function``.  The 2020 value is overwritten
        with the Covid-19-specific value when 2020 falls in the prospective
        window.
        """
        mid = self.market_id
        reference_years = list(input_data[f"{mid}_load_factor_reference_years"])
        reference_years_values = list(input_data[f"{mid}_load_factor_reference_years_values"])
        covid_2020 = float(input_data[f"{mid}_covid_load_factor_2020"])
        rpk_init = input_data["rpk_init"]
        ask_init = input_data["ask_init"]

        col = f"load_factor_{mid}"

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, col] = rpk_init.loc[k] / ask_init.loc[k] * 100

        # Prospective years: linear interpolation across the workbook waypoints.
        series = aeromaps_interpolation_function(
            self, reference_years, reference_years_values, model_name=self.name
        )
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, col] = series.loc[k]

        # Covid-19 override: only applied when 2020 is in the prospective window.
        if self.prospection_start_year <= 2020:
            self.df.loc[2020, col] = covid_2020

        output_data = {col: self.df[col]}
        self._store_outputs(output_data)
        return output_data


class LoadFactorAggregator(AeroMAPSModel):
    """Recombine per-market load factors into the global ``load_factor``.

    Computed as ``rpk / ask * 100`` from the already-aggregated totals, so
    downstream consumers (CO2 emissions, airline costs, plots, ...) keep
    seeing the same global ``load_factor`` series.

    Parameters
    ----------
    name : str
        Discipline name.
    """

    def __init__(self, name: str = "load_factor_aggregator", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.input_names = {
            "rpk": pd.Series([0.0]),
            "ask": pd.Series([0.0]),
        }
        self.output_names = {
            "load_factor": pd.Series([0.0]),
        }

    def compute(self, input_data: dict) -> dict:
        """Aggregate load factor from total RPK and ASK.

        Parameters
        ----------
        input_data : dict
            Model inputs containing aggregated RPK and ASK series.

        Returns
        -------
        dict
            Output dictionary with the global load factor series.
        """
        rpk = input_data["rpk"]
        ask = input_data["ask"]

        load_factor = rpk / ask * 100
        self.df.loc[:, "load_factor"] = load_factor

        output_data = {"load_factor": load_factor}
        self._store_outputs(output_data)
        return output_data
