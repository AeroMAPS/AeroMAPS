"""
rtk_market
==========

Per-market RTK model for freight markets when a MarketManager is loaded.

``RTKMarket`` reads per-market parameters flattened from ``markets.yaml``
(``<market_id>_cagr_reference_periods``, ``<market_id>_covid_*``) and outputs
the legacy ``rtk`` / ``annual_growth_rate_freight`` names so that downstream
models (``RTKReference``, ``TotalAircraftDistance``) remain unaffected.

Only one freight market is supported (the single ``traffic_type=freight`` entry
in ``markets.yaml``).
"""

import pandas as pd
from scipy.interpolate import interp1d

from aeromaps.models.base import AeroMAPSModel, aeromaps_leveling_function


class RTKMarket(AeroMAPSModel):
    """CAGR-based RTK growth with COVID recovery for one freight market.

    Outputs use the legacy names ``rtk`` and ``annual_growth_rate_freight``
    so that ``RTKReference`` and ``TotalAircraftDistance`` need no changes.

    Parameters
    ----------
    name : str
        Discipline name.
    market_id : str
        Market identifier for the freight market (e.g. ``'freight'``).
    """

    def __init__(self, name: str, market_id: str, *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        mid = market_id
        self.market_id = mid
        self.input_names = {
            "rtk_init": pd.Series([0.0]),
            "covid_start_year": 0.0,
            f"{mid}_covid_drop_start_year": 0.0,
            f"{mid}_covid_end_year": 0.0,
            f"{mid}_covid_end_year_reference_ratio": 0.0,
            f"{mid}_cagr_reference_periods": [],
            f"{mid}_cagr_reference_periods_values": [0.0],
        }
        # Keep legacy output names so downstream models are unaffected
        self.output_names = {
            "rtk": pd.Series([0.0]),
            "annual_growth_rate_freight": pd.Series([0.0]),
            "cagr_rtk": 0.0,
            "prospective_evolution_rtk": 0.0,
        }

    def compute(self, input_data: dict) -> dict:
        mid = self.market_id
        rtk_init = input_data["rtk_init"]
        if not isinstance(rtk_init, pd.Series):
            rtk_init = pd.Series(
                rtk_init,
                index=range(self.historic_start_year, self.historic_start_year + len(rtk_init)),
            )
        covid_start_year = int(input_data["covid_start_year"])
        covid_drop = float(input_data[f"{mid}_covid_drop_start_year"])
        covid_end_year = int(input_data[f"{mid}_covid_end_year"])
        covid_end_ratio = float(input_data[f"{mid}_covid_end_year_reference_ratio"])
        cagr_ref_periods = list(input_data[f"{mid}_cagr_reference_periods"])
        cagr_ref_values = list(input_data[f"{mid}_cagr_reference_periods_values"])

        # Initialise from last historic value (prospection_start_year - 1)
        self.df.loc[self.prospection_start_year - 1, "rtk"] = rtk_init.loc[
            self.prospection_start_year - 1
        ]

        # COVID interpolation
        covid_func = interp1d(
            [covid_start_year, covid_end_year],
            [1 - covid_drop / 100, covid_end_ratio / 100],
            kind="linear",
        )

        # CAGR → annual growth rate (prospection years)
        annual_gr = aeromaps_leveling_function(
            self, cagr_ref_periods, cagr_ref_values, model_name=self.name
        )
        self.df.loc[:, "annual_growth_rate_freight"] = annual_gr

        # COVID years
        for k in range(covid_start_year, covid_end_year + 1):
            self.df.loc[k, "rtk"] = self.df.loc[covid_start_year - 1, "rtk"] * covid_func(k)

        # Post-COVID growth
        for k in range(covid_end_year + 1, self.end_year + 1):
            self.df.loc[k, "rtk"] = self.df.loc[k - 1, "rtk"] * (
                1 + self.df.loc[k, "annual_growth_rate_freight"] / 100
            )

        # Fill in full historic series
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, "rtk"] = rtk_init.loc[k]
        for k in range(self.historic_start_year + 1, self.prospection_start_year):
            self.df.loc[k, "annual_growth_rate_freight"] = (
                self.df.loc[k, "rtk"] / self.df.loc[k - 1, "rtk"] - 1
            ) * 100

        cagr_rtk = 100 * (
            (
                self.df.loc[self.end_year, "rtk"]
                / self.df.loc[self.prospection_start_year - 1, "rtk"]
            )
            ** (1 / (self.end_year - self.prospection_start_year))
            - 1
        )
        prospective_evolution_rtk = 100 * (
            self.df.loc[self.end_year, "rtk"] / self.df.loc[self.prospection_start_year - 1, "rtk"]
            - 1
        )

        output_data = {
            "rtk": self.df["rtk"],
            "annual_growth_rate_freight": self.df["annual_growth_rate_freight"],
            "cagr_rtk": cagr_rtk,
            "prospective_evolution_rtk": prospective_evolution_rtk,
        }
        self._store_outputs(output_data)
        return output_data
