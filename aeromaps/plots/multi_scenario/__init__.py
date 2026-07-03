"""Multi-scenario comparison plots.

This module provides plots for comparing multiple AeroMAPS scenarios.
"""

from aeromaps.plots.multi_scenario.emissions import (
    CO2EmissionsComparisonPlot,
    CumulativeCO2EmissionsComparisonPlot,
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
from aeromaps.plots.multi_scenario.drop_in_supply import (
    DropInSupplyBreakdownPlot,
    HydrogenSupplyComparisonPlot,
    ElectricSupplyComparisonPlot,
    BiofuelProductionComparisonPlot,
    ElectrofuelProductionComparisonPlot,
    BiofuelMixComparisonPlot,
)
from aeromaps.plots.multi_scenario.climate import (
    TotalERFComparisonPlot,
    TemperatureIncreaseComparisonPlot,
    CO2ERFComparisonPlot,
    NonCO2ERFComparisonPlot,
)
from aeromaps.plots.multi_scenario.costs import (
    EnergyExpensesComparisonPlot,
    NetEnergyExpensesComparisonPlot,
    DOCComparisonPlot,
    DOCEnergyComparisonPlot,
    AirfareComparisonPlot,
    DocNetEnergyPerRPKComparisonPlot,
)

# Dictionary of available multi-scenario plots
available_multi_plots = {
    # Emissions
    "co2_emissions_comparison": CO2EmissionsComparisonPlot,
    "cumulative_co2_emissions_comparison": CumulativeCO2EmissionsComparisonPlot,
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
    "drop_in_supply_breakdown": DropInSupplyBreakdownPlot,
    "hydrogen_supply_comparison": HydrogenSupplyComparisonPlot,
    "electric_supply_comparison": ElectricSupplyComparisonPlot,
    "biofuel_production_comparison": BiofuelProductionComparisonPlot,
    "electrofuel_production_comparison": ElectrofuelProductionComparisonPlot,
    "biofuel_mix_comparison": BiofuelMixComparisonPlot,
    # Climate
    "total_erf_comparison": TotalERFComparisonPlot,
    "temperature_increase_comparison": TemperatureIncreaseComparisonPlot,
    "co2_erf_comparison": CO2ERFComparisonPlot,
    "non_co2_erf_comparison": NonCO2ERFComparisonPlot,
    # Costs
    "energy_expenses_comparison": EnergyExpensesComparisonPlot,
    "net_energy_expenses_comparison": NetEnergyExpensesComparisonPlot,
    "doc_comparison": DOCComparisonPlot,
    "doc_energy_comparison": DOCEnergyComparisonPlot,
    "airfare_comparison": AirfareComparisonPlot,
    "doc_net_energy_per_rpk_comparison": DocNetEnergyPerRPKComparisonPlot,
}
