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
                if data["df"] is not None and "co2_emissions" in data["df"].columns:
                    years = data["years"]
                    emissions = data["df"].loc[years, "co2_emissions"]
                    
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
                
                if data["df"] is not None and "co2_emissions" in data["df"].columns:
                    years = data["years"]
                    emissions = data["df"].loc[years, "co2_emissions"]
                    
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


class CumulativeCO2ComparisonPlot(MultiScenarioPlot):
    """
    Compare cumulative CO2 emissions across multiple scenarios.
    
    Shows the accumulated CO2 emissions over time for each scenario,
    useful for understanding total carbon budget consumption.
    """
    
    required_outputs = ["cumulative_co2_emissions"]
    
    def _get_default_figsize(self):
        """Return default figure size."""
        return (12, 6)
    
    def create_plot(self):
        """Create the cumulative CO2 emissions comparison plot."""
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                  '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        if isinstance(self.scenario_data, dict):
            for idx, (scenario_name, data) in enumerate(self.scenario_data.items()):
                color = colors[idx % len(colors)]
                
                if data["df"] is not None and "cumulative_co2_emissions" in data["df"].columns:
                    years = data["years"]
                    cumulative_emissions = data["df"].loc[years, "cumulative_co2_emissions"]
                    
                    self.ax.plot(
                        years, 
                        cumulative_emissions, 
                        label=scenario_name,
                        color=color,
                        linewidth=2
                    )
        else:
            for idx, data in enumerate(self.scenario_data):
                color = colors[idx % len(colors)]
                
                if data["df"] is not None and "cumulative_co2_emissions" in data["df"].columns:
                    years = data["years"]
                    cumulative_emissions = data["df"].loc[years, "cumulative_co2_emissions"]
                    
                    self.ax.plot(
                        years, 
                        cumulative_emissions, 
                        label=f"Scenario {idx+1}",
                        color=color,
                        linewidth=2
                    )
        
        self.ax.set_xlabel("Year", fontsize=12)
        self.ax.set_ylabel("Cumulative CO2 Emissions [Gt CO2]", fontsize=12)
        self.ax.set_title("Cumulative CO2 Emissions Comparison", fontsize=14)
        self.ax.legend(loc='best')
        self.ax.grid(True, alpha=0.3)
    
    def _update_plot_elements(self):
        """Update plot elements with new data."""
        self.ax.clear()
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
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                  '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        # Plot cumulative emissions for each scenario
        if isinstance(self.scenario_data, dict):
            for idx, (scenario_name, data) in enumerate(self.scenario_data.items()):
                color = colors[idx % len(colors)]
                
                if data["df"] is not None and "cumulative_co2_emissions" in data["df"].columns:
                    years = data["years"]
                    cumulative_emissions = data["df"].loc[years, "cumulative_co2_emissions"]
                    
                    # Plot emissions line
                    self.ax.plot(
                        years, 
                        cumulative_emissions, 
                        label=f"{scenario_name} - Emissions",
                        color=color,
                        linewidth=2,
                        linestyle='-'
                    )
                    
                    # Plot carbon budget if available
                    if data["float_outputs"] is not None and "aviation_carbon_budget" in data["float_outputs"]:
                        budget = data["float_outputs"]["aviation_carbon_budget"]
                        self.ax.axhline(
                            y=budget,
                            color=color,
                            linestyle='--',
                            linewidth=1.5,
                            alpha=0.7,
                            label=f"{scenario_name} - Budget"
                        )
        else:
            for idx, data in enumerate(self.scenario_data):
                color = colors[idx % len(colors)]
                
                if data["df"] is not None and "cumulative_co2_emissions" in data["df"].columns:
                    years = data["years"]
                    cumulative_emissions = data["df"].loc[years, "cumulative_co2_emissions"]
                    
                    # Plot emissions line
                    self.ax.plot(
                        years, 
                        cumulative_emissions, 
                        label=f"Scenario {idx+1} - Emissions",
                        color=color,
                        linewidth=2,
                        linestyle='-'
                    )
                    
                    # Plot carbon budget if available
                    if data["float_outputs"] is not None and "aviation_carbon_budget" in data["float_outputs"]:
                        budget = data["float_outputs"]["aviation_carbon_budget"]
                        self.ax.axhline(
                            y=budget,
                            color=color,
                            linestyle='--',
                            linewidth=1.5,
                            alpha=0.7,
                            label=f"Scenario {idx+1} - Budget"
                        )
        
        self.ax.set_xlabel("Year", fontsize=12)
        self.ax.set_ylabel("Cumulative CO2 Emissions [Gt CO2]", fontsize=12)
        self.ax.set_title("Cumulative CO2 vs Carbon Budget Comparison", fontsize=14)
        self.ax.legend(loc='best', fontsize=9)
        self.ax.grid(True, alpha=0.3)
    
    def _update_plot_elements(self):
        """Update plot elements with new data."""
        self.ax.clear()
        self.create_plot()
