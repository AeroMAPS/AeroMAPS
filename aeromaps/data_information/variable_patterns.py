"""Pydantic model for variable patterns."""

import re

from pydantic import BaseModel, PrivateAttr, ValidationInfo, field_validator, model_validator

from aeromaps.data_information.units_validator import unit_validator


def _glob_to_regex(pattern: str) -> re.Pattern:
    """Translate a glob pattern with ``*`` wildcards into a capturing regex."""
    parts = pattern.split("*")
    regex = "(.*)".join(re.escape(part) for part in parts)
    return re.compile(f"^{regex}$")


class VariablePattern(BaseModel):
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

    pattern: str
    unit: str | None
    description: str
    source: str | None = None
    _regex: re.Pattern = PrivateAttr()

    @field_validator("unit")
    @classmethod
    def validate_unit(cls, value: str, info: ValidationInfo) -> str:
        """Validate units and atomize them to their corresponding unit."""
        pattern = info.data.get("pattern")
        return unit_validator(value, f"pattern '{pattern}'")

    @model_validator(mode="after")
    def compile_regex(self):
        self._regex = _glob_to_regex(self.pattern)
        return self
