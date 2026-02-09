"""Multi-scenario comparison plots for fuel supply and production."""

from aeromaps.plots.multi_scenario_plot import MultiScenarioPlot


class FuelSupplyBreakdownPlot(MultiScenarioPlot):
    """
    Compare fuel supply breakdown across scenarios.
    
    Shows the breakdown of drop-in fuel (kerosene) by source:
    fossil, biofuel, and electrofuel (efuel).
    """
    
    required_outputs = [
        "energy_consumption_dropin_fossil_fuel",
        "energy_consumption_dropin_biofuel",
        "energy_consumption_dropin_electrofuel"
    ]
    
    def _get_default_figsize(self):
        """Return default figure size based on number of scenarios."""
        n_scenarios = len(self.scenario_data)
        height = max(4, 3 * n_scenarios)
        return (12, height)
    
    def create_plot(self):
        """Create the fuel supply breakdown plot with subplots."""
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
                
                # Get fuel data (convert to EJ)
                fossil = data["df"].loc[years, "energy_consumption_dropin_fossil_fuel"] * 1e-12
                biofuel = data["df"].loc[years, "energy_consumption_dropin_biofuel"] * 1e-12
                efuel = data["df"].loc[years, "energy_consumption_dropin_electrofuel"] * 1e-12
                
                # Create stacked area plot
                ax.stackplot(
                    years,
                    fossil,
                    biofuel, 
                    efuel,
                    labels=['Fossil Kerosene', 'Biofuel', 'Electrofuel'],
                    colors=['#d62728', '#2ca02c', '#1f77b4'],
                    alpha=0.8
                )
                
                ax.set_ylabel("Energy [EJ]", fontsize=10)
                ax.set_title(f"{scenario_name}", fontsize=11, fontweight='bold')
                ax.legend(loc='upper left', fontsize=9)
                ax.grid(True, alpha=0.3)
                
                # Only show x-label on bottom subplot
                if idx == n_scenarios - 1:
                    ax.set_xlabel("Year", fontsize=12)
        
        self.fig.suptitle("Drop-in Fuel Supply Breakdown (Fossil, Biofuel, Electrofuel)", fontsize=14, y=0.995)
        self.fig.tight_layout()
        
        # Store axes for updates
        self.axes = axes
    
    def _update_plot_elements(self):
        """Update plot elements with new data."""
        self.fig.clear()
        self.create_plot()


class HydrogenSupplyComparisonPlot(MultiScenarioPlot):
    """
    Compare hydrogen (LH2) supply across scenarios.
    
    Shows the evolution of hydrogen energy consumption.
    """
    
    required_outputs = ["energy_consumption_hydrogen"]
    
    def _get_default_figsize(self):
        """Return default figure size."""
        return (12, 6)
    
    def create_plot(self):
        """Create the hydrogen supply comparison plot."""
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                  '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        if isinstance(self.scenario_data, dict):
            for idx, (scenario_name, data) in enumerate(self.scenario_data.items()):
                color = colors[idx % len(colors)]
                
                if data["df"] is not None and "energy_consumption_hydrogen" in data["df"].columns:
                    years = data["years"]
                    hydrogen = data["df"].loc[years, "energy_consumption_hydrogen"] * 1e-12  # Convert to EJ
                    
                    self.ax.plot(
                        years, 
                        hydrogen, 
                        label=scenario_name,
                        color=color,
                        linewidth=2
                    )
        else:
            for idx, data in enumerate(self.scenario_data):
                color = colors[idx % len(colors)]
                
                if data["df"] is not None and "energy_consumption_hydrogen" in data["df"].columns:
                    years = data["years"]
                    hydrogen = data["df"].loc[years, "energy_consumption_hydrogen"] * 1e-12
                    
                    self.ax.plot(
                        years, 
                        hydrogen, 
                        label=f"Scenario {idx+1}",
                        color=color,
                        linewidth=2
                    )
        
        self.ax.set_xlabel("Year", fontsize=12)
        self.ax.set_ylabel("Hydrogen Energy Consumption [EJ]", fontsize=12)
        self.ax.set_title("Hydrogen (LH2) Supply Comparison", fontsize=14)
        self.ax.legend(loc='best')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_ylim(bottom=0)
    
    def _update_plot_elements(self):
        """Update plot elements with new data."""
        self.ax.clear()
        self.create_plot()


class ElectricSupplyComparisonPlot(MultiScenarioPlot):
    """
    Compare electric/battery supply across scenarios.
    
    Shows the evolution of electric energy consumption.
    """
    
    required_outputs = ["energy_consumption_electric"]
    
    def _get_default_figsize(self):
        """Return default figure size."""
        return (12, 6)
    
    def create_plot(self):
        """Create the electric supply comparison plot."""
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                  '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        if isinstance(self.scenario_data, dict):
            for idx, (scenario_name, data) in enumerate(self.scenario_data.items()):
                color = colors[idx % len(colors)]
                
                if data["df"] is not None and "energy_consumption_electric" in data["df"].columns:
                    years = data["years"]
                    electric = data["df"].loc[years, "energy_consumption_electric"] * 1e-12  # Convert to EJ
                    
                    self.ax.plot(
                        years, 
                        electric, 
                        label=scenario_name,
                        color=color,
                        linewidth=2
                    )
        else:
            for idx, data in enumerate(self.scenario_data):
                color = colors[idx % len(colors)]
                
                if data["df"] is not None and "energy_consumption_electric" in data["df"].columns:
                    years = data["years"]
                    electric = data["df"].loc[years, "energy_consumption_electric"] * 1e-12
                    
                    self.ax.plot(
                        years, 
                        electric, 
                        label=f"Scenario {idx+1}",
                        color=color,
                        linewidth=2
                    )
        
        self.ax.set_xlabel("Year", fontsize=12)
        self.ax.set_ylabel("Electric Energy Consumption [EJ]", fontsize=12)
        self.ax.set_title("Electric/Battery Supply Comparison", fontsize=14)
        self.ax.legend(loc='best')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_ylim(bottom=0)
    
    def _update_plot_elements(self):
        """Update plot elements with new data."""
        self.ax.clear()
        self.create_plot()


class BiofuelProductionComparisonPlot(MultiScenarioPlot):
    """
    Compare biofuel production across scenarios.
    
    Shows the evolution of biofuel consumption/production.
    """
    
    required_outputs = ["energy_consumption_dropin_biofuel"]
    
    def _get_default_figsize(self):
        """Return default figure size."""
        return (12, 6)
    
    def create_plot(self):
        """Create the biofuel production comparison plot."""
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                  '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        if isinstance(self.scenario_data, dict):
            for idx, (scenario_name, data) in enumerate(self.scenario_data.items()):
                color = colors[idx % len(colors)]
                
                if data["df"] is not None and "energy_consumption_dropin_biofuel" in data["df"].columns:
                    years = data["years"]
                    biofuel = data["df"].loc[years, "energy_consumption_dropin_biofuel"] * 1e-12  # Convert to EJ
                    
                    self.ax.plot(
                        years, 
                        biofuel, 
                        label=scenario_name,
                        color=color,
                        linewidth=2
                    )
        else:
            for idx, data in enumerate(self.scenario_data):
                color = colors[idx % len(colors)]
                
                if data["df"] is not None and "energy_consumption_dropin_biofuel" in data["df"].columns:
                    years = data["years"]
                    biofuel = data["df"].loc[years, "energy_consumption_dropin_biofuel"] * 1e-12
                    
                    self.ax.plot(
                        years, 
                        biofuel, 
                        label=f"Scenario {idx+1}",
                        color=color,
                        linewidth=2
                    )
        
        self.ax.set_xlabel("Year", fontsize=12)
        self.ax.set_ylabel("Biofuel Production [EJ]", fontsize=12)
        self.ax.set_title("Biofuel Production Comparison", fontsize=14)
        self.ax.legend(loc='best')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_ylim(bottom=0)
    
    def _update_plot_elements(self):
        """Update plot elements with new data."""
        self.ax.clear()
        self.create_plot()


class ElectrofuelProductionComparisonPlot(MultiScenarioPlot):
    """
    Compare electrofuel (efuel) production across scenarios.
    
    Shows the evolution of electrofuel consumption/production.
    """
    
    required_outputs = ["energy_consumption_dropin_electrofuel"]
    
    def _get_default_figsize(self):
        """Return default figure size."""
        return (12, 6)
    
    def create_plot(self):
        """Create the electrofuel production comparison plot."""
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                  '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        if isinstance(self.scenario_data, dict):
            for idx, (scenario_name, data) in enumerate(self.scenario_data.items()):
                color = colors[idx % len(colors)]
                
                if data["df"] is not None and "energy_consumption_dropin_electrofuel" in data["df"].columns:
                    years = data["years"]
                    efuel = data["df"].loc[years, "energy_consumption_dropin_electrofuel"] * 1e-12  # Convert to EJ
                    
                    self.ax.plot(
                        years, 
                        efuel, 
                        label=scenario_name,
                        color=color,
                        linewidth=2
                    )
        else:
            for idx, data in enumerate(self.scenario_data):
                color = colors[idx % len(colors)]
                
                if data["df"] is not None and "energy_consumption_dropin_electrofuel" in data["df"].columns:
                    years = data["years"]
                    efuel = data["df"].loc[years, "energy_consumption_dropin_electrofuel"] * 1e-12
                    
                    self.ax.plot(
                        years, 
                        efuel, 
                        label=f"Scenario {idx+1}",
                        color=color,
                        linewidth=2
                    )
        
        self.ax.set_xlabel("Year", fontsize=12)
        self.ax.set_ylabel("Electrofuel Production [EJ]", fontsize=12)
        self.ax.set_title("Electrofuel Production Comparison", fontsize=14)
        self.ax.legend(loc='best')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_ylim(bottom=0)
    
    def _update_plot_elements(self):
        """Update plot elements with new data."""
        self.ax.clear()
        self.create_plot()
