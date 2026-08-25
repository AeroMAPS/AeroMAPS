"""
Test module for the AeroMAPS variable metadata registry
(aeromaps/utils/data_information.py) and its default data file.
"""

from pathlib import Path

import pytest

from aeromaps.utils.data_information import DataInformation
from aeromaps.utils.units import UnitError, normalize_unit, parse_unit

DEFAULT_FILE = Path(__file__).parent.parent.parent / "resources" / "data" / "data_information.yaml"


class TestDefaultFile:
    def test_loads_and_units_are_valid(self):
        # Loading validates every unit (exact entries and patterns)
        info = DataInformation.from_file(DEFAULT_FILE)
        assert len(info.variables) > 800
        assert len(info.patterns) > 50

    def test_known_variable(self):
        info = DataInformation.from_file(DEFAULT_FILE)
        entry = info.lookup("co2_emissions")
        assert entry["Unit"] == "MtCO2"

    def test_pattern_resolution(self):
        info = DataInformation.from_file(DEFAULT_FILE)
        entry = info.lookup("my_new_pathway_mean_mfsp")
        assert entry["Unit"] == "€/MJ"
        assert "my_new_pathway" in entry["Description"]

    def test_market_scoped_patterns(self):
        # Market ids are user-defined in the markets yaml file, so market-scoped
        # variables must resolve through patterns for any market id.
        info = DataInformation.from_file(DEFAULT_FILE)
        assert info.lookup("regional_covid_end_year")["Unit"] == "yr"
        assert info.lookup("cagr_rpk_regional")["Unit"] == "%"
        assert info.lookup("rtk_reference_belly_cargo")["Unit"] == "RTK"

    def test_all_units_normalize_idempotently(self):
        # Canonical spellings in the default file: normalizing must be a no-op
        # and preserve the parsed dimension.
        info = DataInformation.from_file(DEFAULT_FILE)
        units = {str(e["unit"]) for e in info.variables.values()}
        units |= {str(p["unit"]) for p in info.patterns if p.get("unit") is not None}
        units.discard(DataInformation.NOT_APPLICABLE)
        for unit in units:
            normalized = normalize_unit(unit)
            assert normalized == unit, f"'{unit}' is not the canonical spelling '{normalized}'"
            assert parse_unit(normalized).dims == parse_unit(unit).dims


class TestRegistry:
    def test_exact_entry_takes_precedence_over_pattern(self):
        info = DataInformation(
            variables={"special_mean_mfsp": {"unit": "€/L", "description": "special"}},
            patterns=[{"match": "*_mean_mfsp", "unit": "€/MJ", "description": "generic"}],
        )
        assert info.lookup("special_mean_mfsp")["Unit"] == "€/L"
        assert info.lookup("other_mean_mfsp")["Unit"] == "€/MJ"

    def test_first_matching_pattern_wins(self):
        info = DataInformation(
            variables={},
            patterns=[
                {"match": "*_years", "unit": "yr", "description": "years"},
                {"match": "*", "unit": "-", "description": "fallback"},
            ],
        )
        assert info.lookup("reference_years")["Unit"] == "yr"
        assert info.lookup("anything_else")["Unit"] == "-"

    def test_unknown_variable_returns_none(self):
        info = DataInformation(variables={}, patterns=[])
        assert info.lookup("unknown_variable") is None

    def test_multi_star_pattern_prefix_is_first_group(self):
        info = DataInformation(
            variables={},
            patterns=[{"match": "*_share_*", "unit": "%", "description": "Share of `{prefix}`"}],
        )
        assert info.lookup("kerosene_share_2019")["Description"] == "Share of `kerosene`"

    def test_pattern_without_match_key_raises(self):
        with pytest.raises(ValueError):
            DataInformation(variables={}, patterns=[{"unit": "MJ", "description": "d"}])

    def test_description_templating(self):
        info = DataInformation(
            variables={},
            patterns=[
                {
                    "match": "*_energy_consumption",
                    "unit": "MJ",
                    "description": "Energy consumption of `{prefix}` ({name})",
                }
            ],
        )
        entry = info.lookup("atj_energy_consumption")
        assert entry["Description"] == "Energy consumption of `atj` (atj_energy_consumption)"

    def test_invalid_unit_raises(self):
        with pytest.raises(UnitError):
            DataInformation(variables={"x": {"unit": "not_a_unit", "description": "d"}})
        with pytest.raises(UnitError):
            DataInformation(variables={}, patterns=[{"match": "*", "unit": "not_a_unit"}])

    def test_not_applicable_unit_is_accepted(self):
        info = DataInformation(
            variables={"lca_thing": {"unit": "N/A", "description": "LCA impact"}}
        )
        assert info.lookup("lca_thing")["Unit"] == "N/A"

    def test_build_dataframe_and_unresolved(self):
        info = DataInformation(variables={"known": {"unit": "MJ", "description": "d"}}, patterns=[])
        data = {"float_inputs": ["known", "unknown"]}
        df = info.build_dataframe(data)
        assert list(df.columns) == ["Name", "Type", "Unit", "Description", "Source"]
        assert df.loc[df["Name"] == "known", "Unit"].item() == "MJ"
        assert df.loc[df["Name"] == "unknown", "Unit"].item() == "N/A"
        assert info.unresolved_names(data) == ["unknown"]

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            DataInformation.from_file(tmp_path / "does_not_exist.yaml")

    def test_malformed_yaml_raises(self, tmp_path):
        bad_file = tmp_path / "bad.yaml"
        bad_file.write_text("variables: [unclosed", encoding="utf-8")
        with pytest.raises(ValueError):
            DataInformation.from_file(bad_file)

    def test_non_mapping_yaml_raises(self, tmp_path):
        list_file = tmp_path / "list.yaml"
        list_file.write_text("- a\n- b\n", encoding="utf-8")
        with pytest.raises(ValueError):
            DataInformation.from_file(list_file)

    def test_legacy_csv_is_deprecated_but_supported(self, tmp_path):
        csv_file = tmp_path / "data_information.csv"
        csv_file.write_text(
            "Name;Type;Unit;Description;Reference for default input value (if applicable)\n"
            "rpk;Vector;RPK;Revenue Passenger Kilometer;ICAO\n",
            encoding="utf-8",
        )
        with pytest.warns(DeprecationWarning):
            info = DataInformation.from_file(csv_file)
        entry = info.lookup("rpk")
        assert entry["Unit"] == "RPK"
        assert entry["Source"] == "ICAO"
