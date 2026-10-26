from pydantic import BaseModel


class Variable(BaseModel):
    """A data model for AeroMAPS variables.

    Fields
    ----------
    unit: str
        String representation of the unit

    description: str
        The variable's description

    source: str | None = None
        The source of the variable if any.
    """

    unit: str | None
    description: str
    source: str | None = None

    # TODO: To convert to pint based unit registry for units validation.
    # @field_validator("unit")
    # @classmethod
    # def validate_unit(cls, value:str) -> str:
    #     """Validate units and atomize them to their corresponding unit."""
    #     ureg = AeroMAPSUnitRegistry()

    #     return ureg.normalize_unit(value)
