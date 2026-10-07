"""Mandate transforms on an ``energy_carriers`` mapping."""

import pytest

from aeromaps.models.base import AeroMapsCustomDataType
from aeromaps.utils.mandates import quantity_to_share, retime_mandates, zero_mandates


def _carrier(mandate_type, key, years, values):
    return {
        "inputs": {
            "mandate": {
                "mandate_type": mandate_type,
                key: AeroMapsCustomDataType(
                    {"years": list(years), "values": list(values), "method": "linear"}
                ),
            }
        }
    }


def _curve(carriers, name, key):
    mandate = carriers[name]["inputs"]["mandate"]
    return list(mandate[key].years), list(mandate[key].values)


def test_quantity_becomes_share_at_the_same_anchors():
    carriers = {"saf": _carrier("quantity", "mandate_quantity", [2030, 2050], [1e9, 4e9])}
    shares = {"saf": {2030: 12.5, 2050: 40.0}}
    converted = quantity_to_share(carriers, shares)

    mandate = converted["saf"]["inputs"]["mandate"]
    assert mandate["mandate_type"] == "share"
    assert "mandate_quantity" not in mandate, "the volume curve must not survive alongside"
    assert _curve(converted, "saf", "mandate_share") == ([2030, 2050], [12.5, 40.0])


def test_quantity_to_share_refuses_a_carrier_it_cannot_convert():
    """Skipping it would silently drop the pathway from the blend."""
    carriers = {"saf": _carrier("quantity", "mandate_quantity", [2030], [1e9])}
    with pytest.raises(KeyError, match="saf"):
        quantity_to_share(carriers, {})


def test_quantity_to_share_refuses_a_missing_anchor_year():
    carriers = {"saf": _carrier("quantity", "mandate_quantity", [2030, 2050], [1e9, 4e9])}
    with pytest.raises(KeyError, match="2050"):
        quantity_to_share(carriers, {"saf": {2030: 12.5}})


def test_share_mandates_are_left_alone():
    carriers = {"saf": _carrier("share", "mandate_share", [2030], [10.0])}
    assert _curve(quantity_to_share(carriers, {}), "saf", "mandate_share") == ([2030], [10.0])


def test_zero_mandates_empties_the_named_pathways_only():
    carriers = {
        "saf": _carrier("share", "mandate_share", [2030, 2050], [10.0, 40.0]),
        "hydrogen": _carrier("share", "mandate_share", [2030, 2050], [1.0, 5.0]),
    }
    zeroed = zero_mandates(carriers, ["saf"])
    assert _curve(zeroed, "saf", "mandate_share") == ([2030, 2050], [0, 0])
    assert _curve(zeroed, "hydrogen", "mandate_share") == ([2030, 2050], [1.0, 5.0])


@pytest.mark.parametrize(
    "pathways, message",
    [(["absent"], "not declared"), (["bare"], "no mandate curve")],
)
def test_zero_mandates_refuses_a_silent_no_op(pathways, message):
    carriers = {"bare": {"inputs": {}}}
    with pytest.raises(KeyError, match=message):
        zero_mandates(carriers, pathways)


def test_retime_interpolates_the_new_first_anchor():
    """The projected trajectory must survive; only the historic head is dropped."""
    carriers = {"saf": _carrier("quantity", "mandate_quantity", [2020, 2030], [0.0, 100.0])}
    years, values = _curve(retime_mandates(carriers, 2024), "saf", "mandate_quantity")
    assert years == [2024, 2030]
    # Linear from (2020, 0) to (2030, 100): 2024 sits at 40, not at zero. Anchoring
    # the new start at zero instead would cut everything that follows.
    assert values == pytest.approx([40.0, 100.0])


def test_retime_keeps_an_existing_anchor_value():
    carriers = {
        "saf": _carrier("quantity", "mandate_quantity", [2020, 2024, 2030], [0.0, 7.0, 100.0])
    }
    assert _curve(retime_mandates(carriers, 2024), "saf", "mandate_quantity") == (
        [2024, 2030],
        [7.0, 100.0],
    )


def test_retime_is_idempotent():
    carriers = {"saf": _carrier("quantity", "mandate_quantity", [2020, 2030], [0.0, 100.0])}
    once = retime_mandates(carriers, 2024)
    twice = retime_mandates(once, 2024)
    assert _curve(twice, "saf", "mandate_quantity") == _curve(once, "saf", "mandate_quantity")
