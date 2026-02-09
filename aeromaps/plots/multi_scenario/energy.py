"""Multi-scenario comparison plots for energy consumption."""

from aeromaps.plots.multi_scenario_plot import MultiScenarioPlot


class EnergyConsumptionComparisonPlot(MultiScenarioPlot):
    """
    Compare total energy consumption across multiple scenarios.
    
    Shows the evolution of total energy consumption over time for each scenario.
    """
    
    required_outputs = ["energy_consumption"]
    
    def _get_default_figsize(self):
        """Return default figure size."""
        return (12, 6)
    
    def create_plot(self):
        """Create the energy consumption comparison plot."""
        if isinstance(self.scenario_data, dict):
            for scenario_name, data in self.scenario_data.items():
                # Get style from parent class
                style = self.get_scenario_style(scenario_name)

                if data["df"] is not None and "energy_consumption" in data["df"].columns:
                    years = data["years"]
                    energy = data["df"].loc[years, "energy_consumption"] * 1e-12  # Convert to EJ
                    
                    self.ax.plot(
                        years, 
                        energy, 
                        label=scenario_name,
                        color=style['color'],
                        linestyle=style['linestyle'],
                        linewidth=2
                    )
        else:
            for idx, data in enumerate(self.scenario_data):
                scenario_name = f"scenario_{idx}"
                style = self.get_scenario_style(scenario_name)

                if data["df"] is not None and "energy_consumption" in data["df"].columns:
                    years = data["years"]
                    energy = data["df"].loc[years, "energy_consumption"] * 1e-12
                    
                    self.ax.plot(
                        years, 
                        energy, 
                        label=f"Scenario {idx+1}",
                        color=style['color'],
                        linestyle=style['linestyle'],
                        linewidth=2
                    )
        
        self.ax.set_xlabel("Year", fontsize=12)
        self.ax.set_ylabel("Total Energy Consumption [EJ]", fontsize=12)
        self.ax.set_title("Energy Consumption Comparison Across Scenarios", fontsize=14)
        self.ax.legend(loc='best')
        self.ax.grid(True, alpha=0.3)
    
    def _update_plot_elements(self):
        """Update plot elements with new data."""
        self.ax.clear()
        self.create_plot()


class EnergyMixComparisonPlot(MultiScenarioPlot):
    """
    Compare energy mix (kerosene, hydrogen, electricity) across scenarios.
    
    Shows stacked area plots for each scenario's energy sources.
    Creates subplots for each scenario to show the evolution of the energy mix.
    """
    
    required_outputs = [
        "energy_consumption_dropin_fuel",
        "energy_consumption_hydrogen", 
        "energy_consumption_electric"
    ]
    
    def _get_default_figsize(self):
        """Return default figure size based on number of scenarios."""
        n_scenarios = len(self.scenario_data)
        height = max(4, 3 * n_scenarios)
        return (12, height)
    
    def create_plot(self):
        """Create the energy mix comparison plot with subplots."""
        # Get number of scenarios
        if isinstance(self.scenario_data, dict):
            scenario_items = list(self.scenario_data.items())
        else:
            scenario_items = [(f"Scenario {i+1}", data) 
                             for i, data in enumerate(self.scenario_data)]
        
        n_scenarios = len(scenario_items)
        
        # Clear existing axes and create subplots
        self.fig.clear()
        axes = self.fig.subplots(n_scenarios, 1, squeeze=False)
        
        # Plot each scenario
        for idx, (scenario_name, data) in enumerate(scenario_items):
            ax = axes[idx, 0]
            
            if data["df"] is not None:
                years = data["years"]
                
                # Get energy data (convert to EJ)
                kerosene = data["df"].loc[years, "energy_consumption_dropin_fuel"] * 1e-12
                hydrogen = data["df"].loc[years, "energy_consumption_hydrogen"] * 1e-12
                electricity = data["df"].loc[years, "energy_consumption_electric"] * 1e-12
                
                # Create stacked area plot
                ax.stackplot(
                    years,
                    kerosene,
                    hydrogen, 
                    electricity,
                    labels=['Kerosene', 'Hydrogen', 'Electricity'],
                    colors=['#ff7f0e', '#9467bd', '#2ca02c'],
                    alpha=0.8
                )
                
                ax.set_ylabel("Energy [EJ]", fontsize=10)
                ax.set_title(f"{scenario_name}", fontsize=11, fontweight='bold')
                ax.legend(loc='upper left', fontsize=9)
                ax.grid(True, alpha=0.3)
                
                # Only show x-label on bottom subplot
                if idx == n_scenarios - 1:
                    ax.set_xlabel("Year", fontsize=12)
        
        self.fig.suptitle("Energy Mix Comparison Across Scenarios", fontsize=14, y=0.995)
        self.fig.tight_layout()
        
        # Store axes for updates
        self.axes = axes
    
    def _update_plot_elements(self):
        """Update plot elements with new data."""
        self.fig.clear()
        self.create_plot()
