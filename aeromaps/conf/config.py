from dataclasses import dataclass

@dataclass
class Config:
    excel_data_file: str = ""
    excel_data_information_file: str = ""
    parameters_json_data_file: str = ""
    parameters_energy_carriers_data_file: str = ""
    outputs_json_data_file: str = ""
    parameters_climate_data_file: str = ""