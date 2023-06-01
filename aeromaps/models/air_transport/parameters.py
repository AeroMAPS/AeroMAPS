from dataclasses import dataclass
import os.path as pth
import pandas as pd
from aeromaps.utils.functions import _dict_from_json

filename = pth.join(
    pth.dirname(pth.abspath(__file__)), "..", "..", "resources", "data", "parameters.json"
)

data = _dict_from_json(file_name=filename)


@dataclass
class AirTransportParameters(object):

    # DataFrame data air on air traffic
    rpk_init: pd.Series = data["rpk_init"]
    ask_init: pd.Series = data["ask_init"]
    rtk_init: pd.Series = data["rtk_init"]
    pax_init: pd.Series = data["pax_init"]  # Not used
    freight_init: pd.Series = data["freight_init"]  # Not used
    energy_consumption_init: pd.Series = data["energy_consumption_init"]
    total_aircraft_distance_init: pd.Series = data["total_aircraft_distance_init"]

    # Other coefficients
    commercial_aviation_coefficient: float = 0.88

    # Load factor
    load_factor_end_year: float = 85.0  # [%]

    # Simple gains for fleet efficiency
    energy_per_ask_short_range_dropin_fuel_gain: float = 2  # [%]
    energy_per_ask_medium_range_dropin_fuel_gain: float = 2  # [%]
    energy_per_ask_long_range_dropin_fuel_gain: float = 2  # [%]

    # NOx emission index for simple models [%] - Positive means augmentation
    emission_index_nox_dropin_fuel_evolution: float = 0.0
    emission_index_nox_hydrogen_evolution: float = 0.0

    # Energy distribution [%]
    short_range_energy_share_2019: float = 30.6 * 0.85
    medium_range_energy_share_2019: float = 30.8 * 0.85
    long_range_energy_share_2019: float = 38.6 * 0.85
    freight_energy_share_2019: float = 15

    # RPK distribution [%]
    short_range_rpk_share_2019: float = 27.2
    medium_range_rpk_share_2019: float = 35.1
    long_range_rpk_share_2019: float = 37.7
    short_range_basicturbofan_share_2019: float = 88.4
    short_range_regionalturboprop_share_2019: float = 2.5
    short_range_regionalturbofan_share_2019: float = 9.1  # Model ?

    # Covid-19
    covid_start_year: int = 2020
    covid_rpk_drop_start_year: float = 66.0  # [%]
    covid_end_year: int = 2024
    covid_end_year_reference_rpk_ratio: float = 100.0  # [%]
    covid_load_factor_2020: float = 65.2  # [%]
    covid_energy_intensity_per_ask_increase_2020: float = 30.5  # [%]

    # Growth rate [%]
    growth_rate_2020_2030_short_range: float = 3.0
    growth_rate_2030_2040_short_range: float = 3.0
    growth_rate_2040_2050_short_range: float = 3.0
    growth_rate_2020_2030_medium_range: float = 3.0
    growth_rate_2030_2040_medium_range: float = 3.0
    growth_rate_2040_2050_medium_range: float = 3.0
    growth_rate_2020_2030_long_range: float = 3.0
    growth_rate_2030_2040_long_range: float = 3.0
    growth_rate_2040_2050_long_range: float = 3.0
    growth_rate_2020_2030_rtk: float = 3.0
    growth_rate_2030_2040_rtk: float = 3.0
    growth_rate_2040_2050_rtk: float = 3.0

    # Short range distribution [%] - Not used
    short_range_basicturbofan_share_2030: float = 88.4
    short_range_basicturbofan_share_2040: float = 88.4
    short_range_basicturbofan_share_2050: float = 88.4
    short_range_regionalturboprop_share_2030: float = 2.5
    short_range_regionalturboprop_share_2040: float = 2.5
    short_range_regionalturboprop_share_2050: float = 2.5
    # Calcul pour ces valeurs
    # short_range_regionalturbofan_share_2030: float = 9.1
    # short_range_regionalturbofan_share_2040: float = 9.1
    # short_range_regionalturbofan_share_2050: float = 9.1

    # References
    growth_rate_2020_2030_reference: float = 3.0
    growth_rate_2030_2040_reference: float = 3.0
    growth_rate_2040_2050_reference: float = 3.0

    # RPK measures
    rpk_short_range_measures_final_impact: float = 0.0
    rpk_medium_range_measures_final_impact: float = 0.0
    rpk_long_range_measures_final_impact: float = 0.0
    rpk_short_range_measures_start_year: float = 2051
    rpk_medium_range_measures_start_year: float = 2051
    rpk_long_range_measures_start_year: float = 2051
    rpk_short_range_measures_duration: float = 5.0
    rpk_medium_range_measures_duration: float = 5.0
    rpk_long_range_measures_duration: float = 5.0

    # Operations
    operations_final_gain: float = 7.0  # [%]
    operations_start_year: float = 2020
    operations_duration: float = 40.0

    # Operations contrails
    operations_contrails_final_gain: float = 59.4  # [%]
    operations_contrails_final_overconsumption: float = 0.014  # [%]
    operations_contrails_start_year: float = 2051
    operations_contrails_duration: float = 15.0

    # Efficiency for hydrogen simple models
    hydrogen_final_market_share_short_range: float = 20.0  # [%]
    hydrogen_introduction_year_short_range: float = 2035
    hydrogen_final_market_share_medium_range: float = 20.0  # [%]
    hydrogen_introduction_year_medium_range: float = 2035
    hydrogen_final_market_share_long_range: float = 0.0  # [%]
    hydrogen_introduction_year_long_range: float = 2035
    relative_energy_per_ask_hydrogen_wrt_dropin_short_range: float = 1.0
    relative_energy_per_ask_hydrogen_wrt_dropin_medium_range: float = 1.0
    relative_energy_per_ask_hydrogen_wrt_dropin_long_range: float = 1.0
    fleet_renewal_duration: float = 25.0

    # Fuel distribution
    biofuel_share_2020: float = 0.0
    biofuel_share_2030: float = 0.0
    biofuel_share_2040: float = 0.0
    biofuel_share_2050: float = 0.0
    electrofuel_share_2020: float = 0.0
    electrofuel_share_2030: float = 0.0
    electrofuel_share_2040: float = 0.0
    electrofuel_share_2050: float = 0.0
    # Calculation for the following values
    # kerosene_share_2020: float = 100.0
    # kerosene_share_2030: float = 100.0
    # kerosene_share_2040: float = 100.0
    # kerosene_share_2050: float = 100.0

    # Energy efficiencies - Biofuel
    biofuel_ft_efficiency_2020: float = 0.46
    biofuel_ft_efficiency_2050: float = 0.46
    biofuel_atj_efficiency_2020: float = 0.48
    biofuel_atj_efficiency_2050: float = 0.48
    biofuel_hefa_oil_efficiency_2020: float = 0.66
    biofuel_hefa_oil_efficiency_2050: float = 0.66
    biofuel_hefa_fuel_efficiency_2020: float = 0.88
    biofuel_hefa_fuel_efficiency_2050: float = 0.88

    # Has to be integrated
    hydrogen_oil_hefa: float = 0.09

    # Energy selectivity - Biofuel
    # To be done with electrofuel
    biofuel_ft_selectivity: float = 0.5
    biofuel_atj_selectivity: float = 0.75
    biofuel_hefa_selectivity: float = 0.6

    # Energy production choices - Biofuel
    biofuel_hefa_fog_share_2020: float = 100.0
    biofuel_hefa_fog_share_2030: float = 100.0
    biofuel_hefa_fog_share_2040: float = 100.0
    biofuel_hefa_fog_share_2050: float = 100.0
    biofuel_hefa_others_share_2020: float = 0.0
    biofuel_hefa_others_share_2030: float = 0.0
    biofuel_hefa_others_share_2040: float = 0.0
    biofuel_hefa_others_share_2050: float = 0.0
    biofuel_ft_others_share_2020: float = 0.0
    biofuel_ft_others_share_2030: float = 0.0
    biofuel_ft_others_share_2040: float = 0.0
    biofuel_ft_others_share_2050: float = 0.0
    biofuel_ft_msw_share_2020: float = 0.0
    biofuel_ft_msw_share_2030: float = 0.0
    biofuel_ft_msw_share_2040: float = 0.0
    biofuel_ft_msw_share_2050: float = 0.0
    # Calculation for the following values
    # biofuel_atj_share_2020: float = 0.0
    # biofuel_atj_share_2030: float = 0.0
    # biofuel_atj_share_2040: float = 0.0
    # biofuel_atj_share_2050: float = 0.0

    # Energy efficiencies - Hydrogen
    electrolysis_efficiency_2020: float = 0.59
    electrolysis_efficiency_2050: float = 0.59
    liquefaction_efficiency_2020: float = 0.8
    liquefaction_efficiency_2050: float = 0.8

    # Energy production choices - Hydrogen
    hydrogen_electrolysis_share_2020: float = 2.0
    hydrogen_electrolysis_share_2030: float = 2.0
    hydrogen_electrolysis_share_2040: float = 2.0
    hydrogen_electrolysis_share_2050: float = 2.0
    hydrogen_gas_ccs_share_2020: float = 0.0
    hydrogen_gas_ccs_share_2030: float = 0.0
    hydrogen_gas_ccs_share_2040: float = 0.0
    hydrogen_gas_ccs_share_2050: float = 0.0
    hydrogen_coal_ccs_share_2020: float = 0.0
    hydrogen_coal_ccs_share_2030: float = 0.0
    hydrogen_coal_ccs_share_2040: float = 0.0
    hydrogen_coal_ccs_share_2050: float = 0.0
    hydrogen_gas_share_2020: float = 71.0
    hydrogen_gas_share_2030: float = 71.0
    hydrogen_gas_share_2040: float = 71.0
    hydrogen_gas_share_2050: float = 71.0
    # Calculation for the following values
    # hydrogen_coal_share_2020: float = 27.0
    # hydrogen_coal_share_2030: float = 27.0
    # hydrogen_coal_share_2040: float = 27.0
    # hydrogen_coal_share_2050: float = 27.0

    # Energy efficiencies - Electrofuel
    electrofuel_hydrogen_efficiency_2020: float = 0.67
    electrofuel_hydrogen_efficiency_2050: float = 0.67

    # Energy emissions - Biofuel
    biofuel_hefa_fog_emission_factor_2020: float = 20.7
    biofuel_hefa_fog_emission_factor_2050: float = 20.7
    biofuel_hefa_others_emission_factor_2020: float = 61
    biofuel_hefa_others_emission_factor_2050: float = 61
    biofuel_ft_others_emission_factor_2020: float = 7.7
    biofuel_ft_others_emission_factor_2050: float = 7.7
    biofuel_ft_msw_emission_factor_2020: float = 27.6
    biofuel_ft_msw_emission_factor_2050: float = 27.6
    biofuel_atj_emission_factor_2020: float = 52.2
    biofuel_atj_emission_factor_2050: float = 52.2

    # Energy emissions - Electricity [gCO2/kWh]
    electricity_emission_factor_2020: float = 429
    electricity_emission_factor_2030: float = 200
    electricity_emission_factor_2040: float = 200
    electricity_emission_factor_2050: float = 200

    # Energy emissions - Hydrogen [gCO2/MJ]
    hydrogen_gas_ccs_emission_factor: float = 3.7 / 120 * 1000
    hydrogen_coal_ccs_emission_factor: float = 4.9 / 120 * 1000
    hydrogen_gas_emission_factor: float = 12.0 / 120 * 1000
    hydrogen_coal_emission_factor: float = 23.0 / 120 * 1000
