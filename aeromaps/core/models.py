from aeromaps.models.impacts.costs.airlines.direct_operating_costs import (
    PassengerAircraftDocEnergy,
    DropInMeanMfsp,
    PassengerAircraftDocCarbonTax,
    PassengerAircraftDocNonEnergyComplex,
    PassengerAircraftTotalDoc,
    PassengerAircraftDocNonEnergySimple,
)
from aeromaps.models.air_transport.aircraft_fleet_and_operations.fleet.fleet_numeric import (
    FleetEvolution,
)
from aeromaps.models.impacts.costs.efficiency_abatement_cost.fleet_abatement_cost import (
    FleetCarbonAbatementCosts,
    CargoEfficiencyCarbonAbatementCosts,
    FleetTopDownCarbonAbatementCost,
)
from aeromaps.models.impacts.costs.efficiency_abatement_cost.operations_abatement_cost import (
    OperationsAbatementCost,
)
from aeromaps.models.impacts.costs.energy.detailled.biofuel import (
    BiofuelCost,
    BiofuelVarOpex,
    BiofuelFeedstock,
    BiofuelCapex,
)
from aeromaps.models.impacts.costs.energy.simple.biofuel_simple import (
    BiofuelCostSimple,
    BiofuelMfspSimple,
)
from aeromaps.models.impacts.costs.energy.simple.electricity_direct_use import ElectricityDirectUse
from aeromaps.models.impacts.costs.energy.simple.liquid_hydrogen_simple import (
    HydrogenCostSimple,
    HydrogenMfspSimple,
)
from aeromaps.models.impacts.costs.energy.simple.power_to_liquid_simple import (
    ElectrofuelCostSimple,
    ElectrofuelMfspSimple,
)

from aeromaps.models.impacts.costs.manufacturers.non_recurring_costs import NonRecurringCosts
from aeromaps.models.impacts.costs.manufacturers.recurring_costs import RecurringCosts
from aeromaps.models.impacts.costs.operations.operations_cost import (
    LoadFactorEfficiencyCost,
    OperationalEfficiencyCost,
)
from aeromaps.models.impacts.costs.scenario.exogneous_carbon_price import (
    ExogenousCarbonPriceTrajectory,
)
from aeromaps.models.impacts.energy_resources.abatement_potential import (
    DropinAbatementPotential,
    EnergyAbatementEffective,
)

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
    OperationsLogistic,
    OperationsInterpolation,
)
from aeromaps.models.air_transport.aircraft_fleet_and_operations.non_co2.non_co2 import (
    OperationsContrailsSimple,
    FuelEffectCorrectionContrails,
    WithoutFuelEffectCorrectionContrails,
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
    SimplifiedERFCo2,
    SimplifiedERFNox,
    ERFNox,
    ERFOthers,
    ERFTotal,
    ERFDetailed,
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
    ElectricConsumption,
    EnergyConsumption,
)
from aeromaps.models.impacts.energy_resources.resources_consumption import (
    BiomassConsumption,
    ElectricityConsumption,
)
from aeromaps.models.impacts.climate.climate import (
    TemperatureGWPStar,
    TemperatureSimpleGWPStar,
    TemperatureFair,
)
from aeromaps.models.impacts.others.others import (
    EmissionsPerRPK,
    EmissionsPerRTK,
    DropinFuelConsumptionLiterPerPax100km,
)
from aeromaps.models.impacts.others.comparison import (
    CarbonBudgetConsumedShare,
    EquivalentCarbonBudgetConsumedShare,
    ResourcesConsumedShare,
)
from aeromaps.models.impacts.emissions.carbon_offset import (
    LevelCarbonOffset,
    ResidualCarbonOffset,
    CarbonOffset,
    CumulativeCarbonOffset,
)

# COSTS
from aeromaps.models.impacts.costs.energy.market_prices import (
    ElectricityCost,
    Co2Cost,
    KeroseneCost,
    KerosenePrice,
    CarbonTax,
    KeroseneBAUCost,
    CoalCost,
    GasCost,
    ElectricityLoadFactor,
)
from aeromaps.models.impacts.costs.energy.detailled.power_to_liquid import (
    ElectrofuelCost,
    ElectrofuelCapex,
    ElectrofuelFixedOpex,
    ElectrofuelVarOpex,
    ElectrofuelSpecificCo2,
)
from aeromaps.models.impacts.costs.energy.detailled.liquid_hydrogen import (
    LiquidHydrogenCost,
    ElectrolyserCapex,
    ElectrolyserFixedOpex,
    ElectrolyserVarOpex,
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
)
from aeromaps.models.impacts.costs.scenario.scenario_cost import (
    DicountedScenarioCost,
    NonDiscountedScenarioCost,
)

from aeromaps.models.impacts.costs.airlines.non_operating_costs_cost import (
    PassengerAircraftNonOpCosts,
    PassengerAircraftPassengerTax,
)

from aeromaps.models.impacts.costs.airlines.indirect_operating_costs import (
    PassengerAircraftIndirectOpCosts,
    PassengerAircraftNocCarbonOffset,
)

from aeromaps.models.impacts.costs.airlines.operational_profit import (
    PassengerAircraftOperationalProfit,
)

from aeromaps.models.impacts.costs.airlines.total_airline_cost_and_airfare import (
    PassengerAircraftTotalCostAirfare,
)

models_traffic = {
    "rpk_measures": RPKMeasures("rpk_measures"),
    "rpk": RPK("rpk"),
    "rpk_reference": RPKReference("rpk_reference"),
    "total_aircraft_distance": TotalAircraftDistance("total_aircraft_distance"),
    "rtk": RTK("rtk"),
    "rtk_reference": RTKReference("rtk_reference"),
    "ask": ASK("ask"),
}

models_efficiency_top_down = {
    "load_factor": LoadFactor("load_factor"),
    "operations_logistic": OperationsLogistic("operations_logistic"),
    "operations_contrails_simple": OperationsContrailsSimple("operations_contrails_simple"),
    "passenger_aircraft_efficiency_simple": PassengerAircraftEfficiencySimple(
        "passenger_aircraft_efficiency_simple"
    ),
    "freight_aircraft_efficiency": FreightAircraftEfficiency("freight_aircraft_efficiency"),
    "energy_intensity": EnergyIntensity("energy_intensity"),
    "nox_emission_index": NOxEmissionIndex("nox_emission_index"),
    "soot_emission_index": SootEmissionIndex("soot_emission_index"),
}

models_efficiency_top_down_interp = {
    "load_factor": LoadFactor("load_factor"),
    "operations_interpolation": OperationsInterpolation("operations_interpolation"),
    "operations_contrails_simple": OperationsContrailsSimple("operations_contrails_simple"),
    "passenger_aircraft_efficiency_simple": PassengerAircraftEfficiencySimple(
        "passenger_aircraft_efficiency_simple"
    ),
    "freight_aircraft_efficiency": FreightAircraftEfficiency("freight_aircraft_efficiency"),
    "energy_intensity": EnergyIntensity("energy_intensity"),
    "nox_emission_index": NOxEmissionIndex("nox_emission_index"),
    "soot_emission_index": SootEmissionIndex("soot_emission_index"),
}

models_efficiency_bottom_up = {
    "load_factor": LoadFactor("load_factor"),
    "operations_logistic": OperationsLogistic("operations_logistic"),
    "operations_contrails_simple": OperationsContrailsSimple("operations_contrails_simple"),
    "passenger_aircraft_efficiency_complex": PassengerAircraftEfficiencyComplex(
        "passenger_aircraft_efficiency_complex"
    ),
    "freight_aircraft_efficiency": FreightAircraftEfficiency("freight_aircraft_efficiency"),
    "energy_intensity": EnergyIntensity("energy_intensity"),
    "nox_emission_index_complex": NOxEmissionIndexComplex("nox_emission_index_complex"),
    "soot_emission_index_complex": SootEmissionIndexComplex("soot_emission_index_complex"),
}

models_energy_without_fuel_effect = {
    "dropin_fuel_distribution": DropinFuelDistribution("dropin_fuel_distribution"),
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
    "drop_in_fuel_consumption": DropInFuelConsumption("drop_in_fuel_consumption"),
    "hydrogen_consumption": HydrogenConsumption("hydrogen_consumption"),
    "electric_consumption": ElectricConsumption("electric_consumption"),
    "energy_consumption": EnergyConsumption("energy_consumption"),
    "biomass_consumption": BiomassConsumption("biomass_consumption"),
    "electricity_consumption": ElectricityConsumption("electricity_consumption"),
    "dropin_fuel_consumption_liter_per_pax_100km": DropinFuelConsumptionLiterPerPax100km(
        "dropin_fuel_consumption_liter_per_pax_100km"
    ),
    "without_fuel_effect_correction_contrails": WithoutFuelEffectCorrectionContrails(
        "without_fuel_effect_correction_contrails"
    ),
}

models_energy_with_fuel_effect = {
    "dropin_fuel_distribution": DropinFuelDistribution("dropin_fuel_distribution"),
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
    "drop_in_fuel_consumption": DropInFuelConsumption("drop_in_fuel_consumption"),
    "hydrogen_consumption": HydrogenConsumption("hydrogen_consumption"),
    "electric_consumption": ElectricConsumption("electric_consumption"),
    "energy_consumption": EnergyConsumption("energy_consumption"),
    "biomass_consumption": BiomassConsumption("biomass_consumption"),
    "electricity_consumption": ElectricityConsumption("electricity_consumption"),
    "dropin_fuel_consumption_liter_per_pax_100km": DropinFuelConsumptionLiterPerPax100km(
        "dropin_fuel_consumption_liter_per_pax_100km"
    ),
    "fuel_effect_correction_contrails": FuelEffectCorrectionContrails(
        "fuel_effect_correction_contrails"
    ),
}

models_offset = {
    "level_carbon_offset": LevelCarbonOffset("level_carbon_offset"),
    "residual_carbon_offset": ResidualCarbonOffset("residual_carbon_offset"),
    "carbon_offset": CarbonOffset("carbon_offset"),
    "cumulative_carbon_offset": CumulativeCarbonOffset("cumulative_carbon_offset"),
}

models_climate_simple_gwpstar = {
    "simplified_effective_radiative_forcing_co2": SimplifiedERFCo2(
        "simplified_effective_radiative_forcing_co2"
    ),
    "simplified_effective_radiative_forcing_nox": SimplifiedERFNox(
        "simplified_effective_radiative_forcing_nox"
    ),
    "effective_radiative_forcing_others": ERFOthers("effective_radiative_forcing_others"),
    "effective_radiative_forcing_detailed": ERFDetailed("effective_radiative_forcing_detailed"),
    "effective_radiative_forcing_total": ERFTotal("effective_radiative_forcing_total"),
    "kaya_factors": KayaFactors("kaya_factors"),
    "co2_emissions": CO2Emissions("co2_emissions"),
    "cumulative_co2_emissions": CumulativeCO2Emissions("cumulative_co2_emissions"),
    "detailed_co2_emissions": DetailedCo2Emissions("detailed_co2_emissions"),
    "detailed_cumulative_co2_emissions": DetailedCumulativeCO2Emissions(
        "detailed_cumulative_co2_emissions"
    ),
    "non_co2_emissions": NonCO2Emissions("non_co2_emissions"),
    "temperature_simple_gwpstar": TemperatureSimpleGWPStar("temperature_simple_gwpstar"),
    "emissions_per_rpk": EmissionsPerRPK("emissions_per_rpk"),
    "emissions_per_rtk": EmissionsPerRTK("emissions_per_rtk"),
}

models_climate_gwpstar = {
    "simplified_effective_radiative_forcing_co2": SimplifiedERFCo2(
        "simplified_effective_radiative_forcing_co2"
    ),
    "effective_radiative_forcing_nox": ERFNox("effective_radiative_forcing_nox"),
    "effective_radiative_forcing_others": ERFOthers("effective_radiative_forcing_others"),
    "effective_radiative_forcing_detailed": ERFDetailed("effective_radiative_forcing_detailed"),
    "effective_radiative_forcing_total": ERFTotal("effective_radiative_forcing_total"),
    "kaya_factors": KayaFactors("kaya_factors"),
    "co2_emissions": CO2Emissions("co2_emissions"),
    "cumulative_co2_emissions": CumulativeCO2Emissions("cumulative_co2_emissions"),
    "detailed_co2_emissions": DetailedCo2Emissions("detailed_co2_emissions"),
    "detailed_cumulative_co2_emissions": DetailedCumulativeCO2Emissions(
        "detailed_cumulative_co2_emissions"
    ),
    "non_co2_emissions": NonCO2Emissions("non_co2_emissions"),
    "temperature_gwpstar": TemperatureGWPStar("temperature_gwpstar"),
    "emissions_per_rpk": EmissionsPerRPK("emissions_per_rpk"),
    "emissions_per_rtk": EmissionsPerRTK("emissions_per_rtk"),
}

models_climate_fair = {
    "effective_radiative_forcing_nox": ERFNox("effective_radiative_forcing_nox"),
    "effective_radiative_forcing_others": ERFOthers("effective_radiative_forcing_others"),
    "effective_radiative_forcing_detailed": ERFDetailed("effective_radiative_forcing_detailed"),
    "effective_radiative_forcing_total": ERFTotal("effective_radiative_forcing_total"),
    "kaya_factors": KayaFactors("kaya_factors"),
    "co2_emissions": CO2Emissions("co2_emissions"),
    "cumulative_co2_emissions": CumulativeCO2Emissions("cumulative_co2_emissions"),
    "detailed_co2_emissions": DetailedCo2Emissions("detailed_co2_emissions"),
    "detailed_cumulative_co2_emissions": DetailedCumulativeCO2Emissions(
        "detailed_cumulative_co2_emissions"
    ),
    "non_co2_emissions": NonCO2Emissions("non_co2_emissions"),
    "temperature_fair": TemperatureFair("temperature_fair"),
    "emissions_per_rpk": EmissionsPerRPK("emissions_per_rpk"),
    "emissions_per_rtk": EmissionsPerRTK("emissions_per_rtk"),
}

models_sustainability = {
    "gross_carbon_budget": GrossCarbonBudget("gross_carbon_budget"),
    "equivalent_gross_carbon_budget": EquivalentGrossCarbonBudget("equivalent_gross_carbon_budget"),
    "biomass_availability": BiomassAvailability("biomass_availability"),
    "electricity_availability": ElectricityAvailability("electricity_availability"),
    "carbon_budget_consumed_share": CarbonBudgetConsumedShare("carbon_budget_consumed_share"),
    "equivalent_carbon_budget_consumed_share": EquivalentCarbonBudgetConsumedShare(
        "equivalent_carbon_budget_consumed_share"
    ),
    "resources_consumed_share": ResourcesConsumedShare("resources_consumed_share"),
}

models_sustainability_without_equivalent_emissions = {
    "gross_carbon_budget": GrossCarbonBudget("gross_carbon_budget"),
    "equivalent_gross_carbon_budget": EquivalentGrossCarbonBudget("equivalent_gross_carbon_budget"),
    "biomass_availability": BiomassAvailability("biomass_availability"),
    "electricity_availability": ElectricityAvailability("electricity_availability"),
    "carbon_budget_consumed_share": CarbonBudgetConsumedShare("carbon_budget_consumed_share"),
    "resources_consumed_share": ResourcesConsumedShare("resources_consumed_share"),
}


models_energy_cost_complex = {
    "biofuel_capex": BiofuelCapex("biofuel_capex"),
    "kerosene_market_price": KerosenePrice("kerosene_market_price"),
    "kerosene_cost": KeroseneCost("kerosene_cost"),
    "kerosene_BAU_cost": KeroseneBAUCost("kerosene_BAU_cost"),
    "biofuel_cost": BiofuelCost("biofuel_cost"),
    "co2_cost": Co2Cost("co2_cost"),
    "carbon_tax": CarbonTax("carbon_tax"),
    "electricity_cost": ElectricityCost("electricity_cost"),
    "electricity_load_factor": ElectricityLoadFactor("electricity_load_factor"),
    "coal_cost": CoalCost("coal_cost"),
    "gas_cost": GasCost("coal_cost"),
    "liquid_hydrogen_cost": LiquidHydrogenCost("liquid_hydrogen_cost"),
    "electrolyser_capex": ElectrolyserCapex("electrolyser_capex"),
    "electrolyser_fixed_opex": ElectrolyserFixedOpex("electrolyser_fixed_opex"),
    "electrolyser_var_opex": ElectrolyserVarOpex("electrolyser_var_opex"),
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
    "electrofuel_cost": ElectrofuelCost("electrofuel_cost"),
    "electrofuel_capex": ElectrofuelCapex("electrofuel_capex"),
    "electrofuel_fixed_opex": ElectrofuelFixedOpex("electrofuel_fixed_opex"),
    "electrofuel_var_opex": ElectrofuelVarOpex("electrofuel_var_opex"),
    "electrofuel_specific_co2": ElectrofuelSpecificCo2("electrofuel_specific_co2"),
    "biofuel_var_opex": BiofuelVarOpex("biofuel_var_opex"),
    "biofuel_feedstock_cost": BiofuelFeedstock("biofuel_feedstock_cost"),
    "dropin_mean_mfsp": DropInMeanMfsp("dropin_mean_mfsp"),
    "discounted_scenario_cost": DicountedScenarioCost("discounted_scenario_cost"),
    "non_discounted_scenario_cost": NonDiscountedScenarioCost("non_discounted_scenario_cost"),
    "exogenous_carbon_price_trajectory": ExogenousCarbonPriceTrajectory(
        "exogenous_carbon_price_trajectory"
    ),
    "electricity_direct_use": ElectricityDirectUse("electricity_direct_use"),
}

models_energy_cost_simple = {
    "kerosene_market_price": KerosenePrice("kerosene_market_price"),
    "kerosene_cost": KeroseneCost("kerosene_cost"),
    "kerosene_BAU_cost": KeroseneBAUCost("kerosene_BAU_cost"),
    "biofuel_cost_simple": BiofuelCostSimple("biofuel_cost_simple"),
    "biofuel_mfsp_simple": BiofuelMfspSimple("biofuel_mfsp_simple"),
    "electrofuel_cost_simple": ElectrofuelCostSimple("electrofuel_cost_simple"),
    "electrofuel_mfsp_simple": ElectrofuelMfspSimple("electrofuel_mfsp_simple"),
    "hydrogen_cost_simple": HydrogenCostSimple("hydrogen_cost_simple"),
    "hydrogen_mfsp_simple": HydrogenMfspSimple("hydrogen_mfsp_simple"),
    "electricity_cost": ElectricityCost("electricity_cost"),
    "electricity_direct_use": ElectricityDirectUse("electricity_direct_use"),
    "co2_cost": Co2Cost("co2_cost"),
    "carbon_tax": CarbonTax("carbon_tax"),
    "dropin_mean_mfsp": DropInMeanMfsp("dropin_mean_mfsp"),
    "discounted_scenario_cost": DicountedScenarioCost("discounted_scenario_cost"),
    "non_discounted_scenario_cost": NonDiscountedScenarioCost("non_discounted_scenario_cost"),
}


models_operation_cost_top_down = {
    "load_factor_efficiency_cost": LoadFactorEfficiencyCost("load_factor_efficiency_cost"),
    "operational_efficiency_cost": OperationalEfficiencyCost("operational_efficiency_cost"),
    "passenger_aircraft_doc_energy": PassengerAircraftDocEnergy("passenger_aircraft_doc_energy"),
    "passenger_aircraft_total_doc": PassengerAircraftTotalDoc("passenger_aircraft_total_doc"),
    "passenger_aircraft_doc_carbon_tax": PassengerAircraftDocCarbonTax(
        "passenger_aircraft_doc_carbon_tax"
    ),
    "passenger_aircraft_noc_carbon_offset": PassengerAircraftNocCarbonOffset(
        "passenger_aircraft_noc_carbon_offset"
    ),
    "passenger_aircraft_noc": PassengerAircraftNonOpCosts("passenger_aircraft_noc"),
    "passenger_aircraft_ioc": PassengerAircraftIndirectOpCosts("passenger_aircraft_ioc"),
    "passenger_aircraft_operational_profit": PassengerAircraftOperationalProfit(
        "passenger_aircraft_operational_profit"
    ),
    "passenger_aircraft_passenger_tax": PassengerAircraftPassengerTax(
        "passenger_aircraft_passenger_tax"
    ),
    "passenger_aircraft_total_cost_and_airfare": PassengerAircraftTotalCostAirfare(
        "passenger_aircraft_total_cost_and_airfare"
    ),
    "passenger_aircraft_doc_non_energy_simple": PassengerAircraftDocNonEnergySimple(
        "passenger_aircraft_doc_non_energy_simple"
    ),
}

models_operation_cost_bottom_up = {
    "load_factor_efficiency_cost": LoadFactorEfficiencyCost("load_factor_efficiency_cost"),
    "operational_efficiency_cost": OperationalEfficiencyCost("operational_efficiency_cost"),
    "passenger_aircraft_doc_energy": PassengerAircraftDocEnergy("passenger_aircraft_doc_energy"),
    "passenger_aircraft_total_doc": PassengerAircraftTotalDoc("passenger_aircraft_total_doc"),
    "passenger_aircraft_doc_carbon_tax": PassengerAircraftDocCarbonTax(
        "passenger_aircraft_doc_carbon_tax"
    ),
    "passenger_aircraft_noc_carbon_offset": PassengerAircraftNocCarbonOffset(
        "passenger_aircraft_noc_carbon_offset"
    ),
    "passenger_aircraft_noc": PassengerAircraftNonOpCosts("passenger_aircraft_noc"),
    "passenger_aircraft_ioc": PassengerAircraftIndirectOpCosts("passenger_aircraft_ioc"),
    "passenger_aircraft_operational_profit": PassengerAircraftOperationalProfit(
        "passenger_aircraft_operational_profit"
    ),
    "passenger_aircraft_passenger_tax": PassengerAircraftPassengerTax(
        "passenger_aircraft_passenger_tax"
    ),
    "passenger_aircraft_total_cost_and_airfare": PassengerAircraftTotalCostAirfare(
        "passenger_aircraft_total_cost_and_airfare"
    ),
    "passenger_aircraft_doc_non_energy_complex": PassengerAircraftDocNonEnergyComplex(
        "passenger_aircraft_doc_non_energy_complex"
    ),
}

models_production_cost = {
    "fleet_numeric": FleetEvolution("fleet_numeric"),
    "recurring_costs": RecurringCosts("recurring_costs"),
    "non_recurring_costs": NonRecurringCosts("non_recurring_costs"),
}

models_abatements_cost = {
    "drop_in_abatement_potential": DropinAbatementPotential("drop_in_abatement_potential"),
    "energy_abatement_effective": EnergyAbatementEffective("energy_abatement_effective"),
    "operations_abatement_cost": OperationsAbatementCost("operations_abatement_cost"),
    "fleet_abatement_cost": FleetCarbonAbatementCosts("fleet_abatement_cost"),
    "cargo_efficiency_carbon_abatement_cost": CargoEfficiencyCarbonAbatementCosts(
        "cargo_efficiency_carbon_abatement_cost"
    ),
}


models_abatements_cost_simplified = {
    "energy_abatement_effective": EnergyAbatementEffective("energy_abatement_effective"),
    "operations_abatement_cost": OperationsAbatementCost("operations_abatement_cost"),
    "fleet_top_down_carbon_abatement_cost": FleetTopDownCarbonAbatementCost(
        "fleet_top_down_carbon_abatement_cost"
    ),
    "cargo_efficiency_carbon_abatement_cost": CargoEfficiencyCarbonAbatementCosts(
        "cargo_efficiency_carbon_abatement_cost"
    ),
}


default_models_top_down = {
    "models_traffic": models_traffic,
    "models_efficiency_top_down": models_efficiency_top_down,
    "models_energy_without_fuel_effect": models_energy_without_fuel_effect,
    "models_offset": models_offset,
    "models_climate_simple_gwpstar": models_climate_simple_gwpstar,
    "models_sustainability": models_sustainability,
    "models_energy_cost_simple": models_energy_cost_simple,
    "models_operation_cost_top_down": models_operation_cost_top_down,
}

default_models_bottom_up = {
    "models_traffic": models_traffic,
    "models_efficiency_bottom_up": models_efficiency_bottom_up,
    "models_energy_without_fuel_effect": models_energy_without_fuel_effect,
    "models_offset": models_offset,
    "models_climate_simple_gwpstar": models_climate_simple_gwpstar,
    "models_sustainability": models_sustainability,
    "models_energy_cost_complex": models_energy_cost_complex,
    "models_operation_cost_bottom_up": models_operation_cost_bottom_up,
}
