"""
test_fleet_model_regression
============================

Regression tests that pin the numerical output of ``FleetModel.compute()``
so that decomposing the module into separate files does not silently change
any result.

Planned decomposition
---------------------
``fleet_model.py`` will be split into:

* **fleet_assignment.py** — S-curve penetration → per-aircraft shares
  (``_compute_single_aircraft_share``, ``_compute_aircraft_share``)
* **fleet_performance.py** — shares → energy, DOC, NOx/soot per subcategory
  and category means
  (``_compute_energy_consumption_and_share_wrt_energy_type``,
  ``_compute_doc_non_energy``, ``_compute_non_co2_emission_index``,
  ``_compute_mean_*``)

Each test class targets the columns produced by one of these future modules,
so a regression failure immediately points to which module introduced it.

YAML fixtures (``tests/data/``)
--------------------------------
``aircraft_inventory.yaml``
    Two drop-in aircraft: *NB_EIS2035* (EIS 2035, −20 % energy, −10 % NOx,
    −5 % soot, −5 % DOC) and *NB_EIS2045* (EIS 2045, −35 % energy, −20 %
    NOx, −10 % soot, −10 % DOC), with old/recent SR reference aircraft.

``fleet_eis_order.yaml``
    Single SR subcategory, aircraft in correct EIS order.

All expected values were captured from the current implementation and must
remain bit-for-bit identical after the refactor.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet.fleet_model import (
    Fleet,
    FleetModel,
)

# ── paths ─────────────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent / "data"
INVENTORY = DATA_DIR / "aircraft_inventory.yaml"
FLEET_YAML = DATA_DIR / "fleet_eis_order.yaml"

# ── column name helpers ───────────────────────────────────────────────────────

# Tests construct Fleet without a MarketManager → display name falls back to market_id.
CAT = "short_range"
SUBCAT = "SR conventional narrow-body"
P = f"{CAT}:{SUBCAT}"  # subcategory prefix


# ── shared fixture ────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def fleet_df():
    """Run FleetModel once and return the resulting DataFrame.

    Module-scoped so the (slightly expensive) compute runs only once for all
    tests in this file.
    """
    fleet = Fleet(
        parameters=None,
        aircraft_inventory_path=INVENTORY,
        fleet_config_path=FLEET_YAML,
    )
    params = SimpleNamespace(
        climate_historic_start_year=1940,
        historic_start_year=2000,
        prospection_start_year=2020,
        end_year=2060,
    )
    model = FleetModel(name="fleet_model", fleet=fleet, parameters=params)
    model.compute()
    return model.df


# ── helpers ───────────────────────────────────────────────────────────────────


def approx(value, rel=1e-9):
    """Shorthand for pytest.approx with tight relative tolerance."""
    return pytest.approx(value, rel=rel)


# ── fleet_assignment.py regression ───────────────────────────────────────────


class TestFleetAssignment:
    """Columns produced by the future fleet_assignment module.

    Covers ``_compute_single_aircraft_share`` (cumulative S-curves) and
    ``_compute_aircraft_share`` (per-aircraft differential shares).
    """

    # ---- single (cumulative) aircraft share ----------------------------------

    def test_single_share_nb2035_zero_before_eis(self, fleet_df):
        """NB_EIS2035 single share is 0 before its EIS year (2035)."""
        assert fleet_df.loc[2030, f"{P}:NB_EIS2035:single_aircraft_share"] == 0.0

    def test_single_share_nb2045_zero_before_eis(self, fleet_df):
        """NB_EIS2045 single share is 0 before its EIS year (2045)."""
        assert fleet_df.loc[2040, f"{P}:NB_EIS2045:single_aircraft_share"] == 0.0

    def test_single_share_nb2035_at_2040(self, fleet_df):
        assert fleet_df.loc[2040, f"{P}:NB_EIS2035:single_aircraft_share"] == approx(
            8.825804290469849
        )

    def test_single_share_nb2035_at_2050(self, fleet_df):
        assert fleet_df.loc[2050, f"{P}:NB_EIS2035:single_aircraft_share"] == approx(
            68.53274242765801
        )

    def test_single_share_nb2045_at_2050(self, fleet_df):
        assert fleet_df.loc[2050, f"{P}:NB_EIS2045:single_aircraft_share"] == approx(
            8.825804290469849
        )

    def test_single_share_old_reference_always_100(self, fleet_df):
        """Old reference single share is always 100 (it anchors the baseline)."""
        col = f"{P}:old_reference:single_aircraft_share"
        assert (fleet_df[col] == 100.0).all()

    # ---- individual aircraft share ------------------------------------------

    def test_aircraft_share_nb2035_zero_before_eis(self, fleet_df):
        assert fleet_df.loc[2030, f"{P}:NB_EIS2035:aircraft_share"] == 0.0

    def test_aircraft_share_nb2045_zero_before_eis(self, fleet_df):
        assert fleet_df.loc[2040, f"{P}:NB_EIS2045:aircraft_share"] == 0.0

    def test_aircraft_share_nb2035_at_2040(self, fleet_df):
        # share = single(NB2035) − single(NB2045)  [NB2045 not yet active]
        assert fleet_df.loc[2040, f"{P}:NB_EIS2035:aircraft_share"] == approx(8.825804290469849)

    def test_aircraft_share_nb2045_at_2050(self, fleet_df):
        assert fleet_df.loc[2050, f"{P}:NB_EIS2045:aircraft_share"] == approx(8.825804290469849)

    def test_aircraft_share_nb2035_at_2050(self, fleet_df):
        # share = single(NB2035) − single(NB2045)
        assert fleet_df.loc[2050, f"{P}:NB_EIS2035:aircraft_share"] == approx(59.70693813718816)

    def test_aircraft_share_recent_reference_at_2040(self, fleet_df):
        assert fleet_df.loc[2040, f"{P}:recent_reference:aircraft_share"] == approx(
            91.00540646590409
        )

    def test_aircraft_share_old_reference_at_2040(self, fleet_df):
        assert fleet_df.loc[2040, f"{P}:old_reference:aircraft_share"] == approx(0.1687892436260654)

    def test_all_aircraft_shares_sum_to_100(self, fleet_df):
        """At every year, all aircraft shares (incl. references) sum to 100 %."""
        share_cols = [
            c for c in fleet_df.columns if c.startswith(P) and c.endswith(":aircraft_share")
        ]
        total = fleet_df[share_cols].sum(axis=1)
        assert (total - 100.0).abs().max() == approx(0.0, rel=1e-6)


# ── fleet_performance.py regression ──────────────────────────────────────────


class TestFleetPerformance:
    """Columns produced by the future fleet_performance module.

    Covers energy consumption, DOC, and NOx/soot emission indices at both the
    subcategory level (``_compute_energy_consumption_and_share_wrt_energy_type``,
    ``_compute_doc_non_energy``, ``_compute_non_co2_emission_index``) and the
    category-mean level (``_compute_mean_*``).
    """

    # ---- subcategory: energy consumption ------------------------------------

    def test_subcategory_energy_dropin_at_2030(self, fleet_df):
        """Before any new aircraft, energy equals the weighted reference baseline."""
        assert fleet_df.loc[
            2030, f"{P}:energy_consumption:weighted_contribution:dropin_fuel"
        ] == approx(0.9587979795318491)

    def test_subcategory_energy_dropin_at_2040(self, fleet_df):
        """NB_EIS2035 (−20 % consumption) has entered; fleet mean must fall."""
        assert fleet_df.loc[
            2040, f"{P}:energy_consumption:weighted_contribution:dropin_fuel"
        ] == approx(0.9315999067888316)

    def test_subcategory_energy_dropin_at_2050(self, fleet_df):
        """Both NB_EIS2035 and NB_EIS2045 contribute; fleet mean falls further."""
        assert fleet_df.loc[
            2050, f"{P}:energy_consumption:weighted_contribution:dropin_fuel"
        ] == approx(0.805385546184729)

    def test_subcategory_energy_alt_types_zero(self, fleet_df):
        """All aircraft are DROP_IN_FUEL; hydrogen/electric consumption is 0."""
        for energy_type in ("hydrogen", "electric", "hybrid_electric"):
            col = f"{P}:energy_consumption:weighted_contribution:{energy_type}"
            assert (fleet_df[col] == 0.0).all(), f"{col} should be all zeros"

    def test_subcategory_dropin_share_always_100(self, fleet_df):
        """Only drop-in aircraft in this fleet; share:dropin_fuel must be 100."""
        assert (fleet_df[f"{P}:share:dropin_fuel"] == 100.0).all()

    # ---- subcategory: DOC non-energy ----------------------------------------

    def test_subcategory_doc_at_2030(self, fleet_df):
        """Before new aircraft, DOC equals weighted reference baseline."""
        assert fleet_df.loc[
            2030, f"{P}:doc_non_energy:weighted_contribution:dropin_fuel"
        ] == approx(0.048375)

    def test_subcategory_doc_at_2040(self, fleet_df):
        """NB_EIS2035 (−5 % DOC) reduces fleet-mean DOC."""
        assert fleet_df.loc[
            2040, f"{P}:doc_non_energy:weighted_contribution:dropin_fuel"
        ] == approx(0.048161525858724255)

    def test_subcategory_doc_at_2050(self, fleet_df):
        assert fleet_df.loc[
            2050, f"{P}:doc_non_energy:weighted_contribution:dropin_fuel"
        ] == approx(0.04650389015125528)

    # ---- subcategory: NOx emission index ------------------------------------

    def test_subcategory_nox_at_2030(self, fleet_df):
        assert fleet_df.loc[
            2030, f"{P}:emission_index_nox:weighted_contribution:dropin_fuel"
        ] == approx(0.01514)

    def test_subcategory_nox_at_2040(self, fleet_df):
        """NB_EIS2035 (−10 % NOx) reduces fleet-mean NOx index."""
        assert fleet_df.loc[
            2040, f"{P}:emission_index_nox:weighted_contribution:dropin_fuel"
        ] == approx(0.015006377323042287)

    def test_subcategory_nox_at_2050(self, fleet_df):
        assert fleet_df.loc[
            2050, f"{P}:emission_index_nox:weighted_contribution:dropin_fuel"
        ] == approx(0.013968791602687545)

    # ---- subcategory: soot emission index -----------------------------------

    def test_subcategory_soot_at_2040(self, fleet_df):
        """NB_EIS2035 (−5 % soot) reduces fleet-mean soot index."""
        assert fleet_df.loc[
            2040, f"{P}:emission_index_soot:weighted_contribution:dropin_fuel"
        ] == approx(2.986761293564295e-05)

    def test_subcategory_soot_at_2050(self, fleet_df):
        assert fleet_df.loc[
            2050, f"{P}:emission_index_soot:weighted_contribution:dropin_fuel"
        ] == approx(2.883962179922808e-05)

    # ---- category means (aggregated by _compute_mean_* methods) -------------

    def test_category_energy_equals_subcategory_single_subcat(self, fleet_df):
        """With one subcategory, category mean energy equals subcategory energy."""
        diff = (
            fleet_df[f"{CAT}:energy_consumption"]
            - fleet_df[f"{P}:energy_consumption:weighted_contribution:dropin_fuel"]
        ).abs()
        assert diff.max() == approx(0.0, rel=1e-9)

    def test_category_energy_at_2040(self, fleet_df):
        assert fleet_df.loc[2040, f"{CAT}:energy_consumption"] == approx(0.9315999067888316)

    def test_category_energy_at_2050(self, fleet_df):
        assert fleet_df.loc[2050, f"{CAT}:energy_consumption"] == approx(0.805385546184729)

    def test_category_doc_at_2050(self, fleet_df):
        assert fleet_df.loc[2050, f"{CAT}:doc_non_energy"] == approx(0.04650389015125528)

    def test_category_nox_at_2050(self, fleet_df):
        assert fleet_df.loc[2050, f"{CAT}:emission_index_nox"] == approx(0.013968791602687545)

    def test_category_soot_at_2050(self, fleet_df):
        assert fleet_df.loc[2050, f"{CAT}:emission_index_soot"] == approx(2.883962179922808e-05)

    def test_category_alt_energy_types_zero(self, fleet_df):
        """Category-level hydrogen/electric/hybrid-electric columns are all zero."""
        for energy_type in ("hydrogen", "electric", "hybrid_electric"):
            for metric in ("energy_consumption", "doc_non_energy"):
                col = f"{CAT}:{metric}:{energy_type}"
                if col in fleet_df.columns:
                    assert (fleet_df[col] == 0.0).all(), f"{col} should be all zeros"

    # ---- monotonicity sanity checks -----------------------------------------

    def test_energy_decreases_as_fleet_renews(self, fleet_df):
        """Energy per ASK must fall monotonically from 2035 onward as new aircraft enter."""
        prospective = fleet_df.loc[2035:, f"{CAT}:energy_consumption"]
        diffs = prospective.diff().dropna()
        assert (diffs <= 1e-12).all(), "Energy per ASK increased during fleet renewal"

    def test_nox_decreases_as_fleet_renews(self, fleet_df):
        """NOx index must fall monotonically from 2035 onward."""
        prospective = fleet_df.loc[2035:, f"{CAT}:emission_index_nox"]
        diffs = prospective.diff().dropna()
        assert (diffs <= 1e-15).all(), "NOx index increased during fleet renewal"
