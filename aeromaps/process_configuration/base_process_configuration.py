"""AeroMAPS process base configuration model."""

from pydantic import BaseModel, ConfigDict


class BaseProcessConfiguration(BaseModel):
    """Base data model for `AeroMAPSProcess`' configuration."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)
