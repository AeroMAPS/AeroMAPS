"""
test_fleet_custom_markets
=========================

Chantier 3.F acceptance-gate test.

Exercises the complete bottom-up fleet flow against a non-default 5-market
scenario so that any hardcoded reference to the default 3-market structure
would be caught at CI time.

The 5-market layout splits short-range into ``regional`` + ``mainline`` and
adds an ``ultra_long`` market on top of ``medium_range`` / ``long_range``:

    regional      — turboprop / regional jets
    mainline      — conventional narrow-body
    medium_range  — unchanged from default
    long_range    — unchanged from default
    ultra_long    — new ultra-long-range market

What is tested
--------------
1. ``FleetModel.compute()`` runs end-to-end for 5 markets — no
   ``KeyError``, ``AttributeError`` or market-name hard-coding.
2. Per-market columns exist for every (market, energy_type) pair after
   ``FleetModel.compute()``.
3. ``FleetEvolution.compute()`` (fleet_numeric.py) accepts market-driven
   ASK/RPK inputs and produces:
     * ``ask_aircraft_value_dict`` keyed by full aircraft name
     * ``"<market.name>: Aircraft Production"`` and
       ``"<market.name>: Aircraft Disposal"`` for every passenger market
4. Aircraft ASK / RPK values are finite and non-negative.
5. All five ``"<market.name>: Aircraft Production"`` / ``"Disposal"`` keys
   appear in the output dict.

YAML fixtures are written inline to ``tmp_path`` so no persistent files are
added.  The test is self-contained and does not require an
``AeroMAPSProcess`` or the full parameter set.
"""

from __future__ import annotations

import textwrap
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet.fleet_model import (
    Fleet,
    FleetModel,
)
from aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet.fleet_numeric import (
    FleetEvolution,
)
from aeromaps.models.air_transport.markets.market import Market
from aeromaps.models.air_transport.markets.market_manager import MarketManager
from aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet.fleet_performance import (
    ENERGY_TYPES,
)

# ── Inline YAML content ────────────────────────────────────────────────────────

_AIRCRAFT_INVENTORY_YAML = textwrap.dedent(
    """\
    reference_aircraft:
      - id: ref_old
        name: "Old reference"
        parameters:
          entry_into_service_year: 1970.0
          energy_per_ask: 1.2
          emission_index_nox: 0.015
          emission_index_soot: 0.00003
          doc_non_energy_base: 0.048
          cruise_altitude: 12000.0
          ask_year: 280000000.0
          rc_cost: 40000000.0
          nrc_cost: 10000000000.0
          oew: 37.0
      - id: ref_recent
        name: "Recent reference"
        parameters:
          entry_into_service_year: 2007.0
          energy_per_ask: 0.95
          emission_index_nox: 0.015
          emission_index_soot: 0.00003
          doc_non_energy_base: 0.048
          cruise_altitude: 12000.0
          ask_year: 280000000.0
          rc_cost: 40000000.0
          nrc_cost: 10000000000.0
          oew: 43.0

    aircraft:
      - id: ac_2035
        name: "AC_EIS2035"
        energy_type: DROP_IN_FUEL
        parameters:
          entry_into_service_year: 2035
          consumption_evolution: -20.0
          nox_evolution: -10.0
          soot_evolution: -5.0
          doc_non_energy_evolution: -5.0
          cruise_altitude: 12000.0
          hybridization_factor: 0.0
          ask_year: 280000000.0
          rc_cost: 80000000.0
          nrc_cost: 10000000000.0
          oew: 40.0
    """
)

# 5-market fleet: one universal subcategory per market (reuses the same
# aircraft inventory entries, but distinct subcategory ids keep column names
# distinct).
_FLEET_5_MARKETS_YAML = textwrap.dedent(
    """\
    subcategories:
      - id: regional_sub
        name: "Regional aircraft"
        share: 100.0
        reference_aircraft:
          old_ref: ref_old
          recent_ref: ref_recent
        aircraft:
          - ac_2035

      - id: mainline_sub
        name: "Mainline aircraft"
        share: 100.0
        reference_aircraft:
          old_ref: ref_old
          recent_ref: ref_recent
        aircraft:
          - ac_2035

      - id: mr_sub
        name: "MR aircraft"
        share: 100.0
        reference_aircraft:
          old_ref: ref_old
          recent_ref: ref_recent
        aircraft:
          - ac_2035

      - id: lr_sub
        name: "LR aircraft"
        share: 100.0
        reference_aircraft:
          old_ref: ref_old
          recent_ref: ref_recent
        aircraft:
          - ac_2035

      - id: ulr_sub
        name: "ULR aircraft"
        share: 100.0
        reference_aircraft:
          old_ref: ref_old
          recent_ref: ref_recent
        aircraft:
          - ac_2035

    market_served:
      - market: regional
        parameters:
          life: 25
          limit: 2
        calibration_subcategory: regional_sub
        subcategories:
          - regional_sub

      - market: mainline
        parameters:
          life: 25
          limit: 2
        calibration_subcategory: mainline_sub
        subcategories:
          - mainline_sub

      - market: medium_range
        parameters:
          life: 25
          limit: 2
        calibration_subcategory: mr_sub
        subcategories:
          - mr_sub

      - market: long_range
        parameters:
          life: 25
          limit: 2
        calibration_subcategory: lr_sub
        subcategories:
          - lr_sub

      - market: ultra_long
        parameters:
          life: 25
          limit: 2
        calibration_subcategory: ulr_sub
        subcategories:
          - ulr_sub
    """
)

# ── Five-market MarketManager ──────────────────────────────────────────────────

_FIVE_MARKETS = [
    Market(id="regional", name="Regional", traffic_type="passenger", traffic_unit="RPK", inputs={}),
    Market(id="mainline", name="Mainline", traffic_type="passenger", traffic_unit="RPK", inputs={}),
    Market(
        id="medium_range",
        name="Medium Range",
        traffic_type="passenger",
        traffic_unit="RPK",
        inputs={},
    ),
    Market(
        id="long_range",
        name="Long Range",
        traffic_type="passenger",
        traffic_unit="RPK",
        inputs={},
    ),
    Market(
        id="ultra_long",
        name="Ultra Long",
        traffic_type="passenger",
        traffic_unit="RPK",
        inputs={},
    ),
]


def _five_market_manager() -> MarketManager:
    return MarketManager(markets=list(_FIVE_MARKETS))


# ── Shared parameters ─────────────────────────────────────────────────────────

_PARAMS = SimpleNamespace(
    climate_historic_start_year=1940,
    historic_start_year=2000,
    prospection_start_year=2020,
    end_year=2060,
)

# ── Module-level fixtures ──────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def five_market_setup(tmp_path_factory):
    """Build a 5-market Fleet + FleetModel and return (fleet, fleet_model, mm)."""
    tmp = tmp_path_factory.mktemp("custom_markets_3f")
    inv_path = tmp / "aircraft_inventory.yaml"
    fleet_path = tmp / "fleet.yaml"
    inv_path.write_text(_AIRCRAFT_INVENTORY_YAML)
    fleet_path.write_text(_FLEET_5_MARKETS_YAML)

    mm = _five_market_manager()
    fleet = Fleet(
        markets=mm,
        aircraft_inventory_path=inv_path,
        fleet_config_path=fleet_path,
    )
    fleet_model = FleetModel(name="fleet_model_3f", fleet=fleet, parameters=_PARAMS)
    fleet_model.compute()
    return fleet, fleet_model, mm


@pytest.fixture(scope="module")
def fleet_evolution_output(five_market_setup):
    """Run FleetEvolution against the 5-market fleet and return the output dict."""
    fleet, fleet_model, mm = five_market_setup

    # Rebuild all_aircraft_elements (mirrors what AeroMAPSProcess does in _prepare_input_data).
    fleet.all_aircraft_elements = fleet.get_all_aircraft_elements()

    # Instantiate FleetEvolution and inject fleet_model.
    ev = FleetEvolution(name="fleet_numeric_3f", fleet_model=fleet_model)
    ev.parameters = _PARAMS
    ev._initialize_df()
    ev.custom_setup()

    # Build synthetic ASK / RPK series (uniform 1e11 for all years, all markets).
    # Include one pre-covid year (covid_start_year - 1 = 2019) in the index.
    # FleetEvolution reads covid_start_year - 1 and covid_end_year_passenger in the
    # index, so the series must span at least [covid_start_year-1 .. end_year].
    covid_start = 2020
    covid_end = 2021
    full_years = list(range(covid_start - 1, _PARAMS.end_year + 1))

    input_data: dict = {
        "covid_start_year": float(covid_start),
        "covid_end_year_passenger": float(covid_end),
        "dummy_fleet_model_output": np.array([1.0]),
    }
    for market in mm.get(traffic_type="passenger"):
        mid = market.id
        ask_series = pd.Series(1e11, index=full_years, dtype=float)
        rpk_series = pd.Series(8e10, index=full_years, dtype=float)
        input_data[f"ask_{mid}"] = ask_series
        input_data[f"rpk_{mid}"] = rpk_series

    output = ev.compute(input_data)
    return ev, output, mm


# ── Chantier 3.F targeted checks ──────────────────────────────────────────────


class TestFleetModelFiveMarkets:
    """Verify FleetModel.compute() works end-to-end for 5 custom markets."""

    def test_five_categories_built(self, five_market_setup):
        """Fleet must contain exactly 5 Category objects."""
        fleet, _, __ = five_market_setup
        assert len(fleet.categories) == 5, (
            f"Expected 5 categories, got {len(fleet.categories)}: "
            f"{list(fleet.categories.keys())}"
        )

    def test_market_id_set_on_all_categories(self, five_market_setup):
        """Every Category must have a non-None market_id."""
        fleet, _, __ = five_market_setup
        for cat_name, cat in fleet.categories.items():
            assert cat.market_id is not None, f"Category '{cat_name}' has market_id=None"

    def test_market_id_values_are_market_ids(self, five_market_setup):
        """Category.market_id must be a valid MarketManager id."""
        fleet, _, mm = five_market_setup
        valid_ids = {m.id for m in mm.get_all()}
        for cat in fleet.categories.values():
            assert (
                cat.market_id in valid_ids
            ), f"category.market_id='{cat.market_id}' not in {valid_ids}"

    def test_display_names_match_market_manager(self, five_market_setup):
        """Category.name must be the display name from MarketManager."""
        fleet, _, mm = five_market_setup
        market_names = {m.name for m in mm.get_all()}
        for cat in fleet.categories.values():
            assert (
                cat.name in market_names
            ), f"Category display name '{cat.name}' not in MarketManager names {market_names}"

    def test_share_energy_type_columns_exist(self, five_market_setup):
        """<display_name>:share:<energy_type> columns must exist for every market."""
        fleet, fleet_model, __ = five_market_setup
        missing = []
        for cat in fleet.categories.values():
            for energy_type in ENERGY_TYPES:
                col = f"{cat.name}:share:{energy_type}"
                if col not in fleet_model.df.columns:
                    missing.append(col)
        assert not missing, "Missing share columns:\n" + "\n".join(f"  {c}" for c in missing)

    def test_energy_consumption_columns_exist(self, five_market_setup):
        """<display_name>:energy_consumption must exist for every market."""
        fleet, fleet_model, __ = five_market_setup
        missing = [
            f"{cat.name}:energy_consumption"
            for cat in fleet.categories.values()
            if f"{cat.name}:energy_consumption" not in fleet_model.df.columns
        ]
        assert not missing, "Missing energy_consumption columns:\n" + "\n".join(
            f"  {c}" for c in missing
        )

    def test_aircraft_share_columns_sum_to_100(self, five_market_setup):
        """Within each category, all aircraft_share columns sum to ~100 at every year."""
        fleet, fleet_model, __ = five_market_setup
        df = fleet_model.df
        for cat in fleet.categories.values():
            share_cols = [
                c
                for c in df.columns
                if c.startswith(cat.name + ":") and c.endswith(":aircraft_share")
            ]
            assert share_cols, f"No aircraft_share columns for category '{cat.name}'"
            total = df[share_cols].sum(axis=1)
            max_err = (total - 100.0).abs().max()
            assert (
                max_err < 1e-6
            ), f"Category '{cat.name}': shares don't sum to 100 (max_err={max_err:.2e})"


class TestFleetEvolutionFiveMarkets:
    """Verify FleetEvolution.compute() works end-to-end for 5 custom markets."""

    def test_compute_returns_dict(self, fleet_evolution_output):
        """FleetEvolution.compute() must return a dict."""
        _, output, __ = fleet_evolution_output
        assert isinstance(output, dict), f"Expected dict, got {type(output)}"

    def test_ask_aircraft_value_dict_populated(self, fleet_evolution_output):
        """ask_aircraft_value_dict must have entries for every (market, aircraft)."""
        _, output, __ = fleet_evolution_output
        d = output["ask_aircraft_value_dict"]
        assert len(d) > 0, "ask_aircraft_value_dict is empty"

    def test_rpk_aircraft_value_dict_populated(self, fleet_evolution_output):
        """rpk_aircraft_value_dict must have entries for every (market, aircraft)."""
        _, output, __ = fleet_evolution_output
        d = output["rpk_aircraft_value_dict"]
        assert len(d) > 0, "rpk_aircraft_value_dict is empty"

    def test_aircraft_in_fleet_dict_populated(self, fleet_evolution_output):
        """aircraft_in_fleet_value_dict must have entries."""
        _, output, __ = fleet_evolution_output
        d = output["aircraft_in_fleet_value_dict"]
        assert len(d) > 0, "aircraft_in_fleet_value_dict is empty"

    def test_production_keys_present_for_all_five_markets(self, fleet_evolution_output):
        """'<display_name>: Aircraft Production' must exist for each of the 5 markets."""
        _, output, mm = fleet_evolution_output
        missing = []
        for market in mm.get(traffic_type="passenger"):
            key = f"{market.name}: Aircraft Production"
            if key not in output:
                missing.append(key)
        assert not missing, "Missing production keys:\n" + "\n".join(f"  {k}" for k in missing)

    def test_disposal_keys_present_for_all_five_markets(self, fleet_evolution_output):
        """'<display_name>: Aircraft Disposal' must exist for each of the 5 markets."""
        _, output, mm = fleet_evolution_output
        missing = []
        for market in mm.get(traffic_type="passenger"):
            key = f"{market.name}: Aircraft Disposal"
            if key not in output:
                missing.append(key)
        assert not missing, "Missing disposal keys:\n" + "\n".join(f"  {k}" for k in missing)

    def test_ask_values_finite_and_non_negative(self, fleet_evolution_output):
        """All ASK per-aircraft series must be finite and >= 0 within the prospection window.

        The series may have NaN at years before prospection_start_year (e.g. year
        2019 when covid_start_year=2020) because fleet_model.df only holds
        aircraft_share from prospection_start_year onward — that is expected and
        correct behaviour.  We only assert over the prospection window.
        """
        _, output, __ = fleet_evolution_output
        pstart = _PARAMS.prospection_start_year
        for name, series in output["ask_aircraft_value_dict"].items():
            window = series.loc[pstart:]
            vals = window.values
            assert np.all(
                np.isfinite(vals)
            ), f"{name}: ASK contains non-finite values in prospection window"
            assert np.all(vals >= -1e-6), f"{name}: ASK contains negative values"

    def test_rpk_values_finite_and_non_negative(self, fleet_evolution_output):
        """All RPK per-aircraft series must be finite and >= 0 within the prospection window.

        Same rationale as test_ask_values_finite_and_non_negative.
        """
        _, output, __ = fleet_evolution_output
        pstart = _PARAMS.prospection_start_year
        for name, series in output["rpk_aircraft_value_dict"].items():
            window = series.loc[pstart:]
            vals = window.values
            assert np.all(
                np.isfinite(vals)
            ), f"{name}: RPK contains non-finite values in prospection window"
            assert np.all(vals >= -1e-6), f"{name}: RPK contains negative values"

    def test_production_series_non_negative(self, fleet_evolution_output):
        """Aircraft Production series must be non-negative (sums of positive in-out)."""
        _, output, mm = fleet_evolution_output
        for market in mm.get(traffic_type="passenger"):
            key = f"{market.name}: Aircraft Production"
            if key in output:
                vals = output[key].values
                assert np.all(vals >= -1e-6), f"{key}: production contains negative values"

    def test_disposal_series_non_negative(self, fleet_evolution_output):
        """Aircraft Disposal series must be non-negative (abs of sum of negatives)."""
        _, output, mm = fleet_evolution_output
        for market in mm.get(traffic_type="passenger"):
            key = f"{market.name}: Aircraft Disposal"
            if key in output:
                vals = output[key].values
                assert np.all(vals >= -1e-6), f"{key}: disposal contains negative values"

    def test_all_five_markets_have_ask_entries(self, fleet_evolution_output):
        """ASK dict must contain entries for every (market, subcategory, aircraft) triple."""
        ev, output, mm = fleet_evolution_output
        fleet = ev.fleet_model.fleet
        d = output["ask_aircraft_value_dict"]
        missing = []
        for cat in fleet.categories.values():
            for sub in cat.subcategories.values():
                for ac in sub.aircraft.values():
                    key = f"{cat.name}:{sub.name}:{ac.name}"
                    if key not in d:
                        missing.append(key)
        assert not missing, "Missing ask_aircraft_value_dict entries:\n" + "\n".join(
            f"  {k}" for k in missing
        )
