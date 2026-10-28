"""
Lightweight unit vocabulary, parsing, validation and conversion for AeroMAPS.

This module defines the controlled vocabulary of units used to document AeroMAPS
variables (see ``aeromaps/utils/data_information.py``) and provides:

- parsing of compound unit expressions (e.g. ``€/(kg/day)``, ``gCO2/MJ``),
- validation of unit strings against the vocabulary,
- normalization of legacy spellings (e.g. ``Years`` -> ``yr``),
- conversion between commensurable units (e.g. ``EJ`` -> ``MJ``).

Unit expressions are built from atomic symbols combined with ``*`` (or ``·``),
``/`` and parentheses. Atomic symbols are either listed in ``ATOMIC_UNITS`` or
recognized as species-tagged masses (``gCO2``, ``kg_NOx``, ``MtCO2-we``, ...),
which are kept dimensionally distinct per species so that, for instance, tCO2
and tCO2e cannot be silently mixed.
"""

import re
from dataclasses import dataclass
from functools import lru_cache


class UnitError(ValueError):
    """Raised when a unit string cannot be parsed or units are incompatible."""


# Atomic unit symbols: symbol -> (dimension, factor to the canonical unit of the dimension)
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


@dataclass(frozen=True)
class Unit:
    """
    A parsed unit expression.

    Attributes
    ----------
    text
        The unit string as provided (after atom-wise alias normalization).
    dims
        Sorted tuple of (dimension, exponent) pairs, zero exponents removed.
    factor
        Multiplicative factor to the canonical unit of the same dimension.
    """

    text: str
    dims: tuple
    factor: float

    @property
    def dimension(self) -> str:
        """Human-readable dimension string, e.g. 'currency·mass[CO2]⁻¹'."""
        if not self.dims:
            return "dimensionless"

        def _exp(e):
            return "" if e == 1 else f"^{e}"

        return "·".join(f"{d}{_exp(e)}" for d, e in self.dims)

    def is_compatible_with(self, other: "Unit") -> bool:
        """Return True if both units share the same dimension."""
        return self.dims == other.dims


def _resolve_atom(symbol: str):
    """Resolve an atomic symbol to (canonical_symbol, dimension, factor).

    Parameters
    ----------
    symbol
        Atomic unit symbol, possibly a legacy alias or a species-tagged mass.

    Returns
    -------
    resolved
        Tuple (canonical_symbol, dimension, factor).

    Raises
    ------
    UnitError
        If the symbol is not part of the vocabulary.
    """
    symbol = UNIT_ALIASES.get(symbol, symbol)
    if symbol in ATOMIC_UNITS:
        dimension, factor = ATOMIC_UNITS[symbol]
        return symbol, dimension, factor
    species_match = _SPECIES_MASS_RE.match(symbol)
    if species_match:
        prefix, species = species_match.groups()
        _, factor = ATOMIC_UNITS[prefix]
        return symbol, f"mass[{species}]", factor
    raise UnitError(
        f"Unknown unit symbol '{symbol}'. "
        f"Add it to ATOMIC_UNITS or UNIT_ALIASES in aeromaps/utils/units.py if it is legitimate."
    )


def _tokenize(text: str):
    tokens = _TOKEN_RE.findall(text)
    if "".join(tokens).replace(" ", "") != text.replace(" ", ""):
        raise UnitError(f"Cannot tokenize unit '{text}'.")
    return tokens


class _Parser:
    """Recursive-descent parser for unit expressions (left-associative * and /)."""

    def __init__(self, tokens, text):
        self.tokens = tokens
        self.pos = 0
        self.text = text

    def _peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _next(self):
        token = self._peek()
        self.pos += 1
        return token

    def parse(self):
        dims, factor = self._expr()
        if self._peek() is not None:
            raise UnitError(f"Unexpected token '{self._peek()}' in unit '{self.text}'.")
        return dims, factor

    def _expr(self):
        dims, factor = self._term()
        while self._peek() in ("*", "·", "/"):
            operator = self._next()
            rhs_dims, rhs_factor = self._term()
            sign = -1 if operator == "/" else 1
            for dimension, exponent in rhs_dims.items():
                dims[dimension] = dims.get(dimension, 0) + sign * exponent
            factor = factor * rhs_factor if sign == 1 else factor / rhs_factor
        return dims, factor

    def _term(self):
        token = self._next()
        if token is None:
            raise UnitError(f"Unexpected end of unit '{self.text}'.")
        if token == "(":
            dims, factor = self._expr()
            if self._next() != ")":
                raise UnitError(f"Missing closing parenthesis in unit '{self.text}'.")
            return dims, factor
        if token in ("*", "·", "/", ")"):
            raise UnitError(f"Unexpected token '{token}' in unit '{self.text}'.")
        _, dimension, factor = _resolve_atom(token)
        if dimension == "dimensionless":
            return {}, factor
        return {dimension: 1}, factor


@lru_cache(maxsize=None)
def parse_unit(text: str) -> Unit:
    """
    Parse a unit string into a Unit object.

    Parameters
    ----------
    text
        Unit expression, e.g. 'MJ', 'gCO2/MJ', '€/(kg/day)'.

    Returns
    -------
    unit
        Parsed Unit with dimension and conversion factor.

    Raises
    ------
    UnitError
        If the expression is empty, malformed, or uses unknown symbols.
    """
    if text is None or not str(text).strip():
        raise UnitError("Empty unit string.")
    text = str(text).strip()
    dims, factor = _Parser(_tokenize(text), text).parse()
    dims_tuple = tuple(sorted((d, e) for d, e in dims.items() if e != 0))
    return Unit(text=normalize_unit(text), dims=dims_tuple, factor=factor)


def is_valid_unit(text: str) -> bool:
    """Return True if the unit string parses against the vocabulary."""
    try:
        parse_unit(text)
        return True
    except UnitError:
        return False


def normalize_unit(text: str) -> str:
    """
    Rewrite a unit string with canonical atomic spellings, preserving structure.

    Parameters
    ----------
    text
        Unit expression, possibly using legacy aliases (e.g. 'Years', 'ton').

    Returns
    -------
    normalized
        The expression with each atom replaced by its canonical symbol.
    """
    text = str(text).strip()
    normalized_tokens = []
    for token in _tokenize(text):
        if token in ("*", "·", "/", "(", ")"):
            normalized_tokens.append(token)
        else:
            canonical, _, _ = _resolve_atom(token)
            normalized_tokens.append(canonical)
    return "".join(normalized_tokens)


def units_compatible(unit_a: str, unit_b: str) -> bool:
    """Return True if the two unit strings share the same dimension."""
    return parse_unit(unit_a).is_compatible_with(parse_unit(unit_b))


def convert_factor(from_unit: str, to_unit: str) -> float:
    """
    Multiplicative factor converting values from one unit to another.

    Parameters
    ----------
    from_unit
        Source unit string.
    to_unit
        Target unit string, must share the same dimension.

    Returns
    -------
    factor
        Value such that quantity[to_unit] = quantity[from_unit] * factor.

    Raises
    ------
    UnitError
        If the units are not commensurable.
    """
    src = parse_unit(from_unit)
    dst = parse_unit(to_unit)
    if not src.is_compatible_with(dst):
        raise UnitError(
            f"Cannot convert from '{from_unit}' ({src.dimension}) "
            f"to '{to_unit}' ({dst.dimension}): dimensions differ."
        )
    return src.factor / dst.factor


def convert(value, from_unit: str, to_unit: str):
    """
    Convert a value (scalar, numpy array or pandas Series) between units.

    Parameters
    ----------
    value
        Quantity expressed in from_unit.
    from_unit
        Source unit string.
    to_unit
        Target unit string, must share the same dimension.

    Returns
    -------
    converted
        The quantity expressed in to_unit.
    """
    return value * convert_factor(from_unit, to_unit)
