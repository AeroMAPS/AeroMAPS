"""Tests of the ``FuelClearing`` discipline, as distinct from the kernel it calls.

``test_fuel_clearing_kernel.py`` covers the convex programme: 53 tests on a pure
function. Until this file there were **none** on the discipline that feeds it -- the
settings plumbing, the pathway roles, the setup guards. A reviewer pointed that out,
and the first defect it would have caught was already in the tree: a global
``capacity`` reaching the residual pathway, which is what every bench script in the
spike had been doing.

These are deliberately cheap: they exercise the assembly, not an MDA. The end-to-end
reproduction is a separate and still-missing test (REPORT.md section 7).
"""

from __future__ import annotations

import numpy as np
import pytest

from aeromaps.models.impacts.generic_energy_model.fuel_clearing.fuel_clearing import (
    DEFAULT_SETTINGS,
    FuelClearing,
    _SCARCITY_SETTINGS,
)

RESIDUAL = "fossil_kerosene"
MANDATED = "hefa_fog"


def _market(**configuration):
    """A discipline with its settings resolved, without running ``custom_setup``.

    ``custom_setup`` needs an injected region list and pathways manager, which is a
    process to build. The settings plumbing under test runs before any of that.
    """
    market = FuelClearing("fuel_clearing", configuration_data=configuration)
    for key in DEFAULT_SETTINGS:
        if key in configuration:
            market.settings[key] = configuration[key]
    market.residual_name = RESIDUAL
    market.pathway_names = [MANDATED, RESIDUAL]
    market.sustainable_names = [MANDATED]
    return market


def test_a_global_capacity_does_not_reach_the_residual_pathway():
    """The defect the reviewer found, pinned.

    A scenario that says ``capacity: 1.1e13`` means the pathway it is studying. Applied
    to the residual as well, kerosene ran at about 90 % utilisation on the bench, its
    marginal cost rose with output, and ``energy_price`` stopped being the cost of the
    marginal conventional fuel -- 0.01226 against 0.01200, so the identity the report
    asserts and publishes was false by 2.2 %.
    """
    market = _market(capacity=1.1e13, saturation_intensity=1.0)

    assert market._pathway_setting("capacity", MANDATED, np.inf) == 1.1e13
    assert market._pathway_setting("saturation_intensity", MANDATED, 0.0) == 1.0

    assert market._pathway_setting("capacity", RESIDUAL, np.inf) == np.inf
    assert market._pathway_setting("saturation_intensity", RESIDUAL, 0.0) == 0.0


def test_the_residual_can_still_be_given_a_limit_explicitly():
    """Scoping the default is not forbidding the case.

    A fossil supply limit is a legitimate thing to model and step 2 may well want it.
    Naming the pathway is how you ask for it.
    """
    market = _market(capacity=1.1e13, pathways={RESIDUAL: {"capacity": 5.0e13}})
    assert market._pathway_setting("capacity", RESIDUAL, np.inf) == 5.0e13


@pytest.mark.parametrize("key", sorted(_SCARCITY_SETTINGS))
def test_every_scarcity_setting_is_scoped_the_same_way(key):
    """So that adding one to the set cannot leave a hole behind it."""
    market = _market(**{key: 123.0})
    assert market._pathway_setting(key, MANDATED, 0.0) == 123.0
    assert market._pathway_setting(key, RESIDUAL, 0.0) == 0.0


def test_settings_that_are_not_about_scarcity_still_apply_everywhere():
    """The exemption is narrow on purpose.

    The ramp-up keys are deliberately outside it: the kernel applies the growth limit to
    eligible rows only, so a global value is already inert on the residual and scoping
    it here would be a second mechanism doing the same job in a different place.
    """
    market = _market(rampup_limit=0.2, pricing_weight=1.0, buyout_price=0.3)
    for key, expected in (("rampup_limit", 0.2), ("pricing_weight", 1.0), ("buyout_price", 0.3)):
        assert market._pathway_setting(key, RESIDUAL, None) == expected
        assert market._pathway_setting(key, MANDATED, None) == expected


def test_a_per_pathway_block_beats_the_global_value():
    market = _market(capacity=1.0e13, pathways={MANDATED: {"capacity": 2.0e12}})
    assert market._pathway_setting("capacity", MANDATED, np.inf) == 2.0e12


def test_the_defaults_are_no_scarcity():
    """The mode reproduces the current one out of the box, which is decision 10's test.

    ``rampup_limit`` is a large finite number rather than ``inf`` on purpose: it is a
    coefficient inside a constraint and the kernel refuses non-finite inputs. Capacity
    is the opposite -- there ``inf`` is the documented way to say "does not saturate".
    """
    assert DEFAULT_SETTINGS["saturation_intensity"] == 0.0
    assert DEFAULT_SETTINGS["capacity"] == np.inf
    assert DEFAULT_SETTINGS["pricing_weight"] == 0.0
    assert np.isfinite(DEFAULT_SETTINGS["rampup_limit"])
    assert DEFAULT_SETTINGS["demand_elasticity"] == 0.0
    assert DEFAULT_SETTINGS["proximal_weight"] == 0.0
