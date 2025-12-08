"""
This module creates dictionaries of default models for various AeroMAPS configurations.
"""

from aeromaps.models.air_transport.air_traffic.price_elasticity import RPKWithElasticity
from aeromaps.models.impacts.costs.airlines.direct_operating_costs import (
    PassengerAircraftDocEnergy,
    PassengerAircraftDocNonEnergyComplex,
    PassengerAircraftTotalDoc,
    PassengerAircraftDocNonEnergySimple,
    PassengerAircraftDocEnergyCarbonTax,
    PassengerAircraftDocEnergyTax,
    PassengerAircraftDocEnergySubsidy,
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
from aeromaps.models.impacts.costs.carbon_tax.carbon_tax import CarbonTax

from aeromaps.models.impacts.costs.manufacturers.non_recurring_costs import NonRecurringCosts
from aeromaps.models.impacts.costs.manufacturers.recurring_costs import RecurringCosts
from aeromaps.models.impacts.costs.operations.operations_cost import (
    LoadFactorEfficiencyCost,
    OperationalEfficiencyCost,
)
from aeromaps.models.impacts.costs.scenario.exogneous_carbon_price import (
    ExogenousCarbonPriceTrajectory,
)
from aeromaps.models.impacts.generic_energy_model.common.energy_carriers_means import (
    EnergyCarriersMassicShares,
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
    PassengerAircraftEfficiencySimpleShares,
    PassengerAircraftEfficiencyComplex,
    FreightAircraftEfficiency,
    PassengerAircraftEfficiencySimpleASK,
)
from aeromaps.models.air_transport.aircraft_fleet_and_operations.aircraft_fleet_and_operations import (
    EnergyIntensity,
)

from aeromaps.models.optimisation.constraints.carbon_budget_constraint import CarbonBudgetConstraint

# from aeromaps.models.optimisation.constraints.energy_constraint import (
#     BlendCompletenessConstraint,
#     ElectricityAvailabilityConstraintTrajectory,
#     BiomassAvailabilityConstraintTrajectory,
#     ElectrofuelUseGrowthConstraint,
#     BiofuelUseGrowthConstraint,
# )
from aeromaps.models.sustainability_assessment.climate.carbon_budget import GrossCarbonBudget
from aeromaps.models.sustainability_assessment.climate.temperature_target import (
    TemperatureTarget,
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
    H2OEmissionIndex,
    SulfurEmissionIndex,
)
from aeromaps.models.impacts.energy_resources.energy_consumption import (
    DropInFuelConsumption,
    HydrogenConsumption,
    ElectricConsumption,
    EnergyConsumption,
    DropInFuelDetailledConsumption,
)

from aeromaps.models.impacts.others.others import (
    EmissionsPerRPK,
    EmissionsPerRTK,
    DropinFuelConsumptionLiterPerPax100km,
)
from aeromaps.models.sustainability_assessment.climate.comparison import (
    CarbonBudgetConsumedShare,
    TemperatureTargetConsumedShare,
)
from aeromaps.models.impacts.emissions.carbon_offset import (
    LevelCarbonOffset,
    ResidualCarbonOffset,
    CarbonOffset,
    CumulativeCarbonOffset,
)

# COSTS
from aeromaps.models.impacts.costs.scenario.scenario_cost import (
    DicountedScenarioCost,
    NonDiscountedScenarioCost,
    TotalSurplusLoss,
    TotalAirlineCost,
    TotalAirlineCostNoElast,
    # ConsumerSurplusLoss,
    # AirlineSurplusLoss,
    # TaxRevenueLoss,
    # TotalWelfareLoss,
)

from aeromaps.models.impacts.costs.airlines.non_operating_costs import (
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
    PassengerAircraftSimpleAirfare,
    PassengerAircraftTotalCost,
    PassengerAircraftMarginalCost,
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


models_traffic_cost_feedback = {
    "rpk_with_elasticity": RPKWithElasticity("rpk_with_elasticity"),
    "rpk_measures": RPKMeasures("rpk_measures"),
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
    "passenger_aircraft_efficiency_simple_shares": PassengerAircraftEfficiencySimpleShares(
        "passenger_aircraft_efficiency_simple_shares"
    ),
    "passenger_aircraft_efficiency_simple_ask": PassengerAircraftEfficiencySimpleASK(
        "passenger_aircraft_efficiency_simple_ask"
    ),
    "freight_aircraft_efficiency": FreightAircraftEfficiency("freight_aircraft_efficiency"),
    "energy_intensity": EnergyIntensity("energy_intensity"),
    "nox_emission_index": NOxEmissionIndex("nox_emission_index"),
    "soot_emission_index": SootEmissionIndex("soot_emission_index"),
    "h2o_emission_index": H2OEmissionIndex("h2o_emission_index"),
    "sulfur_emission_index": SulfurEmissionIndex("sulfur_emission_index"),
}

models_efficiency_top_down_interp = {
    "load_factor": LoadFactor("load_factor"),
    "operations_interpolation": OperationsInterpolation("operations_interpolation"),
    "operations_contrails_simple": OperationsContrailsSimple("operations_contrails_simple"),
    "passenger_aircraft_efficiency_simple_shares": PassengerAircraftEfficiencySimpleShares(
        "passenger_aircraft_efficiency_simple_shares"
    ),
    "passenger_aircraft_efficiency_simple_ask": PassengerAircraftEfficiencySimpleASK(
        "passenger_aircraft_efficiency_simple_ask"
    ),
    "freight_aircraft_efficiency": FreightAircraftEfficiency("freight_aircraft_efficiency"),
    "energy_intensity": EnergyIntensity("energy_intensity"),
    "nox_emission_index": NOxEmissionIndex("nox_emission_index"),
    "soot_emission_index": SootEmissionIndex("soot_emission_index"),
    "h2o_emission_index": H2OEmissionIndex("h2o_emission_index"),
    "sulfur_emission_index": SulfurEmissionIndex("sulfur_emission_index"),
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
    "h2o_emission_index": H2OEmissionIndex("h2o_emission_index"),
    "sulfur_emission_index": SulfurEmissionIndex("sulfur_emission_index"),
}


models_energy_without_fuel_effect = {
    "drop_in_fuel_consumption": DropInFuelConsumption("drop_in_fuel_consumption"),
    "drop_in_fuel_detailed_consumption": DropInFuelDetailledConsumption(
        "drop_in_fuel_detailed_consumption"
    ),
    "hydrogen_consumption": HydrogenConsumption("hydrogen_consumption"),
    "electric_consumption": ElectricConsumption("electric_consumption"),
    "energy_consumption": EnergyConsumption("energy_consumption"),
    "dropin_fuel_consumption_liter_per_pax_100km": DropinFuelConsumptionLiterPerPax100km(
        "dropin_fuel_consumption_liter_per_pax_100km"
    ),
    "without_fuel_effect_correction_contrails": WithoutFuelEffectCorrectionContrails(
        "without_fuel_effect_correction_contrails"
    ),
    "energy_carriers_massic_shares": EnergyCarriersMassicShares("energy_carriers_massic_shares"),
}

models_energy_with_fuel_effect = {
    "drop_in_fuel_consumption": DropInFuelConsumption("drop_in_fuel_consumption"),
    "drop_in_fuel_detailed_consumption": DropInFuelDetailledConsumption(
        "drop_in_fuel_detailed_consumption"
    ),
    "hydrogen_consumption": HydrogenConsumption("hydrogen_consumption"),
    "electric_consumption": ElectricConsumption("electric_consumption"),
    "energy_consumption": EnergyConsumption("energy_consumption"),
    "dropin_fuel_consumption_liter_per_pax_100km": DropinFuelConsumptionLiterPerPax100km(
        "dropin_fuel_consumption_liter_per_pax_100km"
    ),
    "fuel_effect_correction_contrails": FuelEffectCorrectionContrails(
        "fuel_effect_correction_contrails"
    ),
    "energy_carriers_massic_shares": EnergyCarriersMassicShares("energy_carriers_massic_shares"),
}

models_offset = {
    "level_carbon_offset": LevelCarbonOffset("level_carbon_offset"),
    "residual_carbon_offset": ResidualCarbonOffset("residual_carbon_offset"),
    "carbon_offset": CarbonOffset("carbon_offset"),
    "cumulative_carbon_offset": CumulativeCarbonOffset("cumulative_carbon_offset"),
}

models_emissions = {
    "kaya_factors": KayaFactors("kaya_factors"),
    "co2_emissions": CO2Emissions("co2_emissions"),
    "cumulative_co2_emissions": CumulativeCO2Emissions("cumulative_co2_emissions"),
    "detailed_co2_emissions": DetailedCo2Emissions("detailed_co2_emissions"),
    "detailed_cumulative_co2_emissions": DetailedCumulativeCO2Emissions(
        "detailed_cumulative_co2_emissions"
    ),
    "non_co2_emissions": NonCO2Emissions("non_co2_emissions"),
    "emissions_per_rpk": EmissionsPerRPK("emissions_per_rpk"),
    "emissions_per_rtk": EmissionsPerRTK("emissions_per_rtk"),
}

models_sustainability = {
    "gross_carbon_budget": GrossCarbonBudget("gross_carbon_budget"),
    "temperature_target": TemperatureTarget("temperature_target"),
    "carbon_budget_consumed_share": CarbonBudgetConsumedShare("carbon_budget_consumed_share"),
    "temperature_target_consumed_share": TemperatureTargetConsumedShare("temperature_target_consumed_share"),
}

models_energy_cost = {
    "carbon_tax": CarbonTax("carbon_tax"),
    "discounted_scenario_cost": DicountedScenarioCost("discounted_scenario_cost"),
    "non_discounted_scenario_cost": NonDiscountedScenarioCost("non_discounted_scenario_cost"),
    "exogenous_carbon_price_trajectory": ExogenousCarbonPriceTrajectory(
        "exogenous_carbon_price_trajectory"
    ),
}

models_operation_cost_common = {
    "load_factor_efficiency_cost": LoadFactorEfficiencyCost("load_factor_efficiency_cost"),
    "operational_efficiency_cost": OperationalEfficiencyCost("operational_efficiency_cost"),
    "passenger_aircraft_doc_energy": PassengerAircraftDocEnergy("passenger_aircraft_doc_energy"),
    "passenger_aircraft_doc_energy_carbon_tax": PassengerAircraftDocEnergyCarbonTax(
        "passenger_aircraft_doc_energy_carbon_tax"
    ),
    "passenger_aircraft_doc_energy_tax": PassengerAircraftDocEnergyTax(
        "passenger_aircraft_doc_energy_tax"
    ),
    "passenger_aircraft_doc_energy_subsidy": PassengerAircraftDocEnergySubsidy(
        "passenger_aircraft_doc_energy_subsidy"
    ),
    "passenger_aircraft_total_doc": PassengerAircraftTotalDoc("passenger_aircraft_total_doc"),
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
    "passenger_aircraft_total_cost": PassengerAircraftTotalCost("passenger_aircraft_total_cost"),
}

models_operation_cost_top_down = {
    "models_operation_cost_common": models_operation_cost_common,
    "passenger_aircraft_doc_non_energy_simple": PassengerAircraftDocNonEnergySimple(
        "passenger_aircraft_doc_non_energy_simple"
    ),
    "passenger_aircraft_simple_airfare": PassengerAircraftSimpleAirfare(
        "passenger_aircraft_simple_airfare"
    ),
    "total_airline_cost_no_elast": TotalAirlineCostNoElast("total_airline_cost_no_elast"),
}

models_operation_cost_bottom_up = {
    "models_operation_cost_common": models_operation_cost_common,
    "passenger_aircraft_doc_non_energy_complex": PassengerAircraftDocNonEnergyComplex(
        "passenger_aircraft_doc_non_energy_complex"
    ),
    "passenger_aircraft_simple_airfare": PassengerAircraftSimpleAirfare(
        "passenger_aircraft_simple_airfare"
    ),
    "total_airline_cost_no_elast": TotalAirlineCostNoElast("total_airline_cost_no_elast"),
}

models_operation_cost_top_down_feedback = {
    "models_operation_cost_common": models_operation_cost_common,
    "passenger_aircraft_doc_non_energy_simple": PassengerAircraftDocNonEnergySimple(
        "passenger_aircraft_doc_non_energy_simple"
    ),
    "passenger_aircraft_marginal_cost": PassengerAircraftMarginalCost(
        "passenger_aircraft_marginal_cost"
    ),
    "total_airline_cost": TotalAirlineCost("total_airline_cost"),
}

models_operation_cost_bottom_up_feedback = {
    "models_operation_cost_common": models_operation_cost_common,
    "passenger_aircraft_doc_non_energy_complex": PassengerAircraftDocNonEnergyComplex(
        "passenger_aircraft_doc_non_energy_complex"
    ),
    "passenger_aircraft_marginal_cost": PassengerAircraftMarginalCost(
        "passenger_aircraft_marginal_cost"
    ),
    "total_airline_cost": TotalAirlineCost("total_airline_cost"),
}

models_production_cost = {
    "fleet_numeric": FleetEvolution("fleet_numeric"),
    "recurring_costs": RecurringCosts("recurring_costs"),
    "non_recurring_costs": NonRecurringCosts("non_recurring_costs"),
}

models_abatements_cost = {
    # "drop_in_abatement_potential": DropinAbatementPotential("drop_in_abatement_potential"),
    # "energy_abatement_effective": EnergyAbatementEffective("energy_abatement_effective"),
    "operations_abatement_cost": OperationsAbatementCost("operations_abatement_cost"),
    "fleet_abatement_cost": FleetCarbonAbatementCosts("fleet_abatement_cost"),
    "cargo_efficiency_carbon_abatement_cost": CargoEfficiencyCarbonAbatementCosts(
        "cargo_efficiency_carbon_abatement_cost"
    ),
}

models_abatements_cost_simplified = {
    # "energy_abatement_effective": EnergyAbatementEffective("energy_abatement_effective"),
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
    "models_emissions": models_emissions,
    "models_sustainability": models_sustainability,
    "models_energy_cost": models_energy_cost,
    "models_operation_cost_top_down": models_operation_cost_top_down,
}

default_models_bottom_up = {
    "models_traffic": models_traffic,
    "models_efficiency_bottom_up": models_efficiency_bottom_up,
    "models_energy_without_fuel_effect": models_energy_without_fuel_effect,
    "models_offset": models_offset,
    "models_emissions": models_emissions,
    "models_sustainability": models_sustainability,
    "models_energy_cost": models_energy_cost,
    "models_operation_cost_bottom_up": models_operation_cost_bottom_up,
}

models_optim_simple = {
    "models_traffic": models_traffic,
    "models_efficiency_top_down": models_efficiency_top_down,
    "models_energy_without_fuel_effect": models_energy_without_fuel_effect,
    "models_offset": models_offset,
    "kaya_factors": KayaFactors("kaya_factors"),
    "co2_emissions": CO2Emissions("co2_emissions"),
    "cumulative_co2_emissions": CumulativeCO2Emissions("cumulative_co2_emissions"),
    "detailed_co2_emissions": DetailedCo2Emissions("detailed_co2_emissions"),
    "detailed_cumulative_co2_emissions": DetailedCumulativeCO2Emissions(
        "detailed_cumulative_co2_emissions"
    ),
    "gross_carbon_budget": GrossCarbonBudget("gross_carbon_budget"),
    "carbon_budget_consumed_share": CarbonBudgetConsumedShare("carbon_budget_consumed_share"),
    "models_energy_cost": models_energy_cost,
    "models_operation_cost_top_down": models_operation_cost_top_down,
    "carbon_budget_constraint": CarbonBudgetConstraint("carbon_budget_constraint"),
}

models_optim_complex = {
    "models_traffic_cost_feedback": models_traffic_cost_feedback,
    "models_efficiency_top_down": models_efficiency_top_down,
    "models_energy_without_fuel_effect": models_energy_without_fuel_effect,
    "models_offset": models_offset,
    "kaya_factors": KayaFactors("kaya_factors"),
    "co2_emissions": CO2Emissions("co2_emissions"),
    "cumulative_co2_emissions": CumulativeCO2Emissions("cumulative_co2_emissions"),
    "detailed_co2_emissions": DetailedCo2Emissions("detailed_co2_emissions"),
    "detailed_cumulative_co2_emissions": DetailedCumulativeCO2Emissions(
        "detailed_cumulative_co2_emissions"
    ),
    "gross_carbon_budget": GrossCarbonBudget("gross_carbon_budget"),
    "carbon_budget_consumed_share": CarbonBudgetConsumedShare("carbon_budget_consumed_share"),
    "models_energy_cost": models_energy_cost,
    "models_operation_cost_top_down_feedback": models_operation_cost_top_down_feedback,
    "carbon_budget_constraint": CarbonBudgetConstraint("carbon_budget_constraint"),
    "total_surplus_loss": TotalSurplusLoss("total_surplus_loss"),
}

carbon_budget_constraint = {
    "carbon_budget_constraint": CarbonBudgetConstraint("carbon_budget_constraint"),
}

# models_optim_complex_v2 = {
#     "models_traffic_cost_feedback": models_traffic_cost_feedback,
#     "models_efficiency_top_down": models_efficiency_top_down,
#     "models_energy_without_fuel_effect": models_energy_without_fuel_effect,
#     "models_offset": models_offset,
#     "kaya_factors": KayaFactors("kaya_factors"),
#     "co2_emissions": CO2Emissions("co2_emissions"),
#     "cumulative_co2_emissions": CumulativeCO2Emissions("cumulative_co2_emissions"),
#     "detailed_co2_emissions": DetailedCo2Emissions("detailed_co2_emissions"),
#     "detailed_cumulative_co2_emissions": DetailedCumulativeCO2Emissions(
#         "detailed_cumulative_co2_emissions"
#     ),
#     "gross_carbon_budget": GrossCarbonBudget("gross_carbon_budget"),
#     "emissions_per_rpk": EmissionsPerRPK("emissions_per_rpk"),
#     "biomass_availability": BiomassAvailability("biomass_availability"),
#     "electricity_availability": ElectricityAvailability("electricity_availability"),
#     "carbon_budget_consumed_share": CarbonBudgetConsumedShare("carbon_budget_consumed_share"),
#     "resources_consumed_share": ResourcesConsumedShare("resources_consumed_share"),
#     "models_energy_cost_simple": models_energy_cost_simple,
#     "models_operation_cost_top_down_feedback": models_operation_cost_top_down_feedback,
#     "carbon_budget_constraint": CarbonBudgetConstraint("carbon_budget_constraint"),
#     "blend_completeness_constraint": BlendCompletenessConstraint("blend_completeness_constraint"),
#     "electricity_availability_constraint_trajectory": ElectricityAvailabilityConstraintTrajectory(
#         "electricity_availability_constraint_trajectory"
#     ),
#     "biomass_availability_constraint_trajectory": BiomassAvailabilityConstraintTrajectory(
#         "biomass_availability_constraint_trajectory"
#     ),
#     "electrofuel_use_growth_constraint": ElectrofuelUseGrowthConstraint(
#         "electrofuel_use_growth_constraint"
#     ),
#     "biofuel_use_growth_constraint": BiofuelUseGrowthConstraint("biofuel_use_growth_constraint"),
#     "consumer_surplus_loss": ConsumerSurplusLoss("consumer_surplus_loss"),
#     "airline_surplus_loss": AirlineSurplusLoss("airline_surplus_loss"),
#     "tax_revenue_loss": TaxRevenueLoss("tax_revenue_loss"),
#     "total_welfare_loss": TotalWelfareLoss("total_welfare_loss"),
# }
