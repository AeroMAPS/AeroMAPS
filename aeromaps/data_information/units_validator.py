"""Units validator for data models."""

from aeromaps.utils.units import UnitError, parse_unit


def unit_validator(unit: str, context: str) -> str:
    """Validate a unit against the AeroMAPS unit vocabulary.
    Args:
        unit: the unit to validate.
        context: whether is a variable or pattern unit.

    Returns:
        The validated unit.

    Raises:
        UnitError if the unit is not valid.
    """
    if unit == "N/A":
        return unit

    try:
        parse_unit(unit)
    except UnitError as e:
        raise ValueError(f"Invalid unit in {context}: {e}") from e

    return unit
