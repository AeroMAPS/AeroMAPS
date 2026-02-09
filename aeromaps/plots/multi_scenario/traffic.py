"""Multi-scenario comparison plots for air traffic."""

from aeromaps.plots.multi_scenario_plot import MultiScenarioPlot


class RPKComparisonPlot(MultiScenarioPlot):
    """
    Compare Revenue Passenger Kilometers across multiple scenarios.
    
    Shows the evolution of RPK over time for each scenario.
    """
    
    required_outputs = ["rpk"]
    
    def _get_default_figsize(self):
        """Return default figure size."""
        return (12, 6)
    
    def create_plot(self):
        """Create the RPK comparison plot."""
        if isinstance(self.scenario_data, dict):
            for scenario_name, data in self.scenario_data.items():
                # Get style from parent class
                style = self.get_scenario_style(scenario_name)
                
                if data["df"] is not None and "rpk" in data["df"].columns:
                    years = data["years"]
                    rpk = data["df"].loc[years, "rpk"] * 1e-12  # Convert to trillion pkm
                    
                    self.ax.plot(
                        years, 
                        rpk, 
                        label=scenario_name,
                        color=style['color'],
                        linestyle=style['linestyle'],
                        linewidth=2
                    )
        else:
            for idx, data in enumerate(self.scenario_data):
                scenario_name = f"scenario_{idx}"
                style = self.get_scenario_style(scenario_name)
                
                if data["df"] is not None and "rpk" in data["df"].columns:
                    years = data["years"]
                    rpk = data["df"].loc[years, "rpk"] * 1e-12
                    
                    self.ax.plot(
                        years, 
                        rpk, 
                        label=f"Scenario {idx+1}",
                        color=style['color'],
                        linestyle=style['linestyle'],
                        linewidth=2
                    )
        
        self.ax.set_xlabel("Year", fontsize=12)
        self.ax.set_ylabel("Revenue Passenger Kilometers [trillion pkm]", fontsize=12)
        self.ax.set_title("RPK Comparison Across Scenarios", fontsize=14)
        self.ax.legend(loc='best')
        self.ax.grid(True, alpha=0.3)
    
    def _update_plot_elements(self):
        """Update plot elements with new data."""
        self.ax.clear()
        self.create_plot()


class LoadFactorComparisonPlot(MultiScenarioPlot):
    """
    Compare aircraft load factor across multiple scenarios.
    
    Shows the evolution of load factor over time for each scenario.
    """
    
    required_outputs = ["load_factor"]
    
    def _get_default_figsize(self):
        """Return default figure size."""
        return (12, 6)
    
    def create_plot(self):
        """Create the load factor comparison plot."""
        if isinstance(self.scenario_data, dict):
            for scenario_name, data in self.scenario_data.items():
                # Get style from parent class
                style = self.get_scenario_style(scenario_name)
                
                if data["df"] is not None and "load_factor" in data["df"].columns:
                    years = data["years"]
                    load_factor = data["df"].loc[years, "load_factor"]
                    
                    self.ax.plot(
                        years, 
                        load_factor, 
                        label=scenario_name,
                        color=style['color'],
                        linestyle=style['linestyle'],
                        linewidth=2
                    )
        else:
            for idx, data in enumerate(self.scenario_data):
                scenario_name = f"scenario_{idx}"
                style = self.get_scenario_style(scenario_name)
                
                if data["df"] is not None and "load_factor" in data["df"].columns:
                    years = data["years"]
                    load_factor = data["df"].loc[years, "load_factor"]
                    
                    self.ax.plot(
                        years, 
                        load_factor, 
                        label=f"Scenario {idx+1}",
                        color=style['color'],
                        linestyle=style['linestyle'],
                        linewidth=2
                    )
        
        self.ax.set_xlabel("Year", fontsize=12)
        self.ax.set_ylabel("Load Factor [%]", fontsize=12)
        self.ax.set_title("Load Factor Comparison Across Scenarios", fontsize=14)
        self.ax.legend(loc='best')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_ylim(0, 100)
    
    def _update_plot_elements(self):
        """Update plot elements with new data."""
        self.ax.clear()
        self.create_plot()
