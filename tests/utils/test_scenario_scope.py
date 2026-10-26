"""The ``scope`` block of ``scenario.yaml``: parsing, validation and filtering."""

import pytest

from aeromaps.utils.scenarios import _read_scope, find_scenario, list_scenarios


def test_atag_scenarios_declare_world_domestic_and_international():
    atag = list_scenarios(tag="atag reference")
    assert atag
    for scenario in atag:
        assert scenario.scope["region"] == "world"
        assert scenario.scope["traffic"] == ["domestic", "international"]


def test_filter_by_region_and_traffic():
    world = {s.folder for s in list_scenarios(region="world")}
    international = {s.folder for s in list_scenarios(traffic="international")}
    assert "atag_3rd_edition_full" in world
    assert international <= world
    assert list_scenarios(region="mars") == []


def test_scenario_without_scope_matches_no_scope_filter():
    assert find_scenario("atag_3rd_edition_full").scope
    assert _read_scope(None, "x.yaml") == {}


def test_string_is_read_as_one_item_list_and_lowercased():
    scope = _read_scope({"region": "World", "traffic": "International"}, "x.yaml")
    assert scope == {"region": "world", "traffic": ["international"]}


@pytest.mark.parametrize(
    "raw",
    [
        {"traffic": ["domestc"]},  # typo in a closed vocabulary
        {"emissions": ["tank"]},
        {"regions": "world"},  # unknown key
        {"region": ["world"]},  # region is a string
        ["world"],  # not a mapping
    ],
)
def test_invalid_scope_raises_and_names_the_file(raw):
    with pytest.raises(ValueError, match="x.yaml"):
        _read_scope(raw, "x.yaml")
