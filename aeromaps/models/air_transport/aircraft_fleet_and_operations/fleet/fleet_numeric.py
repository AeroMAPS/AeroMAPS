# @Time : 25/01/2024 16:45
# @Author : a.salgas
# @File : aircrfat_numbe.py
# @Software: PyCharm
from aeromaps.models.base import AeroMAPSModel, aeromaps_interpolation_function
import pandas as pd
import numpy as np


def _ask_year_aligned(model, ask_year, index):
    """Return per-aircraft productivity (``ask_year``) aligned to ``index`` [ASK/yr].

    Accepts either a scalar (constant productivity, broadcast over the index) or
    an ``AeroMapsCustomDataType`` (years/values) — used when productivity evolves
    over time (e.g. fleet_productivity 2025 → 2045). The custom type is interpolated
    with the shared ``aeromaps_interpolation_function`` (honouring its declared
    ``method`` and ``positive_constraint``, with the last value held constant beyond
    the final reference year), exactly like every other custom data type in AeroMAPS.
    ``model`` is the ``FleetEvolution`` instance supplying ``prospection_start_year``,
    ``end_year`` and a scratch ``df``; ``index`` is the prospection range
    (``prospection_start_year..end_year``). Any gap before the first reference year is
    back-filled with the first value (the left-clamp the previous ``np.interp``
    produced). Returns a numpy array so element-wise division by the aircraft ASK
    series yields a per-year fleet count.
    """
    if hasattr(ask_year, "years") and hasattr(ask_year, "values"):
        series = aeromaps_interpolation_function(
            model,
            reference_years=ask_year.years,
            reference_years_values=ask_year.values,
            method=ask_year.method,
            positive_constraint=ask_year.positive_constraint,
            model_name="fleet_productivity_ask_year",
        )
        return series.reindex(index).bfill().values
    return float(ask_year)


class FleetEvolution(AeroMAPSModel):
    """Compute per-aircraft fleet counts, production and disposal for all passenger markets.

    ``model_type="custom"``: input/output names are built dynamically in
    :meth:`custom_setup` once the ``fleet_model`` has been injected by
    ``AeroMAPSProcess._initialize_disciplines``.

    Input variables
    ---------------
    ``covid_start_year``, ``covid_end_year_passenger``, ``dummy_fleet_model_output``
        Global scalars / signals.
    ``ask_{market_id}``
        ASK series for each passenger market (e.g. ``ask_short_range``).
    ``rpk_{market_id}``
        RPK series for each passenger market (e.g. ``rpk_short_range``).

    Output variables
    ----------------
    ``ask_aircraft_value_dict``, ``rpk_aircraft_value_dict``,
    ``aircraft_in_fleet_value_dict``, ``aircraft_in_fleet_value_covid_levelling_dict``,
    ``aircraft_in_out_value_dict``
        Dicts keyed by full aircraft name — consumed by downstream cost/abatement models.
    ``"<market.name>: Aircraft Production"`` / ``"<market.name>: Aircraft Disposal"``
        Aggregated series per market (e.g. ``"Short Range: Aircraft Production"``).
    """

    def __init__(self, name="fleet_numeric", fleet_model=None, *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.fleet_model = fleet_model
        self._skip_data_type_validation = True

        # Minimal placeholder grammar; overwritten by custom_setup() once
        # fleet_model is available.
        self.input_names = {
            "covid_start_year": 0.0,
            "covid_end_year_passenger": 0.0,
            "dummy_fleet_model_output": np.array([1.0]),
        }
        self.output_names = {
            "ask_aircraft_value_dict": {},
            "rpk_aircraft_value_dict": {},
            "aircraft_in_fleet_value_dict": {},
            "aircraft_in_fleet_value_covid_levelling_dict": {},
            "aircraft_in_out_value_dict": {},
        }

    def custom_setup(self):
        """Build dynamic input/output names from the fleet's passenger markets.

        Called by ``AeroMAPSProcess._initialize_disciplines`` immediately after
        ``fleet_model`` has been set and before the discipline is wrapped.
        """
        if self.fleet_model is None:
            return
        markets = self.fleet_model.fleet.markets
        if markets is None:
            return

        passenger_markets = markets.get(traffic_type="passenger")
        if not passenger_markets:
            return

        # inputs
        self.input_names = {
            "covid_start_year": 0.0,
            "covid_end_year_passenger": 0.0,
            "dummy_fleet_model_output": np.array([1.0]),
        }
        for market in passenger_markets:
            mid = market.id
            self.input_names[f"ask_{mid}"] = pd.Series([0.0])
            self.input_names[f"rpk_{mid}"] = pd.Series([0.0])

        # outputs
        self.output_names = {
            "ask_aircraft_value_dict": {},
            "rpk_aircraft_value_dict": {},
            "aircraft_in_fleet_value_dict": {},
            "aircraft_in_fleet_value_covid_levelling_dict": {},
            "aircraft_in_out_value_dict": {},
        }
        for market in passenger_markets:
            cat_name = market.name  # display name used as DataFrame column prefix
            self.output_names[f"{cat_name}: Aircraft Production"] = pd.Series([0.0])
            self.output_names[f"{cat_name}: Aircraft Disposal"] = pd.Series([0.0])

    def compute(self, input_data: dict) -> dict:
        """Compute fleet evolution outputs for each passenger market.

        Parameters
        ----------
        input_data : dict
            Inputs containing market ASK/RPK series and COVID timing.

        Returns
        -------
        dict
            Fleet-level series and per-aircraft dictionaries.
        """
        covid_start_year = int(input_data["covid_start_year"])
        covid_end_year_passenger = int(input_data["covid_end_year_passenger"])

        ask_aircraft_value_dict = {}
        rpk_aircraft_value_dict = {}
        aircraft_in_fleet_value_dict = {}
        aircraft_in_fleet_value_covid_levelling_dict = {}
        aircraft_in_out_value_dict = {}

        for category_name, sets in self.fleet_model.fleet.all_aircraft_elements.items():
            mid = self.fleet_model.fleet.categories[category_name].market_id
            category_ask = input_data[f"ask_{mid}"]
            category_rpk = input_data[f"rpk_{mid}"]

            # Compute virtual-fleet demand assuming production catches up after COVID.
            category_ask_covid_levelling = category_ask.copy()
            category_ask_pre_covid = category_ask.loc[covid_start_year - 1]
            category_ask_post_covid = category_ask.loc[covid_end_year_passenger]

            for year in range(covid_start_year, covid_end_year_passenger + 1):
                category_ask_covid_levelling.loc[year] = (
                    (category_ask_pre_covid - category_ask_post_covid) / (covid_start_year - 1)
                    - (covid_end_year_passenger)
                ) * (year - covid_start_year - 1) + category_ask_pre_covid

            # Compute per-aircraft values.
            for aircraft_var in sets:
                # Check whether this is a reference aircraft or a normal aircraft.
                if hasattr(aircraft_var, "parameters"):
                    aircraft_var_name = aircraft_var.parameters.full_name
                    ask_year = aircraft_var.parameters.ask_year
                else:
                    aircraft_var_name = aircraft_var.full_name
                    ask_year = aircraft_var.ask_year

                share_var_name = aircraft_var_name + ":aircraft_share"
                ask_aircraft_var_name = aircraft_var_name + ":aircraft_ask"
                rpk_aircraft_var_name = aircraft_var_name + ":aircraft_rpk"
                aircraft_in_fleet_var_name = aircraft_var_name + ":aircraft_in_fleet"
                aircraft_in_fleet_covid_levelling_var_name = (
                    aircraft_var_name + ":aircraft_in_fleet_covid_levelling"
                )
                aircraft_in_out_var_name = aircraft_var_name + ":aircraft_in_out"

                ask_aircraft_value = (
                    self.fleet_model.df.loc[
                        self.prospection_start_year : self.end_year, share_var_name
                    ]
                    / 100
                    * category_ask
                )

                rpk_aircraft_value = (
                    self.fleet_model.df.loc[
                        self.prospection_start_year : self.end_year, share_var_name
                    ]
                    / 100
                    * category_rpk
                )

                ask_aircraft_value_covid_levelling = (
                    self.fleet_model.df.loc[
                        self.prospection_start_year : self.end_year, share_var_name
                    ]
                    / 100
                    * category_ask_covid_levelling
                )

                # Productivity may be a scalar or a per-year series (AeroMapsCustomDataType).
                ask_year_aligned = _ask_year_aligned(self, ask_year, ask_aircraft_value.index)
                aircraft_in_fleet_value = np.ceil(ask_aircraft_value / ask_year_aligned)
                aircraft_in_fleet_value_covid_levelling = np.ceil(
                    ask_aircraft_value_covid_levelling / ask_year_aligned
                )
                aircraft_in_out_value = aircraft_in_fleet_value_covid_levelling.diff()

                self.fleet_model.df = pd.concat(
                    [
                        self.fleet_model.df,
                        ask_aircraft_value.rename(ask_aircraft_var_name),
                        rpk_aircraft_value.rename(rpk_aircraft_var_name),
                        aircraft_in_fleet_value.rename(aircraft_in_fleet_var_name),
                        aircraft_in_fleet_value_covid_levelling.rename(
                            aircraft_in_fleet_covid_levelling_var_name
                        ),
                        aircraft_in_out_value.rename(aircraft_in_out_var_name),
                    ],
                    axis=1,
                )

                ask_aircraft_value_dict[aircraft_var_name] = ask_aircraft_value
                rpk_aircraft_value_dict[aircraft_var_name] = rpk_aircraft_value
                aircraft_in_fleet_value_dict[aircraft_var_name] = aircraft_in_fleet_value
                aircraft_in_fleet_value_covid_levelling_dict[aircraft_var_name] = (
                    aircraft_in_fleet_value_covid_levelling
                )
                aircraft_in_out_value_dict[aircraft_var_name] = aircraft_in_out_value

        # Aggregate production / disposal per market category.
        output = {
            "ask_aircraft_value_dict": ask_aircraft_value_dict,
            "rpk_aircraft_value_dict": rpk_aircraft_value_dict,
            "aircraft_in_fleet_value_dict": aircraft_in_fleet_value_dict,
            "aircraft_in_fleet_value_covid_levelling_dict": aircraft_in_fleet_value_covid_levelling_dict,
            "aircraft_in_out_value_dict": aircraft_in_out_value_dict,
        }

        for cat_name, category in self.fleet_model.fleet.categories.items():
            prod_key = f"{cat_name}: Aircraft Production"
            disp_key = f"{cat_name}: Aircraft Disposal"
            cat_cols = filter_columns(
                self.fleet_model.df, f"{cat_name}:", suffix=":aircraft_in_out"
            )
            if cat_cols:
                df_cat = self.fleet_model.df[cat_cols]
                production = df_cat.apply(sum_positive, axis=1)
                disposal = df_cat.apply(sum_negative, axis=1)
            else:
                production = pd.Series(
                    0.0, index=range(self.prospection_start_year, self.end_year + 1)
                )
                disposal = pd.Series(
                    0.0, index=range(self.prospection_start_year, self.end_year + 1)
                )

            self.fleet_model.df[prod_key] = production
            self.fleet_model.df[disp_key] = disposal
            output[prod_key] = production
            output[disp_key] = disposal

        return output


def filter_columns(df, prefix, suffix):
    """
    Filters columns of a dataframe by prefix and suffix
    """
    return [col for col in df.columns if col.startswith(prefix) and col.endswith(suffix)]


def sum_positive(row):
    """
    Calculates the sum of positive values in a row of a dataframe
    """
    return row[row > 0].sum()


def sum_negative(row):
    """
    Calculates the absolute sum of negative values in a row of a dataframe
    """
    return abs(row[row < 0].sum())


class SimpleFleetCount(AeroMAPSModel):
    """Minimal fleet-count model: number of aircraft in fleet, per type and per market.

    A deliberately stripped-down alternative to :class:`FleetEvolution`. For each
    passenger market and each aircraft in the bottom-up fleet it computes only::

        aircraft_in_fleet = ceil(aircraft_ask / productivity)

    with ``aircraft_ask = aircraft_share / 100 * market_ask`` and ``productivity``
    the aircraft's ``ask_year`` (a scalar, or a per-year ``AeroMapsCustomDataType``
    interpolated via :func:`_ask_year_aligned`) — exactly the productivity notion
    ``FleetEvolution`` uses.

    Everything ``FleetEvolution`` layers on top is intentionally omitted: COVID
    levelling, RPK, aircraft production/disposal flows, and the extra per-aircraft
    dictionaries the manufacturing-cost models consume. Use this when a scenario
    only needs fleet sizes (e.g. the custom multi-region workflow). Because it
    skips production/disposal it is *not* a drop-in replacement for
    ``FleetEvolution`` upstream of the recurring/non-recurring cost models.

    Like ``FleetEvolution`` it reads the per-aircraft ``aircraft_share`` columns
    from ``fleet_model.df`` (so ``FleetModel.compute`` must have run first) and
    writes ``{aircraft_full_name}:aircraft_in_fleet`` back onto it.

    Parameters
    ----------
    name : str
        Model instance name ('passenger_aircraft_fleet_count' by default).

    Documentation
    --------------
    Inputs
        - dummy_fleet_model_output: Fleet-model trigger placeholder.
        - ask_<market>: ASK series for each passenger market [ASK].
    Outputs
        - aircraft_in_fleet_value_dict: Per-aircraft fleet counts, keyed by full
          aircraft name [count].
        - "<market.name>: Aircraft In Fleet": Per-market total fleet count [count].
    Notes
        - <market> is the MarketManager id (passenger markets).
        - I/O names are built dynamically from the fleet's market registry once
          ``fleet_model`` is injected by ``AeroMAPSProcess._initialize_disciplines``.

    Attributes
    ----------
    fleet_model : FleetModel
        Bottom-up fleet model supplying the aircraft inventory and share columns.
    """

    def __init__(self, name="passenger_aircraft_fleet_count", fleet_model=None, *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.fleet_model = fleet_model
        self._skip_data_type_validation = True

        # Minimal placeholder grammar; overwritten by custom_setup() once
        # fleet_model is available.
        self.input_names = {"dummy_fleet_model_output": np.array([1.0])}
        self.output_names = {"aircraft_in_fleet_value_dict": {}}

    def custom_setup(self):
        """Build dynamic input/output names from the fleet's passenger markets.

        Called by ``AeroMAPSProcess._initialize_disciplines`` immediately after
        ``fleet_model`` has been set and before the discipline is wrapped.
        """
        if self.fleet_model is None:
            return
        markets = self.fleet_model.fleet.markets
        if markets is None:
            return

        passenger_markets = markets.get(traffic_type="passenger")
        if not passenger_markets:
            return

        self.input_names = {"dummy_fleet_model_output": np.array([1.0])}
        for market in passenger_markets:
            self.input_names[f"ask_{market.id}"] = pd.Series([0.0])

        self.output_names = {"aircraft_in_fleet_value_dict": {}}
        for market in passenger_markets:
            cat_name = market.name  # display name used as DataFrame column prefix
            self.output_names[f"{cat_name}: Aircraft In Fleet"] = pd.Series([0.0])

    def compute(self, input_data: dict) -> dict:
        """Compute the number of aircraft in fleet for each aircraft and market.

        Parameters
        ----------
        input_data : dict
            Inputs containing the per-market ASK series.

        Returns
        -------
        dict
            ``aircraft_in_fleet_value_dict`` plus one per-market total series.
        """
        aircraft_in_fleet_value_dict = {}
        output_data = {}

        for category_name, sets in self.fleet_model.fleet.all_aircraft_elements.items():
            category = self.fleet_model.fleet.categories[category_name]
            category_ask = input_data[f"ask_{category.market_id}"]
            market_total = None

            for aircraft_var in sets:
                # Reference aircraft expose their fields directly; new aircraft via .parameters.
                if hasattr(aircraft_var, "parameters"):
                    aircraft_var_name = aircraft_var.parameters.full_name
                    ask_year = aircraft_var.parameters.ask_year
                else:
                    aircraft_var_name = aircraft_var.full_name
                    ask_year = aircraft_var.ask_year

                aircraft_ask = (
                    self.fleet_model.df.loc[
                        self.prospection_start_year : self.end_year,
                        f"{aircraft_var_name}:aircraft_share",
                    ]
                    / 100
                    * category_ask
                )

                # Productivity may be a scalar or a per-year series (AeroMapsCustomDataType).
                ask_year_aligned = _ask_year_aligned(self, ask_year, aircraft_ask.index)
                aircraft_in_fleet_value = np.ceil(aircraft_ask / ask_year_aligned)

                # Direct assignment (idempotent: overwrites if already present) rather than
                # concat, so re-running the model never produces duplicate columns. The
                # prospection-indexed series leaves historical years NaN on fleet_model.df.
                aircraft_in_fleet_var_name = f"{aircraft_var_name}:aircraft_in_fleet"
                self.fleet_model.df[aircraft_in_fleet_var_name] = aircraft_in_fleet_value
                aircraft_in_fleet_value_dict[aircraft_var_name] = aircraft_in_fleet_value
                market_total = (
                    aircraft_in_fleet_value
                    if market_total is None
                    else market_total + aircraft_in_fleet_value
                )

            output_data[f"{category.name}: Aircraft In Fleet"] = market_total

        # Like FleetEvolution, outputs (Series + the per-aircraft dict) are returned
        # directly for GEMSEO to route; _store_outputs is not used as it rejects dicts.
        output_data["aircraft_in_fleet_value_dict"] = aircraft_in_fleet_value_dict
        return output_data
