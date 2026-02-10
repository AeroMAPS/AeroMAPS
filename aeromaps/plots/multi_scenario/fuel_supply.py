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
        
        # Plot each scenario
        for idx, (scenario_name, data) in enumerate(scenario_items):
            ax = axes[idx, 0]
            
            if data["df"] is not None:
                years = data["years"]
                
                # Dynamically discover all dropin_fuel energy origins
                fuel_data = []
                labels_to_plot = []
                colors_to_use = []
                
                # Color map for known energy origins
                color_map = {
                    'fossil': '#d62728',
                    'biomass': '#2ca02c',
                    'electricity': '#1f77b4',
                }
                default_colors = ['#9467bd', '#8c564b', '#e377c2']
                color_idx = 0
                
                if self.pathways_manager:
                    # Get all energy origins from pathways_manager
                    energy_origins = self.pathways_manager.get_all_types('energy_origin')
                    
                    for energy_origin in energy_origins:
                        # Get all dropin_fuel pathways with this energy origin
                        pathways = self.pathways_manager.get(
                            aircraft_type="dropin_fuel",
                            energy_origin=energy_origin
                        )
                        if pathways:
                            total_fuel = None
                            for pathway in pathways:
                                col_name = f"{pathway.name}_energy_consumption"
                                if col_name in data["df"].columns:
                                    pathway_fuel = data["df"].loc[years, col_name]
                                    if total_fuel is None:
                                        total_fuel = pathway_fuel.copy()
                                    else:
                                        total_fuel += pathway_fuel
                            
                            if total_fuel is not None and total_fuel.sum() > 0:
                                # Create readable label
                                if energy_origin == 'fossil':
                                    label = 'Fossil Kerosene'
                                elif energy_origin == 'biomass':
                                    label = 'Biofuel'
                                elif energy_origin == 'electricity':
                                    label = 'Electrofuel'
                                else:
                                    label = energy_origin.replace('_', ' ').title()
                                
                                fuel_data.append(total_fuel * 1e-12)
                                labels_to_plot.append(label)
                                color = color_map.get(energy_origin, default_colors[color_idx % len(default_colors)])
                                colors_to_use.append(color)
                                color_idx += 1
                
                # Fallback to legacy column names if pathways didn't find anything
                if not fuel_data:
                    legacy_fuels = [
                        ("energy_consumption_dropin_fossil_fuel", "Fossil Kerosene", '#d62728'),
                        ("energy_consumption_dropin_biofuel", "Biofuel", '#2ca02c'),
                        ("energy_consumption_dropin_electrofuel", "Electrofuel", '#1f77b4')
                    ]
                    for fuel_col, fuel_label, color in legacy_fuels:
                        if fuel_col in data["df"].columns:
                            fuel_energy = data["df"].loc[years, fuel_col] * 1e-12
                            if fuel_energy.sum() > 0:
                                fuel_data.append(fuel_energy)
                                labels_to_plot.append(fuel_label)
                                colors_to_use.append(color)
                
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
    
    Shows the evolution of biofuel consumption/production by aggregating
    all dropin_fuel pathways with biomass energy origin.
    """
    
    # Don't require specific columns - aggregate dynamically
    required_outputs = []
    
    def _get_default_figsize(self):
        """Return default figure size."""
        return (12, 6)
    
    def create_plot(self):
        """Create the biofuel production comparison plot."""
        if isinstance(self.scenario_data, dict):
            for scenario_name, data in self.scenario_data.items():
                # Get style from parent class
                style = self.get_scenario_style(scenario_name)
                
                if data["df"] is not None:
                    years = data["years"]
                    
                    # Aggregate all biomass dropin_fuel pathways
                    biofuel = None
                    if self.pathways_manager:
                        pathways = self.pathways_manager.get(
                            aircraft_type="dropin_fuel",
                            energy_origin="biomass"
                        )
                        if pathways:
                            for pathway in pathways:
                                col_name = f"{pathway.name}_energy_consumption"
                                if col_name in data["df"].columns:
                                    pathway_energy = data["df"].loc[years, col_name]
                                    if biofuel is None:
                                        biofuel = pathway_energy.copy()
                                    else:
                                        biofuel += pathway_energy
                    
                    # Try legacy column if pathways didn't work
                    if biofuel is None and "energy_consumption_dropin_biofuel" in data["df"].columns:
                        biofuel = data["df"].loc[years, "energy_consumption_dropin_biofuel"]
                    
                    # Plot if we found data
                    if biofuel is not None:
                        self.ax.plot(
                            years, 
                            biofuel * 1e-12,  # Convert to EJ
                            label=scenario_name,
                            color=style['color'],
                            linestyle=style['linestyle'],
                            linewidth=2
                        )
        else:
            for idx, data in enumerate(self.scenario_data):
                scenario_name = f"scenario_{idx}"
                style = self.get_scenario_style(scenario_name)
                
                if data["df"] is not None:
                    years = data["years"]
                    
                    # Aggregate all biomass dropin_fuel pathways
                    biofuel = None
                    if self.pathways_manager:
                        pathways = self.pathways_manager.get(
                            aircraft_type="dropin_fuel",
                            energy_origin="biomass"
                        )
                        if pathways:
                            for pathway in pathways:
                                col_name = f"{pathway.name}_energy_consumption"
                                if col_name in data["df"].columns:
                                    pathway_energy = data["df"].loc[years, col_name]
                                    if biofuel is None:
                                        biofuel = pathway_energy.copy()
                                    else:
                                        biofuel += pathway_energy
                    
                    # Try legacy column if pathways didn't work
                    if biofuel is None and "energy_consumption_dropin_biofuel" in data["df"].columns:
                        biofuel = data["df"].loc[years, "energy_consumption_dropin_biofuel"]
                    
                    # Plot if we found data
                    if biofuel is not None:
                        self.ax.plot(
                            years, 
                            biofuel * 1e-12,  # Convert to EJ
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
    
    Shows the evolution of electrofuel consumption/production by aggregating
    all dropin_fuel pathways with electricity energy origin.
    """
    
    # Don't require specific columns - aggregate dynamically
    required_outputs = []
    
    def _get_default_figsize(self):
        """Return default figure size."""
        return (12, 6)
    
    def create_plot(self):
        """Create the electrofuel production comparison plot."""
        if isinstance(self.scenario_data, dict):
            for scenario_name, data in self.scenario_data.items():
                # Get style from parent class
                style = self.get_scenario_style(scenario_name)
                
                if data["df"] is not None:
                    years = data["years"]
                    
                    # Aggregate all electricity dropin_fuel pathways
                    electrofuel = None
                    if self.pathways_manager:
                        pathways = self.pathways_manager.get(
                            aircraft_type="dropin_fuel",
                            energy_origin="electricity"
                        )
                        if pathways:
                            for pathway in pathways:
                                col_name = f"{pathway.name}_energy_consumption"
                                if col_name in data["df"].columns:
                                    pathway_energy = data["df"].loc[years, col_name]
                                    if electrofuel is None:
                                        electrofuel = pathway_energy.copy()
                                    else:
                                        electrofuel += pathway_energy
                    
                    # Try legacy column if pathways didn't work
                    if electrofuel is None and "energy_consumption_dropin_electrofuel" in data["df"].columns:
                        electrofuel = data["df"].loc[years, "energy_consumption_dropin_electrofuel"]
                    
                    # Plot if we found data
                    if electrofuel is not None:
                        self.ax.plot(
                            years, 
                            electrofuel * 1e-12,  # Convert to EJ
                            label=scenario_name,
                            color=style['color'],
                            linestyle=style['linestyle'],
                            linewidth=2
                        )
        else:
            for idx, data in enumerate(self.scenario_data):
                scenario_name = f"scenario_{idx}"
                style = self.get_scenario_style(scenario_name)
                
                if data["df"] is not None:
                    years = data["years"]
                    
                    # Aggregate all electricity dropin_fuel pathways
                    electrofuel = None
                    if self.pathways_manager:
                        pathways = self.pathways_manager.get(
                            aircraft_type="dropin_fuel",
                            energy_origin="electricity"
                        )
                        if pathways:
                            for pathway in pathways:
                                col_name = f"{pathway.name}_energy_consumption"
                                if col_name in data["df"].columns:
                                    pathway_energy = data["df"].loc[years, col_name]
                                    if electrofuel is None:
                                        electrofuel = pathway_energy.copy()
                                    else:
                                        electrofuel += pathway_energy
                    
                    # Try legacy column if pathways didn't work
                    if electrofuel is None and "energy_consumption_dropin_electrofuel" in data["df"].columns:
                        electrofuel = data["df"].loc[years, "energy_consumption_dropin_electrofuel"]
                    
                    # Plot if we found data
                    if electrofuel is not None:
                        self.ax.plot(
                            years, 
                            electrofuel * 1e-12,  # Convert to EJ
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


class BiofuelMixComparisonPlot(MultiScenarioPlot):
    """
    Compare biofuel mix across scenarios.
    
    Shows stacked area plots for each scenario's biofuel pathways.
    Creates subplots for each scenario to show the evolution of biofuel production
    among different pathways (HEFA, FT, etc.).
    """
    
    # Don't require specific outputs - aggregate dynamically
    required_outputs = []
    
    def _get_default_figsize(self):
        """Return default figure size based on number of scenarios."""
        n_scenarios = len(self.scenario_data) if hasattr(self, 'scenario_data') else 1
        height = max(4, 3 * n_scenarios)
        return (12, height)
    
    def create_plot(self):
        """Create the biofuel mix comparison plot with subplots."""
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
        
        # Default color palette for biofuel pathways
        default_colors = ['#2ca02c', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', 
                         '#17becf', '#9467bd', '#d62728', '#ff7f0e', '#1f77b4']
        
        # Plot each scenario
        for idx, (scenario_name, data) in enumerate(scenario_items):
            ax = axes[idx, 0]
            
            if data["df"] is not None:
                years = data["years"]
                
                # Collect biofuel data by individual pathways
                biofuel_data = []
                labels_to_plot = []
                colors_to_use = []
                
                if self.pathways_manager:
                    # Get all biomass dropin_fuel pathways
                    pathways = self.pathways_manager.get(
                        aircraft_type="dropin_fuel",
                        energy_origin="biomass"
                    )
                    if pathways:
                        for pathway_idx, pathway in enumerate(pathways):
                            col_name = f"{pathway.name}_energy_consumption"
                            if col_name in data["df"].columns:
                                pathway_energy = data["df"].loc[years, col_name] * 1e-12  # Convert to EJ
                                if pathway_energy.sum() > 0:
                                    # Create readable label from pathway name
                                    label = pathway.name.replace('_', ' ').title()
                                    # Simplify common pathway names
                                    label = label.replace('Hefa ', 'HEFA-')
                                    label = label.replace('Ft ', 'FT-')
                                    label = label.replace('Atj ', 'ATJ-')
                                    
                                    biofuel_data.append(pathway_energy)
                                    labels_to_plot.append(label)
                                    colors_to_use.append(default_colors[pathway_idx % len(default_colors)])
                
                # Create stacked area plot if we have data
                if biofuel_data:
                    ax.stackplot(
                        years,
                        *biofuel_data,
                        labels=labels_to_plot,
                        colors=colors_to_use,
                        alpha=0.8
                    )
                    ax.set_ylabel("Biofuel Production [EJ]", fontsize=10)
                    ax.set_title(f"{scenario_name}", fontsize=11, fontweight='bold')
                    ax.legend(loc='upper left', fontsize=9, ncol=2)
                    ax.grid(True, alpha=0.3)
                else:
                    # No biofuel data available
                    ax.text(0.5, 0.5, 'No biofuel pathway data available', 
                           ha='center', va='center', transform=ax.transAxes)
                    ax.set_ylabel("Biofuel Production [EJ]", fontsize=10)
                    ax.set_title(f"{scenario_name}", fontsize=11, fontweight='bold')
                
                # Only show x-label on bottom subplot
                if idx == n_scenarios - 1:
                    ax.set_xlabel("Year", fontsize=12)
        
        self.fig.suptitle("Biofuel Mix Comparison Across Scenarios", fontsize=14, y=0.995)
        self.fig.tight_layout()
        
        # Store axes for updates
        self.axes = axes
    
    def _update_plot_elements(self):
        """Update plot elements with new data."""
        self.fig.clear()
        self.create_plot()
