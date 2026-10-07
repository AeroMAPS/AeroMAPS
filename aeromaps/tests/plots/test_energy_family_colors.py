"""
Lock the fuel-family grouping used by the detailed CO2 decomposition plot.

Hydrogen (used through hydrogen aircraft) must stay its own family and never be
merged with drop-in electrofuels, even though electrolytic hydrogen and
electrofuels share the "electricity" energy origin.
"""

from aeromaps.plots.colors import (
    ENERGY_FAMILY_COLORMAPS,
    ENERGY_FAMILY_LABELS,
    energy_family,
)


def test_hydrogen_is_not_merged_with_electrofuels():
    # Both share the "electricity" origin but must land in different families.
    assert energy_family("hydrogen", "electricity") == "hydrogen"
    assert energy_family("dropin_fuel", "electricity") == "electricity"
    assert energy_family("hydrogen", "electricity") != energy_family("dropin_fuel", "electricity")


def test_family_of_each_carrier():
    assert energy_family("dropin_fuel", "biomass") == "biomass"
    assert energy_family("dropin_fuel", "fossil") == "fossil"
    assert energy_family("hydrogen", "fossil") == "hydrogen"  # grey/blue H2 still hydrogen
    assert energy_family("electric", "electricity") == "electric"


def test_hydrogen_family_has_its_own_label_and_colour():
    assert ENERGY_FAMILY_LABELS["hydrogen"] == "Hydrogen"
    assert "electrofuel" not in ENERGY_FAMILY_LABELS["hydrogen"].lower()
    # Distinct colormaps for hydrogen vs electrofuels (electricity family).
    assert ENERGY_FAMILY_COLORMAPS["hydrogen"] is not ENERGY_FAMILY_COLORMAPS["electricity"]
