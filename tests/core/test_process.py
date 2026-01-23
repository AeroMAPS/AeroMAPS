"""
Test module for AeroMAPS process.

This module tests the AeroMAPSProcess class functionality.
"""

import pytest
from aeromaps import create_process


def test_process_creation():
    """Test that the process can be created successfully."""
    proc = create_process()
    assert proc is not None


def test_process_compute():
    """Test that the process can be computed successfully."""
    proc = create_process()
    proc.compute()
    assert proc.data is not None
    assert hasattr(proc, 'data')


def test_process_has_parameters():
    """Test that the process has parameters after creation."""
    proc = create_process()
    assert hasattr(proc, 'parameters')


def test_process_has_models():
    """Test that the process has models after creation."""
    proc = create_process()
    assert hasattr(proc, 'models')
