"""Process configuration test module."""

import pytest

from aeromaps.process_configuration.process_configuration import AeroMAPSProcessConfiguration


def test_warning_csv_data_information_file_key():
    """Test that a warning is raised when passing a legacy `csv_data_information_file` key to the configuration."""
    config = AeroMAPSProcessConfiguration()
    with pytest.warns(
        DeprecationWarning,
        match="The 'csv_data_information_file' configuration key is deprecated. "
        "Use 'data_information_file' with a YAML file instead.",
    ):
        config.data.inputs.csv_data_information_file = "file.csv"


def test_warning_for_csv_data_information_file():
    config = AeroMAPSProcessConfiguration()
    with pytest.warns(
        DeprecationWarning,
        match="`.csv` format data information file is deprecated. Use a YAML file instead.",
    ):
        config.data.inputs.data_information_file = "file.csv"
