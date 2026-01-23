"""
Test module for AeroMAPS GEMSEO integration.

This module tests the GEMSEO wrapper classes and data conversion functionality.
"""

import pytest
import numpy as np
import pandas as pd
from aeromaps.core.gemseo import CustomDataConverter, AeroMAPSAutoModelWrapper
from aeromaps.models.base import AeroMAPSModel


class DummyModel(AeroMAPSModel):
    """A dummy model for testing wrapper functionality."""
    
    def __init__(self):
        super().__init__()
        self.name = "DummyModel"
    
    def compute(self, x: float, y: float) -> dict:
        """Simple computation for testing."""
        return {"z": x + y, "product": x * y}


def test_custom_data_converter_float():
    """Test CustomDataConverter handles float values correctly."""
    converter = CustomDataConverter()
    
    # Test float conversion to array
    value = 5.0
    array = converter.convert_value_to_array("test_float", value)
    assert isinstance(array, np.ndarray)
    assert array == 5.0
    
    # Test array back to value
    result = converter.convert_array_to_value("test_float", array)
    assert result == 5.0


def test_custom_data_converter_list():
    """Test CustomDataConverter handles list values correctly."""
    converter = CustomDataConverter()
    
    # Test list conversion to array
    value = [1.0, 2.0, 3.0]
    array = converter.convert_value_to_array("test_list", value)
    assert isinstance(array, np.ndarray)
    assert np.array_equal(array, np.array([1.0, 2.0, 3.0]))
    assert "test_list" in converter._list_names
    
    # Test array back to list
    result = converter.convert_array_to_value("test_list", array)
    assert isinstance(result, list)
    assert result == [1.0, 2.0, 3.0]


def test_custom_data_converter_pandas_series():
    """Test CustomDataConverter handles pandas Series correctly."""
    converter = CustomDataConverter()
    
    # Test pandas Series conversion to array
    index = pd.Index([2020, 2030, 2040])
    value = pd.Series([10.0, 20.0, 30.0], index=index, name="test_series")
    array = converter.convert_value_to_array("test_series", value)
    
    assert isinstance(array, np.ndarray)
    assert np.array_equal(array, np.array([10.0, 20.0, 30.0]))
    assert "test_series" in converter._series_names
    assert "test_series" in converter._series_indexes
    
    # Test array back to pandas Series
    result = converter.convert_array_to_value("test_series", array)
    assert isinstance(result, pd.Series)
    assert result.name == "test_series"
    assert result.index.equals(index)
    assert np.array_equal(result.values, np.array([10.0, 20.0, 30.0]))


def test_custom_data_converter_nan_handling():
    """Test CustomDataConverter handles NaN values correctly."""
    converter = CustomDataConverter()
    
    # Test pandas Series with NaN
    value = pd.Series([10.0, np.nan, 30.0], index=[2020, 2030, 2040])
    array = converter.convert_value_to_array("test_nan", value)
    
    # NaN should be converted to -999999
    assert array[1] == -999999
    
    # Test conversion back (should restore NaN)
    result = converter.convert_array_to_value("test_nan", array)
    assert np.isnan(result.iloc[1])


def test_custom_data_converter_value_size():
    """Test get_value_size method for different data types."""
    converter = CustomDataConverter()
    
    # Test scalar
    assert converter.get_value_size("scalar", 5.0) == 1
    
    # Test list
    assert converter.get_value_size("list", [1.0, 2.0, 3.0]) == 3
    
    # Test array
    assert converter.get_value_size("array", np.array([1.0, 2.0, 3.0, 4.0])) == 4


def test_auto_model_wrapper_creation():
    """Test AeroMAPSAutoModelWrapper can wrap a model."""
    model = DummyModel()
    wrapper = AeroMAPSAutoModelWrapper(model)
    
    assert wrapper is not None
    assert wrapper.name == "DummyModel"
    assert wrapper.model is model


def test_auto_model_wrapper_inputs_outputs():
    """Test AeroMAPSAutoModelWrapper correctly identifies inputs and outputs."""
    model = DummyModel()
    wrapper = AeroMAPSAutoModelWrapper(model)
    
    # Check that wrapper has inputs and outputs based on compute signature
    assert len(wrapper.input_grammar) > 0
    assert len(wrapper.output_grammar) > 0


def test_auto_model_wrapper_execution():
    """Test AeroMAPSAutoModelWrapper executes with changing inputs."""
    model = DummyModel()
    wrapper = AeroMAPSAutoModelWrapper(model)
    
    # Execute with first set of inputs
    wrapper.execute({"x": np.array([2.0]), "y": np.array([3.0])})
    z1 = wrapper.get_output_data()["z"]
    product1 = wrapper.get_output_data()["product"]
    
    assert z1 == 5.0  # 2 + 3
    assert product1 == 6.0  # 2 * 3
    
    # Execute with different inputs
    wrapper.execute({"x": np.array([4.0]), "y": np.array([5.0])})
    z2 = wrapper.get_output_data()["z"]
    product2 = wrapper.get_output_data()["product"]
    
    assert z2 == 9.0  # 4 + 5
    assert product2 == 20.0  # 4 * 5
    
    # Verify outputs changed
    assert z1 != z2
    assert product1 != product2
