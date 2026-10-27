"""Pydantic model for variables metadata."""

from pydantic import BaseModel, ValidationInfo, field_validator

from aeromaps.data_information.units_validator import unit_validator


class Variable(BaseModel):
    """A data model for AeroMAPS variables.

    Fields
    ----------
    variable_name: str
        The name of the variable
    unit: str
        String representation of the unit

    description: str
        The variable's description

    source: str | None = None
        The source of the variable if any.
    """

    variable_name: str
    unit: str
    description: str
    source: str | None = None

    @field_validator("unit")
    @classmethod
    def validate_unit(cls, value: str, info: ValidationInfo) -> str:
        """Validate units and atomize them to their corresponding unit."""
        name = info.data.get("variable_name")
        if str(value) == "N/A":
            return str(value)
        return unit_validator(value, f"  - variable '{name}'")
