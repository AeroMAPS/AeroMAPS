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
        plotted_budgets = {}  # Maps budget value to scenario name
        
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
                            plotted_budgets[budget] = [scenario_name]
                            self.ax.axhline(
                                y=budget,
                                color="k",
                                linestyle='-',
                                linewidth=1,
                                alpha=0.7,
                                label=f"Budget"
                            )
                        else:
                            # Budget already seen - track but don't plot
                            plotted_budgets[budget].append(scenario_name)
            
            # Update legend for budgets shared by multiple scenarios
            # Get current legend and update budget labels if needed
            handles, labels = self.ax.get_legend_handles_labels()
            updated_labels = []
            for handle, label in zip(handles, labels):
                if label == "Budget":
                    # Find which budget value this is
                    for budget_val, scenario_names in plotted_budgets.items():
                        if len(scenario_names) == 1:
                            # Only one scenario has this budget, keep simple "Budget" label
                            updated_labels.append("Budget")
                            break
                        elif len(scenario_names) > 1:
                            # Multiple scenarios share this budget, use detailed label
                            updated_labels.append(f"Budget - {', '.join(scenario_names)}")
                            break
                else:
                    updated_labels.append(label)
            
        else:
            for idx, data in enumerate(self.scenario_data):
                scenario_name = f"scenario_{idx}"
                style = self.get_scenario_style(scenario_name)

                if data["df"] is not None and "cumulative_co2_emissions" in data["df"].columns:
                    years = data["years"]
                    cumulative_emissions = data["df"].loc[years, "cumulative_co2_emissions"]
                    
                    # Plot emissions line
                    self.ax.plot(
                        years, 
                        cumulative_emissions, 
                        label=f"Scenario {idx+1} - Emissions",
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
                            plotted_budgets[budget] = [f"Scenario {idx+1}"]
                            self.ax.axhline(
                                y=budget,
                                color="k",
                                linestyle='-',
                                linewidth=1,
                                alpha=0.7,
                                label=f"Budget"
                            )
                        else:
                            # Budget already seen - track but don't plot
                            plotted_budgets[budget].append(f"Scenario {idx+1}")
            
            # Update legend for budgets shared by multiple scenarios
            handles, labels = self.ax.get_legend_handles_labels()
            updated_labels = []
            for handle, label in zip(handles, labels):
                if label == "Budget":
                    # Find which budget value this is
                    for budget_val, scenario_names in plotted_budgets.items():
                        if len(scenario_names) == 1:
                            # Only one scenario has this budget, keep simple "Budget" label
                            updated_labels.append("Budget")
                            break
                        elif len(scenario_names) > 1:
                            # Multiple scenarios share this budget, use detailed label
                            updated_labels.append(f"Budget - {', '.join(scenario_names)}")
                            break
                else:
                    updated_labels.append(label)
        
        self.ax.set_xlabel("Year", fontsize=12)
        self.ax.set_ylabel("Cumulative CO2 Emissions [Gt CO2]", fontsize=12)
        self.ax.set_title("Cumulative CO2 vs Carbon Budget Comparison", fontsize=14)
        
        # Set legend with updated labels if we modified any
        handles, labels = self.ax.get_legend_handles_labels()
        self.ax.legend(handles, updated_labels if 'updated_labels' in locals() else labels, loc='best', fontsize=9)
        self.ax.grid(True, alpha=0.3)
    
    def _update_plot_elements(self):
        """Update plot elements with new data."""
        self.ax.clear()
        self.create_plot()
