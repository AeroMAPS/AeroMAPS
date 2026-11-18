"""AeroMAPS process data configuration models."""

from pathlib import Path
from aeromaps.process_configuration.base_process_configuration import BaseProcessConfiguration


class ProcessDataInputs(BaseProcessConfiguration):
    """The inputs configuration of the process."""

    json_inputs_file: Path | str | None | list[str | Path] = "./parameters.json"
    """The json inputs file path of the process, either relative or absolute. Contains
    the scenario parameters: scalars and year-indexed vectors.
    """

    partitioning_data_file: Path | str | None = "./partitioning_inputs.json"
    """The optional partitioning data file path of the process, either relative or absolute.
    Year-indexed inputs to partition a global scenario into a subs-scope(region,segment..).
    Omit for a plain global run.
    """

    csv_data_information_file: Path | str | None = "./data_information.csv"
    """The optional data information file path of the process, either relative or absolute.
    Contains inputs metadata (units and description), used for display.
    """

    partitioning_other_data_file: Path | str | None = None
    """The other partitioning data file path process, either relative or absolute."""

    partitioning_climate_data_file: Path | str | None = None
    """The optional partitioning climate data file path of the process, either relative or absolute.
    Historical temperature csv. Falls back to the packaged dataset.
    """


class ProcessDataOutputs(BaseProcessConfiguration):
    """The outputs configuration of the process."""

    json_outputs_file: Path | str | None = "./outputs.json"
    """The json outputs file path of the process, either relative or absolute."""

    excel_outputs_file: Path | str | None = "./data.xlsx"
    """The excel outputs file path of the process, either relative or absolute."""


class ProcessDataConfiguration(BaseProcessConfiguration):
    """The data (inputs and outputs) configuration of the process."""

    inputs: ProcessDataInputs = ProcessDataInputs()
    """The inputs configuration of the process."""

    outputs: ProcessDataOutputs = ProcessDataOutputs()
    """The output configuration process."""
