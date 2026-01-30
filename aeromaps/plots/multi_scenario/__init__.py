"""Multi-scenario comparison plots.

This module provides plots for comparing multiple AeroMAPS scenarios.
"""

from aeromaps.plots.multi_scenario.emissions import (
    CO2EmissionsComparisonPlot,
    CumulativeCO2ComparisonPlot,
)
from aeromaps.plots.multi_scenario.energy import (
    EnergyConsumptionComparisonPlot,
    EnergyMixComparisonPlot,
)
from aeromaps.plots.multi_scenario.traffic import (
    RPKComparisonPlot,
    LoadFactorComparisonPlot,
)

# Dictionary of available multi-scenario plots
available_multi_plots = {
    "co2_emissions_comparison": CO2EmissionsComparisonPlot,
    "cumulative_co2_comparison": CumulativeCO2ComparisonPlot,
    "energy_consumption_comparison": EnergyConsumptionComparisonPlot,
    "energy_mix_comparison": EnergyMixComparisonPlot,
    "rpk_comparison": RPKComparisonPlot,
    "load_factor_comparison": LoadFactorComparisonPlot,
}
