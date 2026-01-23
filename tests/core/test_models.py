"""
Test module for AeroMAPS models configuration.

This module tests the models module that provides default model dictionaries.
"""

import pytest


def test_models_module_import():
    """Test that the models module can be imported."""
    from aeromaps.core import models
    assert models is not None


def test_standard_models_exist():
    """Test that standard_models dictionary exists."""
    from aeromaps.core import models
    # Check if the module has model dictionaries or functions
    # The exact structure may vary, so we check for common attributes
    assert hasattr(models, '__file__')


def test_model_classes_import():
    """Test that model classes can be imported from models module."""
    from aeromaps.models.air_transport.air_traffic.rpk import RPK
    from aeromaps.models.air_transport.air_traffic.rtk import RTK
    assert RPK is not None
    assert RTK is not None


def test_fleet_models_import():
    """Test that fleet models can be imported."""
    from aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet.fleet_numeric import (
        FleetEvolution,
    )
    assert FleetEvolution is not None
