from aeromaps.plots.costs_generic import SimpleMFSP, ScenarioEnergyCapitalPlot
from aeromaps.plots.main import AirTransportCO2EmissionsPlot, AirTransportClimateImpactsPlot
from aeromaps.plots.sustainability_assessment import (
    CarbonBudgetAssessmentPlot,
    TemperatureTargetAssessmentPlot,
    BiomassResourceBudgetAssessmentPlot,
    ElectricityResourceBudgetAssessmentPlot,
    MultidisciplinaryAssessmentPlot,
)
from aeromaps.plots.indicators import (
    MeanCO2PerRPKPlot,
    MeanCO2PerRTKPlot,
    PassengerKayaFactorsPlot,
    FreightKayaFactorsPlot,
    LeversOfActionDistributionPlot,
)
from aeromaps.plots.air_traffic import (
    RevenuePassengerKilometerPlot,
    RevenueTonneKilometerPlot,
    AvailableSeatKilometerPlot,
    TotalAircraftDistancePlot,
)
from aeromaps.plots.aircraft_fleet_and_operations import (
    DropinFuelConsumptionLiterPerPAX100kmPlot,
    MeanLoadFactorPlot,
    MeanEnergyPerASKPlot,
    MeanEnergyPerRTKPlot,
)
from aeromaps.plots.aircraft_energy import (
    MeanFuelEmissionFactorPlot,
    EmissionFactorPerFuelCategory,
    EnergyConsumptionPlot,
    ShareFuelPlot,
)
from aeromaps.plots.emissions import (
    CumulativeCO2EmissionsPlot,
    DirectH2OEmissionsPlot,
    DirectNOxEmissionsPlot,
    DirectSulfurEmissionsPlot,
    DirectSootEmissionsPlot,
    CarbonOffsetPlot,
    CumulativeCarbonOffsetPlot,
)
from aeromaps.plots.climate import (
    FinalEffectiveRadiativeForcingPlot,
    DistributionEffectiveRadiativeForcingPlot,
    TemperatureIncreaseFromAirTransportPlot,
)
from aeromaps.plots.energy_resources import BiomassConsumptionPlot, ElectricityConsumptionPlot

from aeromaps.plots.costs import (
    DiscountEffect,
    ScenarioEnergyExpensesComparison,
    DOCEvolutionBreakdown,
    DOCEvolutionCategory,
    AirfareEvolutionBreakdown,
)

# Left plot
plot_1 = {
    "Air transport CO2 emissions": AirTransportCO2EmissionsPlot,
    "Air transport climate impact": AirTransportClimateImpactsPlot,
}

# Central plot
plot_2 = {
    "Multidisciplinary assessment": MultidisciplinaryAssessmentPlot,
    "Carbon budget assessment": CarbonBudgetAssessmentPlot,
    "Temperature target assessment": TemperatureTargetAssessmentPlot,
    "Biomass resource budget assessment": BiomassResourceBudgetAssessmentPlot,
    "Electricity resource budget assessment": ElectricityResourceBudgetAssessmentPlot,
}

# Right plot
plot_3 = {
    "Temperature increase from air transport": TemperatureIncreaseFromAirTransportPlot,
    "Biomass consumption": BiomassConsumptionPlot,
    "Electricity consumption": ElectricityConsumptionPlot,
    "Passenger flight emission factor (CO2 emissions per RPK)": MeanCO2PerRPKPlot,
    "Freight flight emission factor (CO2 emissions per RTK)": MeanCO2PerRTKPlot,
    "Kaya factors for passenger air transport": PassengerKayaFactorsPlot,
    "Kaya factors for freight air transport": FreightKayaFactorsPlot,
    "Distribution of levers of action impact": LeversOfActionDistributionPlot,
    "Revenue Passenger Kilometer (RPK)": RevenuePassengerKilometerPlot,
    "Revenue Tonne Kilometer (RTK)": RevenueTonneKilometerPlot,
    "Available Seat Kilometer (ASK)": AvailableSeatKilometerPlot,
    "Total distance travelled by aircraft": TotalAircraftDistancePlot,
    "Aircraft load factor": MeanLoadFactorPlot,
    "Fuel consumption (energy consumption per ASK)": MeanEnergyPerASKPlot,
    "Fuel consumption (energy consumption per RTK)": MeanEnergyPerRTKPlot,
    "Fuel consumption (fuel consumption per passenger per 100 km)": DropinFuelConsumptionLiterPerPAX100kmPlot,
    "Energy consumption of the aircraft fleet": EnergyConsumptionPlot,
    "Mean fuel emission factor (CO2 emissions per energy)": MeanFuelEmissionFactorPlot,
    "Fuel emission factors (CO2 emissions per energy)": EmissionFactorPerFuelCategory,
    "Fuel share in the aircraft fleet": ShareFuelPlot,
    "Cumulative CO2 emissions": CumulativeCO2EmissionsPlot,
    "Direct H2O emissions": DirectH2OEmissionsPlot,
    "Direct NOx emissions": DirectNOxEmissionsPlot,
    "Direct sulfur emissions": DirectSulfurEmissionsPlot,
    "Direct soot emissions": DirectSootEmissionsPlot,
    "Carbon offset": CarbonOffsetPlot,
    "Cumulative carbon offset": CumulativeCarbonOffsetPlot,
    "Effective radiative forcing in 2050": FinalEffectiveRadiativeForcingPlot,
    "Distribution of effective radiative forcing causes": DistributionEffectiveRadiativeForcingPlot,
    "Investments required per low-carbon fuel pathway": ScenarioEnergyCapitalPlot,
    "Annual energy expense vs reference situation": ScenarioEnergyExpensesComparison,
    "Evolution of pathways MFSP": SimpleMFSP,
    "Effect of the discount rate on total energy costs": DiscountEffect,
    "Direct Operating Cost breakdown": DOCEvolutionBreakdown,
    "Direct Operating Cost per aircraft category": DOCEvolutionCategory,
    "Airfare breakdown": AirfareEvolutionBreakdown,
}
