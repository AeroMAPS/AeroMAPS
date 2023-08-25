from aeromaps.models.impacts.costs.operations.average_ops_cost import PassengerAircraftDocEnergy, DropInMeanMfsp
from aeromaps.models.impacts.energy_resources.abatement_potential import BiofuelAbatementPotential
from aeromaps.models.parameters import YearParameters
from aeromaps.models.air_transport.air_traffic.rpk import (
    RPK,
    RPKReference,
    RPKMeasures,
)
from aeromaps.models.air_transport.air_traffic.rtk import RTK, RTKReference
from aeromaps.models.air_transport.air_traffic.total_aircraft_distance import TotalAircraftDistance
from aeromaps.models.air_transport.aircraft_fleet_and_operations.load_factor.load_factor import (
    LoadFactor,
)
from aeromaps.models.air_transport.air_traffic.ask import ASK
from aeromaps.models.air_transport.aircraft_fleet_and_operations.operations.operations import (
    OperationsSimple,
)
from aeromaps.models.air_transport.aircraft_fleet_and_operations.non_co2.non_co2 import (
    OperationsContrailsSimple,
)
from aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet.aircraft_efficiency import (
    PassengerAircraftEfficiencySimple,
    FreightAircraftEfficiencySimple,
    PassengerAircraftEfficiencyComplex,
    FreightAircraftEfficiency
)
from aeromaps.models.air_transport.aircraft_fleet_and_operations.aircraft_fleet_and_operations import (
    EnergyIntensity,
)
from aeromaps.models.air_transport.aircraft_energy.fuel_distribution import FuelDistribution
from aeromaps.models.sustainability_assessment.climate.carbon_budgets import GrossCarbonBudget
from aeromaps.models.sustainability_assessment.climate.equivalent_carbon_budgets import (
    EquivalentGrossCarbonBudget,
)
from aeromaps.models.air_transport.aircraft_energy.efficiency import (
    BiofuelEfficiency,
    ElectricityBasedFuelEfficiency,
)
from aeromaps.models.air_transport.aircraft_energy.fuel_emissions import (
    BiofuelEmissionFactor,
    ElectricityEmissionFactor,
    HydrogenEmissionFactor,
    ElectrofuelEmissionFactor,
    KeroseneEmissionFactor,
)
from aeromaps.models.air_transport.aircraft_energy.production_choices import (
    BiofuelProduction,
    HydrogenProduction,
)
from aeromaps.models.sustainability_assessment.energy.resources_availability import (
    BiomassAvailability,
    ElectricityAvailability,
)
from aeromaps.models.parameters import AllParameters
from aeromaps.models.impacts.effective_radiative_forcing.effective_radiative_forcing import (
    ERF,
    DetailedERF,
)
from aeromaps.models.impacts.emissions.co2_emissions import (
    CO2Emissions,
    KayaFactors,
    CumulativeCO2Emissions,
    DetailedCo2Emissions,
    DetailedCumulativeCO2Emissions,
)
from aeromaps.models.impacts.emissions.non_co2_emissions import NOxEmissionIndex, NonCO2Emissions
from aeromaps.models.impacts.energy_resources.energy_consumption import (
    DropInFuelConsumption,
    HydrogenConsumption,
    EnergyConsumption,
)
from aeromaps.models.impacts.energy_resources.resources_consumption import (
    BiomassConsumption,
    ElectricityConsumption,
)
from aeromaps.models.impacts.equivalent_co2_emissions.equivalent_co2_emissions import (
    EquivalentCO2Emissions,
)
from aeromaps.models.impacts.climate.climate import Temperature
from aeromaps.models.impacts.others.others import EmissionsPerRPK, EmissionsPerRTK
from aeromaps.models.impacts.others.comparison import (
    CarbonBudgetConsumedShare,
    ResourcesConsumedShare,
)


# COSTS
from aeromaps.models.impacts.costs.energy.biofuel import BiofuelCost, BiofuelMfsp, BiofuelCapex
from aeromaps.models.impacts.costs.energy.market_prices import ElectricityCost, Co2Cost, KeroseneCost, KerosenePrice, \
    Co2Tax, KeroseneBAUCost, CoalCost, GasCost
from aeromaps.models.impacts.costs.energy.power_to_liquid import (
    ElectrofuelCost,
    ElectrofuelCapex,
    ElectrofuelFixedOpex,
    ElectrofuelVarOpex,
    ElectrofuelSpecificElectricity,
    ElectrofuelSpecificCo2
)

from aeromaps.models.impacts.costs.energy.liquid_hydrogen import (
    LiquidHydrogenCost,
    ElectrolyserCapex,
    ElectrolyserFixedOpex,
    ElectrolyserVarOpex,
    # ElectrolyserSpecificElectricity,
    LiquefierCapex, CcsCost, CoalEfficiency, CoalFixedOpex, CoalCapex, CoalCcsEfficiency, CoalCcsFixedOpex,
    CoalCcsCapex, GasEfficiency, GasFixedOpex, GasCapex, GasCcsEfficiency, GasCcsFixedOpex, GasCcsCapex,
    # LiquefierSpecificElectricity,
)

from aeromaps.models.impacts.costs.scenario.scenario_cost import DicountedScenarioCost, NonDiscountedScenarioCost


year_parameters = YearParameters(
    historic_start_year=2000, prospection_start_year=2020, end_year=2050
)

models_simple = {
    "rpk_measures": RPKMeasures(
        "rpk_measures", parameters=AllParameters(), year_parameters=year_parameters
    ),
    "rpk": RPK("rpk", parameters=AllParameters(), year_parameters=year_parameters),
    "rpk_reference": RPKReference(
        "rpk_reference", parameters=AllParameters(), year_parameters=year_parameters
    ),
    "total_aircraft_distance": TotalAircraftDistance(
        "total_aircraft_distance", parameters=AllParameters(), year_parameters=year_parameters
    ),
    "rtk": RTK("rtk", parameters=AllParameters(), year_parameters=year_parameters),
    "rtk_reference": RTKReference(
        "rtk_reference", parameters=AllParameters(), year_parameters=year_parameters
    ),
    # "short_range_distribution": ShortRangeDistribution(
    #     "short_range_distribution", parameters=AllParameters(), year_parameters=year_parameters
    # ),
    # "rpk_short_range": RPKShortRange(
    #     "rpk_short_range", parameters=AllParameters(), year_parameters=year_parameters
    # ),
    "load_factor": LoadFactor(
        "load_factor", parameters=AllParameters(), year_parameters=year_parameters
    ),
    "ask": ASK("ask", parameters=AllParameters(), year_parameters=year_parameters),
    "operations_simple": OperationsSimple(
        "operations_simple", parameters=AllParameters(), year_parameters=year_parameters
    ),
    "operations_contrails_simple": OperationsContrailsSimple(
        "operations_contrails_simple", parameters=AllParameters(), year_parameters=year_parameters
    ),
    "passenger_aircraft_efficiency_simple": PassengerAircraftEfficiencySimple(
        "passenger_aircraft_efficiency_simple",
        year_parameters=year_parameters,
        parameters=AllParameters(),
    ),
    "freight_aircraft_efficiency_simple": FreightAircraftEfficiencySimple(
        "freight_aircraft_efficiency_simple",
        year_parameters=year_parameters,
        parameters=AllParameters(),
    ),
    "energy_intensity": EnergyIntensity(
        "energy_intensity", parameters=AllParameters(), year_parameters=year_parameters
    ),
    "aircraft_energy": FuelDistribution(
        "aircraft_energy", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "gross_carbon_budget": GrossCarbonBudget(
        "gross_carbon_budget", parameters=AllParameters(), year_parameters=year_parameters
    ),
    "equivalent_gross_carbon_budget": EquivalentGrossCarbonBudget(
        "equivalent_gross_carbon_budget",
        parameters=AllParameters(),
        year_parameters=year_parameters,
    ),
    "biofuel_efficiency": BiofuelEfficiency(
        "biofuel_efficiency", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "electricity_based_fuel_efficiency": ElectricityBasedFuelEfficiency(
        "electricity_based_fuel_efficiency",
        year_parameters=year_parameters,
        parameters=AllParameters(),
    ),
    "biofuel_emission_factor": BiofuelEmissionFactor(
        "biofuel_emission_factor", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "electricity_emission_factor": ElectricityEmissionFactor(
        "electricity_emission_factor", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "hydrogen_emission_factor": HydrogenEmissionFactor(
        "hydrogen_emission_factor", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "electrofuel_emission_factor": ElectrofuelEmissionFactor(
        "electrofuel_emission_factor", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "kerosene_emission_factor": KeroseneEmissionFactor(
        "kerosene_emission_factor", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "biofuel_production": BiofuelProduction(
        "biofuel_production", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "hydrogen_production": HydrogenProduction(
        "hydrogen_production",
        year_parameters=year_parameters,
        parameters=AllParameters(),
    ),
    "biomass_availability": BiomassAvailability(
        "biomass_availability", parameters=AllParameters(), year_parameters=year_parameters
    ),
    "electricity_availability": ElectricityAvailability(
        "electricity_availability", parameters=AllParameters(), year_parameters=year_parameters
    ),
    "effective_radiative_forcing": ERF(
        "effective_radiative_forcing", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "detailed_erf": DetailedERF(
        "detailed_erf", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "kaya_factors": KayaFactors(
        "kaya_factors", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "co2_emissions": CO2Emissions(
        "co2_emissions", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "cumulative_co2_emissions": CumulativeCO2Emissions(
        "cumulative_co2_emissions", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "detailed_co2_emissions": DetailedCo2Emissions(
        "detailed_co2_emissions", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "detailed_cumulative_co2_emissions": DetailedCumulativeCO2Emissions(
        "detailed_cumulative_co2_emissions",
        year_parameters=year_parameters,
        parameters=AllParameters(),
    ),
    "nox_emission_index": NOxEmissionIndex(
        "nox_emission_index", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "non_co2_emissions": NonCO2Emissions(
        "non_co2_emissions", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "drop_in_fuel_consumption": DropInFuelConsumption(
        "drop_in_fuel_consumption", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "hydrogen_consumption": HydrogenConsumption(
        "hydrogen_consumption", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "energy_consumption": EnergyConsumption(
        "energy_consumption", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "biomass_consumption": BiomassConsumption(
        "biomass_consumption", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "electricity_consumption": ElectricityConsumption(
        "electricity_consumption", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "equivalent_co2_emissions": EquivalentCO2Emissions(
        "equivalent_co2_emissions", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "temperature": Temperature(
        "temperature", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "emissions_per_rpk": EmissionsPerRPK(
        "emissions_per_rpk", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "emissions_per_rtk": EmissionsPerRTK(
        "emissions_per_rtk", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "carbon_budget_consumed_share": CarbonBudgetConsumedShare(
        "carbon_budget_consumed_share", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "resources_consumed_share": ResourcesConsumedShare(
        "resources_consumed_share", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "biofuel_mfsp": BiofuelMfsp(
        "biofuel_mfsp", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "biofuel_capex": BiofuelCapex(
        "biofuel_capex", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "kerosene_market_price": KerosenePrice(
        "kerosene_market_price", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "kerosene_cost": KeroseneCost(
        "kerosene_cost", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "kerosene_BAU_cost": KeroseneBAUCost(
        "kerosene_BAU_cost", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "biofuel_cost": BiofuelCost(
        "biofuel_cost", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "co2_cost": Co2Cost(
        "co2_cost", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "co2_tax": Co2Tax(
        "co2_tax", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "electricity_cost": ElectricityCost(
        "electricity_cost", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "coal_cost": CoalCost(
        "coal_cost", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "gas_cost": GasCost(
        "coal_cost", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "liquid_hydrogen_cost": LiquidHydrogenCost(
        "liquid_hydrogen_cost", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "electrolyser_capex": ElectrolyserCapex(
        "electrolyser_capex", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "electrolyser_fixed_opex": ElectrolyserFixedOpex(
        "electrolyser_fixed_opex", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "electrolyser_var_opex": ElectrolyserVarOpex(
        "electrolyser_var_opex", year_parameters=year_parameters, parameters=AllParameters()
    ),
    # "electrolyser_specific_electricity": ElectrolyserSpecificElectricity(
    #     "electrolyser_specific_electricity", year_parameters=year_parameters, parameters=AllParameters()
    # ),
    "gas_ccs_capex": GasCcsCapex(
        "gas_ccs_capex",  year_parameters=year_parameters, parameters=AllParameters()
    ),
    "gas_ccs_fixed_opex": GasCcsFixedOpex(
        "gas_ccs_fixed_opex",  year_parameters=year_parameters, parameters=AllParameters()
    ),
    "gas_ccs_efficiency": GasCcsEfficiency(
        "gas_ccs_efficiency",  year_parameters=year_parameters, parameters=AllParameters()
    ),
    "gas_capex": GasCapex(
        "gas_capex",  year_parameters=year_parameters, parameters=AllParameters()
    ),
    "gas_fixed_opex": GasFixedOpex(
        "gas_fixed_opex",  year_parameters=year_parameters, parameters=AllParameters()
    ),
    "gas_efficiency": GasEfficiency(
        "gas_efficiency",  year_parameters=year_parameters, parameters=AllParameters()
    ),
    "coal_ccs_capex": CoalCcsCapex(
        "coal_ccs_capex", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "coal_ccs_fixed_opex": CoalCcsFixedOpex(
        "coal_ccs_fixed_opex", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "coal_ccs_efficiency": CoalCcsEfficiency(
        "coal_ccs_efficiency", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "coal_capex": CoalCapex(
        "coal_capex", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "coal_fixed_opex": CoalFixedOpex(
        "coal_fixed_opex", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "coal_efficiency": CoalEfficiency(
        "coal_efficiency", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "ccs_cost": CcsCost(
        "ccs_cost", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "liquefier_capex": LiquefierCapex(
        "liquefier_capex", year_parameters=year_parameters, parameters=AllParameters()
    ),
    # "liquefier_specific_electricity": LiquefierSpecificElectricity(
    #     "liquefier_specific_electricity", year_parameters=year_parameters, parameters=AllParameters()
    # ),
    "electrofuel_cost": ElectrofuelCost(
        "electrofuel_cost", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "electrofuel_capex": ElectrofuelCapex(
        "electrofuel_capex", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "electrofuel_fixed_opex": ElectrofuelFixedOpex(
        "electrofuel_fixed_opex", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "electrofuel_var_opex": ElectrofuelVarOpex(
        "electrofuel_var_opex", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "electrofuel_specific_electricity": ElectrofuelSpecificElectricity(
        "electrofuel_specific_electricity", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "electrofuel_specific_co2": ElectrofuelSpecificCo2(
        "electrofuel_specific_co2", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "discounted_scenario_cost": DicountedScenarioCost(
        "discounted_scenario_cost", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "non_discounted_scenario_cost": NonDiscountedScenarioCost(
        "non_discounted_scenario_cost", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "biofuel_abatement_potential": BiofuelAbatementPotential(
        "biofuel_abatement_potential", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "passenger_aircraft_doc_energy": PassengerAircraftDocEnergy(
        "passenger_aircraft_doc_energy", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "dropin_mean_mfsp": DropInMeanMfsp(
        "dropin_mean_mfsp", year_parameters=year_parameters, parameters=AllParameters()
    )
}


models_complex = {
    "rpk_measures": RPKMeasures(
        "rpk_measures", parameters=AllParameters(), year_parameters=year_parameters
    ),
    "rpk": RPK("rpk", parameters=AllParameters(), year_parameters=year_parameters),
    "rpk_reference": RPKReference(
        "rpk_reference", parameters=AllParameters(), year_parameters=year_parameters
    ),
    "total_aircraft_distance": TotalAircraftDistance(
        "total_aircraft_distance", parameters=AllParameters(), year_parameters=year_parameters
    ),
    "rtk": RTK("rtk", parameters=AllParameters(), year_parameters=year_parameters),
    "rtk_reference": RTKReference(
        "rtk_reference", parameters=AllParameters(), year_parameters=year_parameters
    ),
    # "short_range_distribution": ShortRangeDistribution(
    #     "short_range_distribution", parameters=AllParameters(), year_parameters=year_parameters
    # ),
    # "rpk_short_range": RPKShortRange(
    #     "rpk_short_range", parameters=AllParameters(), year_parameters=year_parameters
    # ),
    "load_factor": LoadFactor(
        "load_factor", parameters=AllParameters(), year_parameters=year_parameters
    ),
    "ask": ASK("ask", parameters=AllParameters(), year_parameters=year_parameters),
    "operations_simple": OperationsSimple(
        "operations_simple", parameters=AllParameters(), year_parameters=year_parameters
    ),
    "operations_contrails_simple": OperationsContrailsSimple(
        "operations_contrails_simple", parameters=AllParameters(), year_parameters=year_parameters
    ),
    "passenger_aircraft_efficiency_complex": PassengerAircraftEfficiencyComplex(
        "passenger_aircraft_efficiency_complex",
        year_parameters=year_parameters,
        parameters=AllParameters(),
    ),
    "freight_aircraft_efficiency": FreightAircraftEfficiency(
        "freight_aircraft_efficiency",
        year_parameters=year_parameters,
        parameters=AllParameters(),
    ),
    "energy_intensity": EnergyIntensity(
        "energy_intensity", parameters=AllParameters(), year_parameters=year_parameters
    ),
    "aircraft_energy": FuelDistribution(
        "aircraft_energy", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "gross_carbon_budget": GrossCarbonBudget(
        "gross_carbon_budget", parameters=AllParameters(), year_parameters=year_parameters
    ),
    "equivalent_gross_carbon_budget": EquivalentGrossCarbonBudget(
        "equivalent_gross_carbon_budget",
        parameters=AllParameters(),
        year_parameters=year_parameters,
    ),
    "biofuel_efficiency": BiofuelEfficiency(
        "biofuel_efficiency", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "electricity_based_fuel_efficiency": ElectricityBasedFuelEfficiency(
        "electricity_based_fuel_efficiency",
        year_parameters=year_parameters,
        parameters=AllParameters(),
    ),
    "biofuel_emission_factor": BiofuelEmissionFactor(
        "biofuel_emission_factor", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "electricity_emission_factor": ElectricityEmissionFactor(
        "electricity_emission_factor", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "hydrogen_emission_factor": HydrogenEmissionFactor(
        "hydrogen_emission_factor", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "electrofuel_emission_factor": ElectrofuelEmissionFactor(
        "electrofuel_emission_factor", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "kerosene_emission_factor": KeroseneEmissionFactor(
        "kerosene_emission_factor", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "biofuel_production": BiofuelProduction(
        "biofuel_production", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "hydrogen_production": HydrogenProduction(
        "hydrogen_production",
        year_parameters=year_parameters,
        parameters=AllParameters(),
    ),
    "biomass_availability": BiomassAvailability(
        "biomass_availability", parameters=AllParameters(), year_parameters=year_parameters
    ),
    "electricity_availability": ElectricityAvailability(
        "electricity_availability", parameters=AllParameters(), year_parameters=year_parameters
    ),
    "effective_radiative_forcing": ERF(
        "effective_radiative_forcing", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "detailed_erf": DetailedERF(
        "detailed_erf", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "kaya_factors": KayaFactors(
        "kaya_factors", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "co2_emissions": CO2Emissions(
        "co2_emissions", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "cumulative_co2_emissions": CumulativeCO2Emissions(
        "cumulative_co2_emissions", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "detailed_co2_emissions": DetailedCo2Emissions(
        "detailed_co2_emissions", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "detailed_cumulative_co2_emissions": DetailedCumulativeCO2Emissions(
        "detailed_cumulative_co2_emissions",
        year_parameters=year_parameters,
        parameters=AllParameters(),
    ),
    "nox_emission_index": NOxEmissionIndex(
        "nox_emission_index", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "non_co2_emissions": NonCO2Emissions(
        "non_co2_emissions", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "drop_in_fuel_consumption": DropInFuelConsumption(
        "drop_in_fuel_consumption", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "hydrogen_consumption": HydrogenConsumption(
        "hydrogen_consumption", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "energy_consumption": EnergyConsumption(
        "energy_consumption", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "biomass_consumption": BiomassConsumption(
        "biomass_consumption", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "electricity_consumption": ElectricityConsumption(
        "electricity_consumption", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "equivalent_co2_emissions": EquivalentCO2Emissions(
        "equivalent_co2_emissions", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "temperature": Temperature(
        "temperature", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "emissions_per_rpk": EmissionsPerRPK(
        "emissions_per_rpk", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "emissions_per_rtk": EmissionsPerRTK(
        "emissions_per_rtk", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "carbon_budget_consumed_share": CarbonBudgetConsumedShare(
        "carbon_budget_consumed_share", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "resources_consumed_share": ResourcesConsumedShare(
        "resources_consumed_share", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "biofuel_mfsp": BiofuelMfsp(
        "biofuel_mfsp", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "biofuel_capex": BiofuelCapex(
        "biofuel_capex", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "kerosene_market_price": KerosenePrice(
        "kerosene_market_price", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "kerosene_cost": KeroseneCost(
        "kerosene_cost", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "biofuel_cost": BiofuelCost(
        "biofuel_cost", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "co2_cost": Co2Cost(
        "co2_cost", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "co2_tax": Co2Tax(
        "co2_tax", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "electricity_cost": ElectricityCost(
        "electricity_cost", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "coal_cost": CoalCost(
        "coal_cost", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "gas_cost": GasCost(
        "coal_cost", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "liquid_hydrogen_cost": LiquidHydrogenCost(
        "liquid_hydrogen_cost", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "electrolyser_capex": ElectrolyserCapex(
        "electrolyser_capex", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "electrolyser_fixed_opex": ElectrolyserFixedOpex(
        "electrolyser_fixed_opex", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "electrolyser_var_opex": ElectrolyserVarOpex(
        "electrolyser_var_opex", year_parameters=year_parameters, parameters=AllParameters()
    ),
    # "electrolyser_specific_electricity": ElectrolyserSpecificElectricity(
    #     "electrolyser_specific_electricity", year_parameters=year_parameters, parameters=AllParameters()
    # ),
    "gas_ccs_capex": GasCcsCapex(
        "gas_ccs_capex", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "gas_ccs_fixed_opex": GasCcsFixedOpex(
        "gas_ccs_fixed_opex", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "gas_ccs_efficiency": GasCcsEfficiency(
        "gas_ccs_efficiency", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "gas_capex": GasCapex(
        "gas_capex", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "gas_fixed_opex": GasFixedOpex(
        "gas_fixed_opex", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "gas_efficiency": GasEfficiency(
        "gas_efficiency", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "coal_ccs_capex": CoalCcsCapex(
        "coal_ccs_capex", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "coal_ccs_fixed_opex": CoalCcsFixedOpex(
        "coal_ccs_fixed_opex", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "coal_ccs_efficiency": CoalCcsEfficiency(
        "coal_ccs_efficiency", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "coal_capex": CoalCapex(
        "coal_capex", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "coal_fixed_opex": CoalFixedOpex(
        "coal_fixed_opex", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "coal_efficiency": CoalEfficiency(
        "coal_efficiency", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "ccs_cost": CcsCost(
        "ccs_cost", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "liquefier_capex": LiquefierCapex(
        "liquefier_capex", year_parameters=year_parameters, parameters=AllParameters()
    ),
    # "liquefier_specific_electricity": LiquefierSpecificElectricity(
    #     "liquefier_specific_electricity", year_parameters=year_parameters, parameters=AllParameters()
    # ),
    "electrofuel_cost": ElectrofuelCost(
        "electrofuel_cost", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "electrofuel_capex": ElectrofuelCapex(
        "electrofuel_capex", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "electrofuel_fixed_opex": ElectrofuelFixedOpex(
        "electrofuel_fixed_opex", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "electrofuel_var_opex": ElectrofuelVarOpex(
        "electrofuel_var_opex", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "electrofuel_specific_electricity": ElectrofuelSpecificElectricity(
        "electrofuel_specific_electricity", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "electrofuel_specific_co2": ElectrofuelSpecificCo2(
        "electrofuel_specific_co2", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "discounted_scenario_cost": DicountedScenarioCost(
        "discounted_scenario_cost", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "non_discounted_scenario_cost": NonDiscountedScenarioCost(
        "non_discounted_scenario_cost", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "biofuel_abatement_potential": BiofuelAbatementPotential(
        "biofuel_abatement_potential", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "passenger_aircraft_doc_energy": PassengerAircraftDocEnergy(
        "passenger_aircraft_doc_energy", year_parameters=year_parameters, parameters=AllParameters()
    ),
    "dropin_mean_mfsp": DropInMeanMfsp(
        "dropin_mean_mfsp", year_parameters=year_parameters, parameters=AllParameters()
    )

}
