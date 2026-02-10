"""Multi-scenario comparison plots for emissions."""

from aeromaps.plots.multi_scenario_plot import MultiScenarioPlot


class CO2EmissionsComparisonPlot(MultiScenarioPlot):
    """
    Compare CO2 emissions across multiple scenarios.
    
    Shows the evolution of CO2 emissions over time for each scenario,
    allowing easy comparison of different decarbonization pathways.
    """
    
    # Define required outputs for validation
    required_outputs = ["co2_emissions"]
    
    def _get_default_figsize(self):
        """Return default figure size."""
        return (12, 6)
    
    def create_plot(self):
        """Create the CO2 emissions comparison plot."""
        if isinstance(self.scenario_data, dict):
            # Plot each scenario
            for scenario_name, data in self.scenario_data.items():
                # Get style from parent class
                style = self.get_scenario_style(scenario_name)
                
                # Check if data exists
                if data["df_climate"] is not None and "co2_emissions" in data["df_climate"].columns:
                    years = data["years"]
                    emissions = data["df_climate"].loc[years, "co2_emissions"]
                    
                    self.ax.plot(
                        years, 
                        emissions, 
                        label=scenario_name,
                        color=style['color'],
                        linestyle=style['linestyle'],
                        linewidth=2
                    )
        else:
            # List of scenarios
            for idx, data in enumerate(self.scenario_data):
                scenario_name = f"scenario_{idx}"
                style = self.get_scenario_style(scenario_name)
                
                if data["df_climate"] is not None and "co2_emissions" in data["df_climate"].columns:
                    years = data["years"]
                    emissions = data["df_climate"].loc[years, "co2_emissions"]
                    
                    self.ax.plot(
                        years, 
                        emissions, 
                        label=f"Scenario {idx+1}",
                        color=style['color'],
                        linestyle=style['linestyle'],
                        linewidth=2
                    )
        
        # Configure plot
        self.ax.set_xlabel("Year", fontsize=12)
        self.ax.set_ylabel("CO2 Emissions [Mt CO2]", fontsize=12)
        self.ax.set_title("CO2 Emissions Comparison Across Scenarios", fontsize=14)
        self.ax.legend(loc='best')
        self.ax.grid(True, alpha=0.3)
    
    def _update_plot_elements(self):
        """Update plot elements with new data."""
        # Clear existing lines
        self.ax.clear()
        # Recreate the plot
        self.create_plot()

class CarbonBudgetComparisonPlot(MultiScenarioPlot):
    """
    Compare cumulative CO2 emissions against carbon budget across scenarios.
    
    Shows both the cumulative emissions and the allocated carbon budget
    for each scenario, allowing assessment of budget compliance.
    """
    
    required_outputs = ["cumulative_co2_emissions"]
    
    def _get_default_figsize(self):
        """Return default figure size."""
        return (12, 6)
    
    def create_plot(self):
        """Create the carbon budget comparison plot."""
        # Track budgets to only plot unique ones
        # Maps budget value to list of (scenario_name, line_handle)
        plotted_budgets = {}
        
        # Plot cumulative emissions for each scenario
        if isinstance(self.scenario_data, dict):
            for scenario_name, data in self.scenario_data.items():
                # Get style from parent class
                style = self.get_scenario_style(scenario_name)

                if data["df"] is not None and "cumulative_co2_emissions" in data["df"].columns:
                    years = data["years"]
                    cumulative_emissions = data["df"].loc[years, "cumulative_co2_emissions"]
                    
                    # Plot emissions line
                    self.ax.plot(
                        years, 
                        cumulative_emissions, 
                        label=f"{scenario_name} - Emissions",
                        color=style['color'],
                        linestyle=style['linestyle'],
                        linewidth=2
                    )
                    
                    # Plot carbon budget if available and unique
                    if data["float_outputs"] is not None and "aviation_carbon_budget" in data["float_outputs"]:
                        budget = data["float_outputs"]["aviation_carbon_budget"]
                        
                        # Check if this budget value has been plotted before
                        if budget not in plotted_budgets:
                            # First time seeing this budget value - plot it
                            line = self.ax.axhline(
                                y=budget,
                                color="k",
                                linestyle='-',
                                linewidth=1,
                                alpha=0.7,
                                label=f"Budget"  # Temporary label, will update later
                            )
                            plotted_budgets[budget] = [(scenario_name, line)]
                        else:
                            # Budget already seen - track scenario but don't plot
                            plotted_budgets[budget].append((scenario_name, None))
            
            # Update legend labels based on whether budgets are unique or shared
            # When there are multiple different budget values, differentiate them
            unique_budget_values = len(plotted_budgets)
            
            for budget_val, scenario_info in plotted_budgets.items():
                scenario_names = [name for name, line in scenario_info]
                # Get the line handle (first entry has the actual line)
                line_handle = scenario_info[0][1]
                
                if unique_budget_values == 1:
                    # Only one budget value exists - simple label
                    if len(scenario_names) == 1:
                        line_handle.set_label("Budget")
                    else:
                        # Multiple scenarios share this single budget value
                        line_handle.set_label(f"Budget - {', '.join(scenario_names)}")
                else:
                    # Multiple different budget values - always show which scenarios
                    line_handle.set_label(f"Budget - {', '.join(scenario_names)}")
            
        else:
            for idx, data in enumerate(self.scenario_data):
                scenario_name = f"scenario_{idx}"  # Key for style lookup
                display_name = f"Scenario {idx+1}"  # Readable label for display
                style = self.get_scenario_style(scenario_name)

                if data["df"] is not None and "cumulative_co2_emissions" in data["df"].columns:
                    years = data["years"]
                    cumulative_emissions = data["df"].loc[years, "cumulative_co2_emissions"]
                    
                    # Plot emissions line
                    self.ax.plot(
                        years, 
                        cumulative_emissions, 
                        label=f"{display_name} - Emissions",
                        color=style['color'],
                        linestyle=style['linestyle'],
                        linewidth=2
                    )
                    
                    # Plot carbon budget if available and unique
                    if data["float_outputs"] is not None and "aviation_carbon_budget" in data["float_outputs"]:
                        budget = data["float_outputs"]["aviation_carbon_budget"]
                        
                        # Check if this budget value has been plotted before
                        if budget not in plotted_budgets:
                            # First time seeing this budget value - plot it
                            line = self.ax.axhline(
                                y=budget,
                                color="k",
                                linestyle='-',
                                linewidth=1,
                                alpha=0.7,
                                label=f"Budget"  # Temporary label, will update later
                            )
                            plotted_budgets[budget] = [(display_name, line)]
                        else:
                            # Budget already seen - track scenario but don't plot
                            plotted_budgets[budget].append((display_name, None))
            
            # Update legend labels based on whether budgets are unique or shared
            # When there are multiple different budget values, differentiate them
            unique_budget_values = len(plotted_budgets)
            
            for budget_val, scenario_info in plotted_budgets.items():
                scenario_names = [name for name, line in scenario_info]
                # Get the line handle (first entry has the actual line)
                line_handle = scenario_info[0][1]
                
                if unique_budget_values == 1:
                    # Only one budget value exists - simple label
                    if len(scenario_names) == 1:
                        line_handle.set_label("Budget")
                    else:
                        # Multiple scenarios share this single budget value
                        line_handle.set_label(f"Budget - {', '.join(scenario_names)}")
                else:
                    # Multiple different budget values - always show which scenarios
                    line_handle.set_label(f"Budget - {', '.join(scenario_names)}")
        
        self.ax.set_xlabel("Year", fontsize=12)
        self.ax.set_ylabel("Cumulative CO2 Emissions [Gt CO2]", fontsize=12)
        self.ax.set_title("Cumulative CO2 vs Carbon Budget Comparison", fontsize=14)
        self.ax.legend(loc='best', fontsize=9)
        self.ax.grid(True, alpha=0.3)
    
    def _update_plot_elements(self):
        """Update plot elements with new data."""
        self.ax.clear()
        self.create_plot()
