"""
test_fleet_performance_market_iteration
========================================

Chantier 3.E acceptance-gate test.

Verifies that :class:`~aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet.fleet_performance.FleetPerformanceMixin`
correctly iterates over an arbitrary number of markets when the fleet is
built with more than the default 3-market structure.

The 5-market scenario is built inline using ``tmp_path``-based YAML files so
that no persistent fixture assets are created (those belong to Chantier 3.F).

The 5-market layout splits the default short-range market into two:
  - ``regional``      — turboprop/regional jets (new market id)
  - ``mainline``      — conventional narrow-body  (new market id)
  - ``medium_range``  — unchanged
  - ``long_range``    — unchanged
  - ``ultra_long``    — new ultra-long-range market (simple fixture)

Checks
------
1. Every passenger market produces ``<display_name>:share:<energy_type>``
   columns in ``FleetModel.df`` after ``compute()``.
2. The shares of all energy types for a given market are non-negative and
   finite at every year.
3. No ``KeyError`` or ``AttributeError`` is raised during ``compute()``.
"""

from __future__ import annotations

import textwrap
from types import SimpleNamespace

import pytest

from aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet.fleet_model import (
    Fleet,
    FleetModel,
)
from aeromaps.models.air_transport.markets.market import Market
from aeromaps.models.air_transport.markets.market_manager import MarketManager
from aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet.fleet_performance import (
    ENERGY_TYPES,
)

# ── Inline YAML content (written to tmp_path by the fixture) ──────────────────

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

# 5-market fleet: one universal subcategory definition reused across all markets.
# Each market gets its own subcategory id / display name to keep columns distinct.
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

    categories:
      - market_served: regional
        parameters:
          life: 25
          limit: 2
        calibration_subcategory: regional_sub
        subcategories:
          - regional_sub

      - market_served: mainline
        parameters:
          life: 25
          limit: 2
        calibration_subcategory: mainline_sub
        subcategories:
          - mainline_sub

      - market_served: medium_range
        parameters:
          life: 25
          limit: 2
        calibration_subcategory: mr_sub
        subcategories:
          - mr_sub

      - market_served: long_range
        parameters:
          life: 25
          limit: 2
        calibration_subcategory: lr_sub
        subcategories:
          - lr_sub

      - market_served: ultra_long
        parameters:
          life: 25
          limit: 2
        calibration_subcategory: ulr_sub
        subcategories:
          - ulr_sub
    """
)

# ── Matching 5-market MarketManager ───────────────────────────────────────────

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
        id="long_range", name="Long Range", traffic_type="passenger", traffic_unit="RPK", inputs={}
    ),
    Market(
        id="ultra_long", name="Ultra Long", traffic_type="passenger", traffic_unit="RPK", inputs={}
    ),
]


def _five_market_manager() -> MarketManager:
    return MarketManager(markets=list(_FIVE_MARKETS))


# ── Pytest fixture ────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def five_market_fleet_df(tmp_path_factory):
    """Build a 5-market FleetModel using tmp_path YAML files and return (fleet, df)."""
    tmp = tmp_path_factory.mktemp("five_market")
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
    params = SimpleNamespace(
        climate_historic_start_year=1940,
        historic_start_year=2000,
        prospection_start_year=2020,
        end_year=2060,
    )
    model = FleetModel(name="fleet_model_5m", fleet=fleet, parameters=params)
    model.compute()
    return fleet, model.df


# ── Chantier 3.E targeted checks ─────────────────────────────────────────────


class TestFleetPerformanceFiveMarkets:
    """Verify FleetPerformanceMixin iterates all 5 markets without hardcoded breakage."""

    # ---- 1. Five categories are produced ----------------------------------------

    def test_five_categories_present(self, five_market_fleet_df):
        """Fleet must contain exactly 5 categories."""
        fleet, df = five_market_fleet_df
        assert (
            len(fleet.categories) == 5
        ), f"Expected 5 categories, got {len(fleet.categories)}: {list(fleet.categories.keys())}"

    # ---- 2. market_id plumbed on every category ---------------------------------

    def test_market_id_set_on_all_five_categories(self, five_market_fleet_df):
        """Every Category must have market_id != None."""
        fleet, df = five_market_fleet_df
        for cat_name, cat in fleet.categories.items():
            assert cat.market_id is not None, f"Category '{cat_name}' has market_id=None"

    # ---- 3. share:<energy_type> columns exist for every market ------------------

    def test_share_energy_type_columns_exist_for_all_markets(self, five_market_fleet_df):
        """<display_name>:share:<energy_type> must exist for every (market, energy_type)."""
        fleet, df = five_market_fleet_df
        missing = []
        for cat in fleet.categories.values():
            for energy_type in ENERGY_TYPES:
                col = f"{cat.name}:share:{energy_type}"
                if col not in df.columns:
                    missing.append(col)
        assert not missing, "Missing share columns:\n" + "\n".join(f"  {c}" for c in missing)

    # ---- 4. share values are finite and non-negative ----------------------------

    def test_share_columns_finite_and_non_negative(self, five_market_fleet_df):
        """All share:<energy_type> values must be finite and >= 0."""
        import numpy as np

        fleet, df = five_market_fleet_df
        for cat in fleet.categories.values():
            for energy_type in ENERGY_TYPES:
                col = f"{cat.name}:share:{energy_type}"
                if col in df.columns:
                    vals = df[col].values
                    assert np.all(np.isfinite(vals)), f"{col} contains non-finite values"
                    assert np.all(vals >= -1e-9), f"{col} contains negative values"

    # ---- 5. energy_consumption columns exist for every market -------------------

    def test_energy_consumption_columns_exist_for_all_markets(self, five_market_fleet_df):
        """<display_name>:energy_consumption must exist for every market after compute()."""
        fleet, df = five_market_fleet_df
        missing = []
        for cat in fleet.categories.values():
            col = f"{cat.name}:energy_consumption"
            if col not in df.columns:
                missing.append(col)
        assert not missing, "Missing energy_consumption columns:\n" + "\n".join(
            f"  {c}" for c in missing
        )

    # ---- 6. dropin_fuel share sums to 100 for all-dropin fleet ------------------

    def test_dropin_share_100_for_all_dropin_fleet(self, five_market_fleet_df):
        """All aircraft are DROP_IN_FUEL; dropin_fuel share must be 100 for every market."""
        fleet, df = five_market_fleet_df
        for cat in fleet.categories.values():
            col = f"{cat.name}:share:dropin_fuel"
            assert col in df.columns, f"Missing column: {col}"
            assert (df[col] == 100.0).all(), (
                f"Market '{cat.name}': dropin_fuel share is not 100 "
                f"(min={df[col].min()}, max={df[col].max()})"
            )

    # ---- 7. display names match MarketManager -----------------------------------

    def test_display_names_match_market_manager(self, five_market_fleet_df):
        """Category display names must match the MarketManager's market names."""
        fleet, df = five_market_fleet_df
        mm = fleet.markets
        market_names = {m.name for m in mm.get_all()}
        for cat in fleet.categories.values():
            assert cat.name in market_names, (
                f"Category display name '{cat.name}' not found in MarketManager "
                f"(known names: {market_names})"
            )
