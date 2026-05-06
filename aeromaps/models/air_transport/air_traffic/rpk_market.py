"""
rpk_market
==========

Per-market RPK models for use when a MarketManager is loaded.

Three classes:

* ``RPKMeasuresMarket`` — sigmoid demand-reduction factor for one market.
* ``RPKMarket``         — CAGR+COVID recovery RPK for one market.
* ``RPKReferenceMarket`` — reference RPK trajectory for one market.

All use ``model_type="custom"`` (``AeroMAPSCustomModelWrapper``).  Input/output
names are built from the market id at construction time, so no ``custom_setup``
hook is required.
"""

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from aeromaps.models.base import AeroMAPSModel, aeromaps_leveling_function


class RPKMeasuresMarket(AeroMAPSModel):
    """Sigmoid demand-reduction impact for one passenger market.

    Parameters
    ----------
    name : str
        Discipline name.
    market_id : str
        Market identifier (e.g. ``'short_range'``, ``'domestic'``).
    """

    def __init__(self, name: str, market_id: str, *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        mid = market_id
        self.market_id = mid
        self.input_names = {
            f"{mid}_measures_final_impact": 0.0,
            f"{mid}_measures_start_year": 0.0,
            f"{mid}_measures_duration": 1.0,
        }
        self.output_names = {
            f"rpk_{mid}_measures_impact": pd.Series([0.0]),
        }

    def compute(self, input_data: dict) -> dict:
        """Compute demand-reduction multiplier for one passenger market.

        Parameters
        ----------
        input_data : dict
            Inputs for final impact, start year, and duration.

        Returns
        -------
        dict
            Output dictionary with the measures impact series.
        """
        mid = self.market_id
        final_impact = float(input_data[f"{mid}_measures_final_impact"])
        start_year = float(input_data[f"{mid}_measures_start_year"])
        duration = float(input_data[f"{mid}_measures_duration"])

        col = f"rpk_{mid}_measures_impact"
        transition_year = start_year + duration / 2
        limit = 0.02 * final_impact
        parameter = np.log(100 / 2 - 1) / (duration / 2) if duration > 0 else 1e10

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, col] = 1.0

        for k in range(self.prospection_start_year - 1, self.end_year + 1):
            sigmoid_val = final_impact / (1 + np.exp(-parameter * (k - transition_year)))
            if sigmoid_val < limit:
                self.df.loc[k, col] = 1.0
            else:
                self.df.loc[k, col] = 1.0 - final_impact / 100 / (
                    1 + np.exp(-parameter * (k - transition_year))
                )

        output_data = {col: self.df[col]}
        self._store_outputs(output_data)
        return output_data


class RPKMarket(AeroMAPSModel):
    """CAGR-based RPK growth with COVID recovery for one passenger market.

    Reads per-market parameters flattened from ``markets.yaml`` by
    ``_initialize_markets()``:

    * ``<mid>_rpk_share_2019``
    * ``<mid>_cagr_reference_periods`` / ``<mid>_cagr_reference_periods_values``
    * ``<mid>_covid_drop_start_year``, ``<mid>_covid_end_year``,
      ``<mid>_covid_end_year_reference_ratio``
    * ``<mid>_measures_impact``   (output of ``RPKMeasuresMarket``)
    * ``covid_start_year``         (global, from ``parameters.json``)
    * ``rpk_init``                 (global historical series)

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
            "rpk_init": pd.Series([0.0]),
            f"{mid}_rpk_share_2019": 0.0,
            f"{mid}_cagr_reference_periods": [],
            f"{mid}_cagr_reference_periods_values": [0.0],
            "covid_start_year": 0.0,
            f"{mid}_covid_drop_start_year": 0.0,
            f"{mid}_covid_end_year": 0.0,
            f"{mid}_covid_end_year_reference_ratio": 0.0,
            # Optional default=1.0 when no dedicated measures discipline is instantiated.
            f"rpk_{mid}_measures_impact": pd.Series([0.0]),
        }
        self.output_names = {
            f"rpk_{mid}": pd.Series([0.0]),
            f"annual_growth_rate_rpk_{mid}": pd.Series([0.0]),
            f"cagr_rpk_{mid}": 0.0,
            f"prospective_evolution_rpk_{mid}": 0.0,
        }

    def compute(self, input_data: dict) -> dict:
        """Compute per-market RPK with CAGR, COVID recovery, and measures impact.

        Parameters
        ----------
        input_data : dict
            Inputs containing market shares, CAGR references, and COVID settings.

        Returns
        -------
        dict
            Output series for market RPK and growth metrics.
        """
        mid = self.market_id
        rpk_init = input_data["rpk_init"]
        rpk_share_2019 = float(input_data[f"{mid}_rpk_share_2019"])
        cagr_ref_periods = list(input_data[f"{mid}_cagr_reference_periods"])
        cagr_ref_values = list(input_data[f"{mid}_cagr_reference_periods_values"])
        covid_start_year = int(input_data["covid_start_year"])
        covid_drop = float(input_data[f"{mid}_covid_drop_start_year"])
        covid_end_year = int(input_data[f"{mid}_covid_end_year"])
        covid_end_ratio = float(input_data[f"{mid}_covid_end_year_reference_ratio"])
        measures_impact = input_data[f"rpk_{mid}_measures_impact"]

        if not isinstance(rpk_init, pd.Series):
            rpk_init = pd.Series(
                rpk_init,
                index=range(self.historic_start_year, self.historic_start_year + len(rpk_init)),
            )
        if not isinstance(measures_impact, pd.Series):
            measures_impact = pd.Series(
                float(measures_impact),
                index=range(self.historic_start_year, self.end_year + 1),
            )

        rpk_col = f"rpk_{mid}"
        rate_col = f"annual_growth_rate_rpk_{mid}"

        # Historic initialisation: split total RPK by market share
        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, rpk_col] = rpk_share_2019 / 100 * rpk_init.loc[k]

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

        # COVID years (direct interpolation from last pre-COVID value)
        for k in range(covid_start_year, covid_end_year + 1):
            self.df.loc[k, rpk_col] = self.df.loc[covid_start_year - 1, rpk_col] * covid_func(k)

        # Post-COVID compounding growth
        for k in range(covid_end_year + 1, self.end_year + 1):
            self.df.loc[k, rpk_col] = self.df.loc[k - 1, rpk_col] * (
                1 + self.df.loc[k, rate_col] / 100
            )

        # Demand-reduction measures multiplier
        self.df.loc[:, rpk_col] = self.df[rpk_col] * measures_impact

        # Overwrite with actual historic growth rates
        for k in range(self.historic_start_year + 1, self.prospection_start_year):
            self.df.loc[k, rate_col] = (
                self.df.loc[k, rpk_col] / self.df.loc[k - 1, rpk_col] - 1
            ) * 100

        cagr = 100 * (
            (
                self.df.loc[self.end_year, rpk_col]
                / self.df.loc[self.prospection_start_year - 1, rpk_col]
            )
            ** (1 / (self.end_year - self.prospection_start_year))
            - 1
        )
        prospective_evolution = 100 * (
            self.df.loc[self.end_year, rpk_col]
            / self.df.loc[self.prospection_start_year - 1, rpk_col]
            - 1
        )

        output_data = {
            rpk_col: self.df[rpk_col],
            rate_col: self.df[rate_col],
            f"cagr_rpk_{mid}": cagr,
            f"prospective_evolution_rpk_{mid}": prospective_evolution,
        }
        self._store_outputs(output_data)
        return output_data


class RPKAggregator(AeroMAPSModel):
    """Sum per-market RPKs into a single total ``rpk`` consumed by downstream models.

    Also computes total ``annual_growth_rate_passenger``, ``cagr_rpk``, and
    ``prospective_evolution_rpk`` so legacy downstream disciplines need no changes.

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
        self.input_names = {}
        for mid in self.passenger_market_ids:
            self.input_names[f"rpk_{mid}"] = pd.Series([0.0])
            self.input_names[f"rpk_reference_{mid}"] = pd.Series([0.0])
        self.output_names = {
            "rpk": pd.Series([0.0]),
            "annual_growth_rate_passenger": pd.Series([0.0]),
            "cagr_rpk": 0.0,
            "prospective_evolution_rpk": 0.0,
            "rpk_reference": pd.Series([0.0]),
            "reference_annual_growth_rate_passenger": pd.Series([0.0]),
        }

    def compute(self, input_data: dict) -> dict:
        """Aggregate per-market RPK and compute growth metrics.

        Parameters
        ----------
        input_data : dict
            Inputs containing per-market RPK and reference series.

        Returns
        -------
        dict
            Output totals and growth metrics for passenger RPK.
        """
        total_rpk = None
        total_rpk_reference = None
        for mid in self.passenger_market_ids:
            series = input_data[f"rpk_{mid}"]
            total_rpk = series if total_rpk is None else total_rpk + series
            series_ref = input_data[f"rpk_reference_{mid}"]
            total_rpk_reference = (
                series_ref if total_rpk_reference is None else total_rpk_reference + series_ref
            )

        self.df.loc[:, "rpk"] = total_rpk
        self.df.loc[:, "rpk_reference"] = total_rpk_reference

        self.df.loc[
            self.historic_start_year + 1 : self.end_year, "annual_growth_rate_passenger"
        ] = self.df["rpk"].pct_change() * 100

        self.df.loc[
            self.prospection_start_year + 1 : self.end_year,
            "reference_annual_growth_rate_passenger",
        ] = self.df["rpk_reference"].pct_change() * 100

        cagr_rpk = 100 * (
            (
                self.df.loc[self.end_year, "rpk"]
                / self.df.loc[self.prospection_start_year - 1, "rpk"]
            )
            ** (1 / (self.end_year - self.prospection_start_year))
            - 1
        )
        prospective_evolution_rpk = 100 * (
            self.df.loc[self.end_year, "rpk"] / self.df.loc[self.prospection_start_year - 1, "rpk"]
            - 1
        )

        output_data = {
            "rpk": self.df["rpk"],
            "annual_growth_rate_passenger": self.df["annual_growth_rate_passenger"],
            "cagr_rpk": cagr_rpk,
            "prospective_evolution_rpk": prospective_evolution_rpk,
            "rpk_reference": self.df["rpk_reference"],
            "reference_annual_growth_rate_passenger": self.df[
                "reference_annual_growth_rate_passenger"
            ],
        }
        self._store_outputs(output_data)
        return output_data


class RPKReferenceMarket(AeroMAPSModel):
    """Reference RPK trajectory for one passenger market.

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
            f"rpk_{mid}": pd.Series([0.0]),
            f"{mid}_reference_cagr_reference_periods": [],
            f"{mid}_reference_cagr_reference_periods_values": [0.0],
            "covid_start_year": 0.0,
            f"{mid}_covid_drop_start_year": 0.0,
            f"{mid}_covid_end_year": 0.0,
            f"{mid}_covid_end_year_reference_ratio": 0.0,
        }
        self.output_names = {
            f"rpk_reference_{mid}": pd.Series([0.0]),
            f"reference_annual_growth_rate_rpk_{mid}": pd.Series([0.0]),
        }

    def compute(self, input_data: dict) -> dict:
        """Compute reference RPK trajectory for one passenger market.

        Parameters
        ----------
        input_data : dict
            Inputs containing market RPK, CAGR reference, and COVID settings.

        Returns
        -------
        dict
            Output series for reference RPK and its growth rate.
        """
        mid = self.market_id
        rpk = input_data[f"rpk_{mid}"]
        reference_periods = list(input_data[f"{mid}_reference_cagr_reference_periods"])
        reference_values = list(input_data[f"{mid}_reference_cagr_reference_periods_values"])
        covid_start_year = int(input_data["covid_start_year"])
        covid_drop_start_year = float(input_data[f"{mid}_covid_drop_start_year"])
        covid_end_year = int(input_data[f"{mid}_covid_end_year"])
        covid_end_ratio = float(input_data[f"{mid}_covid_end_year_reference_ratio"])

        col = f"rpk_reference_{mid}"
        rate_col = f"reference_annual_growth_rate_rpk_{mid}"

        for k in range(self.historic_start_year, self.prospection_start_year):
            self.df.loc[k, col] = rpk.loc[k]

        self.df.loc[covid_start_year - 1, col] = rpk.loc[covid_start_year - 1]

        reference_years = [covid_start_year, covid_end_year]
        reference_values_covid = [1 - covid_drop_start_year / 100, covid_end_ratio / 100]
        covid_function = interp1d(reference_years, reference_values_covid, kind="linear")

        reference_annual_growth_rate = aeromaps_leveling_function(
            self,
            reference_periods,
            reference_values,
            model_name=self.name,
        )
        self.df.loc[:, rate_col] = reference_annual_growth_rate

        for k in range(covid_start_year, covid_end_year + 1):
            self.df.loc[k, col] = self.df.loc[covid_start_year - 1, col] * covid_function(k)
        for k in range(covid_end_year + 1, self.end_year + 1):
            self.df.loc[k, col] = self.df.loc[k - 1, col] * (1 + self.df.loc[k, rate_col] / 100)

        output_data = {col: self.df[col], rate_col: self.df[rate_col]}
        self._store_outputs(output_data)
        return output_data
