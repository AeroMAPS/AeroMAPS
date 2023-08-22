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


    ### COSTS ###
    # Hydrogen Cost parameters
    hydrogen_replacement_ratio: float =1.0


    # Electrolysis CAPEX (€ / (kg/day)
    electrolyser_capex_2020: float = 588.0
    electrolyser_capex_2030: float = 459.0
    electrolyser_capex_2040: float = 433.0
    electrolyser_capex_2050: float = 419.0

    # Electrolysis Opex (€ / (kg/day) /year and €/kg

    electrolyser_fixed_opex_2020: float = 21.3
    electrolyser_fixed_opex_2030: float = 20.57
    electrolyser_fixed_opex_2040: float = 20.25
    electrolyser_fixed_opex_2050: float = 20.04
    electrolyser_var_opex_2020: float = 0.20
    electrolyser_var_opex_2030: float = 0.19
    electrolyser_var_opex_2040: float = 0.18
    electrolyser_var_opex_2050: float = 0.18

    # Electrolysis Specific Electricity (kWh/kg)
    electrolyser_specific_electricity_2020: float = 51.0
    electrolyser_specific_electricity_2030: float = 49.3
    electrolyser_specific_electricity_2040: float = 48.5
    electrolyser_specific_electricity_2050: float = 48.0

    # Liquefier Capex (€/ (kg/day))
    liquefier_capex_2020: float = 1457.33
    liquefier_capex_2030: float = 1457.33
    liquefier_capex_2040: float = 1457.33
    liquefier_capex_2050: float = 1457.33

    # Liquefier sp. electricity (kWh/kg)
    liquefier_specific_electricity_2020: float = 7.54
    liquefier_specific_electricity_2030: float = 7.54
    liquefier_specific_electricity_2040: float = 7.54
    liquefier_specific_electricity_2050: float = 7.54

    # Electrofuel plant capex € / (kg/day)
    electrofuel_capex_2020: float = 2311
    electrofuel_capex_2030: float = 2311
    electrofuel_capex_2040: float = 2311
    electrofuel_capex_2050: float = 2311

    # Electrofuel plant Opex (€ / (kg/day) /year
    electrofuel_fixed_opex_2020: float = 0.0
    electrofuel_fixed_opex_2030: float = 0.0
    electrofuel_fixed_opex_2040: float = 0.0
    electrofuel_fixed_opex_2050: float = 0.0

    # €/kg
    electrofuel_var_opex_2020: float = 0.38
    electrofuel_var_opex_2030: float = 0.38
    electrofuel_var_opex_2040: float = 0.38
    electrofuel_var_opex_2050: float = 0.38

    # Electrofuel plant specific electricity (kWh/kg)

    electrofuel_specific_electricity_2020: float = 22.9
    electrofuel_specific_electricity_2030: float = 22.9
    electrofuel_specific_electricity_2040: float = 22.9
    electrofuel_specific_electricity_2050: float = 22.9

    # Electrofuel plant specific co2 (kg/kg)
    electrofuel_specific_co2_2020: float = 4.47
    electrofuel_specific_co2_2030: float = 4.47
    electrofuel_specific_co2_2040: float = 4.47
    electrofuel_specific_co2_2050: float = 4.47

    # Electricity market price (€/kWh)

    electricity_cost_2020: float = 0.08
    electricity_cost_2030: float = 0.08
    electricity_cost_2040: float = 0.08
    electricity_cost_2050: float = 0.08

    # Electricity load factor

    electricity_load_factor: float = 0.95

    # CO2 DAC market price (€/kg)

    co2_cost_2020: float = 0.225
    co2_cost_2030: float = 0.225
    co2_cost_2040: float = 0.225
    co2_cost_2050: float = 0.225

    # CO2 tax level (€/ton)

    co2_tax_2020: float = 0
    co2_tax_2030: float = 0
    co2_tax_2040: float = 0
    co2_tax_2050: float = 0

    ### Kerosene

    # €/L

    kerosene_price_2020: float = 0.41
    kerosene_price_2030: float = 0.41
    kerosene_price_2040: float = 0.41
    kerosene_price_2050: float = 0.41

    ### Biofuel

    # €/L

    biofuel_hefa_fog_mfsp_2020: float = 0.89
    biofuel_hefa_fog_mfsp_2050: float = 0.89
    biofuel_hefa_others_mfsp_2020: float = 1.08
    biofuel_hefa_others_mfsp_2050: float = 1.08
    biofuel_ft_others_mfsp_2020: float = 0.54 * 1.02 + 0.46 * 1.28
    biofuel_ft_others_mfsp_2050: float = 0.54 * 1.02 + 0.46 * 1.28
    biofuel_ft_msw_mfsp_2020: float = 1.02
    biofuel_ft_msw_mfsp_2050: float = 1.02
    biofuel_atj_mfsp_2020: float = 1.42
    biofuel_atj_mfsp_2050: float = 1.42

    # €/kg/day
    biofuel_hefa_fog_capex_2020: float = 307.0
    biofuel_hefa_fog_capex_2050: float = 307.0
    biofuel_hefa_others_capex_2020: float = 276.0
    biofuel_hefa_others_capex_2050: float = 276.0
    biofuel_ft_others_capex_2020: float = 1601 * 0.54 + 2192 * 0.46
    biofuel_ft_others_capex_2050: float = 1601 * 0.54 + 2192 * 0.46
    biofuel_ft_msw_capex_2020: float = 2056.0
    biofuel_ft_msw_capex_2050: float = 2056.0
    biofuel_atj_capex_2020: float = 1211.0
    biofuel_atj_capex_2050: float = 1212.0

    # Economic analyses
    social_discount_rate: float = 0.03
