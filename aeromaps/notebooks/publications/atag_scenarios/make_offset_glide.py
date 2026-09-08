"""
make_offset_glide
=================
Write the post-CORSIA offset schedule into the third-edition scenario inputs.

The reports model regionally-resolved CORSIA offsets through 2035 and then assume
"an extra policy" to reach net zero by 2050 without saying what it is. That policy
does not exist, so there is nothing to reproduce; what the reports do publish is
the *shape* their net CO2 line takes, and in all three third-edition scenarios it
is the same: net emissions sit on the carbon-neutral-growth level through the
mid-2030s and then fall to zero at 2050 along a straight line.

So the assumption taken here is a target on net emissions rather than a share of
residual ones:

    net(t) = net(2035) * (2050 - t) / (2050 - 2035),   t = 2036 ... 2050

with the CORSIA-derived manual offsets left untouched up to 2035. It is continuous
at the handover by construction, monotone, and reaches exactly 100 % offsetting at
2050.

AeroMAPS parameterises offsetting as a share of residual emissions, so the target
is inverted into one. With no level offset and no manual offset after 2035,
``net = gross * (1 - share/100)``, hence

    share(t) = 100 * (1 - net(t) / gross(t))

Gross emissions do not depend on offsets, so reading ``gross`` from the committed
outputs and writing the share back is a single pass, not an iteration. It does
have to be redone whenever a scenario's gross trajectory changes, which is why
this is a script and not a hand-edited constant: the share is scenario-specific,
and copying one scenario's schedule to another is exactly the mistake that made
S0's net line rise between 2036 and 2040.

Run from this directory, after the scenarios have been generated once::

    python make_offset_glide.py

then re-run the five notebooks so the outputs match the inputs.
"""

import json
from pathlib import Path

import numpy as np

from aeromaps.utils.offsets import residual_share_for_net_target
from aeromaps.utils.scenarios import find_scenario

FIRST_YEAR = 2000
HANDOVER = 2035  # last year covered by the CORSIA-derived manual offsets
NET_ZERO = 2050

# label -> (packaged scenario, publication folder holding its results,
#           inputs file to rewrite, outputs file the gross trajectory comes from)
SCENARIOS = {
    "3rd edition full S1": (
        "atag_3rd_edition_full",
        "3rd_edition_full",
        "s1_inputs.json",
        "s1.json",
    ),
    "3rd edition full S2": (
        "atag_3rd_edition_full",
        "3rd_edition_full",
        "s2_inputs.json",
        "s2.json",
    ),
    "3rd edition light S0": (
        "atag_3rd_edition_light",
        "3rd_edition_light",
        "s0_inputs.json",
        "s0.json",
    ),
    "3rd edition light S1": (
        "atag_3rd_edition_light",
        "3rd_edition_light",
        "s1_inputs.json",
        "s1.json",
    ),
    "3rd edition light S2": (
        "atag_3rd_edition_light",
        "3rd_edition_light",
        "s2_inputs.json",
        "s2.json",
    ),
}

KEY_YEARS = "residual_carbon_offset_share_reference_years"
KEY_VALUES = "residual_carbon_offset_share_reference_years_values"


def _series(outputs, name):
    """One vector output as a year-indexed float array."""
    raw = outputs["vector_outputs"][name]
    return np.asarray(list(raw.values()) if isinstance(raw, dict) else raw, dtype=float)


def _find(node, key):
    """The value of ``key`` wherever it sits in a nested inputs file."""
    if isinstance(node, dict):
        for name, value in node.items():
            if name == key:
                return node, value
            found = _find(value, key)
            if found is not None:
                return found
    return None


def glide(outputs):
    """The annual share schedule, plus the net trajectory it produces."""
    years, shares, net_handover = residual_share_for_net_target(
        _series(outputs, "co2_emissions_including_energy"),
        _series(outputs, "carbon_offset"),
        handover_year=HANDOVER,
        net_zero_year=NET_ZERO,
        first_year=FIRST_YEAR,
    )
    span = NET_ZERO - HANDOVER
    target = [net_handover * (NET_ZERO - year) / span for year in years]
    return net_handover, years, shares, target


def main():
    here = Path(__file__).parent
    for label, (scenario, edition, inputs_name, outputs_name) in SCENARIOS.items():
        inputs_path = find_scenario(scenario).path / "data_inputs" / inputs_name
        outputs_path = here / edition / "data_outputs" / outputs_name
        if not outputs_path.exists():
            print("%-22s SKIPPED, no committed output yet" % label)
            continue

        outputs = json.loads(outputs_path.read_text(encoding="utf-8"))
        net_handover, years, shares, _ = glide(outputs)

        inputs = json.loads(inputs_path.read_text(encoding="utf-8"))
        holder, _ = _find(inputs, KEY_VALUES)
        holder[KEY_YEARS] = [2020, HANDOVER] + years
        holder[KEY_VALUES] = [0.0, 0.0] + shares
        inputs_path.write_text(json.dumps(inputs, indent=4) + "\n", encoding="utf-8")

        print(
            "%-22s net(%d) = %7.1f Mt, share %5.1f %% at %d rising to %5.1f %% at %d"
            % (
                label,
                HANDOVER,
                net_handover,
                shares[0],
                years[0],
                shares[-1],
                years[-1],
            )
        )


if __name__ == "__main__":
    main()
