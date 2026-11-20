"""Base settings for the different climate models' species."""

from pydantic import model_validator

from aeromaps.process_configuration.base_process_configuration import BaseProcessConfiguration

_SPECIES_NAME_MAPPING = {
    "NOx - ST O3 increase": "NOx_ST_O3_increase",
    "NOx - CH4 decrease and induced": "NOx_CH4_decrease_induced",
}


class BaseSpeciesSettings(BaseProcessConfiguration):
    """Base class for climate model's species settings."""

    ratio_erf_rf: float

    sensitivity_rf: float | None = None

    efficacy_erf: float | None = None


class NoxCH4DecreaseInducedSettings(BaseSpeciesSettings):
    """The settings for the NOx - CH4 decrease and induced."""

    ch4_loss_per_nox: float | None = None
    """Settings for the amount of CH4 loss per NOx"""


class SpeciesSettings(BaseProcessConfiguration):
    """Settings for the different atmospheric species."""

    CO2: BaseSpeciesSettings
    """The setting for the CO2."""

    Contrails: BaseSpeciesSettings
    """The settings for contrails."""

    H2O: BaseSpeciesSettings
    """The settings for the H2O."""

    Soot: BaseSpeciesSettings
    """The settings for soot."""

    Sulfur: BaseSpeciesSettings
    """The settings for sulfur."""

    NOx_ST_O3_increase: BaseSpeciesSettings
    """The settings for the NOx - ST O3 increase."""

    NOx_CH4_decrease_induced: NoxCH4DecreaseInducedSettings
    """The settings for the NOx - CH4 decrease and induced."""

    @model_validator(mode="before")
    @classmethod
    def normalize_species_names(cls, data):
        """Normalize species names from data files."""
        if not isinstance(data, dict):
            return data

        data = data.copy()

        for external_name, internal_name in _SPECIES_NAME_MAPPING.items():
            if external_name in data:
                data[internal_name] = data.pop(external_name)

        return data
