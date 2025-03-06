import os
from dataclasses import dataclass
from pathlib import Path

# Absolute path of the current file
file_absolute_path = Path(__file__).resolve().parent

@dataclass
class Config:
    excel_data_file: str = str(file_absolute_path / "../resources/data/data.xlsx")
    excel_data_information_file: str = str(file_absolute_path / "../resources/data/data_information.csv")
    parameters_json_data_file: str = str(file_absolute_path / "../resources/data/parameters.json")
    parameters_energy_carriers_data_file: str = str(file_absolute_path / "../resources/data/energy_carriers_data.yaml")
    outputs_json_data_file: str = str(file_absolute_path / "../resources/data/outputs.json")
    parameters_climate_data_file: str = str(file_absolute_path / "../resources/climate_data/temperature_historical_dataset.csv")