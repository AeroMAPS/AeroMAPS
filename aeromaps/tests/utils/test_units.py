"""Tests for AeroMAPS units framework."""

import numpy as np
import pandas as pd
from pint import DimensionalityError, UndefinedUnitError  # noqa: F401
import pytest
import pint_pandas

from aeromaps.units.aeromaps_unit_registry import AeroMAPSUnitRegistry


@pytest.fixture
def ureg():
    return AeroMAPSUnitRegistry()


def test_units_quantities(ureg):
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


def test_parenthesis(ureg):
    """Test parenthesis expressions parsing."""
    # €/(kg/day) = €·day/kg
    dims = ureg.dimension("€/(kg/day)")
    assert dims == {"[currency]": 1, "[mass]": -1, "[time]": 1}


def test_left_associative_division(ureg):
    """Test left associative divisions."""
    # a/b/c = a/(b·c)
    assert ureg("L/PAX/100km").dimensionality == ureg("L/(PAX*100km)").dimensionality


# @pytest.mark.parametrize(
#         "invalid_unit",["foobar", "MJ/", "€/(kg", "MJ//ASK"]
# )

# def test_invalid_units(ureg,invalid_unit):
# # TODO: To define if this test is necessary as invalid units are handled by pint and
# # the error depends on the why the unit is invalid
#     with pytest.raises(UndefinedUnitError):
#         ureg(invalid_unit)


def test_aliases(ureg):
    assert ureg.normalize_unit("Years") == "yr"
    assert ureg.normalize_unit("ton") == "t"
    assert ureg.normalize_unit("€/ton") == "€/t"
    assert ureg.normalize_unit("kgCO2/kgfuel") == "kgCO2/kg_fuel"


# TODO: check if (kg/day) should be processed as single unit
# assert ureg("€/(kg/day)/year").normalize_unit == "€/(kg/day)/year"


def test_canonical_spelling_unchanged(ureg):
    for text in ["MJ/ASK", "gCO2/MJ", "€/tCO2e", "W/m²"]:
        assert ureg.normalize_unit(text) == text


def test_normalization_is_idempotent_and_preserves_dimension(ureg):
    for text in ["Years", "€/ton", "kgCO2/kgfuel", "€/(kg/day)/year"]:
        normalized = ureg.normalize_unit(text)
        assert ureg.normalize_unit(normalized) == normalized
        assert ureg(normalized).dimensionality == ureg(text).dimensionality


def test_simple_factors(ureg):
    assert ureg("EJ").to("MJ").magnitude == pytest.approx(1e12)
    assert ureg("kWh").to("MJ").magnitude == pytest.approx(3.6)
    assert ureg("%").to("").magnitude == pytest.approx(0.01)


def test_compound_conversion(ureg):
    assert ureg("gCO2/MJ").to("tCO2/EJ").magnitude == pytest.approx(1e6)
    assert ureg("88.7gCO2/MJ").to("kgCO2/MJ").magnitude == pytest.approx(0.0887)


def test_pandas_series_and_numpy(ureg):
    pint_pandas.PintType.ureg = ureg
    series = pd.Series([1.0, 2.0])
    pax_series = series.astype("pint[PAX]")
    assert str(pax_series.pint.units) == "PAX"
    series_with_units = series.astype("pint[EJ]")
    converted = series_with_units.pint.to("MJ")
    assert isinstance(converted, pd.Series)
    assert converted.iloc[1].magnitude == pytest.approx(2e12)

    array = ureg.Quantity(np.array([1.0]), "Mt").to("kg")
    assert array[0].magnitude == pytest.approx(1e9)


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
