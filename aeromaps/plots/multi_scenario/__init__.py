"""Multi-scenario comparison plots.

This module provides plots for comparing multiple AeroMAPS scenarios.
"""

from aeromaps.plots.multi_scenario.emissions import (
    CO2EmissionsComparisonPlot,
    CarbonBudgetComparisonPlot,
)
from aeromaps.plots.multi_scenario.energy import (
    EnergyConsumptionComparisonPlot,
    EnergyMixComparisonPlot,
)
from aeromaps.plots.multi_scenario.traffic import (
    RPKComparisonPlot,
    LoadFactorComparisonPlot,
)
from aeromaps.plots.multi_scenario.intensities import (
    CO2PerRPKComparisonPlot,
    CO2PerRTKComparisonPlot,
    EnergyPerASKComparisonPlot,
    EnergyPerRTKComparisonPlot,
)
from aeromaps.plots.multi_scenario.fuel_supply import (
    FuelSupplyBreakdownPlot,
    HydrogenSupplyComparisonPlot,
    ElectricSupplyComparisonPlot,
    BiofuelProductionComparisonPlot,
    ElectrofuelProductionComparisonPlot,
    BiofuelMixComparisonPlot,
)

# Dictionary of available multi-scenario plots
available_multi_plots = {
    # Emissions
    "co2_emissions_comparison": CO2EmissionsComparisonPlot,
    "carbon_budget_comparison": CarbonBudgetComparisonPlot,
    
    # Energy
    "energy_consumption_comparison": EnergyConsumptionComparisonPlot,
    "energy_mix_comparison": EnergyMixComparisonPlot,
    
    # Traffic
    "rpk_comparison": RPKComparisonPlot,
    "load_factor_comparison": LoadFactorComparisonPlot,
    
    # Intensities
    "co2_per_rpk_comparison": CO2PerRPKComparisonPlot,
    "co2_per_rtk_comparison": CO2PerRTKComparisonPlot,
    "energy_per_ask_comparison": EnergyPerASKComparisonPlot,
    "energy_per_rtk_comparison": EnergyPerRTKComparisonPlot,
    
    # Fuel Supply
    "fuel_supply_breakdown": FuelSupplyBreakdownPlot,
    "hydrogen_supply_comparison": HydrogenSupplyComparisonPlot,
    "electric_supply_comparison": ElectricSupplyComparisonPlot,
    "biofuel_production_comparison": BiofuelProductionComparisonPlot,
    "electrofuel_production_comparison": ElectrofuelProductionComparisonPlot,
    "biofuel_mix_comparison": BiofuelMixComparisonPlot,
}
