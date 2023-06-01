from aeromaps.plots.main import AirTransportCO2EmissionsPlot, AirTransportClimateImpactsPlot
from aeromaps.plots.sustainability_assessment import (
    CarbonBudgetAssessmentPlot,
    EquivalentCarbonBudgetAssessmentPlot,
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
    MeanFuelConsumptionLiterPerPAX100kmPlot,
    MeanLoadFactorPlot,
    MeanEnergyPerASKPlot,
    MeanEnergyPerRTKPlot,
)
from aeromaps.plots.aircraft_energy import (
    MeanFuelEmissionFactorPlot,
    EmissionFactorPerFuelPlot,
    EnergyConsumptionPlot,
)
from aeromaps.plots.emissions import (
    CumulativeCO2EmissionsPlot,
    DirectH2OEmissionsPlot,
    DirectNOxEmissionsPlot,
    DirectSulfurEmissionsPlot,
    DirectSootEmissionsPlot,
)
from aeromaps.plots.climate import (
    FinalEffectiveRadiativeForcingPlot,
    DistributionEffectiveRadiativeForcingPlot,
    EquivalentEmissionsPlot,
    CumulativeEquivalentEmissionsPlot,
    EquivalentEmissionsRatioPlot,
    TemperatureIncreaseFromAirTransportPlot,
)
from aeromaps.plots.energy_resources import BiomassConsumptionPlot, ElectricityConsumptionPlot

# Left plot
plot_1 = {
    "Air transport CO2 emissions": AirTransportCO2EmissionsPlot,
    "Air transport climate impact": AirTransportClimateImpactsPlot,
}

# Central plot
plot_2 = {
    "Carbon budget assessment": CarbonBudgetAssessmentPlot,
    "Equivalent carbon budget assessment": EquivalentCarbonBudgetAssessmentPlot,
    "Biomass resource budget assessment": BiomassResourceBudgetAssessmentPlot,
    "Electricity resource budget assessment": ElectricityResourceBudgetAssessmentPlot,
    # "Multidisciplinary assessment": MultidisciplinaryAssessmentPlot,
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
    "Fuel consumption (fuel consumption per passenger per 100 km)": MeanFuelConsumptionLiterPerPAX100kmPlot,
    "Energy consumption of the aircraft fleet": EnergyConsumptionPlot,
    "Mean fuel emission factor (CO2 emissions per energy)": MeanFuelEmissionFactorPlot,
    "Fuel emission factors (CO2 emissions per energy)": EmissionFactorPerFuelPlot,
    "Cumulative CO2 emissions": CumulativeCO2EmissionsPlot,
    "Direct H2O emissions": DirectH2OEmissionsPlot,
    "Direct NOx emissions": DirectNOxEmissionsPlot,
    "Direct sulfur emissions": DirectSulfurEmissionsPlot,
    "Direct soot emissions": DirectSootEmissionsPlot,
    "Equivalent emissions": EquivalentEmissionsPlot,
    "Cumulative equivalent emissions": CumulativeEquivalentEmissionsPlot,
    "Equivalent emissions ratio": EquivalentEmissionsRatioPlot,
    "Effective radiative forcing in 2050": FinalEffectiveRadiativeForcingPlot,
    "Distribution of effective radiative forcing causes": DistributionEffectiveRadiativeForcingPlot,
}
