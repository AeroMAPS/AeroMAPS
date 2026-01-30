# Required Outputs Feature

## Overview

The `required_outputs` feature has been added to both `SingleScenarioPlot` and `MultiScenarioPlot` parent classes. This feature provides automatic validation of data requirements and makes plot classes self-documenting.

## Key Features

### 1. Class-Level Declaration
Every plot class can now declare what outputs it needs:

```python
class CO2EmissionsPlot(SingleScenarioPlot):
    required_outputs = ["co2_emissions"]
    
    def create_plot(self):
        # Use self.df["co2_emissions"]
        pass
```

### 2. Automatic Validation
When a plot is created, the parent class automatically validates that required outputs exist:

```python
# Validation happens automatically in __init__
plot = CO2EmissionsPlot(process)  # Warns if co2_emissions is missing
```

### 3. Optional Validation
Validation can be disabled when needed:

```python
# Skip validation
plot = CO2EmissionsPlot(process, check_outputs=False)
```

### 4. Self-Documenting
Any code can query what outputs a plot needs:

```python
# Check requirements without creating the plot
required = CO2EmissionsPlot.get_required_outputs()
# Returns: ["co2_emissions"]
```

## Usage Examples

### Single Scenario Plots

```python
from aeromaps.plots.single_scenario_plot import SingleScenarioPlot

class MyCustomPlot(SingleScenarioPlot):
    # Declare required outputs
    required_outputs = ["energy_consumption", "co2_emissions"]
    
    def _get_default_figsize(self):
        return (10, 6)
    
    def create_plot(self):
        # These columns are guaranteed to exist (or warnings were issued)
        energy = self.df["energy_consumption"]
        co2 = self.df["co2_emissions"]
        
        self.ax.plot(self.years, energy, label="Energy")
        self.ax.plot(self.years, co2, label="CO2")
        self.ax.legend()
    
    def _update_plot_elements(self):
        # Update logic here
        pass

# Create with validation (default)
plot = MyCustomPlot(process)

# Create without validation
plot = MyCustomPlot(process, check_outputs=False)

# Check requirements
print(MyCustomPlot.get_required_outputs())
# Output: ["energy_consumption", "co2_emissions"]
```

### Multi Scenario Plots

```python
from aeromaps.plots.multi_scenario_plot import MultiScenarioPlot

class ScenarioComparisonPlot(MultiScenarioPlot):
    # Declare required outputs
    required_outputs = ["co2_emissions"]
    
    def _get_default_figsize(self):
        return (12, 6)
    
    def create_plot(self):
        # Only scenarios with co2_emissions will be included
        for scenario_name, data in self.scenario_data.items():
            years = data["years"]
            co2 = data["df"]["co2_emissions"]
            self.ax.plot(years, co2, label=scenario_name)
        
        self.ax.legend()
    
    def _update_plot_elements(self):
        # Update logic here
        pass

# Scenarios without required outputs are automatically filtered
# with warnings issued
processes = {
    "Scenario A": process_a,  # Has co2_emissions
    "Scenario B": process_b,  # Missing co2_emissions - will be excluded
    "Scenario C": process_c,  # Has co2_emissions
}

plot = ScenarioComparisonPlot(processes)
# Warning: Scenario 'Scenario B' is missing required outputs: ['co2_emissions'].
#          It will be excluded from the plot.
# Plot shows only Scenario A and Scenario C
```

## Behavior Details

### Single Scenario Plots

1. **Validation**: Checks if required outputs exist in `vector_outputs`
2. **Warnings**: Issues `UserWarning` for missing outputs
3. **No Exceptions**: Does not raise exceptions - allows plot to attempt rendering
4. **Optional**: Can be disabled with `check_outputs=False`

Example warning:
```
UserWarning: MyCustomPlot requires outputs ['energy_consumption', 'co2_emissions'] 
but the following are missing: ['co2_emissions']. 
The plot may not render correctly.
```

### Multi Scenario Plots

1. **Filtering**: Automatically excludes scenarios with missing outputs
2. **Warnings**: Issues `UserWarning` for each excluded scenario
3. **Exceptions**: Raises `ValueError` if NO scenarios have required outputs
4. **Optional**: Can be disabled with `check_outputs=False`

Example warning:
```
UserWarning: Scenario 'Baseline' is missing required outputs: ['co2_emissions']. 
It will be excluded from the plot.
```

Example error (when all scenarios missing outputs):
```
ValueError: No scenarios have all required outputs: ['co2_emissions']
```

## Backward Compatibility

### Plots Without required_outputs

Plots that don't define `required_outputs` continue to work exactly as before:

```python
class OldPlot(SingleScenarioPlot):
    # No required_outputs defined - that's fine!
    
    def _get_default_figsize(self):
        return (8, 6)
    
    def create_plot(self):
        # Works as before, no validation
        pass
    
    def _update_plot_elements(self):
        pass

# No validation occurs
plot = OldPlot(process)  # No warnings, just works
```

### Default Behavior

- Default `required_outputs = []` (empty list)
- Empty list means no validation occurs
- Fully backward compatible with existing plots

## Best Practices

### 1. Always Declare Required Outputs

Make your plots self-documenting:

```python
class EnergyMixPlot(SingleScenarioPlot):
    # Good: Clearly states what's needed
    required_outputs = [
        "energy_consumption_kerosene",
        "energy_consumption_hydrogen",
        "energy_consumption_electric"
    ]
```

### 2. Use Validation by Default

Only disable validation when you have a specific reason:

```python
# Good: Validation happens
plot = MyPlot(process)

# Only if needed
plot = MyPlot(process, check_outputs=False)
```

### 3. Handle Missing Data Gracefully

Even with validation, check for missing data in complex scenarios:

```python
def create_plot(self):
    if "co2_emissions" in self.df.columns:
        # Plot the data
        self.ax.plot(self.years, self.df["co2_emissions"])
    else:
        # Fallback or informative message
        self.ax.text(0.5, 0.5, "Data not available", 
                    ha='center', va='center')
```

### 4. Document Requirements

Add docstrings explaining what outputs are needed and why:

```python
class CarbonIntensityPlot(SingleScenarioPlot):
    """
    Plot carbon intensity over time.
    
    Required Outputs
    ----------------
    - co2_emissions : Total CO2 emissions (Mt)
    - rpk : Revenue passenger kilometers (billion pkm)
    
    The plot shows co2_emissions / rpk to display carbon intensity.
    """
    required_outputs = ["co2_emissions", "rpk"]
```

## Implementation Details

### Parent Classes

Both `SingleScenarioPlot` and `MultiScenarioPlot` now have:

1. **Class Attribute**: `required_outputs = []`
2. **Class Method**: `get_required_outputs() -> List[str]`
3. **Instance Parameter**: `check_outputs: bool = True`
4. **Validation Logic**: Built into `__init__()`

### Validation Flow

#### SingleScenarioPlot

```
__init__(process, check_outputs=True)
  ↓
  if check_outputs and required_outputs:
    ↓
    _validate_required_outputs(data)
      ↓
      Check vector_outputs for each required output
      ↓
      Issue warnings for missing outputs
```

#### MultiScenarioPlot

```
__init__(processes, check_outputs=True)
  ↓
  if check_outputs and required_outputs:
    ↓
    _filter_processes_by_outputs(required_outputs)
      ↓
      For each scenario:
        Check if required outputs exist
        ↓
        If missing: warn and exclude
        If present: include in filtered list
      ↓
      If no scenarios remain: raise ValueError
      ↓
      Return filtered processes
```

## Migration Guide

### For Existing Plots

No changes required! Existing plots without `required_outputs` continue to work.

### To Add Validation to Existing Plots

1. Identify what columns your plot uses from `self.df`
2. Add `required_outputs` class attribute
3. Test with data that has and doesn't have those outputs

Example:

```python
# Before
class MyPlot(SingleScenarioPlot):
    def create_plot(self):
        self.ax.plot(self.years, self.df["energy"])

# After
class MyPlot(SingleScenarioPlot):
    required_outputs = ["energy"]  # Added this line
    
    def create_plot(self):
        self.ax.plot(self.years, self.df["energy"])
```

### For New Plots

Always include `required_outputs`:

```python
class NewPlot(SingleScenarioPlot):
    # Start with this
    required_outputs = ["output1", "output2"]
    
    def _get_default_figsize(self):
        return (10, 6)
    
    def create_plot(self):
        # Use output1 and output2
        pass
    
    def _update_plot_elements(self):
        pass
```

## Testing

### Test That Validation Works

```python
import warnings
from aeromaps import create_process

# Create plot class with required outputs
class TestPlot(SingleScenarioPlot):
    required_outputs = ["nonexistent_output"]
    
    def _get_default_figsize(self):
        return (8, 6)
    
    def create_plot(self):
        pass
    
    def _update_plot_elements(self):
        pass

# Create process
process = create_process()
process.compute()

# Capture warnings
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    plot = TestPlot(process)
    
    # Check that warning was issued
    assert len(w) > 0
    assert "missing" in str(w[0].message).lower()
```

### Test That Filtering Works

```python
# Create plot class
class TestMultiPlot(MultiScenarioPlot):
    required_outputs = ["co2_emissions"]
    
    def _get_default_figsize(self):
        return (10, 6)
    
    def create_plot(self):
        pass
    
    def _update_plot_elements(self):
        pass

# Create processes
proc1 = create_process()
proc1.compute()
proc2 = create_process()
proc2.compute()

processes = {"A": proc1, "B": proc2}

# Create plot
plot = TestMultiPlot(processes)

# Both should be included (if they have co2_emissions)
assert len(plot.scenario_data) == 2
```

## Summary

The `required_outputs` feature provides:

- ✅ **Self-documentation** - Easy to see what a plot needs
- ✅ **Automatic validation** - Catches missing data early
- ✅ **Informative warnings** - Users know what's wrong
- ✅ **Flexible** - Can be disabled when needed
- ✅ **Backward compatible** - Existing code works unchanged
- ✅ **Consistent** - Same pattern for single and multi scenarios

This makes the plotting system more robust and easier to use!
