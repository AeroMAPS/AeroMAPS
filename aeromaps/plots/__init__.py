from .main import AirTransportCO2EmissionsPlot, AirTransportClimateImpactsPlot
from .sustainability_assessment import (
    CarbonBudgetAssessmentPlot,
    EquivalentCarbonBudgetAssessmentPlot,
    BiomassResourceBudgetAssessmentPlot,
    ElectricityResourceBudgetAssessmentPlot,
    MultidisciplinaryAssessmentPlot,
)
from .indicators import (
    MeanCO2PerRPKPlot,
    MeanCO2PerRTKPlot,
    PassengerKayaFactorsPlot,
    FreightKayaFactorsPlot,
    LeversOfActionDistributionPlot,
)
from .air_traffic import (
    RevenuePassengerKilometerPlot,
    RevenueTonneKilometerPlot,
    AvailableSeatKilometerPlot,
    TotalAircraftDistancePlot,
)
from .aircraft_fleet_and_operations import (
    DropinFuelConsumptionLiterPerPAX100kmPlot,
    MeanLoadFactorPlot,
    MeanEnergyPerASKPlot,
    MeanEnergyPerRTKPlot,
)
from .aircraft_energy import (
    MeanFuelEmissionFactorPlot,
    EmissionFactorPerFuelPlot,
    EnergyConsumptionPlot,
)
from .emissions import (
    CumulativeCO2EmissionsPlot,
    DirectH2OEmissionsPlot,
    DirectNOxEmissionsPlot,
    DirectSulfurEmissionsPlot,
    DirectSootEmissionsPlot,
    CarbonOffsetPlot,
    CumulativeCarbonOffsetPlot,
)
from .climate import (
    FinalEffectiveRadiativeForcingPlot,
    DistributionEffectiveRadiativeForcingPlot,
    EquivalentEmissionsPlot,
    CumulativeEquivalentEmissionsPlot,
    EquivalentEmissionsRatioPlot,
    TemperatureIncreaseFromAirTransportPlot,
)
from .energy_resources import BiomassConsumptionPlot, ElectricityConsumptionPlot

from aeromaps.plots.costs import (
    ScenarioEnergyCapitalPlot,
    ScenarioEnergyExpensesPlot,
    ScenarioEnergyUnitCostPlot,
    DiscountEffect,
    ScenarioEnergyCarbonTaxPlot,
    ScenarioEnergyUnitCostWithCarbonTaxPlot,
    DropInMACC,
    DOCEvolutionBreakdown,
    DOCEvolutionCategory,
    AirfareEvolutionBreakdown,
)


available_plots = {
    "air_transport_co2_emissions": AirTransportCO2EmissionsPlot,
    "air_transport_climate_impacts": AirTransportClimateImpactsPlot,
    "carbon_budget_assessment": CarbonBudgetAssessmentPlot,
    "equivalent_carbon_budget_assessment": EquivalentCarbonBudgetAssessmentPlot,
    "biomass_resource_budget_assessment": BiomassResourceBudgetAssessmentPlot,
    "electricity_resource_budget_assessment": ElectricityResourceBudgetAssessmentPlot,
    "multidisciplinary_assessment": MultidisciplinaryAssessmentPlot,
    "temperature_increase_from_air_transport": TemperatureIncreaseFromAirTransportPlot,
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
    "emission_factor_per_fuel": EmissionFactorPerFuelPlot,
    "cumulative_co2_emissions": CumulativeCO2EmissionsPlot,
    "direct_h2o_emissions": DirectH2OEmissionsPlot,
    "direct_nox_emissions": DirectNOxEmissionsPlot,
    "direct_sulfur_emissions": DirectSulfurEmissionsPlot,
    "direct_soot_emissions": DirectSootEmissionsPlot,
    "carbon_offset": CarbonOffsetPlot,
    "cumulative_carbon_offset": CumulativeCarbonOffsetPlot,
    "equivalent_emissions": EquivalentEmissionsPlot,
    "cumulative_equivalent_emissions": CumulativeEquivalentEmissionsPlot,
    "equivalent_emissions_ratio": EquivalentEmissionsRatioPlot,
    "final_effective_radiative_forcing": FinalEffectiveRadiativeForcingPlot,
    "distribution_effective_radiative_forcing": DistributionEffectiveRadiativeForcingPlot,
    "energy_capex": ScenarioEnergyCapitalPlot,
    "energy_expenses": ScenarioEnergyExpensesPlot,
    "energy_mfsp": ScenarioEnergyUnitCostPlot,
    "energy_mfsp_with_carbon_tax": ScenarioEnergyUnitCostWithCarbonTaxPlot,
    "energy_expenses_discounted": DiscountEffect,
    "energy_expenses_with_carbon_tax": ScenarioEnergyCarbonTaxPlot,
    "drop_in_macc_curve": DropInMACC,
    "doc_fleet_breakdown": DOCEvolutionBreakdown,
    "doc_fleet_category": DOCEvolutionCategory,
    "airfare_fleet_breakdown": AirfareEvolutionBreakdown,
}
