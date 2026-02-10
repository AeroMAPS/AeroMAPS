"""Multi-scenario comparison plots for fuel supply and production."""

from aeromaps.plots.multi_scenario_plot import MultiScenarioPlot


class FuelSupplyBreakdownPlot(MultiScenarioPlot):
    """
    Compare fuel supply breakdown across scenarios.
    
    Shows the breakdown of drop-in fuel (kerosene) by source:
    fossil, biofuel, and electrofuel (efuel).
    """
    
    # Don't require specific outputs - check dynamically
    required_outputs = []
    
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
        
        # Determine fuel types from pathways_manager dynamically
        # This is similar to how EnergyMix determines carriers
        fuel_columns = []
        fuel_labels = []
        fuel_colors_map = {
            'fossil': '#d62728',
            'biomass': '#2ca02c', 
            'electricity': '#1f77b4',
            'biofuel': '#2ca02c',
            'electrofuel': '#1f77b4',
        }
        default_fuel_colors = ['#d62728', '#2ca02c', '#1f77b4', '#9467bd', '#8c564b']
        
        if self.pathways_manager and hasattr(self.pathways_manager, 'get_all_types'):
            # Get energy origins from pathways_manager
            energy_origins = self.pathways_manager.get_all_types('energy_origin')
            
            # Build list of dropin fuel columns by energy origin
            for energy_origin in energy_origins:
                # Check for dropin fuel breakdown by origin
                column_name = f"energy_consumption_dropin_{energy_origin}"
                fuel_columns.append(column_name)
                # Create readable label
                label = energy_origin.replace('_', ' ').title()
                if 'fossil' in energy_origin.lower():
                    label = 'Fossil Kerosene'
                elif 'bio' in energy_origin.lower():
                    label = 'Biofuel'
                elif 'electro' in energy_origin.lower() or 'electric' in energy_origin.lower():
                    label = 'Electrofuel'
                fuel_labels.append(label)
        
        # Fallback to hardcoded fuel types if pathways not available
        if not fuel_columns:
            fuel_columns = [
                "energy_consumption_dropin_fossil_fuel",
                "energy_consumption_dropin_biofuel",
                "energy_consumption_dropin_electrofuel"
            ]
            fuel_labels = ['Fossil Kerosene', 'Biofuel', 'Electrofuel']
        
        # Plot each scenario
        for idx, (scenario_name, data) in enumerate(scenario_items):
            ax = axes[idx, 0]
            
            if data["df"] is not None:
                years = data["years"]
                
                # Check which fuel types are available and collect them
                fuel_data = []
                labels_to_plot = []
                colors_to_use = []
                
                for fuel_idx, (fuel_col, fuel_label) in enumerate(zip(fuel_columns, fuel_labels)):
                    if fuel_col in data["df"].columns:
                        fuel_energy = data["df"].loc[years, fuel_col] * 1e-12
                        fuel_data.append(fuel_energy)
                        labels_to_plot.append(fuel_label)
                        # Try to get color from map, otherwise use default palette
                        color_key = fuel_label.lower().replace(' ', '_')
                        if 'fossil' in color_key:
                            color_key = 'fossil'
                        elif 'bio' in color_key:
                            color_key = 'biofuel'
                        elif 'electro' in color_key:
                            color_key = 'electrofuel'
                        colors_to_use.append(fuel_colors_map.get(color_key, default_fuel_colors[fuel_idx % len(default_fuel_colors)]))
                
                # Create stacked area plot if we have data
                if fuel_data:
                    ax.stackplot(
                        years,
                        *fuel_data,
                        labels=labels_to_plot,
                        colors=colors_to_use,
                        alpha=0.8
                    )
                    ax.legend(loc='upper left', fontsize=9)
                    ax.grid(True, alpha=0.3)
                else:
                    # No fuel breakdown data available
                    ax.text(0.5, 0.5, 'No fuel breakdown data available', 
                           ha='center', va='center', transform=ax.transAxes)
                
                # Set common labels regardless of data availability
                ax.set_ylabel("Energy [EJ]", fontsize=10)
                ax.set_title(f"{scenario_name}", fontsize=11, fontweight='bold')
                
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
        if isinstance(self.scenario_data, dict):
            for scenario_name, data in self.scenario_data.items():
                # Get style from parent class
                style = self.get_scenario_style(scenario_name)
                
                if data["df"] is not None and "energy_consumption_hydrogen" in data["df"].columns:
                    years = data["years"]
                    hydrogen = data["df"].loc[years, "energy_consumption_hydrogen"] * 1e-12  # Convert to EJ
                    
                    self.ax.plot(
                        years, 
                        hydrogen, 
                        label=scenario_name,
                        color=style['color'],
                        linestyle=style['linestyle'],
                        linewidth=2
                    )
        else:
            for idx, data in enumerate(self.scenario_data):
                scenario_name = f"scenario_{idx}"
                style = self.get_scenario_style(scenario_name)
                
                if data["df"] is not None and "energy_consumption_hydrogen" in data["df"].columns:
                    years = data["years"]
                    hydrogen = data["df"].loc[years, "energy_consumption_hydrogen"] * 1e-12
                    
                    self.ax.plot(
                        years, 
                        hydrogen, 
                        label=f"Scenario {idx+1}",
                        color=style['color'],
                        linestyle=style['linestyle'],
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
        if isinstance(self.scenario_data, dict):
            for scenario_name, data in self.scenario_data.items():
                # Get style from parent class
                style = self.get_scenario_style(scenario_name)
                
                if data["df"] is not None and "energy_consumption_electric" in data["df"].columns:
                    years = data["years"]
                    electric = data["df"].loc[years, "energy_consumption_electric"] * 1e-12  # Convert to EJ
                    
                    self.ax.plot(
                        years, 
                        electric, 
                        label=scenario_name,
                        color=style['color'],
                        linestyle=style['linestyle'],
                        linewidth=2
                    )
        else:
            for idx, data in enumerate(self.scenario_data):
                scenario_name = f"scenario_{idx}"
                style = self.get_scenario_style(scenario_name)
                
                if data["df"] is not None and "energy_consumption_electric" in data["df"].columns:
                    years = data["years"]
                    electric = data["df"].loc[years, "energy_consumption_electric"] * 1e-12
                    
                    self.ax.plot(
                        years, 
                        electric, 
                        label=f"Scenario {idx+1}",
                        color=style['color'],
                        linestyle=style['linestyle'],
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
        if isinstance(self.scenario_data, dict):
            for scenario_name, data in self.scenario_data.items():
                # Get style from parent class
                style = self.get_scenario_style(scenario_name)
                
                if data["df"] is not None and "energy_consumption_dropin_biofuel" in data["df"].columns:
                    years = data["years"]
                    biofuel = data["df"].loc[years, "energy_consumption_dropin_biofuel"] * 1e-12  # Convert to EJ
                    
                    self.ax.plot(
                        years, 
                        biofuel, 
                        label=scenario_name,
                        color=style['color'],
                        linestyle=style['linestyle'],
                        linewidth=2
                    )
        else:
            for idx, data in enumerate(self.scenario_data):
                scenario_name = f"scenario_{idx}"
                style = self.get_scenario_style(scenario_name)
                
                if data["df"] is not None and "energy_consumption_dropin_biofuel" in data["df"].columns:
                    years = data["years"]
                    biofuel = data["df"].loc[years, "energy_consumption_dropin_biofuel"] * 1e-12
                    
                    self.ax.plot(
                        years, 
                        biofuel, 
                        label=f"Scenario {idx+1}",
                        color=style['color'],
                        linestyle=style['linestyle'],
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
        if isinstance(self.scenario_data, dict):
            for scenario_name, data in self.scenario_data.items():
                # Get style from parent class
                style = self.get_scenario_style(scenario_name)
                
                if data["df"] is not None and "energy_consumption_dropin_electrofuel" in data["df"].columns:
                    years = data["years"]
                    efuel = data["df"].loc[years, "energy_consumption_dropin_electrofuel"] * 1e-12  # Convert to EJ
                    
                    self.ax.plot(
                        years, 
                        efuel, 
                        label=scenario_name,
                        color=style['color'],
                        linestyle=style['linestyle'],
                        linewidth=2
                    )
        else:
            for idx, data in enumerate(self.scenario_data):
                scenario_name = f"scenario_{idx}"
                style = self.get_scenario_style(scenario_name)
                
                if data["df"] is not None and "energy_consumption_dropin_electrofuel" in data["df"].columns:
                    years = data["years"]
                    efuel = data["df"].loc[years, "energy_consumption_dropin_electrofuel"] * 1e-12
                    
                    self.ax.plot(
                        years, 
                        efuel, 
                        label=f"Scenario {idx+1}",
                        color=style['color'],
                        linestyle=style['linestyle'],
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
