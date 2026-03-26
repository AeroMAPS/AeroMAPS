"""
Test module for AeroMAPS GEMSEO integration.

This module tests the GEMSEO wrapper classes and data conversion functionality.
"""

import numpy as np
import pandas as pd
from gemseo.core.grammars.simple_grammar import SimpleGrammar

from aeromaps.core.gemseo import CustomDataConverter, AeroMAPSAutoModelWrapper
from aeromaps.models.base import AeroMAPSModel


class DummyModel(AeroMAPSModel):
    """A dummy model for testing wrapper functionality."""
    
    def __init__(self):
        super().__init__(name="DummyModel")

    def compute(self, x: float=4.0, y: float=3.0) -> tuple[float, float]:
        """Simple computation for testing."""
        z = x + y
        product = x * y

        return z, product


def test_custom_data_converter_float():
    """Test CustomDataConverter handles float values correctly."""
    grammar = SimpleGrammar("dummy")
    grammar.update_from_types({"test_float": float})
    converter = CustomDataConverter(grammar)
    
    # Test float conversion to array
    value = 5.0
    array = converter.convert_value_to_array("test_float", value)
    assert isinstance(array, np.ndarray)
    assert array == 5.0
    
    # Test array back to value (floats go through default conversion)
    result = converter.convert_array_to_value("test_float", array)
    # For floats, the result should be a scalar
    assert result == 5.0


def test_custom_data_converter_list():
    """Test CustomDataConverter handles list values correctly."""
    grammar = SimpleGrammar("dummy")
    grammar.update_from_types({"test_list": list})
    converter = CustomDataConverter(grammar)
    
    # Test list conversion to array
    value = [1.0, 2.0, 3.0]
    array = converter.convert_value_to_array("test_list", value)
    assert isinstance(array, np.ndarray)
    assert np.array_equal(array, np.array([1.0, 2.0, 3.0]))
    assert "test_list" in converter._list_names
    
    # Test array back to list - must be in a single conversion cycle
    # The converter tracks the name during convert_value_to_array
    result = converter.convert_array_to_value("test_list", array)
    assert isinstance(result, list)
    assert result == [1.0, 2.0, 3.0]


def test_custom_data_converter_pandas_series():
    """Test CustomDataConverter handles pandas Series correctly."""
    converter = CustomDataConverter(SimpleGrammar("dummy"))
    
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
    converter = CustomDataConverter(SimpleGrammar("dummy"))
    
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
    converter = CustomDataConverter(SimpleGrammar("dummy"))
    
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

    assert all(key in wrapper.input_grammar.names for key in ["x", "y"])
    assert all(key in wrapper.output_grammar.names for key in ["z", "product"])

    assert all(wrapper.input_grammar[key] == float for key in ["x", "y"])
    assert all(wrapper.output_grammar[key] == float for key in ["z", "product"])


def test_auto_model_wrapper_execution():
    """Test AeroMAPSAutoModelWrapper executes with changing inputs."""
    model = DummyModel()
    wrapper = AeroMAPSAutoModelWrapper(model)
    
    # Execute with first set of inputs (as floats, not arrays)
    wrapper.execute({"x": 2.0, "y": 3.0})
    z1 = wrapper.get_output_data()["z"]
    product1 = wrapper.get_output_data()["product"]
    
    # Results may be arrays, so convert to float for comparison
    z1_val = float(z1) if hasattr(z1, '__iter__') and not isinstance(z1, str) else float(z1)
    product1_val = float(product1) if hasattr(product1, '__iter__') and not isinstance(product1, str) else float(product1)
    
    assert z1_val == 5.0  # 2 + 3
    assert product1_val == 6.0  # 2 * 3
    
    # Execute with different inputs
    wrapper.execute({"x": 4.0, "y": 5.0})
    z2 = wrapper.get_output_data()["z"]
    product2 = wrapper.get_output_data()["product"]
    
    z2_val = float(z2) if hasattr(z2, '__iter__') and not isinstance(z2, str) else float(z2)
    product2_val = float(product2) if hasattr(product2, '__iter__') and not isinstance(product2, str) else float(product2)
    
    assert z2_val == 9.0  # 4 + 5
    assert product2_val == 20.0  # 4 * 5
    
    # Verify outputs changed
    assert z1_val != z2_val
    assert product1_val != product2_val
