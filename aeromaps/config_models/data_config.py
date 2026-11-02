"""AeroMAPS process data configuration models."""

from pathlib import Path
from aeromaps.config_models.base_config import BaseConfig


class DataInputs(BaseConfig):
    data_information_file: Path = Path("./data_information.yaml")
    json_inputs_file: Path = Path("./parameters.json")
    partitioning_data_file: Path = Path("./partitioning_inputs.json")


class DataOutputs(BaseConfig):
    json_outputs_file: Path = Path("./outputs.json")
    excel_outputs_file: Path = Path("./data.xlsx")


class DataConfig(BaseConfig):
    inputs: DataInputs
    outputs: DataOutputs
