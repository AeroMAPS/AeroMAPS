# Plot Fixes Summary

## Overview
Fixed inheritance and initialization issues in single scenario plot classes that were causing test failures.

## Issues Fixed

### 1. MeanCO2PerRPKPlot - Improper Inheritance Pattern
**File:** `aeromaps/plots/single_scenario/indicators.py`
**Problem:** Using old manual data extraction pattern instead of proper SingleScenarioPlot inheritance
**Fix:** Refactored to match MeanCO2PerRTKPlot pattern with:
- Proper `super().__init__()` call
- Added `_get_default_figsize()` method
- Use of helper methods (`_setup_grid_and_labels()`, `_set_x_limits()`)
- Simplified `_update_plot_elements()`

### 2. pathways_manager Access Before super().__init__()
**Files:**
- `aeromaps/plots/single_scenario/aircraft_energy.py`
- `aeromaps/plots/single_scenario/costs_generic.py`
- `aeromaps/plots/single_scenario/macc.py`

**Problem:** Multiple classes accessed `process.pathways_manager` before calling `super().__init__()`, causing AttributeError

**Classes Fixed (8 total):**
1. `EmissionFactorPerFuel` (aircraft_energy.py)
2. `ShareFuelPlot` (aircraft_energy.py)
3. `ScenarioEnergyCapitalPlot` (costs_generic.py)
4. `ScenarioEnergyExpensesPlot` (costs_generic.py)
5. `DetailledMFSPBreakdown` (costs_generic.py)
6. `SimpleMFSP` (costs_generic.py)
7. `AnnualMACCSimple` (macc.py)
8. `ShadowCarbonPriceSimple` (macc.py)

**Fix Pattern:**
```python
# BEFORE (WRONG):
def __init__(self, process, figsize=None):
    self.pathways_manager = process.pathways_manager  # ERROR
    super().__init__(process, figsize)

# AFTER (CORRECT):
def __init__(self, process, figsize=None):
    figsize = figsize or self._get_default_figsize()
    super().__init__(process, figsize)  # Store process first
    self.pathways_manager = self.process.pathways_manager  # Now accessible
```

## Test Impact
These fixes resolve test failures in `test_single_scenario_plots.py`:
- `test_co2_per_rpk_plot` ✅
- `test_emission_factor_per_fuel_plot` ✅
- All other plots that use pathways_manager ✅

## Commits
1. `65bc1c7` - Fix MeanCO2PerRPKPlot inheritance
2. `f584f2e` - Fix pathways_manager access in 8 plot classes

## Benefits
✅ Consistent inheritance pattern across all SingleScenarioPlot subclasses
✅ Proper initialization order prevents AttributeErrors
✅ Uses standard helper methods from parent class
✅ Cleaner, more maintainable code
✅ All tests now pass
