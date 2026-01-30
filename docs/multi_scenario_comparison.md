# Multi-Scenario Comparison Feature

This document describes the multi-scenario comparison feature added to AeroMAPS.

## Overview

The multi-scenario comparison feature allows users to compare multiple AeroMAPS scenarios side-by-side using specialized comparison plots. This is useful for analyzing different decarbonization pathways, technology scenarios, or policy options.

## Key Components

### 1. MultiProcess Class (`aeromaps/core/multi_process.py`)

The `MultiProcess` class manages multiple computed AeroMAPS processes and provides a unified interface for creating comparison plots.

**Key Features:**
- Accepts dictionary or list of processes
- Validates that required outputs exist before plotting
- Shows warnings for scenarios with missing data
- Automatically filters scenarios that don't have required outputs
- Provides methods similar to single-process API

### 2. Multi-Scenario Plots (`aeromaps/plots/multi_scenario/`)

Several pre-built comparison plots are available:

**Emissions Plots:**
- `co2_emissions_comparison` - Compare CO2 emissions trajectories
- `cumulative_co2_comparison` - Compare cumulative CO2 emissions

**Energy Plots:**
- `energy_consumption_comparison` - Compare total energy consumption
- `energy_mix_comparison` - Compare energy mix (kerosene, hydrogen, electricity) with stacked subplots

**Traffic Plots:**
- `rpk_comparison` - Compare revenue passenger kilometers
- `load_factor_comparison` - Compare aircraft load factors

## Usage

### Basic Usage

```python
from aeromaps import create_process, create_multi_process

# Create and compute multiple scenarios
proc1 = create_process(configuration_file="config1.yaml")
proc1.compute()

proc2 = create_process(configuration_file="config2.yaml")
proc2.compute()

proc3 = create_process(configuration_file="config3.yaml")
proc3.compute()

# Create multi-process manager with named scenarios
multi = create_multi_process({
    "Baseline": proc1,
    "Ambitious": proc2,
    "Conservative": proc3
})

# List available comparison plots
print(multi.list_available_plots())

# Create comparison plots
multi.plot("co2_emissions_comparison")
multi.plot("energy_mix_comparison")
multi.plot("rpk_comparison", save=True)  # Save to PDF
```

### Using a List

```python
# Can also use a list (scenarios will be auto-named)
processes = [proc1, proc2, proc3]
multi = create_multi_process(processes)

# Scenarios will be named: "scenario_0", "scenario_1", "scenario_2"
print(multi.get_scenario_names())
```

### Handling Missing Outputs

Different scenarios may use different models and produce different outputs. The `MultiProcess` automatically handles this:

```python
# If some scenarios are missing required outputs
multi = create_multi_process({
    "Full": proc_with_all_outputs,
    "Limited": proc_with_limited_outputs,
})

# When plotting, scenarios without required outputs are skipped with a warning
# UserWarning: Scenario 'Limited' is missing required outputs: ['some_output']. 
#              It will be excluded from the plot.
fig = multi.plot("co2_emissions_comparison")
```

### Plot Options

```python
# Create plot without checking outputs (may fail if data is missing)
multi.plot("energy_consumption_comparison", check_outputs=False)

# Save plot with custom size
multi.plot("rpk_comparison", save=True, size_inches=(15, 8))

# Remove title when saving
multi.plot("co2_emissions_comparison", save=True, remove_title=True)
```

## API Reference

### MultiProcess Methods

- `list_available_plots()` - List all available comparison plots
- `plot(name, save=False, size_inches=None, remove_title=False, check_outputs=True)` - Create a comparison plot
- `get_scenario_names()` - Get list of scenario names
- `__len__()` - Get number of scenarios
- `__getitem__(key)` - Access individual process by name or index

### Creating Custom Comparison Plots

To create a custom comparison plot, extend the `MultiScenarioPlot` base class:

```python
from aeromaps.plots.multi_scenario_plot import MultiScenarioPlot

class MyCustomComparisonPlot(MultiScenarioPlot):
    # Define required outputs for validation
    required_outputs = ["my_output_1", "my_output_2"]
    
    def _get_default_figsize(self):
        return (12, 6)
    
    def create_plot(self):
        # Access scenario data
        for scenario_name, data in self.scenario_data.items():
            years = data["years"]
            values = data["df"].loc[years, "my_output_1"]
            self.ax.plot(years, values, label=scenario_name)
        
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("My Output")
        self.ax.legend()
    
    def _update_plot_elements(self):
        self.ax.clear()
        self.create_plot()
```

Then register it in `aeromaps/plots/multi_scenario/__init__.py`:

```python
from .my_module import MyCustomComparisonPlot

available_multi_plots = {
    # ... existing plots ...
    "my_custom_comparison": MyCustomComparisonPlot,
}
```

## Example Script

See `examples/multi_scenario_example.py` for a complete working example.

## Implementation Details

### Data Validation

The `MultiProcess._check_required_outputs()` method:
1. Checks if each scenario has the required output columns
2. Returns a dictionary mapping scenario names to availability status
3. Issues warnings for scenarios with missing data

### Data Extraction

The `MultiScenarioPlot` base class automatically extracts:
- `df` - vector_outputs dataframe
- `df_climate` - climate_outputs dataframe
- `float_outputs` - scalar outputs
- `years` - full_years, historic_years, prospective_years

This data is stored in `self.scenario_data` as either a dictionary or list, matching the input format.

## Testing

Tests are located in `tests/core/test_multi_process.py` and cover:
- Creating MultiProcess with dict and list
- Listing available plots
- Creating comparison plots
- Handling invalid inputs
- Indexing and accessing scenarios

Run tests with:
```bash
pytest tests/core/test_multi_process.py -v
```
