"""
load_factor
================
Module for computing aircraft load factor evolution.

``LoadFactorMarket``     — per-market load factor.
``LoadFactorAggregator`` — recombines per-market load factors into the global
                           ``load_factor`` consumed by downstream models
                           (CO2 emissions, airline costs, etc.).
"""

import pandas as pd

from aeromaps.models.base import AeroMAPSModel


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
    # Calculate via derivative : 2ax+b, evaluated at the end_year offset
    horizon = end_year - last_historical_year
    derivative = 2 * (-5.62003082e-05) * horizon + 3.59670410e-03
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
