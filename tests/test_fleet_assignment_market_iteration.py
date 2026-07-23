"""
test_fleet_assignment_market_iteration
=======================================

Chantier 3.D acceptance-gate test.

Verifies that :class:`~aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet.fleet_assignment.FleetAssignmentMixin`
correctly iterates over all (market, subcategory, aircraft) tuples when the
fleet is built from the new ``market_served:`` YAML schema (post-3.A) with a
:class:`~aeromaps.models.air_transport.markets.market_manager.MarketManager`
attached.

Checks
------
1. ``Category.market_id`` is set (not ``None``) for every category produced by
   the new schema.
2. ``_compute_single_aircraft_share`` produces
   ``<display_name>:<sub>:<aircraft>:single_aircraft_share`` columns for every
   (market, subcategory, aircraft) triple in the default fleet.
3. ``_compute_aircraft_share`` produces the corresponding
   ``<display_name>:<sub>:<aircraft>:aircraft_share`` columns.
4. No ``KeyError`` is raised during either computation.
5. At each year the aircraft-share columns within a category (including
   references) sum to ~100 %.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet.fleet_model import (
    Fleet,
    FleetModel,
)
from aeromaps.models.air_transport.markets.market import Market
from aeromaps.models.air_transport.markets.market_manager import MarketManager

# ── build a MarketManager that mirrors the three passenger markets in the
#    default fleet.yaml / markets.yaml ─────────────────────────────────────


def _default_market_manager() -> MarketManager:
    """Return a MarketManager with the three default passenger markets."""
    mm = MarketManager(
        markets=[
            Market(
                id="short_range",
                name="Short Range",
                traffic_type="passenger",
                traffic_unit="RPK",
                inputs={},
            ),
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
        ]
    )
    return mm


# ── shared fixture ─────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def fleet_df_with_markets():
    """Run FleetModel with the default market_served fleet and return (fleet, df)."""
    mm = _default_market_manager()
    fleet = Fleet(markets=mm)  # uses DEFAULT_FLEET_CONFIG_FILE (market_served schema)

    params = SimpleNamespace(
        climate_historic_start_year=1940,
        historic_start_year=2000,
        prospection_start_year=2020,
        end_year=2060,
    )
    model = FleetModel(name="fleet_model", fleet=fleet, parameters=params)
    model.compute()
    return fleet, model.df


# ── Chantier 3.D targeted checks ───────────────────────────────────────────


class TestAssignmentMarketIteration:
    """Verify FleetAssignmentMixin iterates all markets/subcategories correctly."""

    # ---- 1. market_id plumbing -----------------------------------------------

    def test_market_id_set_on_all_categories(self, fleet_df_with_markets):
        """Every Category built from market_served: must have market_id != None."""
        fleet, df = fleet_df_with_markets
        for cat_name, cat in fleet.categories.items():
            assert cat.market_id is not None, (
                f"Category '{cat_name}' has market_id=None — "
                "market_id was not plumbed during _build_fleet_from_yaml"
            )

    def test_market_id_matches_market_name(self, fleet_df_with_markets):
        """category.market_id should match the MarketManager id, not the display name."""
        fleet, df = fleet_df_with_markets
        mm = fleet.markets
        market_ids = {m.id for m in mm.get_all()}
        for cat in fleet.categories.values():
            assert cat.market_id in market_ids, (
                f"category.market_id='{cat.market_id}' is not a known market id "
                f"(known: {market_ids})"
            )

    # ---- 2. single_aircraft_share columns exist for all tuples ---------------

    def test_single_share_columns_exist(self, fleet_df_with_markets):
        """single_aircraft_share column present for every (category, sub, aircraft)."""
        fleet, df = fleet_df_with_markets
        for cat in fleet.categories.values():
            for sub in cat.subcategories.values():
                for ac in sub.aircraft.values():
                    col = f"{cat.name}:{sub.name}:{ac.name}:single_aircraft_share"
                    assert col in df.columns, f"Missing column: {col}"

    def test_single_share_reference_columns_exist(self, fleet_df_with_markets):
        """recent_reference / old_reference single_aircraft_share columns present."""
        fleet, df = fleet_df_with_markets
        for cat in fleet.categories.values():
            first_sub = cat.subcategories[0]
            for ref_type in ("recent_reference", "old_reference"):
                col = f"{cat.name}:{first_sub.name}:{ref_type}:single_aircraft_share"
                assert col in df.columns, f"Missing column: {col}"

    # ---- 3. aircraft_share columns exist for all tuples ----------------------

    def test_aircraft_share_columns_exist(self, fleet_df_with_markets):
        """aircraft_share column present for every (category, sub, aircraft)."""
        fleet, df = fleet_df_with_markets
        for cat in fleet.categories.values():
            for sub in cat.subcategories.values():
                for ac in sub.aircraft.values():
                    col = f"{cat.name}:{sub.name}:{ac.name}:aircraft_share"
                    assert col in df.columns, f"Missing column: {col}"

    def test_aircraft_share_reference_columns_exist(self, fleet_df_with_markets):
        """recent_reference / old_reference aircraft_share columns present."""
        fleet, df = fleet_df_with_markets
        for cat in fleet.categories.values():
            first_sub = cat.subcategories[0]
            for ref_type in ("recent_reference", "old_reference"):
                col = f"{cat.name}:{first_sub.name}:{ref_type}:aircraft_share"
                assert col in df.columns, f"Missing column: {col}"

    # ---- 4. shares sum to ~100% per category ---------------------------------

    def test_shares_sum_to_100_per_category(self, fleet_df_with_markets):
        """Within every category, all aircraft_share columns sum to ~100 at every year."""
        fleet, df = fleet_df_with_markets
        for cat in fleet.categories.values():
            share_cols = [
                c
                for c in df.columns
                if c.startswith(cat.name + ":") and c.endswith(":aircraft_share")
            ]
            assert share_cols, f"No aircraft_share columns found for category '{cat.name}'"
            total = df[share_cols].sum(axis=1)
            max_err = (total - 100.0).abs().max()
            assert max_err < 1e-6, (
                f"Category '{cat.name}': aircraft shares do not sum to 100 "
                f"(max deviation {max_err:.2e})"
            )

    # ---- 5. three passenger markets produced columns -------------------------

    def test_all_three_markets_have_columns(self, fleet_df_with_markets):
        """Short Range, Medium Range and Long Range must each produce share columns."""
        fleet, df = fleet_df_with_markets
        expected_display_names = {"Short Range", "Medium Range", "Long Range"}
        for display_name in expected_display_names:
            matching = [c for c in df.columns if c.startswith(display_name + ":")]
            assert matching, f"No columns produced for market '{display_name}'"
