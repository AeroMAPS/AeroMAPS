"""
Test module for the AeroMAPS unit system (aeromaps/utils/units.py).
"""

import numpy as np
import pandas as pd
from pint import DimensionalityError, UndefinedUnitError
import pytest

from aeromaps.units.aeromaps_unit_registry import AeroMAPSUnitRegistry
from aeromaps.utils.units import (
    convert,
    is_valid_unit,
    normalize_unit,
    parse_unit,
)


@pytest.fixture
def ureg():
    return AeroMAPSUnitRegistry()


def test_atomic_units(ureg):
    assert ureg.unit_quantity("MJ") == "energy"
    assert ureg.unit_quantity("yr") == "time"
    assert ureg.unit_quantity("ASK") == "ASK"
    assert ureg.unit_quantity("") == "dimensionless"
    assert ureg.unit_quantity("%") == "dimensionless"


def test_species_tagged_masses(ureg):
    assert ureg.unit_quantity("gCO2") == "mass[CO2]"
    assert ureg.unit_quantity("tCO2e") == "mass[CO2e]"
    assert ureg.unit_quantity("GtCO2we") == "mass[CO2we]"
    assert ureg.unit_quantity("kg_NOx") == "mass[NOx]"
    assert ureg.unit_quantity("kg_fuel") == "mass[fuel]"


def test_compound_units(ureg):
    dims = ureg.dimension("gCO2/MJ")
    assert dims == {"[energy]": -1, "[mass[CO2]]": 1}


def test_parentheses(ureg):
    # €/(kg/day) = €·day/kg
    dims = ureg.dimension("€/(kg/day)")
    assert dims == {"[currency]": 1, "[mass]": -1, "[time]": 1}


def test_left_associative_division(ureg):
    # a/b/c = a/(b·c)
    assert ureg("L/PAX/100km").dimensionality == ureg("L/(PAX*100km)").dimensionality


def test_invalid_units(ureg):
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


def test_simple_factors(ureg):
    assert ureg("EJ").to("MJ").magnitude == pytest.approx(1e12)
    assert ureg("kWh").to("MJ").magnitude == pytest.approx(3.6)
    assert ureg("%").to("").magnitude == pytest.approx(0.01)


def test_compound_conversion(ureg):
    assert ureg("gCO2/MJ").to("tCO2/EJ").magnitude == pytest.approx(1e6)
    assert ureg("88.7gCO2/MJ").to("kgCO2/MJ").magnitude == pytest.approx(0.0887)


def test_pandas_series_and_numpy():
    series = pd.Series([1.0, 2.0])
    converted = convert(series, "EJ", "MJ")
    assert isinstance(converted, pd.Series)
    assert converted.iloc[1] == pytest.approx(2e12)
    array = convert(np.array([1.0]), "Mt", "kg")
    assert array[0] == pytest.approx(1e9)


def test_incompatible_dimensions_raise(ureg):
    with pytest.raises(DimensionalityError):
        ureg("MJ").to("kg")
    # CO2 and CO2e are deliberately not interchangeable
    with pytest.raises(DimensionalityError):
        ureg("tCO2").to("tCO2e")
    # euros and dollars are deliberately not interchangeable
    with pytest.raises(DimensionalityError):
        ureg("€").to("$")


def test_compatibility_check(ureg):
    assert ureg("MJ").dimensionality == ureg("EJ").dimensionality
    assert ureg("gCO2/MJ").dimensionality == ureg("MtCO2/EJ").dimensionality
    assert not ureg("MJ").dimensionality == ureg("MJ/ASK").dimensionality


def test_dimension_cancellation(ureg):
    # Identical dimensions cancel out to dimensionless
    assert ureg.dimension("MJ/MJ") == "dimensionless"
    assert ureg.dimension("MJ/MJ") == ureg.dimension("")


def test_dimensionless_factor_in_compound(ureg):
    # The 0.01 factor of % must survive inside a compound expression
    assert ureg("%/yr").to("1/yr").magnitude == pytest.approx(0.01)


def test_nested_parentheses_conversion(ureg):
    # €/(MJ/yr) -> €/(EJ/yr): 1 € per MJ/yr of capacity = 1e12 € per EJ/yr
    assert ureg("€/(MJ/yr)").to("€/(EJ/yr)").magnitude == pytest.approx(1e12)
