"""Base AeroMAPSModel tests."""

from aeromaps.models.base import AeroMAPSModel
import pytest


class DummySubClassWithNoCompute(AeroMAPSModel):
    """Dummy AeroMAPSModel subclass for testing."""

    def __init__(self, name, parameters=None, model_type="auto"):
        super().__init__(name, parameters, model_type)


class DummyClassWithCompute(DummySubClassWithNoCompute):
    def compute(self, input_data):
        return input_data


def test_base_class_instantiation_error():
    """Test that the base class itself cannot be instantiated."""
    with pytest.raises(
        TypeError,
        match="Can't instantiate abstract class AeroMAPSModel with abstract method compute",
    ):
        AeroMAPSModel(name="model")


def test_error_for_subclass_without_compute():
    """Test that an error is raise when a AeroMAPSModel subclass doesn't implement the compute method."""

    with pytest.raises(
        TypeError,
        match="Can't instantiate abstract class DummySubClassWithNoCompute with abstract method compute",
    ):
        DummySubClassWithNoCompute(name="model")


def test_concrete_class_instantiation():
    """Test that a class with it's compute method can be instantiated."""
    dummy = DummyClassWithCompute(name="model")
    input_data = {"x": 1, "y": 1}
    assert hasattr(dummy, "compute")
    assert input_data == dummy.compute(input_data)
