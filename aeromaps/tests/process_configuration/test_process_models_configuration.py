"""Test module for process models configuration."""

import pytest

from aeromaps.process_configuration.process_models_configuration import ProcessModelsConfiguration


def test_invalid_standar_model():
    """Test that an error is raised if a non valid standard model is given."""
    with pytest.raises(ValueError, match="The model foo doesn't correspond to any standard model"):
        ProcessModelsConfiguration(standards=["foo"])
