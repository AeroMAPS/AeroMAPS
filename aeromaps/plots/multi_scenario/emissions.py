"""Multi-scenario comparison plots for emissions."""

import matplotlib.pyplot as plt
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
        # Define colors for different scenarios
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                  '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        if isinstance(self.scenario_data, dict):
            # Plot each scenario
            for idx, (scenario_name, data) in enumerate(self.scenario_data.items()):
                color = colors[idx % len(colors)]
                
                # Check if data exists
                if data["df"] is not None and "co2_emissions" in data["df"].columns:
                    years = data["years"]
                    emissions = data["df"].loc[years, "co2_emissions"]
                    
                    self.ax.plot(
                        years, 
                        emissions, 
                        label=scenario_name,
                        color=color,
                        linewidth=2
                    )
        else:
            # List of scenarios
            for idx, data in enumerate(self.scenario_data):
                color = colors[idx % len(colors)]
                
                if data["df"] is not None and "co2_emissions" in data["df"].columns:
                    years = data["years"]
                    emissions = data["df"].loc[years, "co2_emissions"]
                    
                    self.ax.plot(
                        years, 
                        emissions, 
                        label=f"Scenario {idx+1}",
                        color=color,
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
