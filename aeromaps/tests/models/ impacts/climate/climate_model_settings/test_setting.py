"""Test for the climate model settings."""

import pytest

from aeromaps.models.impacts.climate.climate_models_settings.default_model_loader import (
    load_default_climate_model_settings,
)
from aeromaps.models.impacts.climate.climate_models_settings.settings import ClimateModelSettings


@pytest.mark.parametrize("model_name", ["FaIR", "GWP*", "IPCC", "LWE"])
def test_default_models_loader(model_name):
    """Test the settings loader function."""

    settings = load_default_climate_model_settings(model_name)

    assert isinstance(settings, ClimateModelSettings)


def test_error_for_wrong_default_model_name():
    """Test that an error is raised when a wrong default error name is given."""

    with pytest.raises(ValueError, match=r"Unknown climate model: .+, available models are:"):
        load_default_climate_model_settings("foo")
