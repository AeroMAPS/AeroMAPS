"""AeroMAPS process base configuration model."""

from pydantic import BaseModel, ConfigDict


class BaseProcessConfiguration(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)
