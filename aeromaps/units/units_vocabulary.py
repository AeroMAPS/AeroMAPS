"""This module defines the controlled vocabulary of units.

Used to document AeroMAPS variables (see ``aeromaps/utils/data_information.py``)
"""

# Atomic unit symbols: symbol -> (dimension, factor to the canonical unit of the dimension)
import re


ATOMIC_UNITS = {
    # Dimensionless
    "-": ("dimensionless", 1.0),
    "1": ("dimensionless", 1.0),
    "%": ("dimensionless", 0.01),
    # Time (canonical: yr)
    "yr": ("time", 1.0),
    "day": ("time", 1.0 / 365.25),
    # Energy (canonical: MJ)
    "J": ("energy", 1e-6),
    "kJ": ("energy", 1e-3),
    "MJ": ("energy", 1.0),
    "GJ": ("energy", 1e3),
    "TJ": ("energy", 1e6),
    "PJ": ("energy", 1e9),
    "EJ": ("energy", 1e12),
    "kWh": ("energy", 3.6),
    "MWh": ("energy", 3.6e3),
    "GWh": ("energy", 3.6e6),
    "TWh": ("energy", 3.6e9),
    # Mass (canonical: kg); species-tagged masses (gCO2, kg_NOx, ...) are
    # recognized separately, see _SPECIES_MASS_RE.
    "g": ("mass", 1e-3),
    "kg": ("mass", 1.0),
    "t": ("mass", 1e3),
    "kt": ("mass", 1e6),
    "Mt": ("mass", 1e9),
    "Gt": ("mass", 1e12),
    # Distance (canonical: km)
    "m": ("distance", 1e-3),
    "km": ("distance", 1.0),
    "100km": ("distance", 100.0),
    # Area (canonical: m²)
    "m²": ("area", 1.0),
    # Volume (canonical: L)
    "L": ("volume", 1.0),
    "m³": ("volume", 1e3),
    # Currency (canonical: €); constant-euro variants are not distinguished.
    # US dollars are a separate dimension: no implicit exchange-rate conversion.
    "€": ("currency", 1.0),
    "k€": ("currency", 1e3),
    "M€": ("currency", 1e6),
    "$": ("currency[USD]", 1.0),
    "k$": ("currency[USD]", 1e3),
    "M$": ("currency[USD]", 1e6),
    # Temperature difference (canonical: °C)
    "°C": ("temperature", 1.0),
    "K": ("temperature", 1.0),
    # Power (canonical: W)
    "mW": ("power", 1e-3),
    "W": ("power", 1.0),
    "kW": ("power", 1e3),
    "MW": ("power", 1e6),
    "GW": ("power", 1e9),
    "TW": ("power", 1e12),
    # Population (canonical: capita)
    "capita": ("capita", 1.0),
    # Air transport quantities (each is its own dimension)
    "ASK": ("ASK", 1.0),
    "RPK": ("RPK", 1.0),
    "RTK": ("RTK", 1.0),
    "PAX": ("PAX", 1.0),
    "seat": ("seat", 1.0),
    "aircraft": ("aircraft", 1.0),
}

# Legacy or alternative spellings, normalized atom-wise before lookup
UNIT_ALIASES = {
    "Years": "yr",
    "years": "yr",
    "Year": "yr",
    "year": "yr",
    "ton": "t",
    "tonne": "t",
    "kgfuel": "kg_fuel",
    "degC": "°C",
    "m2": "m²",
    "m3": "m³",
    "l": "L",
    "EUR": "€",
    "euro": "€",
    "euros": "€",
}

# Species-tagged masses: mass prefix + species (CO2, CO2e, CO2-we, NOx, H2O, fuel, ...).
# The species must start with an uppercase letter (chemical-like tag) or be "fuel".
# Each species defines its own dimension so different species are not interchangeable.
_SPECIES_MASS_RE = re.compile(r"^(g|kg|t|kt|Mt|Gt)_?([A-Z][A-Za-z0-9]*(?:-we)?|fuel)$")

_TOKEN_RE = re.compile(r"[*/·()]|[^*/·()\s]+")
