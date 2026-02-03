# Final Plot Fixes Summary

## Overview
Successfully fixed all 8 remaining test failures in single scenario plots by correcting inheritance patterns and implementing missing abstract methods.

## Test Results
- **Before:** 39 passing, 8 failing
- **After:** 47 passing, 0 failing ✅

## Issues and Solutions

### Issue 1: pathways_manager Access Timing (6 classes)

**Problem:**
Classes stored `self.pathways_manager = self.process.pathways_manager` in `__init__` AFTER calling `super().__init__()`. However, `super().__init__()` calls `create_plot()`, which then tried to access `self.pathways_manager` before it was assigned.

**Solution:**
Removed the `self.pathways_manager` assignment entirely. All methods now access `self.process.pathways_manager` directly.

**Pattern Before (WRONG):**
```python
def __init__(self, process, figsize=None):
    figsize = figsize or self._get_default_figsize()
    super().__init__(process, figsize)  # This calls create_plot()
    self.pathways_manager = self.process.pathways_manager  # Too late!

def create_plot(self):
    pathways = self.pathways_manager.get_all()  # ERROR: not assigned yet
```

**Pattern After (CORRECT):**
```python
def __init__(self, process, figsize=None):
    figsize = figsize or self._get_default_figsize()
    super().__init__(process, figsize)  # This calls create_plot()
    # No pathways_manager assignment needed

def create_plot(self):
    pathways = self.process.pathways_manager.get_all()  # Direct access
```

**Classes Fixed:**
1. `EmissionFactorPerFuel` (aircraft_energy.py:133)
2. `ScenarioEnergyCapitalPlot` (costs_generic.py:15)
3. `ScenarioEnergyExpensesPlot` (costs_generic.py:222)
4. `SimpleMFSP` (costs_generic.py:2847)
5. `DetailledMFSPBreakdown` (costs_generic.py:681)

### Issue 2: Missing Abstract Methods (3 classes)

**Problem:**
Classes didn't implement required abstract methods from `SingleScenarioPlot`:
- `create_plot()`
- `_update_plot_elements()`

**Solutions:**

#### ScenarioEnergyExpensesComparison (costs.py:16)
- **Missing:** `_update_plot_elements()`
- **Fix:** Implemented method to update all line plots with new data
- Had old-style `update(df_data)` method but needed `_update_plot_elements()`

#### AnnualMACCSimple (macc.py:1883)
- **Missing:** `create_plot()`
- **Fix:** Added empty `create_plot()` method
- **Reason:** Plot is created dynamically in interactive `update()` method via widgets
- Also removed unnecessary `pathways_manager` assignment

#### ShadowCarbonPriceSimple (macc.py:2387)
- **Missing:** `create_plot()` and `_update_plot_elements()`
- **Fix:** Added both methods as empty stubs
- **Reason:** Plot is created dynamically in interactive `update()` method via widgets
- Also removed unnecessary `pathways_manager` assignment

## Files Modified

1. **aeromaps/plots/single_scenario/aircraft_energy.py**
   - `EmissionFactorPerFuel`: Removed pathways_manager, use self.process.pathways_manager

2. **aeromaps/plots/single_scenario/costs_generic.py**
   - `ScenarioEnergyCapitalPlot`: Removed pathways_manager, use self.process.pathways_manager
   - `ScenarioEnergyExpensesPlot`: Removed pathways_manager, use self.process.pathways_manager
   - `SimpleMFSP`: Removed pathways_manager, use self.process.pathways_manager
   - `DetailledMFSPBreakdown`: Removed pathways_manager, use self.process.pathways_manager

3. **aeromaps/plots/single_scenario/costs.py**
   - `ScenarioEnergyExpensesComparison`: Added `_update_plot_elements()` method

4. **aeromaps/plots/single_scenario/macc.py**
   - `AnnualMACCSimple`: Added `create_plot()` method, removed pathways_manager
   - `ShadowCarbonPriceSimple`: Added `create_plot()` and `_update_plot_elements()`, removed pathways_manager

## Key Lessons

1. **Initialization Order Matters:**
   - Always call `super().__init__()` FIRST in child class
   - Parent's `__init__` may call abstract methods
   - Don't assign attributes that will be needed in abstract methods after `super().__init__()`

2. **Access via self.process:**
   - Instead of storing references like `self.pathways_manager = self.process.pathways_manager`
   - Just access directly: `self.process.pathways_manager`
   - Cleaner and avoids timing issues

3. **Implement All Abstract Methods:**
   - Even if methods are empty stubs for interactive plots
   - Required by Python's ABC (Abstract Base Class) system

## Pattern for All SingleScenarioPlot Subclasses

```python
class MyPlot(SingleScenarioPlot):
    def __init__(self, process, figsize=None):
        # 1. Calculate figsize
        figsize = figsize or self._get_default_figsize()
        
        # 2. Call super().__init__() FIRST
        super().__init__(process, figsize)
        
        # 3. Any additional initialization (after super)
        # Access process attributes via self.process
        
    def _get_default_figsize(self):
        return (width, height)
        
    def create_plot(self):
        # Create initial plot
        # Access: self.df, self.years, self.prospective_years, self.process
        pass
        
    def _update_plot_elements(self):
        # Update plot data when df changes
        # Update line data, bar heights, etc.
        pass
```

## Test Coverage

All 47 tests in `test_single_scenario_plots.py` now pass:
- ✅ Emissions plots
- ✅ Energy plots
- ✅ Indicator plots
- ✅ Traffic plots
- ✅ Cost plots
- ✅ MACC plots
- ✅ All previously failing plots

## Conclusion

All single scenario plot classes now properly follow the SingleScenarioPlot inheritance pattern with:
- Correct initialization order
- Proper attribute access via self.process
- All required abstract methods implemented
- Clean, maintainable code structure

**Status: ALL TESTS PASSING ✅**
