from dataclasses import dataclass
import os.path as pth
import pandas as pd
from aeromaps.utils.functions import _dict_from_json

filename = pth.join(
    pth.dirname(pth.abspath(__file__)), "..", "..", "resources", "data", "parameters.json"
)

data = _dict_from_json(file_name=filename)


@dataclass
class ImpactsParameters(object):

    # CO2 emission factor [gCO2/MJ]
    kerosene_emission_factor_2019: float = 87.5  # Global (direct emissions: 73.2)

    # NOx emission index in 2019 [kg_NOx/kg_fuel]
    emission_index_nox_biofuel_2019: float = 0.01514
    emission_index_nox_electrofuel_2019: float = 0.01514
    emission_index_nox_kerosene_2019: float = 0.01514
    emission_index_nox_hydrogen_2019: float = 0.007

    # Other emission index [kg/kg_fuel]
    emission_index_soot_biofuel: float = 3e-5
    emission_index_soot_electrofuel: float = 3e-5
    emission_index_soot_kerosene: float = 3e-5
    emission_index_soot_hydrogen: float = 0.0
    emission_index_h2o_biofuel: float = 1.231
    emission_index_h2o_electrofuel: float = 1.231
    emission_index_h2o_kerosene: float = 1.231
    emission_index_h2o_hydrogen: float = 9.0
    emission_index_sulfur_biofuel: float = 0.0
    emission_index_sulfur_electrofuel: float = 0.0
    emission_index_sulfur_kerosene: float = 0.0012
    emission_index_sulfur_hydrogen: float = 0.0

    # LHV [MJ/kg]
    lhv_kerosene: float = 44
    lhv_biofuel: float = 44
    lhv_electrofuel: float = 44
    lhv_hydrogen: float = 120

    # ERF coefficients
    erf_coefficient_soot: float = 100.7
    erf_coefficient_co2: float = 0.88
    erf_coefficient_contrails: float = 1.058e-09
    erf_coefficient_h2o: float = 0.0052
    erf_coefficient_nox: float = 11.55 * 0.304348  # Convertir directement de N à NOx !
    erf_coefficient_sulfur: float = -19.9
    direct_co2_erf_2018_reference: float = 30.184

    # Temperature
    temperature_increase_from_aviation_init: pd.Series = data[
        "temperature_increase_from_aviation_init"
    ]  # [°C] Using Grewe et al. (2021)
    TCRE: float = 0.00045  # [°C/GtCO2]
