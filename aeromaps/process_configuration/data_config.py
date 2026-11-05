"""AeroMAPS process data configuration models."""

from pathlib import Path
from aeromaps.process_configuration.base_config import BaseConfig


class DataInputs(BaseConfig):
    data_information_file: Path | str = Path("./data_information.yaml")
    json_inputs_file: Path | str = Path("./parameters.json")
    partitioning_data_file: Path | str = Path("./partitioning_inputs.json")


class DataOutputs(BaseConfig):
    json_outputs_file: Path | str = Path("./outputs.json")
    excel_outputs_file: Path | str = Path("./data.xlsx")


class DataConfig(BaseConfig):
    inputs: DataInputs
    outputs: DataOutputs
