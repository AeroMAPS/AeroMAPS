"""AeroMAPS process data configuration models."""

from pathlib import Path
from aeromaps.process_configuration.base_process_configuration import BaseProcessConfiguration


class ProcessDataInputs(BaseProcessConfiguration):
    json_inputs_file: Path | str | None = "./parameters.json"
    partitioning_data_file: Path | str | None = "./partitioning_inputs.json"
    csv_data_information_file: Path | str | None = "./data_information.csv"


class ProcessDataOutputs(BaseProcessConfiguration):
    json_outputs_file: Path | str | None = "./outputs.json"
    excel_outputs_file: Path | str | None = "./data.xlsx"


class ProcessDataConfiguration(BaseProcessConfiguration):
    inputs: ProcessDataInputs = ProcessDataInputs()
    outputs: ProcessDataOutputs = ProcessDataOutputs()
