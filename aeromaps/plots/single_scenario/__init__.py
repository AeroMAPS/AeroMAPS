from aeromaps.plots.single_scenario.main import AirTransportCO2EmissionsPlot, AirTransportClimateImpactsPlot
from aeromaps.plots.single_scenario.sustainability_assessment import (
    CarbonBudgetAssessmentPlot,
    TemperatureTargetAssessmentPlot,
    BiomassResourceBudgetAssessmentPlot,
    ElectricityResourceBudgetAssessmentPlot,
    MultidisciplinaryAssessmentPlot,
)
from aeromaps.plots.single_scenario.indicators import (
    MeanCO2PerRPKPlot,
    MeanCO2PerRTKPlot,
    PassengerKayaFactorsPlot,
    FreightKayaFactorsPlot,
    LeversOfActionDistributionPlot,
)
from aeromaps.plots.single_scenario.air_traffic import (
    RevenuePassengerKilometerPlot,
    RevenueTonneKilometerPlot,
    AvailableSeatKilometerPlot,
    TotalAircraftDistancePlot,
)
from aeromaps.plots.single_scenario.aircraft_fleet_and_operations import (
    DropinFuelConsumptionLiterPerPAX100kmPlot,
    MeanLoadFactorPlot,
    MeanEnergyPerASKPlot,
    MeanEnergyPerRTKPlot,
)
from aeromaps.plots.single_scenario.aircraft_energy import (
    MeanFuelEmissionFactorPlot,
    EmissionFactorPerFuelCategory,
    EnergyConsumptionPlot,
    ShareFuelPlot,
    EmissionFactorPerFuel,
)
from aeromaps.plots.single_scenario.emissions import (
    CumulativeCO2EmissionsPlot,
    DirectH2OEmissionsPlot,
    DirectNOxEmissionsPlot,
    DirectSulfurEmissionsPlot,
    DirectSootEmissionsPlot,
    CarbonOffsetPlot,
    CumulativeCarbonOffsetPlot,
)
from aeromaps.plots.single_scenario.climate import (
    FinalEffectiveRadiativeForcingPlot,
    DistributionEffectiveRadiativeForcingPlot,
    TemperatureIncreaseFromAirTransportPlot,
    DetailedTemperatureIncreaseFromAirTransportPlot,
)
from aeromaps.plots.single_scenario.energy_resources import BiomassConsumptionPlot, ElectricityConsumptionPlot

from aeromaps.plots.single_scenario.energy_mix import (
    EnergyMixPlot,
    DropInSupplyBreakdownPlot,
    BiofuelMixPlot,
)

from aeromaps.plots.single_scenario.costs import (
    DiscountEffect,
    ScenarioEnergyExpensesComparison,
    DOCEvolutionBreakdown,
    DOCEvolutionCategory,
    AllEnergyCostsPerRPKBreakdown,
    AirfareEvolutionBreakdown,
)

from aeromaps.plots.single_scenario.macc import (
    AnnualMACC,
    ScenarioMACC,
    CumulativeMACC,
    ShadowCarbonPrice,
    AnnualMACCSimple,
    ShadowCarbonPriceSimple,
)

from aeromaps.plots.single_scenario.costs_generic import (
    ScenarioEnergyExpensesPlot,
    DetailledMFSPBreakdown,
    SimpleMFSP,
    ScenarioEnergyCapitalPlot,
)

available_plots = {
    "air_transport_co2_emissions": AirTransportCO2EmissionsPlot,
    "air_transport_climate_impacts": AirTransportClimateImpactsPlot,
    "carbon_budget_assessment": CarbonBudgetAssessmentPlot,
    "temperature_target_assessment": TemperatureTargetAssessmentPlot,
    "biomass_resource_budget_assessment": BiomassResourceBudgetAssessmentPlot,
    "electricity_resource_budget_assessment": ElectricityResourceBudgetAssessmentPlot,
    "multidisciplinary_assessment": MultidisciplinaryAssessmentPlot,
    "temperature_increase_from_air_transport": TemperatureIncreaseFromAirTransportPlot,
    "detailed_temperature_increase_from_air_transport": DetailedTemperatureIncreaseFromAirTransportPlot,
    "biomass_consumption": BiomassConsumptionPlot,
    "electricity_consumption": ElectricityConsumptionPlot,
    "co2_per_rpk": MeanCO2PerRPKPlot,
    "co2_per_rtk": MeanCO2PerRTKPlot,
    "passenger_kaya_factors": PassengerKayaFactorsPlot,
    "freight_kaya_factors": FreightKayaFactorsPlot,
    "levers_of_action_distribution": LeversOfActionDistributionPlot,
    "revenue_passenger_kilometer": RevenuePassengerKilometerPlot,
    "revenue_tonne_kilometer": RevenueTonneKilometerPlot,
    "available_seat_kilometer": AvailableSeatKilometerPlot,
    "total_aircraft_distance": TotalAircraftDistancePlot,
    "load_factor": MeanLoadFactorPlot,
    "energy_per_ask": MeanEnergyPerASKPlot,
    "energy_per_rtk": MeanEnergyPerRTKPlot,
    "energy_consumption": EnergyConsumptionPlot,
    "fuel_consumption_liter_per_pax_100km": DropinFuelConsumptionLiterPerPAX100kmPlot,
    "mean_fuel_emission_factor": MeanFuelEmissionFactorPlot,
    "emission_factor_per_fuel_category": EmissionFactorPerFuelCategory,
    "emission_factor_per_fuel": EmissionFactorPerFuel,
    "fuel_shares": ShareFuelPlot,
    "cumulative_co2_emissions": CumulativeCO2EmissionsPlot,
    "direct_h2o_emissions": DirectH2OEmissionsPlot,
    "direct_nox_emissions": DirectNOxEmissionsPlot,
    "direct_sulfur_emissions": DirectSulfurEmissionsPlot,
    "direct_soot_emissions": DirectSootEmissionsPlot,
    "carbon_offset": CarbonOffsetPlot,
    "cumulative_carbon_offset": CumulativeCarbonOffsetPlot,
    "final_effective_radiative_forcing": FinalEffectiveRadiativeForcingPlot,
    "distribution_effective_radiative_forcing": DistributionEffectiveRadiativeForcingPlot,
    "energy_capex": ScenarioEnergyCapitalPlot,
    "energy_expenses": ScenarioEnergyExpensesPlot,
    "energy_mfsp": SimpleMFSP,
    "energy_expenses_discounted": DiscountEffect,
    "energy_expenses_comparison": ScenarioEnergyExpensesComparison,
    "doc_fleet_breakdown": DOCEvolutionBreakdown,
    "doc_fleet_category": DOCEvolutionCategory,
    "airfare_breakdown": AirfareEvolutionBreakdown,
    "all_energy_costs_per_rpk_breakdown": AllEnergyCostsPerRPKBreakdown,
    "mfsp_detailled": DetailledMFSPBreakdown,
    # Generic pathways-manager-driven plots
    "energy_mix": EnergyMixPlot,
    "drop_in_supply_breakdown": DropInSupplyBreakdownPlot,
    "biofuel_mix": BiofuelMixPlot,
    "annual_MACC_simple_fleet": AnnualMACCSimple,
    "shadow_carbon_pricing_simple_fleet": ShadowCarbonPriceSimple,
}

available_plots_fleet = {
    "annual_MACC": AnnualMACC,
    "scenario_MACC": ScenarioMACC,
    "cumulative_MACC": CumulativeMACC,
    "shadow_carbon_pricing": ShadowCarbonPrice,
}
