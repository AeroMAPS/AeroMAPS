"""
rtk_market
==========

Per-market RTK models for freight markets when a MarketManager is loaded.

``RTKMarket``          — CAGR + COVID freight traffic for one freight market.
``RTKReferenceMarket`` — reference (counterfactual) RTK trajectory for one freight market.
``RTKAggregator``      — sums per-market RTK into the legacy ``rtk`` / ``rtk_reference``
                         totals consumed by downstream models.

All classes use ``model_type="custom"`` (``AeroMAPSCustomModelWrapper``).
"""

import pandas as pd
from scipy.interpolate import interp1d

from aeromaps.models.base import AeroMAPSModel, aeromaps_leveling_function


class RTKMarket(AeroMAPSModel):
    """CAGR-based RTK growth with COVID recovery for one freight market.

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
            f"{mid}_rtk_share_last_historical_year": 0.0,
            "covid_start_year": 0.0,
            f"{mid}_covid_drop_start_year": 0.0,
            f"{mid}_covid_end_year": 0.0,
            f"{mid}_covid_end_year_reference_ratio": 0.0,
            f"{mid}_cagr_reference_periods": [],
            f"{mid}_cagr_reference_periods_values": [0.0],
        }
        self.output_names = {
            f"rtk_{mid}": pd.Series([0.0]),
            f"annual_growth_rate_rtk_{mid}": pd.Series([0.0]),
            f"cagr_rtk_{mid}": 0.0,
            f"prospective_evolution_rtk_{mid}": 0.0,
        }

    def compute(self, input_data: dict) -> dict:
        """Compute per-market RTK with CAGR and COVID recovery.

        Parameters
        ----------
        input_data : dict
            Inputs containing market share, CAGR references, and COVID settings.

        Returns
        -------
        dict
            Output series for market RTK and growth metrics.
        """
        mid = self.market_id
        rtk_init = input_data["rtk_init"]
        rtk_share_last_historical_year = float(input_data[f"{mid}_rtk_share_last_historical_year"])
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

        rtk_col = f"rtk_{mid}"
        rate_col = f"annual_growth_rate_rtk_{mid}"

        # Historic initialisation: split total RTK by market share
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, rtk_col] = rtk_share_last_historical_year / 100 * rtk_init.loc[k]

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
        self.df.loc[:, rate_col] = annual_gr

        # COVID + post-COVID only shape the *prospective* window. When historic
        # data already extends past COVID (prospection_start_year > covid_end_year)
        # the COVID loop is empty and post-COVID compounds from the historic value
        # at prospection_start_year-1, so the observed dip in rtk_init is preserved.
        # COVID years (direct interpolation from last pre-COVID value)
        for k in range(max(covid_start_year, self.prospection_start_year), covid_end_year + 1):
            self.df.loc[k, rtk_col] = self.df.loc[covid_start_year - 1, rtk_col] * covid_func(k)

        # Post-COVID compounding growth
        for k in range(max(covid_end_year + 1, self.prospection_start_year), self.end_year + 1):
            self.df.loc[k, rtk_col] = self.df.loc[k - 1, rtk_col] * (
                1 + self.df.loc[k, rate_col] / 100
            )

        # Overwrite with actual historic growth rates
        for k in range(self.historic_start_year + 1, self.prospection_start_year):
            self.df.loc[k, rate_col] = (
                self.df.loc[k, rtk_col] / self.df.loc[k - 1, rtk_col] - 1
            ) * 100

        cagr_rtk = 100 * (
            (
                self.df.loc[self.end_year, rtk_col]
                / self.df.loc[self.prospection_start_year - 1, rtk_col]
            )
            ** (1 / (self.end_year - self.prospection_start_year))
            - 1
        )
        prospective_evolution_rtk = 100 * (
            self.df.loc[self.end_year, rtk_col]
            / self.df.loc[self.prospection_start_year - 1, rtk_col]
            - 1
        )

        output_data = {
            rtk_col: self.df[rtk_col],
            rate_col: self.df[rate_col],
            f"cagr_rtk_{mid}": cagr_rtk,
            f"prospective_evolution_rtk_{mid}": prospective_evolution_rtk,
        }
        self._store_outputs(output_data)
        return output_data


class RTKReferenceMarket(AeroMAPSModel):
    """Reference RTK trajectory for one freight market.

    Reads the actual ``rtk_{mid}`` series (output of ``RTKMarket``) and applies an
    independent reference CAGR + COVID recovery to produce the counterfactual
    ``rtk_reference_{mid}`` used by downstream abatement-cost and policy models.

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
            f"rtk_{mid}": pd.Series([0.0]),
            f"{mid}_reference_cagr_reference_periods": [],
            f"{mid}_reference_cagr_reference_periods_values": [0.0],
            "covid_start_year": 0.0,
            f"{mid}_covid_drop_start_year": 0.0,
            f"{mid}_covid_end_year": 0.0,
            f"{mid}_covid_end_year_reference_ratio": 0.0,
        }
        self.output_names = {
            f"rtk_reference_{mid}": pd.Series([0.0]),
            f"reference_annual_growth_rate_rtk_{mid}": pd.Series([0.0]),
        }

    def compute(self, input_data: dict) -> dict:
        """Compute reference RTK trajectory for one freight market.

        Parameters
        ----------
        input_data : dict
            Inputs containing market RTK, CAGR reference, and COVID settings.

        Returns
        -------
        dict
            Output series for reference RTK and its growth rate.
        """
        mid = self.market_id
        rtk = input_data[f"rtk_{mid}"]
        reference_periods = list(input_data[f"{mid}_reference_cagr_reference_periods"])
        reference_values = list(input_data[f"{mid}_reference_cagr_reference_periods_values"])
        covid_start_year = int(input_data["covid_start_year"])
        covid_drop = float(input_data[f"{mid}_covid_drop_start_year"])
        covid_end_year = int(input_data[f"{mid}_covid_end_year"])
        covid_end_ratio = float(input_data[f"{mid}_covid_end_year_reference_ratio"])

        col = f"rtk_reference_{mid}"
        rate_col = f"reference_annual_growth_rate_rtk_{mid}"

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, col] = rtk.loc[k]

        self.df.loc[covid_start_year - 1, col] = rtk.loc[covid_start_year - 1]

        covid_function = interp1d(
            [covid_start_year, covid_end_year],
            [1 - covid_drop / 100, covid_end_ratio / 100],
            kind="linear",
        )

        reference_annual_growth_rate = aeromaps_leveling_function(
            self, reference_periods, reference_values, model_name=self.name
        )
        self.df.loc[:, rate_col] = reference_annual_growth_rate

        # Clamp to the prospective window so observed historic COVID data isn't
        # overwritten when prospection_start_year > covid_end_year.
        for k in range(max(covid_start_year, self.prospection_start_year), covid_end_year + 1):
            self.df.loc[k, col] = self.df.loc[covid_start_year - 1, col] * covid_function(k)
        for k in range(max(covid_end_year + 1, self.prospection_start_year), self.end_year + 1):
            self.df.loc[k, col] = self.df.loc[k - 1, col] * (1 + self.df.loc[k, rate_col] / 100)

        output_data = {
            col: self.df[col],
            rate_col: self.df[rate_col],
        }
        self._store_outputs(output_data)
        return output_data


class RTKAggregator(AeroMAPSModel):
    """Sum per-market RTKs into the legacy ``rtk`` / ``rtk_reference`` totals.

    Parameters
    ----------
    name : str
        Discipline name.
    freight_market_ids : list of str
        Ordered list of freight market ids.
    """

    def __init__(self, name: str, freight_market_ids: list, *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.freight_market_ids = list(freight_market_ids)
        self.input_names = {}
        for mid in self.freight_market_ids:
            self.input_names[f"rtk_{mid}"] = pd.Series([0.0])
            self.input_names[f"rtk_reference_{mid}"] = pd.Series([0.0])
        self.output_names = {
            "rtk": pd.Series([0.0]),
            "annual_growth_rate_freight": pd.Series([0.0]),
            "cagr_rtk": 0.0,
            "prospective_evolution_rtk": 0.0,
            "rtk_reference": pd.Series([0.0]),
            "reference_annual_growth_rate_freight": pd.Series([0.0]),
        }

    def compute(self, input_data: dict) -> dict:
        """Aggregate per-market RTK and reference RTK totals.

        Parameters
        ----------
        input_data : dict
            Inputs containing per-market RTK and RTK reference series.

        Returns
        -------
        dict
            Output totals and growth metrics for freight RTK.
        """
        total_rtk = None
        total_rtk_reference = None
        for mid in self.freight_market_ids:
            series = input_data[f"rtk_{mid}"]
            total_rtk = series if total_rtk is None else total_rtk + series
            series_ref = input_data[f"rtk_reference_{mid}"]
            total_rtk_reference = (
                series_ref if total_rtk_reference is None else total_rtk_reference + series_ref
            )

        self.df.loc[:, "rtk"] = total_rtk
        self.df.loc[:, "rtk_reference"] = total_rtk_reference

        self.df.loc[self.historic_start_year + 1 : self.end_year, "annual_growth_rate_freight"] = (
            self.df["rtk"].pct_change() * 100
        )
        self.df.loc[
            self.prospection_start_year + 1 : self.end_year, "reference_annual_growth_rate_freight"
        ] = self.df["rtk_reference"].pct_change() * 100

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
            "rtk_reference": self.df["rtk_reference"],
            "reference_annual_growth_rate_freight": self.df["reference_annual_growth_rate_freight"],
        }
        self._store_outputs(output_data)
        return output_data
