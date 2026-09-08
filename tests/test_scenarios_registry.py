"""Discovery of the packaged reference scenarios, and the sandbox they run in.

The sandbox is the point of the module: these notebooks write, so running one
against the packaged copy would edit the installed AeroMAPS. What is asserted here
is that a prepared copy is complete enough to run from -- shared markets present,
cross-referenced scenarios present -- and that preparing one never touches the
originals.
"""

import filecmp

import pytest

from aeromaps.utils.scenarios import (
    find_scenario,
    list_scenarios,
    prepare_scenario,
    publish_outputs,
    scenarios_root,
)

CATEGORIES = {"institutional", "industrial", "academic"}


def test_every_scenario_declares_a_known_category():
    scenarios = list_scenarios()
    assert scenarios, "no packaged scenarios were discovered"
    for scenario in scenarios:
        assert scenario.category in CATEGORIES, (scenario.folder, scenario.category)
        assert scenario.name and scenario.name != scenario.folder.upper()
        assert scenario.configs(), f"{scenario.folder} holds no configuration"


def test_the_shared_markets_folder_is_not_a_scenario():
    """It has no configurations of its own and would otherwise list as one."""
    assert (scenarios_root() / "markets").is_dir()
    assert "markets" not in {s.folder for s in list_scenarios()}


def test_filters_agree_with_the_metadata():
    institutional = {s.folder for s in list_scenarios(category="institutional")}
    assert "atag_3rd_edition_full" in institutional
    coupled = {s.folder for s in list_scenarios(tag="coupled demand")}
    # A tag cuts across families, which is what categories cannot express.
    assert {"atag_3rd_edition_coupled_demand", "icao_ltag_coupled_wctr"} <= coupled
    assert coupled.isdisjoint(institutional)


def test_lookup_by_folder_and_by_display_name():
    by_folder = find_scenario("atag_3rd_edition_full")
    assert find_scenario(by_folder.name).folder == by_folder.folder


def test_an_unknown_key_names_the_near_misses():
    with pytest.raises(KeyError) as excinfo:
        find_scenario("atag_3rd_full")
    assert "atag_3rd_edition_full" in str(excinfo.value)


def test_a_sandbox_carries_what_the_configurations_reach_for(tmp_path):
    """Shared markets and any sibling scenario a configuration names."""
    sandbox = prepare_scenario("atag_climate_analysis", workdir=tmp_path)
    assert (sandbox / "config_files").is_dir()
    assert (tmp_path / "markets" / "markets_central.yaml").is_file()
    # Its configurations read energy files from the editions they perturb.
    assert (tmp_path / "atag_3rd_edition_full" / "data_inputs").is_dir()
    assert (tmp_path / "atag_2nd_edition_full" / "data_inputs").is_dir()


def test_preparing_a_scenario_leaves_the_original_alone(tmp_path):
    scenario = find_scenario("atag_3rd_edition_light")
    before = sorted(p.name for p in (scenario.path / "data_inputs").iterdir())
    sandbox = prepare_scenario("atag_3rd_edition_light", workdir=tmp_path)

    victim = sandbox / "data_inputs" / before[0]
    victim.write_text("edited in the sandbox\n", encoding="utf-8")

    original = scenario.path / "data_inputs" / before[0]
    assert original.read_text(encoding="utf-8") != "edited in the sandbox\n"
    assert sorted(p.name for p in (scenario.path / "data_inputs").iterdir()) == before


def test_a_second_prepare_does_not_discard_sandbox_edits(tmp_path):
    sandbox = prepare_scenario("atag_3rd_edition_light", workdir=tmp_path)
    marker = sandbox / "data_inputs" / "sandbox_marker.txt"
    marker.write_text("mine\n", encoding="utf-8")

    prepare_scenario("atag_3rd_edition_light", workdir=tmp_path)
    assert marker.is_file(), "re-running a notebook must not wipe the sandbox"

    prepare_scenario("atag_3rd_edition_light", workdir=tmp_path, overwrite=True)
    assert not marker.is_file(), "overwrite=True was asked for and should replace"


def test_publish_outputs_copies_results_where_a_publication_reads_them(tmp_path):
    sandbox = prepare_scenario("atag_3rd_edition_light", workdir=tmp_path)
    produced = sandbox / "data_outputs"
    produced.mkdir(exist_ok=True)
    (produced / "s0.json").write_text('{"vector_outputs": {}}', encoding="utf-8")

    destination = tmp_path / "publication"
    written = publish_outputs(sandbox, destination)
    assert written == [destination / "data_outputs" / "s0.json"]
    assert filecmp.cmp(produced / "s0.json", written[0], shallow=False)
