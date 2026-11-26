"""Test the climate model settings factory."""

from aeromaps.models.impacts.climate.climate_models_settings.settings import ClimateModelSettings
from aeromaps.models.impacts.climate.default_models.fair import FaIRModelSettings
from aeromaps.models.impacts.climate.model_settings_factory import ModelSettingsFactory


class CustomSettings(ClimateModelSettings):
    climate_model: str = "custom"


known_settings = set(["FaIR", "GWP*", "LWE", "custom", "IPCC"])
FaIRModelSettings(climate_model="fair2").register_instance()


def test_get_available_model_settings():
    """Test that the factory discover all model settings."""

    assert set(ModelSettingsFactory.get_available_model_settings_names()).issubset(known_settings)


def test_factory_discover_instances():
    """Test that the factory properly discover class instances."""

    assert "fair2" in ModelSettingsFactory.get_available_model_settings_instances()


def test_factory_create():
    """Test the creation of settings classes."""

    fair = ModelSettingsFactory().create("FaIR")
    assert isinstance(fair, FaIRModelSettings)

    fair2 = ModelSettingsFactory().create("fair2")
    assert isinstance(fair2, FaIRModelSettings)
    assert fair2.climate_model == "fair2"
