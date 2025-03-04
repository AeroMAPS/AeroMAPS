from dataclasses import dataclass

@dataclass
class Config:
    EXCEL_DATA_FILE: str = ""
    EXCEL_DATA_INFORMATION_FILE: str = ""
    PARAMETERS_JSON_DATA_FILE: str = ""
    PARAMETERS_ENERGY_CARRIERS_DATA_FILE: str = ""
    OUTPUTS_JSON_DATA_FILE: str = ""
    PARAMETERS_CLIMATE_DATA_FILE: str = ""