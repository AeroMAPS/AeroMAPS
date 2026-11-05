"""AeroMAPS process data configuration models."""

from pathlib import Path
from aeromaps.process_configuration.base_process_configuration import BaseProcessConfiguration


class ProcessDataInputs(BaseProcessConfiguration):
    data_information_file: Path = Path("./data_information.yaml")
    json_inputs_file: Path = Path("./parameters.json")
    partitioning_data_file: Path = Path("./partitioning_inputs.json")


class ProcessDataOutputs(BaseProcessConfiguration):
    json_outputs_file: Path = Path("./outputs.json")
    excel_outputs_file: Path = Path("./data.xlsx")


class ProcessDataConfiguration(BaseProcessConfiguration):
    inputs: ProcessDataInputs = ProcessDataInputs()
    outputs: ProcessDataOutputs = ProcessDataOutputs()
