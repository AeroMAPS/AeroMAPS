"""AeroMAPS process data configuration models."""

from pathlib import Path
import warnings

from pydantic import model_validator
from aeromaps.process_configuration.base_process_configuration import BaseProcessConfiguration


class ProcessDataInputs(BaseProcessConfiguration):
    """The process' inputs configuration."""

    json_inputs_file: Path | str | None | list[str | Path] = "./parameters.json"
    """The process' json inputs file path, either relative or absolute."""

    partitioning_data_file: Path | str | None = "./partitioning_inputs.json"
    """The process' the partitioning data file path, either relative or absolute."""

    csv_data_information_file: Path | str | None = None
    """The legacy process' the data information csv file path, either relative or absolute.

    !!! warning
     This field is depreciated and will be remove in a future version of AeroMAPS.
    """

    data_information_file: Path | str | None = "./data_information.yaml"
    """The process' the data information file path, either relative or absolute."""

    partitioning_other_data_file: Path | str | None = None
    """The process' other partitioning data file path, either relative or absolute."""

    partitioning_climate_data_file: Path | str | None = None
    """The process' the partitioning climate data file path, either relative or absolute."""

    @model_validator(mode="before")
    @classmethod
    def set_data_information_file_if_csv_is_set(cls, data):
        if isinstance(data, dict) and data.get("csv_data_information_file"):
            data["data_information_file"] = data.pop("csv_data_information_file")
            warnings.warn(
                "The 'csv_data_information_file' configuration key is deprecated. "
                "Use 'data_information_file' with a YAML file instead.",
                DeprecationWarning,
            )
        return data


class ProcessDataOutputs(BaseProcessConfiguration):
    """The process' outputs configuration."""

    json_outputs_file: Path | str | None = "./outputs.json"
    """The process' json outputs file path, either relative or absolute."""

    excel_outputs_file: Path | str | None = "./data.xlsx"
    """The process' excel outputs file path, either relative or absolute."""


class ProcessDataConfiguration(BaseProcessConfiguration):
    """The process' data (inputs and outputs) configuration."""

    inputs: ProcessDataInputs = ProcessDataInputs()
    """The process' inputs configuration."""

    outputs: ProcessDataOutputs = ProcessDataOutputs()
    """The process' output configuration."""
