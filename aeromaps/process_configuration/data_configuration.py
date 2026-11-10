"""AeroMAPS process data configuration models."""

from pathlib import Path
from aeromaps.process_configuration.base_process_configuration import BaseProcessConfiguration


class ProcessDataInputs(BaseProcessConfiguration):
    """The process' inputs configuration."""

    json_inputs_file: Path | str | None | list[str | Path] = "./parameters.json"
    """The process' json inputs file path, either relative or absolute."""

    partitioning_data_file: Path | str | None = "./partitioning_inputs.json"
    """The process' the partitioning data file path, either relative or absolute."""

    csv_data_information_file: Path | str | None = "./data_information.csv"
    """The process' the data information file path, either relative or absolute."""

    partitioning_other_data_file: Path | str | None = None
    """The process' other partitioning data file path, either relative or absolute."""

    partitioning_climate_data_file: Path | str | None = None
    """The process' the partitioning climate data file path, either relative or absolute."""


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
