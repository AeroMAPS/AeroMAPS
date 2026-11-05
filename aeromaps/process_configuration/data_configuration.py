"""AeroMAPS process data configuration models."""

from pathlib import Path
from aeromaps.process_configuration.base_process_configuration import BaseConfig


class ProcessDataInputs(BaseConfig):
    data_information_file: Path | str = Path("./data_information.yaml")
    json_inputs_file: Path | str = Path("./parameters.json")
    partitioning_data_file: Path | str = Path("./partitioning_inputs.json")


class ProcessDataOutputs(BaseConfig):
    json_outputs_file: Path | str = Path("./outputs.json")
    excel_outputs_file: Path | str = Path("./data.xlsx")


class ProcessDataConfiguration(BaseConfig):
    inputs: ProcessDataInputs = ProcessDataInputs()
    outputs: ProcessDataOutputs = ProcessDataOutputs()
