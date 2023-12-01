from aeromaps.models.impacts.costs.operations.average_ops_cost import (
    PassengerAircraftDocEnergy,
    DropInMeanMfsp,
    PassengerAircraftDocCarbonTax,
    PassengerAircraftDocNonEnergyComplex,
    PassengerAircraftTotalDoc,
    PassengerAircraftDocNonEnergySimple,
)
from aeromaps.models.impacts.energy_resources.abatement_potential import BiofuelAbatementPotential

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
    PassengerAircraftEfficiencyComplex,
    FreightAircraftEfficiency,
)
from aeromaps.models.air_transport.aircraft_fleet_and_operations.aircraft_fleet_and_operations import (
    EnergyIntensity,
)
from aeromaps.models.air_transport.aircraft_energy.fuel_distribution import DropinFuelDistribution
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
from aeromaps.models.impacts.emissions.non_co2_emissions import (
    NOxEmissionIndex,
    NOxEmissionIndexComplex,
    SootEmissionIndex,
    SootEmissionIndexComplex,
    NonCO2Emissions,
)
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
from aeromaps.models.impacts.others.others import (
    EmissionsPerRPK,
    EmissionsPerRTK,
    DropinFuelConsumptionLiterPerPax100km,
)
from aeromaps.models.impacts.others.comparison import (
    CarbonBudgetConsumedShare,
    ResourcesConsumedShare,
)
from aeromaps.models.impacts.emissions.carbon_offset import (
    LevelCarbonOffset,
    ResidualCarbonOffset,
    CarbonOffset,
    CumulativeCarbonOffset,
)


# COSTS
from aeromaps.models.impacts.costs.energy.biofuel import BiofuelCost, BiofuelMfsp, BiofuelCapex
from aeromaps.models.impacts.costs.energy.market_prices import (
    ElectricityCost,
    Co2Cost,
    KeroseneCost,
    KerosenePrice,
    CarbonTax,
    KeroseneBAUCost,
    CoalCost,
    GasCost,
)
from aeromaps.models.impacts.costs.energy.power_to_liquid import (
    ElectrofuelCost,
    ElectrofuelCapex,
    ElectrofuelFixedOpex,
    ElectrofuelVarOpex,
    # ElectrofuelSpecificElectricity,
    ElectrofuelSpecificCo2,
)

from aeromaps.models.impacts.costs.energy.liquid_hydrogen import (
    LiquidHydrogenCost,
    ElectrolyserCapex,
    ElectrolyserFixedOpex,
    ElectrolyserVarOpex,
    # ElectrolyserSpecificElectricity,
    LiquefierCapex,
    CcsCost,
    CoalEfficiency,
    CoalFixedOpex,
    CoalCapex,
    CoalCcsEfficiency,
    CoalCcsFixedOpex,
    CoalCcsCapex,
    GasEfficiency,
    GasFixedOpex,
    GasCapex,
    GasCcsEfficiency,
    GasCcsFixedOpex,
    GasCcsCapex,
    # LiquefierSpecificElectricity,
)

from aeromaps.models.impacts.costs.scenario.scenario_cost import (
    DicountedScenarioCost,
    NonDiscountedScenarioCost,
)

from aeromaps.models.impacts.costs.non_operations.non_ops_cost import (
    PassengerAircraftNocCarbonOffset,
)


models_simple = {
    "rpk_measures": RPKMeasures("rpk_measures"),
    "rpk": RPK("rpk"),
    "rpk_reference": RPKReference("rpk_reference"),
    "total_aircraft_distance": TotalAircraftDistance("total_aircraft_distance"),
    "rtk": RTK("rtk"),
    "rtk_reference": RTKReference("rtk_reference"),
    # "short_range_distribution": ShortRangeDistribution(
    #     "short_range_distribution"
    # ),
    # "rpk_short_range": RPKShortRange(
    #     "rpk_short_range"
    # ),
    "load_factor": LoadFactor("load_factor"),
    "ask": ASK("ask"),
    "operations_simple": OperationsSimple("operations_simple"),
    "operations_contrails_simple": OperationsContrailsSimple("operations_contrails_simple"),
    "passenger_aircraft_efficiency_simple": PassengerAircraftEfficiencySimple(
        "passenger_aircraft_efficiency_simple"
    ),
    "freight_aircraft_efficiency": FreightAircraftEfficiency("freight_aircraft_efficiency"),
    "energy_intensity": EnergyIntensity("energy_intensity"),
    "dropin_fuel_distribution": DropinFuelDistribution("dropin_fuel_distribution"),
    "gross_carbon_budget": GrossCarbonBudget("gross_carbon_budget"),
    "equivalent_gross_carbon_budget": EquivalentGrossCarbonBudget("equivalent_gross_carbon_budget"),
    "biofuel_efficiency": BiofuelEfficiency("biofuel_efficiency"),
    "electricity_based_fuel_efficiency": ElectricityBasedFuelEfficiency(
        "electricity_based_fuel_efficiency"
    ),
    "biofuel_emission_factor": BiofuelEmissionFactor("biofuel_emission_factor"),
    "electricity_emission_factor": ElectricityEmissionFactor("electricity_emission_factor"),
    "hydrogen_emission_factor": HydrogenEmissionFactor("hydrogen_emission_factor"),
    "electrofuel_emission_factor": ElectrofuelEmissionFactor("electrofuel_emission_factor"),
    "kerosene_emission_factor": KeroseneEmissionFactor("kerosene_emission_factor"),
    "biofuel_production": BiofuelProduction("biofuel_production"),
    "hydrogen_production": HydrogenProduction("hydrogen_production"),
    "biomass_availability": BiomassAvailability("biomass_availability"),
    "electricity_availability": ElectricityAvailability("electricity_availability"),
    "effective_radiative_forcing": ERF("effective_radiative_forcing"),
    "detailed_erf": DetailedERF("detailed_erf"),
    "kaya_factors": KayaFactors("kaya_factors"),
    "co2_emissions": CO2Emissions("co2_emissions"),
    "cumulative_co2_emissions": CumulativeCO2Emissions("cumulative_co2_emissions"),
    "detailed_co2_emissions": DetailedCo2Emissions("detailed_co2_emissions"),
    "detailed_cumulative_co2_emissions": DetailedCumulativeCO2Emissions(
        "detailed_cumulative_co2_emissions"
    ),
    "nox_emission_index": NOxEmissionIndex("nox_emission_index"),
    "soot_emission_index": SootEmissionIndex("soot_emission_index"),
    "non_co2_emissions": NonCO2Emissions("non_co2_emissions"),
    "drop_in_fuel_consumption": DropInFuelConsumption("drop_in_fuel_consumption"),
    "hydrogen_consumption": HydrogenConsumption("hydrogen_consumption"),
    "energy_consumption": EnergyConsumption("energy_consumption"),
    "biomass_consumption": BiomassConsumption("biomass_consumption"),
    "electricity_consumption": ElectricityConsumption("electricity_consumption"),
    "equivalent_co2_emissions": EquivalentCO2Emissions("equivalent_co2_emissions"),
    "temperature": Temperature("temperature"),
    "emissions_per_rpk": EmissionsPerRPK("emissions_per_rpk"),
    "emissions_per_rtk": EmissionsPerRTK("emissions_per_rtk"),
    "dropin_fuel_consumption_liter_per_pax_100km": DropinFuelConsumptionLiterPerPax100km(
        "dropin_fuel_consumption_liter_per_pax_100km"
    ),
    "carbon_budget_consumed_share": CarbonBudgetConsumedShare("carbon_budget_consumed_share"),
    "resources_consumed_share": ResourcesConsumedShare("resources_consumed_share"),
    "biofuel_mfsp": BiofuelMfsp("biofuel_mfsp"),
    "biofuel_capex": BiofuelCapex("biofuel_capex"),
    "kerosene_market_price": KerosenePrice("kerosene_market_price"),
    "kerosene_cost": KeroseneCost("kerosene_cost"),
    "kerosene_BAU_cost": KeroseneBAUCost("kerosene_BAU_cost"),
    "biofuel_cost": BiofuelCost("biofuel_cost"),
    "co2_cost": Co2Cost("co2_cost"),
    "carbon_tax": CarbonTax("carbon_tax"),
    "electricity_cost": ElectricityCost("electricity_cost"),
    "coal_cost": CoalCost("coal_cost"),
    "gas_cost": GasCost("coal_cost"),
    "liquid_hydrogen_cost": LiquidHydrogenCost("liquid_hydrogen_cost"),
    "electrolyser_capex": ElectrolyserCapex("electrolyser_capex"),
    "electrolyser_fixed_opex": ElectrolyserFixedOpex("electrolyser_fixed_opex"),
    "electrolyser_var_opex": ElectrolyserVarOpex("electrolyser_var_opex"),
    # "electrolyser_specific_electricity": ElectrolyserSpecificElectricity(
    #     "electrolyser_specific_electricity"
    # ),
    "gas_ccs_capex": GasCcsCapex("gas_ccs_capex"),
    "gas_ccs_fixed_opex": GasCcsFixedOpex("gas_ccs_fixed_opex"),
    "gas_ccs_efficiency": GasCcsEfficiency("gas_ccs_efficiency"),
    "gas_capex": GasCapex("gas_capex"),
    "gas_fixed_opex": GasFixedOpex("gas_fixed_opex"),
    "gas_efficiency": GasEfficiency("gas_efficiency"),
    "coal_ccs_capex": CoalCcsCapex("coal_ccs_capex"),
    "coal_ccs_fixed_opex": CoalCcsFixedOpex("coal_ccs_fixed_opex"),
    "coal_ccs_efficiency": CoalCcsEfficiency("coal_ccs_efficiency"),
    "coal_capex": CoalCapex("coal_capex"),
    "coal_fixed_opex": CoalFixedOpex("coal_fixed_opex"),
    "coal_efficiency": CoalEfficiency("coal_efficiency"),
    "ccs_cost": CcsCost("ccs_cost"),
    "liquefier_capex": LiquefierCapex("liquefier_capex"),
    # "liquefier_specific_electricity": LiquefierSpecificElectricity(
    #     "liquefier_specific_electricity"
    # ),
    "electrofuel_cost": ElectrofuelCost("electrofuel_cost"),
    "electrofuel_capex": ElectrofuelCapex("electrofuel_capex"),
    "electrofuel_fixed_opex": ElectrofuelFixedOpex("electrofuel_fixed_opex"),
    "electrofuel_var_opex": ElectrofuelVarOpex("electrofuel_var_opex"),
    # "electrofuel_specific_electricity": ElectrofuelSpecificElectricity("electrofuel_specific_electricity"),
    "electrofuel_specific_co2": ElectrofuelSpecificCo2("electrofuel_specific_co2"),
    "discounted_scenario_cost": DicountedScenarioCost("discounted_scenario_cost"),
    "non_discounted_scenario_cost": NonDiscountedScenarioCost("non_discounted_scenario_cost"),
    "biofuel_abatement_potential": BiofuelAbatementPotential("biofuel_abatement_potential"),
    "passenger_aircraft_doc_energy": PassengerAircraftDocEnergy("passenger_aircraft_doc_energy"),
    "passenger_aircraft_doc_non_energy_simple": PassengerAircraftDocNonEnergySimple(
        "passenger_aircraft_doc_non_energy_simple"
    ),
    "passenger_aircraft_total_doc": PassengerAircraftTotalDoc("passenger_aircraft_total_doc"),
    "dropin_mean_mfsp": DropInMeanMfsp("dropin_mean_mfsp"),
    "passenger_aircraft_doc_carbon_tax": PassengerAircraftDocCarbonTax(
        "passenger_aircraft_doc_carbon_tax"
    ),
    "level_carbon_offset": LevelCarbonOffset("level_carbon_offset"),
    "residual_carbon_offset": ResidualCarbonOffset("residual_carbon_offset"),
    "carbon_offset": CarbonOffset("carbon_offset"),
    "cumulative_carbon_offset": CumulativeCarbonOffset("cumulative_carbon_offset"),
    "passenger_aircraft_noc_carbon_offset": PassengerAircraftNocCarbonOffset(
        "passenger_aircraft_noc_carbon_offset"
    ),
}


models_complex = {
    "rpk_measures": RPKMeasures("rpk_measures"),
    "rpk": RPK("rpk"),
    "rpk_reference": RPKReference("rpk_reference"),
    "total_aircraft_distance": TotalAircraftDistance("total_aircraft_distance"),
    "rtk": RTK("rtk"),
    "rtk_reference": RTKReference("rtk_reference"),
    # "short_range_distribution": ShortRangeDistribution(
    #     "short_range_distribution"
    # ),
    # "rpk_short_range": RPKShortRange(
    #     "rpk_short_range"
    # ),
    "load_factor": LoadFactor("load_factor"),
    "ask": ASK("ask"),
    "operations_simple": OperationsSimple("operations_simple"),
    "operations_contrails_simple": OperationsContrailsSimple("operations_contrails_simple"),
    "passenger_aircraft_efficiency_complex": PassengerAircraftEfficiencyComplex(
        "passenger_aircraft_efficiency_complex"
    ),
    "freight_aircraft_efficiency": FreightAircraftEfficiency("freight_aircraft_efficiency"),
    "energy_intensity": EnergyIntensity("energy_intensity"),
    "dropin_fuel_distribution": DropinFuelDistribution("dropin_fuel_distribution"),
    "gross_carbon_budget": GrossCarbonBudget("gross_carbon_budget"),
    "equivalent_gross_carbon_budget": EquivalentGrossCarbonBudget("equivalent_gross_carbon_budget"),
    "biofuel_efficiency": BiofuelEfficiency("biofuel_efficiency"),
    "electricity_based_fuel_efficiency": ElectricityBasedFuelEfficiency(
        "electricity_based_fuel_efficiency"
    ),
    "biofuel_emission_factor": BiofuelEmissionFactor("biofuel_emission_factor"),
    "electricity_emission_factor": ElectricityEmissionFactor("electricity_emission_factor"),
    "hydrogen_emission_factor": HydrogenEmissionFactor("hydrogen_emission_factor"),
    "electrofuel_emission_factor": ElectrofuelEmissionFactor("electrofuel_emission_factor"),
    "kerosene_emission_factor": KeroseneEmissionFactor("kerosene_emission_factor"),
    "biofuel_production": BiofuelProduction("biofuel_production"),
    "hydrogen_production": HydrogenProduction("hydrogen_production"),
    "biomass_availability": BiomassAvailability("biomass_availability"),
    "electricity_availability": ElectricityAvailability("electricity_availability"),
    "effective_radiative_forcing": ERF("effective_radiative_forcing"),
    "detailed_erf": DetailedERF("detailed_erf"),
    "kaya_factors": KayaFactors("kaya_factors"),
    "co2_emissions": CO2Emissions("co2_emissions"),
    "cumulative_co2_emissions": CumulativeCO2Emissions("cumulative_co2_emissions"),
    "detailed_co2_emissions": DetailedCo2Emissions("detailed_co2_emissions"),
    "detailed_cumulative_co2_emissions": DetailedCumulativeCO2Emissions(
        "detailed_cumulative_co2_emissions"
    ),
    "nox_emission_index_complex": NOxEmissionIndexComplex("nox_emission_index_complex"),
    "soot_emission_index_complex": SootEmissionIndexComplex("soot_emission_index_complex"),
    "non_co2_emissions": NonCO2Emissions("non_co2_emissions"),
    "drop_in_fuel_consumption": DropInFuelConsumption("drop_in_fuel_consumption"),
    "hydrogen_consumption": HydrogenConsumption("hydrogen_consumption"),
    "energy_consumption": EnergyConsumption("energy_consumption"),
    "biomass_consumption": BiomassConsumption("biomass_consumption"),
    "electricity_consumption": ElectricityConsumption("electricity_consumption"),
    "equivalent_co2_emissions": EquivalentCO2Emissions("equivalent_co2_emissions"),
    "temperature": Temperature("temperature"),
    "emissions_per_rpk": EmissionsPerRPK("emissions_per_rpk"),
    "emissions_per_rtk": EmissionsPerRTK("emissions_per_rtk"),
    "dropin_fuel_consumption_liter_per_pax_100km": DropinFuelConsumptionLiterPerPax100km(
        "dropin_fuel_consumption_liter_per_pax_100km"
    ),
    "carbon_budget_consumed_share": CarbonBudgetConsumedShare("carbon_budget_consumed_share"),
    "resources_consumed_share": ResourcesConsumedShare("resources_consumed_share"),
    "biofuel_mfsp": BiofuelMfsp("biofuel_mfsp"),
    "biofuel_capex": BiofuelCapex("biofuel_capex"),
    "kerosene_market_price": KerosenePrice("kerosene_market_price"),
    "kerosene_cost": KeroseneCost("kerosene_cost"),
    "biofuel_cost": BiofuelCost("biofuel_cost"),
    "co2_cost": Co2Cost("co2_cost"),
    "carbon_tax": CarbonTax("carbon_tax"),
    "electricity_cost": ElectricityCost("electricity_cost"),
    "coal_cost": CoalCost("coal_cost"),
    "gas_cost": GasCost("coal_cost"),
    "liquid_hydrogen_cost": LiquidHydrogenCost("liquid_hydrogen_cost"),
    "electrolyser_capex": ElectrolyserCapex("electrolyser_capex"),
    "electrolyser_fixed_opex": ElectrolyserFixedOpex("electrolyser_fixed_opex"),
    "electrolyser_var_opex": ElectrolyserVarOpex("electrolyser_var_opex"),
    # "electrolyser_specific_electricity": ElectrolyserSpecificElectricity(
    #     "electrolyser_specific_electricity"
    # ),
    "gas_ccs_capex": GasCcsCapex("gas_ccs_capex"),
    "gas_ccs_fixed_opex": GasCcsFixedOpex("gas_ccs_fixed_opex"),
    "gas_ccs_efficiency": GasCcsEfficiency("gas_ccs_efficiency"),
    "gas_capex": GasCapex("gas_capex"),
    "gas_fixed_opex": GasFixedOpex("gas_fixed_opex"),
    "gas_efficiency": GasEfficiency("gas_efficiency"),
    "coal_ccs_capex": CoalCcsCapex("coal_ccs_capex"),
    "coal_ccs_fixed_opex": CoalCcsFixedOpex("coal_ccs_fixed_opex"),
    "coal_ccs_efficiency": CoalCcsEfficiency("coal_ccs_efficiency"),
    "coal_capex": CoalCapex("coal_capex"),
    "coal_fixed_opex": CoalFixedOpex("coal_fixed_opex"),
    "coal_efficiency": CoalEfficiency("coal_efficiency"),
    "ccs_cost": CcsCost("ccs_cost"),
    "liquefier_capex": LiquefierCapex("liquefier_capex"),
    # "liquefier_specific_electricity": LiquefierSpecificElectricity(
    #     "liquefier_specific_electricity"
    # ),
    "electrofuel_cost": ElectrofuelCost("electrofuel_cost"),
    "electrofuel_capex": ElectrofuelCapex("electrofuel_capex"),
    "electrofuel_fixed_opex": ElectrofuelFixedOpex("electrofuel_fixed_opex"),
    "electrofuel_var_opex": ElectrofuelVarOpex("electrofuel_var_opex"),
    # "electrofuel_specific_electricity": ElectrofuelSpecificElectricity("electrofuel_specific_electricity"),
    "electrofuel_specific_co2": ElectrofuelSpecificCo2("electrofuel_specific_co2"),
    "discounted_scenario_cost": DicountedScenarioCost("discounted_scenario_cost"),
    "non_discounted_scenario_cost": NonDiscountedScenarioCost("non_discounted_scenario_cost"),
    "biofuel_abatement_potential": BiofuelAbatementPotential("biofuel_abatement_potential"),
    "passenger_aircraft_doc_energy": PassengerAircraftDocEnergy("passenger_aircraft_doc_energy"),
    "passenger_aircraft_doc_non_energy_complex": PassengerAircraftDocNonEnergyComplex(
        "passenger_aircraft_doc_non_energy_complex"
    ),
    "passenger_aircraft_total_doc": PassengerAircraftTotalDoc("passenger_aircraft_total_doc"),
    "dropin_mean_mfsp": DropInMeanMfsp("dropin_mean_mfsp"),
    "passenger_aircraft_doc_carbon_tax": PassengerAircraftDocCarbonTax(
        "passenger_aircraft_doc_carbon_tax"
    ),
    "level_carbon_offset": LevelCarbonOffset("level_carbon_offset"),
    "residual_carbon_offset": ResidualCarbonOffset("residual_carbon_offset"),
    "carbon_offset": CarbonOffset("carbon_offset"),
    "cumulative_carbon_offset": CumulativeCarbonOffset("cumulative_carbon_offset"),
    "passenger_aircraft_noc_carbon_offset": PassengerAircraftNocCarbonOffset(
        "passenger_aircraft_noc_carbon_offset"
    ),
}
