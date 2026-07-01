"""
fleet_push_model
================

AeroMAPS-model wrapper around Paco's delivery-driven ("push") fleet-renewal
engine (:func:`market_process` in ``fleet_model_push``).

:class:`PassengerAircraftEfficiencyFleetPush` makes the push engine selectable
like any other AeroMAPS efficiency model: it emits the per-passenger-market
**efficiency bridge** (drop-in only) that downstream consumers
(``PassengerAircraftEfficiencySimpleASK``, ``FreightAircraftEfficiency``,
``EnergyIntensity`` …) read, mirroring
:class:`PassengerAircraftEfficiencySimpleShares`.

Scope (this phase): efficiency bridge only — drop-in fuel carries 100 % of the
ASK; the hydrogen/electric columns mirror the drop-in series so downstream
relative-intensity reads stay finite. Fleet-count / deliveries outputs and the
plot migration are a later phase.

I/O grammar (per passenger market ``mid``)
    Inputs
        - ask_<mid>                                    : passenger ASK [ASK] (Series)
        - <mid>_energy_share_last_historical_year      : pivot-year energy share [%]
        - <mid>_rpk_share_last_historical_year         : pivot-year RPK share [%]
        plus global ``energy_consumption_init`` [MJ] and ``ask_init`` [ASK].
    Outputs (per ``mid`` and ``et`` in dropin_fuel/hydrogen/electric)
        - energy_per_ask_without_operations_<mid>_<et> : energy per ASK [MJ/ASK]
        - ask_<mid>_<et>_share                         : ASK share per energy [%]
"""

import logging
from functools import lru_cache

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel
from aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet.fleet_model_push import (
    _load_yaml,
    _resolve_project_path,
    _build_aircraft_to_market_mapping,
    _build_market_to_types_mapping,
    calculate_stats_by_market,
    market_process,
)

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Static resource paths (Hybrid input layer — Decision #2).
# The four scenario YAMLs ship as resources; the calibration Excel currently
# still lives under utils/calibration_notebooks/ (moving it is out of scope).
# --------------------------------------------------------------------------- #
_FLEET_PUSH_RES = "aeromaps/resources/data/default_fleet_push"
_FLEET_PUSH_XLS = "aeromaps/utils/calibration_notebooks/fleet_calibrated_inputs_processed_here"

_CLASSIFICATION_YAML = f"{_FLEET_PUSH_RES}/default_aircraft_classification.yaml"
_MARKET_PARAM_YAML = f"{_FLEET_PUSH_RES}/default_market_param.yaml"
_IN_PRODUCTION_YAML = f"{_FLEET_PUSH_RES}/default_in_production_aircraft_inventory.yaml"
_NEW_AIRCRAFT_YAML = f"{_FLEET_PUSH_RES}/default_new_aircraft_inventory.yaml"
_AIRCRAFT_PARAMS_XLS = f"{_FLEET_PUSH_XLS}/aircraft_type_key_parameters.xlsx"
_FLEET_XLS = f"{_FLEET_PUSH_XLS}/agg_fleet_end_2024.xlsx"

# AeroMAPS market id -> Paco engine segment label.
_MARKET_ID_TO_ENGINE_LABEL = {
    "turboprop": "TP",
    "regional_jet": "RJ",
    "narrow_body": "NB",
    "wide_body": "WB",
}

# The push engine is calibrated to the end-2024 fleet (``agg_fleet_end_2024.xlsx``)
# and the 2024 per-type ASK / MJ-per-ASK. Its pivot is therefore fixed at 2024, so a
# scenario using this model MUST have ``last_historical_year == 2024`` (equivalently
# ``prospection_start_year == 2025``). Running it on any other pivot would mis-date the
# fleet by (2024 - last_historical_year) years.
_ENGINE_ANCHOR_YEAR = 2024


@lru_cache(maxsize=1)
def _load_push_engine_inputs():
    """Load the four scenario YAMLs + the calibration Excel **once** and build the
    per-engine-segment input structures consumed by :func:`market_process`.

    This replicates ``fleet_process``'s loading (without its prints / plots /
    matplotlib) and returns, keyed by engine label (TP/RJ/NB/WB), the per-market
    engine arguments. Cached so the static Excel is read exactly once per process
    (and reused across the four segments).

    Returns
    -------
    dict[str, dict]
        ``{engine_label: {total_asks, distance_per_aircraft, fleet_market,
        old_ac_carac, in_prod_ac_carac, future_ac_carac, market_data}}``.
    """
    classification_data = _load_yaml(_CLASSIFICATION_YAML)
    market_data_config = _load_yaml(_MARKET_PARAM_YAML)
    in_production_fleet_data = _load_yaml(_IN_PRODUCTION_YAML)
    new_fleet_data = _load_yaml(_NEW_AIRCRAFT_YAML)

    mapping_types = _build_aircraft_to_market_mapping(classification_data)
    market_to_types = _build_market_to_types_mapping(mapping_types)

    fleet_df = pd.read_excel(_resolve_project_path(_FLEET_XLS)).copy()
    params_df = pd.read_excel(_resolve_project_path(_AIRCRAFT_PARAMS_XLS)).copy()
    fleet_df["Aircraft Type"] = fleet_df["Aircraft Type"].astype(str).str.strip()
    params_df["Aircraft Type"] = params_df["Aircraft Type"].astype(str).str.strip()
    fleet_df["market"] = fleet_df["Aircraft Type"].map(mapping_types)
    params_df["market"] = params_df["Aircraft Type"].map(mapping_types)

    rows = []
    for market, content in new_fleet_data["markets"].items():
        for aircraft in content.get("new_aircraft_types", []):
            row = aircraft.copy()
            row["market"] = market
            rows.append(row)
    new_ac_carac = pd.DataFrame(rows)
    if not new_ac_carac.empty:
        new_ac_carac["market"] = new_ac_carac["market"].astype(str).str.strip()

    rows = []
    for market, content in in_production_fleet_data["markets"].items():
        for aircraft in content.get("current_aircraft_types", []):
            ref_points = aircraft.get("reference_production_points", [])
            years = [p["year"] for p in ref_points]
            values = [p["value"] for p in ref_points]
            rows.append(
                {
                    "name": aircraft["name"],
                    "market": market,
                    "energy_efficiency": aircraft["energy_efficiency"],
                    "seats": aircraft["seats"],
                    "ret_year_delay": aircraft["ret_year_delay"],
                    "production_profile": [years, values],
                }
            )
    in_prod_ac_carac = pd.DataFrame(rows)
    if not in_prod_ac_carac.empty:
        in_prod_ac_carac["market"] = in_prod_ac_carac["market"].astype(str).str.strip()

    rows = []
    for market, content in market_data_config["markets"].items():
        ref_points = content.get("reference_growth", [])
        years = [p["year"] for p in ref_points]
        rate = [p["rate"] for p in ref_points]
        rows.append(
            {
                "market": market,
                "age_utilisation_sensib": content["age_utilisation_sensib"],
                "age_retirement_sensib": content["age_retirement_sensib"],
                "production_profile": [years, rate],
            }
        )
    markets_data = pd.DataFrame(rows)
    markets_data["market"] = markets_data["market"].astype(str).str.strip()
    markets_data.index = markets_data["market"]

    markets = calculate_stats_by_market(
        classification_yaml_path=_resolve_project_path(_CLASSIFICATION_YAML),
        aircraft_parameters_excel_path=_resolve_project_path(_AIRCRAFT_PARAMS_XLS),
    )

    engine_inputs = {}
    for i in range(markets.shape[0]):
        engine_label = markets.iloc[i, 0]
        keys_market = market_to_types.get(engine_label, [])
        engine_inputs[engine_label] = {
            "total_asks": markets.iloc[i, 1],
            "distance_per_aircraft": markets.iloc[i, 2],
            "fleet_market": fleet_df[fleet_df["Aircraft Type"].isin(keys_market)],
            "old_ac_carac": params_df[params_df["Aircraft Type"].isin(keys_market)],
            "future_ac_carac": new_ac_carac[new_ac_carac["market"] == engine_label],
            "in_prod_ac_carac": in_prod_ac_carac[in_prod_ac_carac["market"] == engine_label],
            "market_data": markets_data.loc[engine_label],
        }
    return engine_inputs


class PassengerAircraftEfficiencyFleetPush(AeroMAPSModel):
    """Per-market energy per ASK from Paco's delivery-driven ("push") fleet engine.

    Drop-in replacement for :class:`PassengerAircraftEfficiencySimpleShares` in
    the passenger efficiency slot: same I/O grammar for the drop-in bridge, but
    the projection energy-per-ASK is produced by running :func:`market_process`
    per segment with the AeroMAPS ASK series injected, instead of a gain curve.

    v1 is drop-in only: ``ask_<mid>_dropin_fuel_share`` is 100, hydrogen/electric
    shares are 0 and their ``energy_per_ask`` columns mirror the drop-in series.
    """

    def __init__(self, name="passenger_aircraft_efficiency_fleet_push", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.markets = None

    def custom_setup(self):
        # Hard pivot guard: the engine is anchored to the end-2024 fleet, so the
        # scenario MUST pivot on 2024 (prospection_start_year == 2025). Fail fast at
        # build time rather than silently mis-dating the fleet.
        if self.last_historical_year != _ENGINE_ANCHOR_YEAR:
            raise ValueError(
                f"{type(self).__name__} requires the scenario to pivot on "
                f"{_ENGINE_ANCHOR_YEAR}, i.e. prospection_start_year == "
                f"{_ENGINE_ANCHOR_YEAR + 1} (last_historical_year == {_ENGINE_ANCHOR_YEAR}). "
                f"The push engine is calibrated to the end-{_ENGINE_ANCHOR_YEAR} fleet "
                f"(agg_fleet_end_{_ENGINE_ANCHOR_YEAR}.xlsx) and the {_ENGINE_ANCHOR_YEAR} "
                f"per-type ASK/MJ. Got prospection_start_year="
                f"{self.prospection_start_year} (last_historical_year="
                f"{self.last_historical_year}). Provide a {_ENGINE_ANCHOR_YEAR + 1}-pivot "
                f"scenario whose historic *_init vectors run 2000-{_ENGINE_ANCHOR_YEAR} "
                f"(see tutorials/13_change_the_prospection_start_year/data/inputs_2025.json)."
            )

        passenger_markets = self.markets.get(traffic_type="passenger")
        self.input_names = {
            "energy_consumption_init": pd.Series([0.0]),
            "ask_init": pd.Series([0.0]),
        }
        for m in passenger_markets:
            mid = m.id
            self.input_names[f"ask_{mid}"] = pd.Series([0.0])
            self.input_names[f"{mid}_energy_share_last_historical_year"] = 0.0
            self.input_names[f"{mid}_rpk_share_last_historical_year"] = 0.0

        self.output_names = {}
        for m in passenger_markets:
            mid = m.id
            for et in ("dropin_fuel", "hydrogen", "electric"):
                self.output_names[f"energy_per_ask_without_operations_{mid}_{et}"] = pd.Series(
                    [0.0]
                )
                self.output_names[f"ask_{mid}_{et}_share"] = pd.Series([0.0])

    def compute(self, input_data: dict) -> dict:
        """Run the push engine per passenger market and emit the drop-in bridge.

        Parameters
        ----------
        input_data : dict
            Per-market ASK series and pivot-year calibration shares.

        Returns
        -------
        dict
            Energy-per-ASK series and ASK shares by energy type per market.
        """
        passenger_markets = self.markets.get(traffic_type="passenger")

        energy_consumption_init = input_data["energy_consumption_init"]
        ask_init = input_data["ask_init"]
        energy_consumption_per_ask_init = energy_consumption_init / ask_init

        idx_hist = pd.Index(np.arange(self.historic_start_year, self.last_historical_year + 1))

        # The engine pivots on the last historical year and projects to end_year.
        # Set the horizon to end_year + 1 so the convergence loop covers every year
        # up to and including end_year (ask_volumes[t] exists for t = 0 .. end_year-pivot).
        horizon = self.end_year + 1
        # ASK series the engine consumes directly as ``yearly_traffic``, indexed
        # [last_historical_year .. end_year]. The engine needs ``modeled_periods + 1``
        # values, i.e. one extra entry for the horizon year (end_year + 1) which only
        # fixes the axis and is never read for a year we output. The AeroMAPS ASK
        # series stops at end_year, so that trailing entry is held flat at the
        # end_year value (a NaN there would poison the engine's capacity guard).
        ask_sample_years = np.arange(self.last_historical_year, self.end_year + 1)

        engine_inputs = _load_push_engine_inputs()

        output_data = {}

        for m in passenger_markets:
            mid = m.id
            engine_label = _MARKET_ID_TO_ENGINE_LABEL.get(mid)
            energy_share = float(input_data[f"{mid}_energy_share_last_historical_year"])
            rpk_share = float(input_data[f"{mid}_rpk_share_last_historical_year"])

            dropin_col = f"energy_per_ask_without_operations_{mid}_dropin_fuel"
            h2_col = f"energy_per_ask_without_operations_{mid}_hydrogen"
            el_col = f"energy_per_ask_without_operations_{mid}_electric"

            # --- History splice (identical construction to SimpleShares) --------
            self.df.loc[idx_hist, dropin_col] = np.where(
                rpk_share != 0,
                energy_consumption_per_ask_init.loc[idx_hist] * energy_share / rpk_share,
                np.nan,
            )

            if engine_label is None:
                # Passenger market not mapped to a push segment: cannot run the
                # engine. Carry the last-historical value flat over the projection
                # so downstream reads stay finite.
                logger.warning(
                    "Market '%s' has no push engine segment mapping; "
                    "holding last-historical energy/ASK flat over the projection.",
                    mid,
                )
                self.df.loc[self.prospection_start_year :, dropin_col] = self.df.loc[
                    self.last_historical_year, dropin_col
                ]
            else:
                cfg = engine_inputs[engine_label]
                ask_proj = input_data[f"ask_{mid}"].reindex(ask_sample_years).to_numpy(dtype=float)
                # Append the horizon-year (end_year + 1) entry, held flat at end_year,
                # so the engine has modeled_periods + 1 finite traffic targets.
                ask_series = np.concatenate([ask_proj, ask_proj[-1:]])

                # Override the engine horizon (growth rates unused under ASK injection;
                # only the last production-profile year matters for the axis).
                market_data = cfg["market_data"].copy()
                pp = market_data["production_profile"]
                market_data["production_profile"] = [
                    [pp[0][0], horizon],
                    [pp[1][0], pp[1][-1]],
                ]

                (_years, _deliveries, ask_volumes, _seats, energy_consumption, feasible) = (
                    market_process(
                        cfg["total_asks"],
                        market_data,
                        cfg["distance_per_aircraft"],
                        cfg["fleet_market"],
                        cfg["old_ac_carac"],
                        cfg["in_prod_ac_carac"],
                        cfg["future_ac_carac"],
                        ask_series=ask_series,
                        last_historical_year=self.last_historical_year,
                    )
                )
                if not feasible:
                    logger.warning(
                        "push engine: demand not fully met by deliveries in segment '%s' "
                        "(market id '%s'); proceeding (robustness/clamping is a later phase).",
                        engine_label,
                        mid,
                    )

                # YEAR ALIGNMENT: ask_volumes[t] <-> year (last_historical_year + t).
                # Do NOT use the returned `years` axis (off by one). Write the projection
                # years [prospection_start_year .. end_year] from t = 1 .. end_year-pivot.
                n_periods = ask_volumes.shape[0]
                for year in range(self.prospection_start_year, self.end_year + 1):
                    t = year - self.last_historical_year
                    if t >= n_periods:
                        # Horizon did not reach this year (should not happen with
                        # horizon = end_year + 1); hold previous value.
                        self.df.loc[year, dropin_col] = self.df.loc[year - 1, dropin_col]
                        continue
                    ask_t = ask_volumes[t].sum()
                    energy_t = energy_consumption[t].sum()
                    self.df.loc[year, dropin_col] = energy_t / ask_t if ask_t != 0 else np.nan

            dropin_series = self.df[dropin_col]

            # --- Route 100 % to drop-in; mirror H2/electric energy columns -------
            self.df.loc[:, h2_col] = dropin_series
            self.df.loc[:, el_col] = dropin_series

            dropin_share_col = f"ask_{mid}_dropin_fuel_share"
            h2_share_col = f"ask_{mid}_hydrogen_share"
            el_share_col = f"ask_{mid}_electric_share"
            self.df.loc[:, dropin_share_col] = 100.0
            self.df.loc[:, h2_share_col] = 0.0
            self.df.loc[:, el_share_col] = 0.0

            output_data[dropin_col] = self.df[dropin_col]
            output_data[h2_col] = self.df[h2_col]
            output_data[el_col] = self.df[el_col]
            output_data[dropin_share_col] = self.df[dropin_share_col]
            output_data[h2_share_col] = self.df[h2_share_col]
            output_data[el_share_col] = self.df[el_share_col]

        self._store_outputs(output_data)
        return output_data
