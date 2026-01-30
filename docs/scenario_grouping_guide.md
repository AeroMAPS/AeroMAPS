# Scenario Grouping Guide

## Overview

The scenario grouping feature allows you to visually organize related scenarios in multi-scenario comparison plots. Scenarios within a group share the same color but use different line styles, making it easy to compare variations within a policy type or scenario family.

## Key Concepts

### Without Grouping (Default)
By default, each scenario gets its own unique color and solid line style:
- Scenario 1: Blue solid line
- Scenario 2: Orange solid line  
- Scenario 3: Green solid line
- etc.

### With Grouping
When you define groups, scenarios within each group share a color but use different line styles:
- **Group A** (Blue color):
  - Scenario A1: Blue solid line (-)
  - Scenario A2: Blue dashed line (--)
  - Scenario A3: Blue dash-dot line (-.)
- **Group B** (Orange color):
  - Scenario B1: Orange solid line (-)
  - Scenario B2: Orange dashed line (--)

## Usage

### Basic Example

```python
from aeromaps import create_process, create_multi_process

# Create scenarios
baseline_2030 = create_process(configuration_file="baseline_2030.yaml")
baseline_2040 = create_process(configuration_file="baseline_2040.yaml")
optimistic_2030 = create_process(configuration_file="optimistic_2030.yaml")
optimistic_2040 = create_process(configuration_file="optimistic_2040.yaml")

# Create multi-process manager
multi = create_multi_process({
    "Baseline_2030": baseline_2030,
    "Baseline_2040": baseline_2040,
    "Optimistic_2030": optimistic_2030,
    "Optimistic_2040": optimistic_2040
})

# Compute all scenarios
multi.compute_all()

# Define scenario groups
scenario_groups = {
    "Baseline": ["Baseline_2030", "Baseline_2040"],
    "Optimistic": ["Optimistic_2030", "Optimistic_2040"]
}

# Create plot with grouping
multi.plot("co2_emissions_comparison", scenario_groups=scenario_groups)
```

### Use Cases

#### 1. Time Variations
Group scenarios by policy type, vary by time period:
```python
groups = {
    "Current Policy": ["Current_2030", "Current_2040", "Current_2050"],
    "Net Zero": ["NetZero_2030", "NetZero_2040", "NetZero_2050"]
}
```

#### 2. Technology Variations
Group by target year, vary by technology mix:
```python
groups = {
    "2030 Scenarios": ["2030_BioOnly", "2030_Hybrid", "2030_Electric"],
    "2050 Scenarios": ["2050_BioOnly", "2050_Hybrid", "2050_Electric"]
}
```

#### 3. Sensitivity Analysis
Group by base scenario, vary by parameter:
```python
groups = {
    "High Demand": ["High_LowPrice", "High_MidPrice", "High_HighPrice"],
    "Low Demand": ["Low_LowPrice", "Low_MidPrice", "Low_HighPrice"]
}
```

### Direct Plot Creation

You can also use grouping when creating plots directly:

```python
from aeromaps.plots.multi_scenario.emissions import CO2EmissionsComparisonPlot

processes = {
    "S1": proc1,
    "S2": proc2,
    "S3": proc3,
    "S4": proc4
}

groups = {
    "GroupA": ["S1", "S2"],
    "GroupB": ["S3", "S4"]
}

plot = CO2EmissionsComparisonPlot(processes, scenario_groups=groups)
```

## Styling Details

### Default Color Palette
The system uses 10 default colors (cycling if more groups needed):
1. Blue (#1f77b4)
2. Orange (#ff7f0e)
3. Green (#2ca02c)
4. Red (#d62728)
5. Purple (#9467bd)
6. Brown (#8c564b)
7. Pink (#e377c2)
8. Gray (#7f7f7f)
9. Olive (#bcbd22)
10. Cyan (#17becf)

### Default Line Styles
Within each group, 4 line styles cycle (repeating if more scenarios in group):
1. Solid: `-`
2. Dashed: `--`
3. Dash-dot: `-.`
4. Dotted: `:`

### Ungrouped Scenarios
Scenarios not included in any group will:
- Get their own unique color (continuing from the group colors)
- Use solid line style
- Appear normally in the legend

## Advanced Usage

### Mixed Grouping
You can have some scenarios grouped and others independent:

```python
groups = {
    "Policy Variants": ["Policy_A", "Policy_B", "Policy_C"]
    # "Reference" scenario not in any group - gets its own color
}

multi.plot("co2_emissions_comparison", scenario_groups=groups)
```

### Programmatic Group Creation

```python
# Create groups based on naming convention
scenarios = multi.get_scenario_names()

groups = {}
for scenario in scenarios:
    # Extract policy type from scenario name
    policy = scenario.split('_')[0]
    if policy not in groups:
        groups[policy] = []
    groups[policy].append(scenario)

multi.plot("co2_emissions_comparison", scenario_groups=groups)
```

## Implementation in Custom Plots

If you're creating custom multi-scenario plots, you can use the grouping feature:

```python
from aeromaps.plots.multi_scenario_plot import MultiScenarioPlot

class MyCustomPlot(MultiScenarioPlot):
    required_outputs = ["my_metric"]
    
    def _get_default_figsize(self):
        return (12, 6)
    
    def create_plot(self):
        # Use get_scenario_style() to get coordinated colors/styles
        for scenario_name, data in self.scenario_data.items():
            style = self.get_scenario_style(scenario_name)
            
            self.ax.plot(
                data["years"],
                data["df"]["my_metric"],
                label=scenario_name,
                color=style['color'],
                linestyle=style['linestyle'],
                linewidth=2
            )
        
        self.ax.legend()
        self.ax.grid(True)
```

## Best Practices

### 1. Logical Grouping
Group scenarios that share a common characteristic:
- ✅ Same policy approach with different time horizons
- ✅ Same base year with different technology mixes
- ✅ Same assumptions with parameter sensitivity
- ❌ Random or unrelated scenarios

### 2. Group Size
Keep groups manageable:
- ✅ 2-4 scenarios per group (best)
- ⚠️ 5-6 scenarios per group (acceptable)
- ❌ 7+ scenarios per group (hard to distinguish)

### 3. Naming Convention
Use clear, consistent scenario names:
- ✅ "Policy_2030", "Policy_2040", "Policy_2050"
- ✅ "Base_Conservative", "Base_Moderate", "Base_Aggressive"
- ❌ "Scenario1", "Scenario2", "Test"

### 4. Legend Clarity
The legend will show all scenarios with their line styles. Ensure:
- Scenario names are descriptive
- Groups are logically organized
- Not too many total scenarios (10-12 maximum recommended)

## Troubleshooting

### Scenario Not Found in Group
If you specify a scenario name in groups that doesn't exist in the processes:
- The scenario will be silently ignored
- No error will be raised
- Check scenario names match exactly (case-sensitive)

### Too Many Groups
If you have more groups than colors (>10):
- Colors will cycle (groups may share colors)
- Consider consolidating groups or using fewer scenarios

### Line Styles Not Distinguishable
If scenarios within a group are hard to distinguish:
- Reduce number of scenarios per group
- Use thicker lines (linewidth parameter)
- Consider splitting into separate plots

## Backward Compatibility

The grouping feature is completely optional:
- Existing code without scenario_groups works unchanged
- Default behavior (each scenario different color) is preserved
- No breaking changes to any existing functionality

## Examples Gallery

### Example 1: Policy Comparison

```python
groups = {
    "Current Trajectory": [
        "Current_2030",
        "Current_2040", 
        "Current_2050"
    ],
    "Paris Agreement": [
        "Paris_2030",
        "Paris_2040",
        "Paris_2050"
    ],
    "Net Zero": [
        "NetZero_2030",
        "NetZero_2040",
        "NetZero_2050"
    ]
}
```
Result: 3 colors (one per policy), 3 line styles within each

### Example 2: Regional Comparison

```python
groups = {
    "North America": ["NA_Low", "NA_Base", "NA_High"],
    "Europe": ["EU_Low", "EU_Base", "EU_High"],
    "Asia": ["Asia_Low", "Asia_Base", "Asia_High"]
}
```
Result: 3 colors (one per region), 3 line styles within each

### Example 3: Technology Pathways

```python
groups = {
    "Biofuels": ["Bio_Rapid", "Bio_Moderate", "Bio_Slow"],
    "Hydrogen": ["H2_Rapid", "H2_Moderate", "H2_Slow"],
    "Electric": ["Elec_Rapid", "Elec_Moderate", "Elec_Slow"],
    "Hybrid": ["Hybrid_Rapid", "Hybrid_Moderate", "Hybrid_Slow"]
}
```
Result: 4 colors (one per technology), 3 line styles within each

## Summary

Scenario grouping is a powerful feature for organizing and visualizing complex multi-scenario comparisons:

✅ **Visual clarity** - Related scenarios share colors  
✅ **Easy comparison** - Line styles distinguish within groups  
✅ **Flexible** - Works with any number of scenarios and groups  
✅ **Optional** - Completely backward compatible  
✅ **Simple API** - Just pass a dictionary to plot()

Use it to make your multi-scenario plots more readable and informative!
