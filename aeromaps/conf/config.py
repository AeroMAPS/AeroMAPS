from pathlib import Path
from dataclasses import dataclass

BASE_DIR = Path(__file__).resolve().parent.parent

@dataclass
class Config:
    excel_data_file: Path = BASE_DIR / "resources" / "data" / "data.xlsx"
    excel_data_information_file: Path = BASE_DIR / "resources" / "data" / "data_information.csv"
    parameters_json_data_file: Path = BASE_DIR / "resources" / "data" / "parameters.json"
    parameters_energy_carriers_data_file: Path = BASE_DIR / "resources" / "data" / "energy_carriers_data.yaml"
    outputs_json_data_file: Path = BASE_DIR / "resources" / "data" / "outputs.json"
    parameters_climate_data_file: Path = BASE_DIR / "resources" / "climate_data" / "temperature_historical_dataset.csv"