"""
Test module for the AeroMAPS unit system (aeromaps/utils/units.py).
"""

import numpy as np
import pandas as pd
import pytest

from aeromaps.utils.units import (
    UnitError,
    convert,
    convert_factor,
    is_valid_unit,
    normalize_unit,
    parse_unit,
    units_compatible,
)


class TestParsing:
    def test_atomic_units(self):
        assert parse_unit("MJ").dimension == "energy"
        assert parse_unit("yr").dimension == "time"
        assert parse_unit("ASK").dimension == "ASK"
        assert parse_unit("-").dimension == "dimensionless"
        assert parse_unit("%").dimension == "dimensionless"

    def test_species_tagged_masses(self):
        assert parse_unit("gCO2").dimension == "mass[CO2]"
        assert parse_unit("tCO2e").dimension == "mass[CO2e]"
        assert parse_unit("GtCO2-we").dimension == "mass[CO2-we]"
        assert parse_unit("kg_NOx").dimension == "mass[NOx]"
        assert parse_unit("kg_fuel").dimension == "mass[fuel]"

    def test_compound_units(self):
        unit = parse_unit("gCO2/MJ")
        assert unit.dims == (("energy", -1), ("mass[CO2]", 1))

    def test_parentheses(self):
        # €/(kg/day) = €·day/kg
        unit = parse_unit("€/(kg/day)")
        assert unit.dims == (("currency", 1), ("mass", -1), ("time", 1))

    def test_left_associative_division(self):
        # a/b/c = a/(b·c)
        assert parse_unit("L/PAX/100km").dims == parse_unit("L/(PAX*100km)").dims

    def test_invalid_units(self):
        for text in ["", "foobar", "MJ/", "€/(kg", "MJ//ASK"]:
            with pytest.raises(UnitError):
                parse_unit(text)
        assert not is_valid_unit("foobar")
        assert is_valid_unit("MJ/ASK")


class TestNormalization:
    def test_aliases(self):
        assert normalize_unit("Years") == "yr"
        assert normalize_unit("ton") == "t"
        assert normalize_unit("€/ton") == "€/t"
        assert normalize_unit("kgCO2/kgfuel") == "kgCO2/kg_fuel"
        assert normalize_unit("€/(kg/day)/year") == "€/(kg/day)/yr"

    def test_canonical_spelling_unchanged(self):
        for text in ["MJ/ASK", "gCO2/MJ", "€/tCO2e", "W/m²"]:
            assert normalize_unit(text) == text


class TestConversion:
    def test_simple_factors(self):
        assert convert_factor("EJ", "MJ") == pytest.approx(1e12)
        assert convert_factor("kWh", "MJ") == pytest.approx(3.6)
        assert convert_factor("%", "-") == pytest.approx(0.01)

    def test_compound_conversion(self):
        assert convert(1.0, "gCO2/MJ", "tCO2/EJ") == pytest.approx(1e6)
        assert convert(88.7, "gCO2/MJ", "kgCO2/MJ") == pytest.approx(0.0887)

    def test_pandas_series_and_numpy(self):
        series = pd.Series([1.0, 2.0])
        converted = convert(series, "EJ", "MJ")
        assert isinstance(converted, pd.Series)
        assert converted.iloc[1] == pytest.approx(2e12)
        array = convert(np.array([1.0]), "Mt", "kg")
        assert array[0] == pytest.approx(1e9)

    def test_incompatible_dimensions_raise(self):
        with pytest.raises(UnitError):
            convert(1.0, "MJ", "kg")
        # CO2 and CO2e are deliberately not interchangeable
        with pytest.raises(UnitError):
            convert(1.0, "tCO2", "tCO2e")
        # euros and dollars are deliberately not interchangeable
        with pytest.raises(UnitError):
            convert(1.0, "€", "$")

    def test_compatibility_check(self):
        assert units_compatible("MJ", "EJ")
        assert units_compatible("gCO2/MJ", "MtCO2/EJ")
        assert not units_compatible("MJ", "MJ/ASK")
