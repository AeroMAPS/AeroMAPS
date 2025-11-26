"""
Constants for air transport energy and fuel types.
FIXME: Typo in 'HYDROGENE' should be 'HYDROGEN'.
FIXME: Where are the constants used?
"""

from aenum import Enum


# Definition of energy types
class EnergyTypes(Enum):
    """
    Enumeration of Energy Types.
    """

    DROP_IN_FUEL = "Drop-in Fuel"
    HYDROGENE = "Hydrogene"


# Definition of fuel types
class FuelTypes(Enum):
    """
    Enumeration of Fuel Types.
    """

    KEROSENE = "Kerosene"
    BIOFUEL = "Biofuel"
    ELECTROFUEL = "Electrofuel"
