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
    Compare energy mix across scenarios.

    Shows stacked area plots for each scenario's energy carriers.
    Creates subplots for each scenario to show the evolution of the energy mix.
    Energy carriers are determined dynamically from the pathways_manager.
    """
    
    # No hardcoded required outputs - will be determined dynamically
    required_outputs = []
    
    # Color palette for energy carriers
    DEFAULT_CARRIER_COLORS = ['#ff7f0e', '#9467bd', '#2ca02c', '#d62728', '#1f77b4', 
                              '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

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
        
        # Find common year range across all scenarios to ensure consistent x-axis
        min_year = None
        max_year = None
        for scenario_name, data in scenario_items:
            if data["years"] is not None and len(data["years"]) > 0:
                years = data["years"]
                if min_year is None or years[0] < min_year:
                    min_year = years[0]
                if max_year is None or years[-1] > max_year:
                    max_year = years[-1]
        
        # Determine energy carriers from pathways_manager
        # Default to legacy carriers if pathways_manager is not available
        if self.pathways_manager and hasattr(self.pathways_manager, 'get_all_types'):
            aircraft_types = self.pathways_manager.get_all_types('aircraft_type')
            
            # Build list of energy carrier columns to plot
            energy_carriers = []
            energy_labels = []
            
            for aircraft_type in aircraft_types:
                # Get all energy origins for this aircraft type
                energy_origins = self.pathways_manager.get_all_types('energy_origin')
                
                for energy_origin in energy_origins:
                    # Check if this combination exists
                    pathways = self.pathways_manager.get(
                        aircraft_type=aircraft_type,
                        energy_origin=energy_origin
                    )
                    if pathways:
                        column_name = f"{aircraft_type}_{energy_origin}_energy_consumption"
                        energy_carriers.append(column_name)
                        # Create readable label
                        label = f"{aircraft_type.replace('_', ' ').title()} - {energy_origin.replace('_', ' ').title()}"
                        energy_labels.append(label)
            
            # If no specific aircraft/origin combinations found, try aircraft types
            if not energy_carriers:
                for aircraft_type in aircraft_types:
                    column_name = f"energy_consumption_{aircraft_type}"
                    energy_carriers.append(column_name)
                    energy_labels.append(aircraft_type.replace('_', ' ').title())
        else:
            # Fallback to legacy hardcoded carriers
            energy_carriers = [
                "energy_consumption_dropin_fuel",
                "energy_consumption_hydrogen",
                "energy_consumption_electric"
            ]
            energy_labels = ['Kerosene', 'Hydrogen', 'Electricity']
        
        # Plot each scenario
        for idx, (scenario_name, data) in enumerate(scenario_items):
            ax = axes[idx, 0]
            
            if data["df"] is not None:
                years = data["years"]
                
                # Collect energy data for available carriers (convert to EJ)
                energy_data = []
                labels_to_plot = []
                colors_to_use = []
                
                for carrier_idx, (carrier_col, carrier_label) in enumerate(zip(energy_carriers, energy_labels)):
                    if carrier_col in data["df"].columns:
                        carrier_energy = data["df"].loc[years, carrier_col] * 1e-12
                        # Include carrier even if sum is zero - it may have data in some years
                        # This ensures consistent carriers across all scenarios
                        energy_data.append(carrier_energy)
                        labels_to_plot.append(carrier_label)
                        colors_to_use.append(self.DEFAULT_CARRIER_COLORS[carrier_idx % len(self.DEFAULT_CARRIER_COLORS)])
                
                # Create stacked area plot if we have data
                if energy_data:
                    ax.stackplot(
                        years,
                        *energy_data,
                        labels=labels_to_plot,
                        colors=colors_to_use,
                        alpha=0.8
                    )

                    ax.set_ylabel("Energy [EJ]", fontsize=10)
                    ax.set_title(f"{scenario_name}", fontsize=11, fontweight='bold')
                    ax.legend(loc='upper left', fontsize=9)
                    ax.grid(True, alpha=0.3)
                else:
                    # No energy data available
                    ax.text(0.5, 0.5, 'No energy data available', 
                           ha='center', va='center', transform=ax.transAxes)
                    ax.set_ylabel("Energy [EJ]", fontsize=10)
                    ax.set_title(f"{scenario_name}", fontsize=11, fontweight='bold')
                
                # Set consistent x-axis limits for all subplots
                if min_year is not None and max_year is not None:
                    ax.set_xlim(min_year, max_year)
                
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

