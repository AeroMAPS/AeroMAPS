"""
Test module for AeroMAPS GEMSEO integration.

This module tests the GEMSEO wrapper classes and integration.
"""

import pytest


def test_custom_data_converter_import():
    """Test that CustomDataConverter can be imported."""
    from aeromaps.core.gemseo import CustomDataConverter
    assert CustomDataConverter is not None


def test_auto_model_wrapper_import():
    """Test that AeroMAPSAutoModelWrapper can be imported."""
    from aeromaps.core.gemseo import AeroMAPSAutoModelWrapper
    assert AeroMAPSAutoModelWrapper is not None


def test_custom_model_wrapper_import():
    """Test that AeroMAPSCustomModelWrapper can be imported."""
    from aeromaps.core.gemseo import AeroMAPSCustomModelWrapper
    assert AeroMAPSCustomModelWrapper is not None


def test_extended_json_grammar_import():
    """Test that ExtendedJSONGrammar can be imported."""
    from aeromaps.core.gemseo import ExtendedJSONGrammar
    assert ExtendedJSONGrammar is not None
