"""
Test module for the AeroMAPS unit system (aeromaps/utils/units.py).
"""

import numpy as np
import pandas as pd
from pint import UndefinedUnitError
import pytest

from aeromaps.units.aeromaps_unit_registry import AeroMAPSUnitRegistry
from aeromaps.utils.units import (
    UnitError,
    convert,
    convert_factor,
    is_valid_unit,
    normalize_unit,
    parse_unit,
    units_compatible,
)


def test_atomic_units():
    ureg = AeroMAPSUnitRegistry()
    assert ureg.unit_quantity("MJ") == "energy"
    assert ureg.unit_quantity("yr") == "time"
    assert ureg.unit_quantity("ASK") == "ASK"
    assert ureg.unit_quantity("") == "dimensionless"
    assert ureg.unit_quantity("%") == "dimensionless"


def test_species_tagged_masses():
    ureg = AeroMAPSUnitRegistry()
    assert ureg.unit_quantity("gCO2") == "mass[CO2]"
    assert ureg.unit_quantity("tCO2e") == "mass[CO2e]"
    assert ureg.unit_quantity("GtCO2we") == "mass[CO2we]"
    assert ureg.unit_quantity("kg_NOx") == "mass[NOx]"
    assert ureg.unit_quantity("kg_fuel") == "mass[fuel]"


def test_compound_units():
    ureg = AeroMAPSUnitRegistry()
    dims = ureg.dimension("gCO2/MJ")
    assert dims == {"[energy]": -1, "[mass[CO2]]": 1}


def test_parentheses():
    # €/(kg/day) = €·day/kg
    ureg = AeroMAPSUnitRegistry()
    dims = ureg.dimension("€/(kg/day)")
    assert dims == {"[currency]": 1, "[mass]": -1, "[time]": 1}


def test_left_associative_division():
    # a/b/c = a/(b·c)
    ureg = AeroMAPSUnitRegistry()
    assert ureg("L/PAX/100km").dimensionality == ureg("L/(PAX*100km)").dimensionality


def test_invalid_units():
    ureg = AeroMAPSUnitRegistry()
    for text in ["", "foobar", "MJ/", "€/(kg", "MJ//ASK"]:
        with pytest.raises(UndefinedUnitError):
            ureg(text)
    assert not is_valid_unit("foobar")
    assert is_valid_unit("MJ/ASK")


def test_aliases():
    assert normalize_unit("Years") == "yr"
    assert normalize_unit("ton") == "t"
    assert normalize_unit("€/ton") == "€/t"
    assert normalize_unit("kgCO2/kgfuel") == "kgCO2/kg_fuel"
    assert normalize_unit("€/(kg/day)/year") == "€/(kg/day)/yr"


def test_canonical_spelling_unchanged():
    for text in ["MJ/ASK", "gCO2/MJ", "€/tCO2e", "W/m²"]:
        assert normalize_unit(text) == text


def test_normalization_is_idempotent_and_preserves_dimension():
    for text in ["Years", "€/ton", "kgCO2/kgfuel", "€/(kg/day)/year"]:
        normalized = normalize_unit(text)
        assert normalize_unit(normalized) == normalized
        assert parse_unit(normalized).dims == parse_unit(text).dims


def test_simple_factors():
    assert convert_factor("EJ", "MJ") == pytest.approx(1e12)
    assert convert_factor("kWh", "MJ") == pytest.approx(3.6)
    assert convert_factor("%", "-") == pytest.approx(0.01)


def test_compound_conversion():
    assert convert(1.0, "gCO2/MJ", "tCO2/EJ") == pytest.approx(1e6)
    assert convert(88.7, "gCO2/MJ", "kgCO2/MJ") == pytest.approx(0.0887)


def test_pandas_series_and_numpy():
    series = pd.Series([1.0, 2.0])
    converted = convert(series, "EJ", "MJ")
    assert isinstance(converted, pd.Series)
    assert converted.iloc[1] == pytest.approx(2e12)
    array = convert(np.array([1.0]), "Mt", "kg")
    assert array[0] == pytest.approx(1e9)


def test_incompatible_dimensions_raise():
    with pytest.raises(UnitError):
        convert(1.0, "MJ", "kg")
    # CO2 and CO2e are deliberately not interchangeable
    with pytest.raises(UnitError):
        convert(1.0, "tCO2", "tCO2e")
    # euros and dollars are deliberately not interchangeable
    with pytest.raises(UnitError):
        convert(1.0, "€", "$")


def test_compatibility_check():
    assert units_compatible("MJ", "EJ")
    assert units_compatible("gCO2/MJ", "MtCO2/EJ")
    assert not units_compatible("MJ", "MJ/ASK")


def test_dimension_cancellation():
    # Identical dimensions cancel out to dimensionless
    assert parse_unit("MJ/MJ").dims == ()
    assert units_compatible("MJ/MJ", "-")


def test_dimensionless_factor_in_compound():
    # The 0.01 factor of % must survive inside a compound expression
    assert convert_factor("%/yr", "-/yr") == pytest.approx(0.01)


def test_nested_parentheses_conversion():
    # €/(MJ/yr) -> €/(EJ/yr): 1 € per MJ/yr of capacity = 1e12 € per EJ/yr
    assert convert_factor("€/(MJ/yr)", "€/(EJ/yr)") == pytest.approx(1e12)
