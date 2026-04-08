"""
test_fleet_aircraft_ordering
============================

Verify that FleetModel share computations are independent of the order in
which aircraft appear inside a SubCategory YAML configuration.

Background
----------
Each aircraft's individual share is derived by differencing consecutive
cumulative S-curves (``single_aircraft_share``).  The difference is
physically meaningful only when aircraft are ordered oldest-EIS → newest-EIS.
Before the fix, iteration followed YAML/insertion order, so listing aircraft
out of EIS order produced wrong (sometimes negative) individual share curves.

The fix adds ``FleetModel._sorted_aircraft``, which sorts by
``entry_into_service_year`` before every iteration that drives share
derivation.  These tests verify the fix and document the magnitude of the
old bug.

YAML fixtures (``tests/data/``)
--------------------------------
``aircraft_inventory.yaml``
    Minimal inventory: one old/recent reference pair + two drop-in aircraft
    *NB_EIS2035* (EIS 2035, −20 % consumption) and *NB_EIS2045* (EIS 2045,
    −35 % consumption).

``fleet_eis_order.yaml``
    Single SR subcategory.  Aircraft listed in correct EIS order:
    ``sr_nb_2035`` → ``sr_nb_2045``.

``fleet_reversed_order.yaml``
    Identical structure but aircraft listed in *reversed* EIS order:
    ``sr_nb_2045`` → ``sr_nb_2035``.  This is the mis-configured YAML that
    exposed the ordering bug.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet.fleet_model import (
    Fleet,
    FleetModel,
)

DATA_DIR = Path(__file__).parent / "data"
INVENTORY = DATA_DIR / "aircraft_inventory.yaml"
FLEET_EIS_ORDER = DATA_DIR / "fleet_eis_order.yaml"
FLEET_REVERSED_ORDER = DATA_DIR / "fleet_reversed_order.yaml"

# Column shortcuts
CAT = "Short Range"
SUBCAT = "SR conventional narrow-body"
PREFIX = f"{CAT}:{SUBCAT}"
COL_A = f"{PREFIX}:NB_EIS2035:aircraft_share"
COL_B = f"{PREFIX}:NB_EIS2045:aircraft_share"


def _make_params() -> SimpleNamespace:
    """Minimal year parameters for AeroMAPSModel initialisation."""
    return SimpleNamespace(
        climate_historic_start_year=1940,
        historic_start_year=2000,
        prospection_start_year=2020,
        end_year=2060,
    )


def _run(fleet_yaml: Path) -> pd.DataFrame:
    """Load a fleet from YAML and run FleetModel with the fixed EIS-sorted behaviour."""
    fleet = Fleet(
        parameters=None,  # skip calibration — reference EIS years taken from YAML
        aircraft_inventory_path=INVENTORY,
        fleet_config_path=fleet_yaml,
    )
    model = FleetModel(name="fleet_model", fleet=fleet, parameters=_make_params())
    model.compute()
    return model.df.copy()


def _run_without_sort(fleet_yaml: Path) -> pd.DataFrame:
    """Load a fleet from YAML and run FleetModel with the *old* insertion-order behaviour.

    Simulates the pre-fix behaviour by replacing ``_sorted_aircraft`` on the
    model instance with an identity function that preserves YAML listing order.
    """
    fleet = Fleet(
        parameters=None,
        aircraft_inventory_path=INVENTORY,
        fleet_config_path=fleet_yaml,
    )
    model = FleetModel(name="fleet_model", fleet=fleet, parameters=_make_params())
    # Bypass EIS sort → revert to YAML insertion order
    model._sorted_aircraft = lambda subcat: list(subcat.aircraft.values())
    model.compute()
    return model.df.copy()


class TestFleetAircraftOrdering:
    """Fleet model share results must be invariant to aircraft listing order in YAML."""


    def test_aircraft_shares_invariant_to_listing_order(self):
        """``aircraft_share`` columns are identical for both YAML orderings."""
        df_ordered = _run(FLEET_EIS_ORDER)
        df_reversed = _run(FLEET_REVERSED_ORDER)

        share_cols = [c for c in df_ordered.columns if c.endswith(":aircraft_share")]
        assert share_cols, "No aircraft_share columns found — check YAML fleet setup."

        diff = (df_ordered[share_cols] - df_reversed[share_cols]).abs()
        max_diff = diff.max().max()

        _print_diff_table(diff, label="aircraft_share [pp]")

        assert max_diff < 1e-10, (
            f"Aircraft shares differ by up to {max_diff:.4f} pp between "
            f"{FLEET_EIS_ORDER.name} and {FLEET_REVERSED_ORDER.name} — "
            "_sorted_aircraft is not applied correctly.\n"
            f"Per-column max diff:\n{diff.max().to_string()}"
        )


    def test_single_aircraft_shares_invariant_to_listing_order(self):
        """``single_aircraft_share`` cumulative curves are identical for both orderings."""
        df_ordered = _run(FLEET_EIS_ORDER)
        df_reversed = _run(FLEET_REVERSED_ORDER)

        single_cols = [c for c in df_ordered.columns if c.endswith(":single_aircraft_share")]
        assert single_cols

        diff = (df_ordered[single_cols] - df_reversed[single_cols]).abs()
        max_diff = diff.max().max()

        assert max_diff < 1e-10, (
            f"Single aircraft shares differ by up to {max_diff:.4f} pp between orderings."
        )

    # ------------------------------------------------------------------
    # 3. Energy consumption columns
    # ------------------------------------------------------------------

    def test_energy_consumption_invariant_to_listing_order(self):
        """Energy consumption columns are identical for both YAML orderings."""
        df_ordered = _run(FLEET_EIS_ORDER)
        df_reversed = _run(FLEET_REVERSED_ORDER)

        energy_cols = [c for c in df_ordered.columns if "energy_consumption" in c]
        assert energy_cols

        diff = (df_ordered[energy_cols] - df_reversed[energy_cols]).abs()
        max_diff = diff.max().max()

        assert max_diff < 1e-12, (
            f"Energy consumption differs by up to {max_diff:.2e} MJ/ASK between orderings."
        )


    def test_ordering_bug_magnitude(self):
        """Document and bound the error that existed before the EIS-sort fix.

        With the old behaviour (YAML insertion order, no EIS sort), loading
        ``fleet_reversed_order.yaml`` caused NB_EIS2035 to receive its full
        S-curve as if it were the *newest* aircraft, while NB_EIS2045 was
        differenced in the wrong direction (negative shares in early years).

        This test runs the old behaviour explicitly via ``_run_without_sort``,
        compares it to the corrected output, and prints the per-year diff table.
        Two assertions confirm:

        1. The bug produced a meaningful error (> 1 pp) in NB_EIS2035's share.
        2. The old NB_EIS2045 share went negative (displacement computed in the
           wrong direction).
        """
        df_correct = _run(FLEET_EIS_ORDER)                         # fixed, EIS order
        df_old_bug = _run_without_sort(FLEET_REVERSED_ORDER)       # old, wrong order

        diff_a = df_correct[COL_A] - df_old_bug[COL_A]
        diff_b = df_correct[COL_B] - df_old_bug[COL_B]

        comparison = pd.DataFrame(
            {
                "NB2035_correct  [pp]": df_correct[COL_A].round(4),
                "NB2035_old_bug  [pp]": df_old_bug[COL_A].round(4),
                "Δ_NB2035        [pp]": diff_a.round(4),
                "NB2045_correct  [pp]": df_correct[COL_B].round(4),
                "NB2045_old_bug  [pp]": df_old_bug[COL_B].round(4),
                "Δ_NB2045        [pp]": diff_b.round(4),
            }
        )
        # Only show rows where the values changed (prospection period)
        changed = comparison[comparison["Δ_NB2035        [pp]"].abs() > 0.0001]

        print("\n=== Old ordering bug: share difference (correct − old-bug) [pp] ===")
        print(changed.to_string())
        print(
            f"\nMax |Δ NB_EIS2035| = {diff_a.abs().max():.4f} pp   "
            f"Max |Δ NB_EIS2045| = {diff_b.abs().max():.4f} pp"
        )

        # 1. The old bug must have produced a meaningful error (> 1 pp).
        assert diff_a.abs().max() > 1.0, (
            "Expected the old insertion-order bug to produce >1 pp error in "
            f"NB_EIS2035 share, but max difference was {diff_a.abs().max():.4f} pp."
        )

        # 2. The old NB_EIS2045 share must have gone negative.
        old_b_min = df_old_bug[COL_B].min()
        assert old_b_min < 0, (
            "Expected old-bug NB_EIS2045 share to go negative (displacement computed "
            f"in wrong direction), but min was {old_b_min:.4f} pp."
        )


def _print_diff_table(diff: pd.DataFrame, label: str) -> None:
    max_per_col = diff.max()
    print(f"\n=== {label} — max |EIS-ordered − reversed| per column ===")
    for col, val in max_per_col.items():
        short = ":".join(str(col).split(":")[-2:])
        print(f"  {short:<45s}  {val:.2e}")
