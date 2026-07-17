"""
test_fleet_perf_mode_validation
===============================

Locks in the aircraft-inventory performance-mode validation: each of the four
performance metrics of a new aircraft card must be declared in exactly ONE of
its two modes —

    energy_per_ask      (absolute)  XOR  consumption_evolution    (relative)
    emission_index_nox  (absolute)  XOR  nox_evolution            (relative)
    emission_index_soot (absolute)  XOR  soot_evolution           (relative)
    doc_non_energy_base (absolute)  XOR  doc_non_energy_evolution (relative)

Declaring both (or neither) for the same metric must raise a ``ValueError`` at
YAML load time (``Fleet._load_aircraft_inventory`` -> ``_validate_perf_mode``),
with no silent precedence/bypass logic. Mixing modes across *different* metrics
on the same card is legitimate and must keep working (the SAE custom workflow
relies on it: absolute energy_per_ask + relative nox/soot/doc evolutions).

YAML fixtures are written inline to ``tmp_path``; no MarketManager is needed
because the validation fires while loading the inventory, before any market
wiring.
"""

from __future__ import annotations

import textwrap

import pytest

from aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet.fleet_model import (
    Fleet,
)

# ── Inline YAML fixtures ───────────────────────────────────────────────────────

_REFERENCE_BLOCK = textwrap.dedent(
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
    """
)

# Non-performance fields shared by every aircraft card below (indented to sit
# under ``parameters:``).
_COMMON_AIRCRAFT_FIELDS = """\
          entry_into_service_year: 2035
          cruise_altitude: 12000.0
          hybridization_factor: 0.0
          ask_year: 280000000.0
          rc_cost: 80000000.0
          nrc_cost: 10000000000.0
          oew: 40.0
"""

_FLEET_YAML = textwrap.dedent(
    """\
    subcategories:
      - id: main_sub
        name: "Main subcategory"
        share: 100.0
        reference_aircraft:
          old_ref: ref_old
          recent_ref: ref_recent
        aircraft:
          - ac_test

    categories:
      - market_served: medium_range
        parameters:
          life: 25
          limit: 2
        calibration_subcategory: main_sub
        subcategories:
          - main_sub
    """
)


def _build_fleet(tmp_path, perf_fields: str) -> Fleet:
    """Build a Fleet whose single new aircraft carries ``perf_fields``.

    ``perf_fields`` is the YAML fragment holding the performance-metric fields
    of the card (one ``key: value`` per line, unindented).
    """
    indented_perf = textwrap.indent(perf_fields, " " * 10)
    inventory = (
        _REFERENCE_BLOCK
        + textwrap.dedent(
            """\
            aircraft:
              - id: ac_test
                name: "Test aircraft"
                energy_type: DROP_IN_FUEL
                parameters:
            """
        )
        + _COMMON_AIRCRAFT_FIELDS
        + indented_perf
    )
    inv_path = tmp_path / "aircraft_inventory.yaml"
    fleet_path = tmp_path / "fleet.yaml"
    inv_path.write_text(inventory)
    fleet_path.write_text(_FLEET_YAML)
    return Fleet(aircraft_inventory_path=inv_path, fleet_config_path=fleet_path)


# ── Valid declarations ─────────────────────────────────────────────────────────


def test_relative_only_card_loads(tmp_path):
    """All four metrics in relative mode (the historical default) load fine."""
    fleet = _build_fleet(
        tmp_path,
        "consumption_evolution: -20.0\n"
        "nox_evolution: -10.0\n"
        "soot_evolution: -5.0\n"
        "doc_non_energy_evolution: -5.0\n",
    )
    (aircraft,) = fleet.categories["medium_range"].subcategories[0].aircraft.values()
    recent_ref = fleet.categories["medium_range"].subcategories[0].recent_reference_aircraft
    assert aircraft.resolved("energy_per_ask", recent_ref) == pytest.approx(0.95 * 0.8)


def test_mixed_modes_across_metrics_load(tmp_path):
    """Absolute energy + relative nox/soot/doc on one card is valid (SAE workflow)."""
    fleet = _build_fleet(
        tmp_path,
        "energy_per_ask: 0.7\n"
        "nox_evolution: 0.0\n"
        "soot_evolution: 0.0\n"
        "doc_non_energy_evolution: 0.0\n",
    )
    (aircraft,) = fleet.categories["medium_range"].subcategories[0].aircraft.values()
    recent_ref = fleet.categories["medium_range"].subcategories[0].recent_reference_aircraft
    # Absolute value returned as-is; relative metric resolved against the reference.
    assert aircraft.resolved("energy_per_ask", recent_ref) == pytest.approx(0.7)
    assert aircraft.resolved("emission_index_nox", recent_ref) == pytest.approx(0.015)


# ── Invalid declarations: both modes set for the same metric ──────────────────


@pytest.mark.parametrize(
    ("absolute_field", "relative_field"),
    [
        ("energy_per_ask: 0.7", "consumption_evolution: -20.0"),
        ("emission_index_nox: 0.01", "nox_evolution: -10.0"),
        ("emission_index_soot: 0.00002", "soot_evolution: -5.0"),
        ("doc_non_energy_base: 0.04", "doc_non_energy_evolution: -5.0"),
    ],
)
def test_both_absolute_and_relative_raises(tmp_path, absolute_field, relative_field):
    """Setting a metric in both modes must raise at load time, no bypass."""
    valid_others = {
        "energy_per_ask": "consumption_evolution: -20.0",
        "emission_index_nox": "nox_evolution: 0.0",
        "emission_index_soot": "soot_evolution: 0.0",
        "doc_non_energy_base": "doc_non_energy_evolution: 0.0",
    }
    metric = absolute_field.split(":")[0]
    lines = [f"{absolute_field}\n{relative_field}"]
    lines += [line for key, line in valid_others.items() if key != metric]
    with pytest.raises(ValueError, match=rf"ac_test.*both '{metric}'"):
        _build_fleet(tmp_path, "\n".join(lines) + "\n")


# ── Invalid declarations: neither mode set ─────────────────────────────────────


def test_neither_mode_raises(tmp_path):
    """Omitting a metric entirely must raise at load time."""
    with pytest.raises(ValueError, match=r"ac_test.*neither 'energy_per_ask'"):
        _build_fleet(
            tmp_path,
            "nox_evolution: 0.0\nsoot_evolution: 0.0\ndoc_non_energy_evolution: 0.0\n",
        )
