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

    # Soot emission index in 2019 [kg_BC/kg_fuel]
    emission_index_soot_biofuel_2019: float = 6e-6
    emission_index_soot_electrofuel_2019: float = 6e-6
    emission_index_soot_kerosene_2019: float = 3e-5
    emission_index_soot_hydrogen_2019: float = 0.0

    # Other emission index [kg/kg_fuel]
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
    hydrogen_replacement_ratio: float = 1.0

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

    # Deprecated since move to efficiency, might be reactivated
    # Electrolysis Specific Electricity (kWh/kg)
    # electrolyser_specific_electricity_2020: float = 51.0
    # electrolyser_specific_electricity_2030: float = 49.3
    # electrolyser_specific_electricity_2040: float = 48.5
    # electrolyser_specific_electricity_2050: float = 48.0

    # Fossil hydrogen plant load factors (also called availability factors)
    gas_ccs_load_factor: float = 0.95
    gas_load_factor: float = 0.95
    coal_ccs_load_factor: float = 0.9
    coal_load_factor: float = 0.9

    # Define carbon capture and storage efficiencies
    gas_ccs_ccs_efficiency: float = 0.95
    coal_ccs_ccs_efficiency: float = 0.95

    # GAS + CCS CAPEX (€/ (kg/day))
    gas_ccs_eis_capex_2020: float = 1728
    gas_ccs_eis_capex_2030: float = 1728
    gas_ccs_eis_capex_2040: float = 1728
    gas_ccs_eis_capex_2050: float = 1728

    # GAS + CCS OPEX (€/ (kg/day)) / year
    gas_ccs_eis_fixed_opex_2020: float = 1728 * 0.04
    gas_ccs_eis_fixed_opex_2030: float = 1728 * 0.04
    gas_ccs_eis_fixed_opex_2040: float = 1728 * 0.04
    gas_ccs_eis_fixed_opex_2050: float = 1728 * 0.04

    # GAS + CCS efficicency
    gas_ccs_efficiency_2020: float = 0.69
    gas_ccs_efficiency_2030: float = 0.69
    gas_ccs_efficiency_2040: float = 0.69
    gas_ccs_efficiency_2050: float = 0.69

    # GAS + CAPEX (€/ (kg/day))
    gas_eis_capex_2020: float = 917
    gas_eis_capex_2030: float = 917
    gas_eis_capex_2040: float = 917
    gas_eis_capex_2050: float = 917

    # GAS OPEX (€/ (kg/day)) / year
    gas_eis_fixed_opex_2020: float = 917 * 0.047
    gas_eis_fixed_opex_2030: float = 917 * 0.047
    gas_eis_fixed_opex_2040: float = 917 * 0.047
    gas_eis_fixed_opex_2050: float = 917 * 0.047

    # GAS efficicency
    gas_efficiency_2020: float = 0.76
    gas_efficiency_2030: float = 0.76
    gas_efficiency_2040: float = 0.76
    gas_efficiency_2050: float = 0.76

    # Coal + CCS CAPEX (€/ (kg/day))
    coal_ccs_eis_capex_2020: float = 2399
    coal_ccs_eis_capex_2030: float = 2399
    coal_ccs_eis_capex_2040: float = 2399
    coal_ccs_eis_capex_2050: float = 2399

    # Coal + CCS OPEX (€/ (kg/day)) / year
    coal_ccs_eis_fixed_opex_2020: float = 2399 * 0.05
    coal_ccs_eis_fixed_opex_2030: float = 2399 * 0.05
    coal_ccs_eis_fixed_opex_2040: float = 2399 * 0.05
    coal_ccs_eis_fixed_opex_2050: float = 2399 * 0.05

    # Coal + CCS efficicency
    coal_ccs_efficiency_2020: float = 0.58
    coal_ccs_efficiency_2030: float = 0.58
    coal_ccs_efficiency_2040: float = 0.58
    coal_ccs_efficiency_2050: float = 0.58

    # Coal CAPEX (€/ (kg/day))
    coal_eis_capex_2020: float = 2304
    coal_eis_capex_2030: float = 2304
    coal_eis_capex_2040: float = 2304
    coal_eis_capex_2050: float = 2304

    # Coal OPEX (€/ (kg/day)) / year
    coal_eis_fixed_opex_2020: float = 2304 * 0.05
    coal_eis_fixed_opex_2030: float = 2304 * 0.05
    coal_eis_fixed_opex_2040: float = 2304 * 0.05
    coal_eis_fixed_opex_2050: float = 2304 * 0.05

    # Coal efficicency
    coal_efficiency_2020: float = 0.6
    coal_efficiency_2030: float = 0.6
    coal_efficiency_2040: float = 0.6
    coal_efficiency_2050: float = 0.6

    # CCS price (€/kgCO2)
    ccs_cost_2020: float = 0.02
    ccs_cost_2030: float = 0.02
    ccs_cost_2040: float = 0.02
    ccs_cost_2050: float = 0.02

    # Liquefier Capex (€/ (kg/day))
    liquefier_capex_2020: float = 1457.33
    liquefier_capex_2030: float = 1457.33
    liquefier_capex_2040: float = 1457.33
    liquefier_capex_2050: float = 1457.33

    # Hydrogen transport cost ratio (Hoelzen et al.)
    transport_cost_ratio: float = 0.1

    # Deprecated since move to efficiency, might be reactivated
    # Liquefier sp. electricity (kWh/kg)
    # liquefier_specific_electricity_2020: float = 7.54
    # liquefier_specific_electricity_2030: float = 7.54
    # liquefier_specific_electricity_2040: float = 7.54
    # liquefier_specific_electricity_2050: float = 7.54

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

    # Deprecated since move to efficiency, might be reactivated
    # Electrofuel plant specific electricity (kWh/kg)
    # electrofuel_specific_electricity_2020: float = 22.9
    # electrofuel_specific_electricity_2030: float = 22.9
    # electrofuel_specific_electricity_2040: float = 22.9
    # electrofuel_specific_electricity_2050: float = 22.9

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

    # Gas market price (€/kWh)

    gas_cost_2020: float = 0.005
    gas_cost_2030: float = 0.011
    gas_cost_2040: float = 0.010
    gas_cost_2050: float = 0.009

    # Coal market price (€/kWh)
    coal_cost_2020: float = 0.006
    coal_cost_2030: float = 0.0057
    coal_cost_2040: float = 0.0054
    coal_cost_2050: float = 0.0052

    # Electricity load factor
    # todo switch cases for ded renwb/grid

    electricity_load_factor: float = 0.95

    # CO2 DAC market price (€/kg)

    co2_cost_2020: float = 0.225
    co2_cost_2030: float = 0.225
    co2_cost_2040: float = 0.225
    co2_cost_2050: float = 0.225

    # CO2 tax level (€/ton)

    co2_tax_2020: float = 50
    co2_tax_2030: float = 100
    co2_tax_2040: float = 200
    co2_tax_2050: float = 300

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

    # DOC simple initialisation

    doc_non_energy_per_ask_short_range_dropin_fuel_init: float = 0.045
    doc_non_energy_per_ask_medium_range_dropin_fuel_init: float = 0.028
    doc_non_energy_per_ask_long_range_dropin_fuel_init: float = 0.023
    doc_non_energy_per_ask_short_range_dropin_fuel_gain: float = 0.0
    doc_non_energy_per_ask_medium_range_dropin_fuel_gain: float = 0.0
    doc_non_energy_per_ask_long_range_dropin_fuel_gain: float = 0.0
    relative_doc_non_energy_per_ask_hydrogen_wrt_dropin_short_range: float = 1.1
    relative_doc_non_energy_per_ask_hydrogen_wrt_dropin_medium_range: float = 1.1
    relative_doc_non_energy_per_ask_hydrogen_wrt_dropin_long_range: float = 1.1
