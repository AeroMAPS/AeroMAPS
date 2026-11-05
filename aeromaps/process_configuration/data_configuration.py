"""AeroMAPS process data configuration models."""

from pathlib import Path
from aeromaps.process_configuration.base_process_configuration import BaseProcessConfiguration


class ProcessDataInputs(BaseProcessConfiguration):
    data_information_file: Path | str | None = Path("./data_information.yaml")
    json_inputs_file: Path | str | None = Path("./parameters.json")
    partitioning_data_file: Path | str | None = Path("./partitioning_inputs.json")


class ProcessDataOutputs(BaseProcessConfiguration):
    json_outputs_file: Path | str | None = Path("./outputs.json")
    excel_outputs_file: Path | str | None = Path("./data.xlsx")


class ProcessDataConfiguration(BaseProcessConfiguration):
    inputs: ProcessDataInputs = ProcessDataInputs()
    outputs: ProcessDataOutputs = ProcessDataOutputs()
