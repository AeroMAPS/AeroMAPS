"""
aircraft_efficiency_fleet_push
==============================

AeroMAPS-model wrapper around Paco's delivery-driven ("push") fleet-renewal
engine (:func:`market_process` in ``fleet_model_push``).

:class:`PassengerAircraftEfficiencyFleetPush` makes the push engine selectable
like any other AeroMAPS efficiency model: it emits the per-passenger-market
**efficiency bridge** (drop-in only) that downstream consumers
(``PassengerAircraftEfficiencySimpleASK``, ``FreightAircraftEfficiency``,
``EnergyIntensity`` …) read, mirroring
:class:`PassengerAircraftEfficiencySimpleShares`.

Scope: the per-passenger-market efficiency bridge (drop-in fuel carries 100 % of
the ASK; the hydrogen/electric columns mirror the drop-in series so downstream
relative-intensity reads stay finite) **plus** (Phase 5) the push model's native
fleet state — per-segment & per-type fleet counts and per-type deliveries —
emitted as plain ``pd.Series`` columns mirroring :class:`SimpleFleetCount`'s naming.

I/O grammar (per passenger market ``mid``)
    Inputs
        - ask_<mid>                                    : passenger ASK [ASK] (Series)
        - <mid>_energy_share_last_historical_year      : pivot-year energy share [%]
        - <mid>_rpk_share_last_historical_year         : pivot-year RPK share [%]
        plus global ``energy_consumption_init`` [MJ] and ``ask_init`` [ASK].
    Outputs (per ``mid`` and ``et`` in dropin_fuel/hydrogen/electric)
        - energy_per_ask_without_operations_<mid>_<et> : energy per ASK [MJ/ASK]
        - ask_<mid>_<et>_share                         : ASK share per energy [%]
    Fleet outputs (Phase 5)
        - "<market.name>: Aircraft In Fleet"           : per-segment total fleet
          count [count] (mirrors :class:`SimpleFleetCount`).
        - <mid>:<aircraft_type>:aircraft_in_fleet      : per-type fleet count [count].
        - <mid>:<aircraft_type>:aircraft_deliveries    : per-type new deliveries
          per year [count].

Fleet-output year alignment (verified empirically against the engine)
    The engine returns ``aircraft_seats_volumes`` of shape ``(periods, F, T)`` with
    period ``t`` <-> year ``last_historical_year + t`` (``t = 0`` is the pivot), and
    ``deliveries`` of shape ``(periods - 1, T)`` with row ``k`` <-> year
    ``first_projection_year + k = last_historical_year + 1 + k``. The returned
    ``years`` axis is off-by-one and is **not** used. Per-type aircraft count at a
    period is ``aircraft_seats_volumes[t].sum(axis=0) / seats_array``; the per-segment
    total is the sum over types. Pre-pivot history years are left at NaN for fleet
    counts and deliveries (the engine has no fleet state there — the calibrated
    fleet is the end-of-pivot-year snapshot).
"""

import logging

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel
from aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet_push.fleet_model_push import (
    _load_yaml,
    _resolve_project_path,
    _build_aircraft_to_market_mapping,
    _build_market_to_types_mapping,
    calculate_stats_by_market,
    market_process,
)
from aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet_push.fleet_model_push_visualisations import (
    visu_fleet_array,
    visu_retirements_array,
    visu_retirement_age,
    visu_energy_intensity,
)

logger = logging.getLogger(__name__)

# Input-file grammar (Hybrid input layer — Decision #2). These are the field names
# accepted under the ``models.fleet_push`` config block, in the order
# :func:`_load_push_engine_inputs` consumes them. The model owns no default *paths*:
# like every other AeroMAPS model, ``process.py`` resolves the paths from config (the
# package default config.yaml supplies the shipped defaults; the ``default`` keyword and
# per-key overrides both work) and injects them as ``self.input_files`` before setup.
# Imported by process.py as the single source of truth for the accepted field names.
PUSH_FLEET_INPUT_FILE_KEYS = (
    "classification_data_file",
    "market_param_data_file",
    "in_production_inventory_file",
    "new_aircraft_inventory_file",
    "aircraft_parameters_file",
    "fleet_snapshot_file",
)

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


def _load_push_engine_inputs(
    classification_yaml,
    market_param_yaml,
    in_production_yaml,
    new_aircraft_yaml,
    aircraft_params_xls,
    fleet_xls,
):
    """Load the four scenario YAMLs + the calibration Excel and build the
    per-engine-segment input structures consumed by :func:`market_process`.

    The six paths come from the model's ``self.input_files`` (resolved from config by
    ``process.py``). Called **once** from :meth:`custom_setup`, which caches the result
    on the instance (``self._engine_inputs``) for reuse across segments and across
    every ``compute()`` — mirroring how ``Fleet`` loads its YAMLs once at build time.

    Returns
    -------
    dict[str, dict]
        ``{engine_label: {distance_per_aircraft, fleet_market,
        old_ac_carac, in_prod_ac_carac, future_ac_carac, market_data}}``.
    """
    classification_data = _load_yaml(classification_yaml)
    market_data_config = _load_yaml(market_param_yaml)
    in_production_fleet_data = _load_yaml(in_production_yaml)
    new_fleet_data = _load_yaml(new_aircraft_yaml)

    mapping_types = _build_aircraft_to_market_mapping(classification_data)
    market_to_types = _build_market_to_types_mapping(mapping_types)

    fleet_df = pd.read_excel(_resolve_project_path(fleet_xls)).copy()
    params_df = pd.read_excel(_resolve_project_path(aircraft_params_xls)).copy()
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
        # Only the age sensibilities are read from default_market_param.yaml. The
        # legacy per-segment growth profile lives in the markets config now (it drives
        # the injected ASK via the AeroMAPS demand chain); the engine's production-
        # profile axis is set from the calendar in compute().
        rows.append(
            {
                "market": market,
                "age_utilisation_sensib": content["age_utilisation_sensib"],
                "age_retirement_sensib": content["age_retirement_sensib"],
            }
        )
    markets_data = pd.DataFrame(rows)
    markets_data["market"] = markets_data["market"].astype(str).str.strip()
    markets_data.index = markets_data["market"]

    markets = calculate_stats_by_market(
        classification_yaml_path=_resolve_project_path(classification_yaml),
        aircraft_parameters_excel_path=_resolve_project_path(aircraft_params_xls),
    )

    engine_inputs = {}
    for i in range(markets.shape[0]):
        engine_label = markets.iloc[i, 0]
        keys_market = market_to_types.get(engine_label, [])
        old_ac_carac = params_df[params_df["Aircraft Type"].isin(keys_market)]
        in_prod = in_prod_ac_carac[in_prod_ac_carac["market"] == engine_label]
        future = new_ac_carac[new_ac_carac["market"] == engine_label]
        # Assembled per-type NAMES and SEATS in the engine's column order
        # (old types, then in-production, then future) -- identical to
        # market_process's internal ``seats_array`` / ``ac_names`` construction.
        ac_names = (
            list(old_ac_carac["Aircraft Type"]) + list(in_prod["name"]) + list(future["name"])
        )
        seats_array = np.concatenate(
            [
                old_ac_carac["average_seats"].to_numpy(dtype=float),
                in_prod["seats"].to_numpy(dtype=float),
                future["seats"].to_numpy(dtype=float),
            ]
        )
        engine_inputs[engine_label] = {
            "distance_per_aircraft": markets.iloc[i, 2],
            "fleet_market": fleet_df[fleet_df["Aircraft Type"].isin(keys_market)],
            "old_ac_carac": old_ac_carac,
            "future_ac_carac": future,
            "in_prod_ac_carac": in_prod,
            "market_data": markets_data.loc[engine_label],
            "ac_names": ac_names,
            "seats_array": seats_array,
        }
    return engine_inputs


def _sanitize_type_name(name: str) -> str:
    """Make an aircraft type name safe to use inside a DataFrame column key.

    The output names are ``<mid>:<aircraft_type>:aircraft_in_fleet`` / ``...
    :aircraft_deliveries``; ``:`` is the field separator so any colon (or
    surrounding whitespace) in a raw type name is collapsed to ``_``.
    """
    return "_".join(str(name).split()).replace(":", "_")


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
        # Engine input files: a dict keyed by PUSH_FLEET_INPUT_FILE_KEYS, injected by
        # process.py (resolved from the models.fleet_push config block) before
        # custom_setup(). The model owns no default paths of its own.
        self.input_files = None
        # Engine inputs loaded once in custom_setup() (mirrors Fleet loading its YAMLs
        # at build time); reused across segments and every compute().
        self._engine_inputs = None
        # Per-segment engine arrays cached on the last compute() for plot().
        # Keyed by market id; each value holds the raw (age-resolved) engine
        # returns that the flat output columns sum away.
        self._engine_results = {}

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

        if not self.input_files:
            raise RuntimeError(
                f"{type(self).__name__}.input_files was not injected. It is set by "
                "process.py from the models.fleet_push config block before custom_setup()."
            )
        # Load the static engine inputs once and cache on the instance (reused across
        # segments and every compute()).
        self._engine_inputs = _load_push_engine_inputs(
            *(self.input_files[k] for k in PUSH_FLEET_INPUT_FILE_KEYS)
        )
        engine_inputs = self._engine_inputs

        self.output_names = {}
        for m in passenger_markets:
            mid = m.id
            for et in ("dropin_fuel", "hydrogen", "electric"):
                self.output_names[f"energy_per_ask_without_operations_{mid}_{et}"] = pd.Series(
                    [0.0]
                )
                self.output_names[f"ask_{mid}_{et}_share"] = pd.Series([0.0])

            # Fleet bridge (Phase 5): per-segment total + per-type counts/deliveries.
            # Mirror SimpleFleetCount's per-segment name so existing consumers/plots
            # pick it up. Per-type columns use the engine's assembled ac_names.
            self.output_names[f"{m.name}: Aircraft In Fleet"] = pd.Series([0.0])
            engine_label = _MARKET_ID_TO_ENGINE_LABEL.get(mid)
            if engine_label is None:
                continue
            for raw_name in engine_inputs[engine_label]["ac_names"]:
                ac = _sanitize_type_name(raw_name)
                self.output_names[f"{mid}:{ac}:aircraft_in_fleet"] = pd.Series([0.0])
                self.output_names[f"{mid}:{ac}:aircraft_deliveries"] = pd.Series([0.0])

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
        # Reset the per-segment engine cache (rebuilt below for plot()).
        self._engine_results = {}

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

        # Reuse the engine inputs loaded once in custom_setup().
        engine_inputs = self._engine_inputs

        # Full year index for the fleet-state columns (NaN pre-pivot history).
        full_years = np.arange(self.historic_start_year, self.end_year + 1)

        output_data = {}

        for m in passenger_markets:
            mid = m.id
            engine_label = _MARKET_ID_TO_ENGINE_LABEL.get(mid)
            energy_share = float(input_data[f"{mid}_energy_share_last_historical_year"])
            rpk_share = float(input_data[f"{mid}_rpk_share_last_historical_year"])

            fleet_total_col = f"{m.name}: Aircraft In Fleet"
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
                # No fleet state available for an unmapped market: leave the
                # per-segment total at NaN over the full index.
                self.df.loc[full_years, fleet_total_col] = np.nan
            else:
                cfg = engine_inputs[engine_label]
                ask_proj = input_data[f"ask_{mid}"].reindex(ask_sample_years).to_numpy(dtype=float)
                # Append the horizon-year (end_year + 1) entry, held flat at end_year,
                # so the engine has modeled_periods + 1 finite traffic targets.
                ask_series = np.concatenate([ask_proj, ask_proj[-1:]])

                # The engine's production_profile is only used to size the year axis
                # (its last year). Growth is injected as ASK, so build the axis straight
                # from the calendar [first_projection_year .. horizon]; the rates are inert.
                market_data = cfg["market_data"].copy()
                market_data["production_profile"] = [
                    [self.last_historical_year + 1, horizon],
                    [0.0, 0.0],
                ]

                (
                    _years,
                    deliveries,
                    ask_volumes,
                    aircraft_seats_volumes,
                    energy_consumption,
                ) = market_process(
                    market_data,
                    cfg["distance_per_aircraft"],
                    cfg["fleet_market"],
                    cfg["old_ac_carac"],
                    cfg["in_prod_ac_carac"],
                    cfg["future_ac_carac"],
                    ask_series=ask_series,
                    last_historical_year=self.last_historical_year,
                )

                # Cache the raw (age-resolved) engine arrays for plot(). The flat
                # output columns below sum these over the age axis; the retirement /
                # retirement-age charts need the full 3D arrays.
                self._engine_results[mid] = {
                    "market_name": m.name,
                    "years": _years,
                    "deliveries": deliveries,
                    "ask_volumes": ask_volumes,
                    "aircraft_seats_volumes": aircraft_seats_volumes,
                    "energy_consumption": energy_consumption,
                    "ac_names": cfg["ac_names"],
                }

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

                # --- Fleet bridge (Phase 5): counts & deliveries -------------------
                # Per-type aircraft count at period t = seats per type / seats_array,
                # where seats per type = aircraft_seats_volumes[t].sum(axis=0). Counts
                # are aligned aircraft_seats_volumes[t] <-> year (last_historical_year + t)
                # (t = 0 is the pivot), so we write [last_historical_year .. end_year].
                # Deliveries[k] <-> year (first_projection_year + k); written over the
                # projection only. Pre-pivot history stays NaN (no engine fleet state).
                seats_array = cfg["seats_array"]
                ac_names = cfg["ac_names"]
                n_deliv = deliveries.shape[0]

                # Per-type counts: (periods, T) seats -> counts, then a per-year column.
                per_type_seats = aircraft_seats_volumes.sum(axis=1)  # (periods, T)
                with np.errstate(divide="ignore", invalid="ignore"):
                    per_type_counts = np.where(
                        seats_array[None, :] != 0,
                        per_type_seats / seats_array[None, :],
                        np.nan,
                    )

                count_years = np.arange(
                    self.last_historical_year,
                    self.last_historical_year + n_periods,
                )
                count_years = count_years[count_years <= self.end_year]
                deliv_years = np.arange(
                    self.prospection_start_year,
                    self.prospection_start_year + n_deliv,
                )
                deliv_years = deliv_years[deliv_years <= self.end_year]

                segment_total = np.zeros(len(count_years))
                for j, raw_name in enumerate(ac_names):
                    ac = _sanitize_type_name(raw_name)
                    counts_j = per_type_counts[: len(count_years), j]
                    self.df.loc[count_years, f"{mid}:{ac}:aircraft_in_fleet"] = counts_j
                    segment_total = segment_total + np.nan_to_num(counts_j)

                    deliv_col = f"{mid}:{ac}:aircraft_deliveries"
                    self.df.loc[deliv_years, deliv_col] = deliveries[: len(deliv_years), j]

                self.df.loc[count_years, fleet_total_col] = segment_total

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

            # Fleet bridge (Phase 5) outputs declared in custom_setup. The per-segment
            # total always exists; per-type columns only for mapped segments.
            output_data[fleet_total_col] = self.df[fleet_total_col]
            if engine_label is not None:
                for raw_name in engine_inputs[engine_label]["ac_names"]:
                    ac = _sanitize_type_name(raw_name)
                    fleet_col = f"{mid}:{ac}:aircraft_in_fleet"
                    deliv_col = f"{mid}:{ac}:aircraft_deliveries"
                    output_data[fleet_col] = self.df[fleet_col]
                    output_data[deliv_col] = self.df[deliv_col]

        self._store_outputs(output_data)
        return output_data

    def plot(self):
        """Render the push fleet model's per-segment diagnostic charts.

        Standalone matplotlib (outside the ``SingleScenarioPlot`` registry),
        mirroring :meth:`FleetModel.plot`: it reads the engine arrays cached by the
        last :meth:`compute` and draws, per mapped passenger segment, the fleet /
        ASK / deliveries / energy stacks, the retirement and retirement-age
        diagnostics (which need the engine's internal age-resolved arrays), and the
        energy-intensity curve.

        Must be called after the process has run (``compute`` populates the cache).
        """
        if not self._engine_results:
            raise RuntimeError(
                "No cached engine results to plot. Run the process (compute) before plot()."
            )

        for res in self._engine_results.values():
            market_name = res["market_name"]
            ac_names = res["ac_names"]
            ask_content = res["ask_volumes"]
            fleet_content = res["aircraft_seats_volumes"]
            energy_content = res["energy_consumption"]
            deliveries = res["deliveries"]
            years = res["years"]

            visu_fleet_array(ask_content[1:].sum(axis=1), ac_names, f"ASK ({market_name})")
            visu_fleet_array(
                fleet_content[1:].sum(axis=1), ac_names, f"Aircraft seats ({market_name})"
            )
            visu_fleet_array(deliveries, ac_names, f"# Aircraft produced ({market_name})")
            visu_retirements_array(fleet_content, ac_names)  # aircraft-seats outflow
            visu_retirements_array(ask_content, ac_names)  # ASK outflow
            visu_retirement_age(fleet_content, ac_names)
            visu_fleet_array(
                energy_content[1:].sum(axis=1), ac_names, f"energy consumption (MJ) ({market_name})"
            )
            visu_energy_intensity(energy_content, ask_content, years, market_name)
