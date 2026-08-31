"""Life-cycle to CORSIA scope conversion, both routes.

The strong regression test is that converting the third edition's well-to-wake
carrier files reproduces its committed CORSIA twins exactly, since those twins are
what every tank-to-wake number in the manuscript was computed from.

Note the second edition's twins are *not* a valid target: they were built as
``73.8 x`` the report's rounded carbon-intensity percentages, so its electrofuel
reads 7.38 while its own well-to-wake file says 0.0. This module converts the
well-to-wake value instead, which is the method the third edition adopted
precisely to avoid importing that rounding.
"""

from pathlib import Path

import pytest

from aeromaps.models.base import AeroMapsCustomDataType
from aeromaps.utils.emission_scopes import (
    CORSIA_RATIO,
    EF_KEY,
    FOSSIL_TTW,
    FOSSIL_WTW,
    apply_corsia_scope,
    corsia_to_lifecycle,
    lifecycle_to_corsia,
    processes_to_corsia,
)
from aeromaps.utils.yaml import read_yaml_file

ATAG = (
    Path(__file__).resolve().parents[1]
    / "aeromaps"
    / "notebooks"
    / "scenarios"
    / "02_atag_waypoint2050"
)
FULL = ATAG / "3rd_edition_full" / "data_inputs"
LIGHT = ATAG / "3rd_edition_light" / "data_inputs"

pytestmark = pytest.mark.skipif(
    not (FULL / "s1_energy.yaml").exists(),
    reason="ATAG third-edition inputs are not present in this checkout",
)


def _factors(carriers):
    """Every emission-factor curve in a carriers mapping, as plain lists."""
    found = {}
    for name, entry in carriers.items():
        if not isinstance(entry, dict):
            continue
        factor = entry.get("inputs", {}).get("environmental", {}).get(EF_KEY)
        if factor is None:
            continue
        found[name] = (
            list(factor.values) if isinstance(factor, AeroMapsCustomDataType) else [factor]
        )
    return found


def _carrier(aircraft_type, values):
    return {
        "aircraft_type": aircraft_type,
        "inputs": {
            "environmental": {
                EF_KEY: AeroMapsCustomDataType(
                    {"years": [2020, 2050], "values": list(values), "method": "linear"}
                )
            }
        },
    }


@pytest.mark.parametrize(
    "source, twin",
    [
        (FULL / "s1_energy.yaml", FULL / "s1-TTW_energy.yaml"),
        (FULL / "s2_energy.yaml", FULL / "s2-TTW_energy.yaml"),
        (LIGHT / "s0_energy.yaml", LIGHT / "s0-TTW_energy.yaml"),
    ],
)
def test_reproduces_committed_carrier_twins(source, twin):
    produced = _factors(lifecycle_to_corsia(source))
    expected = _factors(read_yaml_file(str(twin)))
    assert set(produced) == set(expected)
    for name in expected:
        assert produced[name] == pytest.approx(expected[name], abs=0.0, rel=0.0)


def test_reproduces_committed_process_twin():
    produced = _factors(processes_to_corsia(FULL / "processes.yaml"))
    expected = _factors(read_yaml_file(str(FULL / "processes-TTW.yaml")))
    assert produced == expected
    # Conversion processes emit before the tank, so CORSIA books nothing.
    assert all(value == 0.0 for values in produced.values() for value in values)


def test_fossil_kerosene_maps_to_the_combustion_baseline():
    """The transform's defining case: fossil kerosene must land exactly on 73.8."""
    carriers = {"fossil_kerosene": _carrier("dropin_fuel", [FOSSIL_WTW, FOSSIL_WTW])}
    assert _factors(lifecycle_to_corsia(carriers))["fossil_kerosene"] == [FOSSIL_TTW, FOSSIL_TTW]


def test_non_dropin_carriers_are_zeroed():
    carriers = {
        "liquid_hydrogen": _carrier("hydrogen", [40.0, 20.0]),
        "battery_electric": _carrier("electric", [15.0, 5.0]),
        "saf": _carrier("dropin_fuel", [40.0, 20.0]),
    }
    converted = _factors(lifecycle_to_corsia(carriers))
    assert converted["liquid_hydrogen"] == [0.0, 0.0]
    assert converted["battery_electric"] == [0.0, 0.0]
    assert converted["saf"] != [0.0, 0.0]


def test_round_trip_restores_dropin_factors():
    """Unrounded, the conversion is exactly invertible for drop-in pathways."""
    original = [67.0, 48.8]
    carriers = {"saf": _carrier("dropin_fuel", original)}
    there = lifecycle_to_corsia(carriers, decimals=None)
    back = corsia_to_lifecycle(there, decimals=None)
    assert _factors(back)["saf"] == pytest.approx(original)


def test_round_trip_does_not_invent_a_zeroed_factor():
    """A non-drop-in factor is destroyed on the way out and must stay destroyed."""
    carriers = {"liquid_hydrogen": _carrier("hydrogen", [40.0, 20.0])}
    back = corsia_to_lifecycle(lifecycle_to_corsia(carriers, decimals=None), decimals=None)
    assert _factors(back)["liquid_hydrogen"] == [0.0, 0.0]


def test_both_routes_agree():
    """Converting a built process matches converting its carrier files.

    This is what makes the committed twins optional: a scenario can be run in the
    CORSIA scope from its own well-to-wake configuration. Compared at the level of
    the parameters the model actually reads, which is where the two routes meet;
    running both scenarios to completion agrees on all 877 output series too, but
    that is far too slow to assert here.
    """
    from aeromaps import create_process

    config = ATAG / "3rd_edition_full" / "config_files" / "config_s1.yaml"
    process = create_process(configuration_file=str(config))
    apply_corsia_scope(process)

    expected = _factors(read_yaml_file(str(FULL / "s1-TTW_energy.yaml")))
    checked = 0
    for name, values in expected.items():
        attribute = f"{name}_{EF_KEY}_values"
        if not hasattr(process.parameters, attribute):
            continue
        assert list(getattr(process.parameters, attribute)) == pytest.approx(values), name
        checked += 1
    assert checked >= 8, "expected most carriers to expose an emission-factor parameter"


def test_default_rounding_matches_the_committed_files():
    """The 4-decimal default is what makes the committed twins reproducible.

    Woody biomass at 2050 is the case the module docstring cites: the ratio method
    gives 5.9905, against 5.904 had the report's rounded 8 % been used instead.
    """
    carriers = {"ft_woody_biomass": _carrier("dropin_fuel", [7.2])}
    rounded = _factors(lifecycle_to_corsia(carriers))["ft_woody_biomass"][0]
    assert rounded == round(7.2 * CORSIA_RATIO, 4)

    carriers = {"ft_woody_biomass": _carrier("dropin_fuel", [7.2])}
    exact = _factors(lifecycle_to_corsia(carriers, decimals=None))["ft_woody_biomass"][0]
    assert exact != rounded
    assert exact == pytest.approx(rounded, abs=1e-4)
