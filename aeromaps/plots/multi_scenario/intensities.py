"""Multi-scenario comparison plots for intensity metrics."""

from aeromaps.plots.multi_scenario_plot import MultiScenarioPlot


class CO2PerRPKComparisonPlot(MultiScenarioPlot):
    """
    Compare CO2 emissions per passenger kilometer across scenarios.
    
    Shows carbon intensity evolution for passenger transport.
    """
    
    required_outputs = ["co2_emissions_per_rpk"]
    
    def _get_default_figsize(self):
        """Return default figure size."""
        return (12, 6)
    
    def create_plot(self):
        """Create the CO2 per RPK comparison plot."""
        if isinstance(self.scenario_data, dict):
            for scenario_name, data in self.scenario_data.items():
                # Get style from parent class
                style = self.get_scenario_style(scenario_name)
                
                if data["df"] is not None and "co2_emissions_per_rpk" in data["df"].columns:
                    years = data["years"]
                    intensity = data["df"].loc[years, "co2_emissions_per_rpk"]
                    
                    self.ax.plot(
                        years, 
                        intensity, 
                        label=scenario_name,
                        color=style['color'],
                        linestyle=style['linestyle'],
                        linewidth=2
                    )
        else:
            for idx, data in enumerate(self.scenario_data):
                scenario_name = f"scenario_{idx}"
                style = self.get_scenario_style(scenario_name)
                
                if data["df"] is not None and "co2_emissions_per_rpk" in data["df"].columns:
                    years = data["years"]
                    intensity = data["df"].loc[years, "co2_emissions_per_rpk"]
                    
                    self.ax.plot(
                        years, 
                        intensity, 
                        label=f"Scenario {idx+1}",
                        color=style['color'],
                        linestyle=style['linestyle'],
                        linewidth=2
                    )
        
        self.ax.set_xlabel("Year", fontsize=12)
        self.ax.set_ylabel("CO2 per RPK [gCO2/RPK]", fontsize=12)
        self.ax.set_title("Carbon Intensity per Passenger Kilometer", fontsize=14)
        self.ax.legend(loc='best')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_ylim(bottom=0)
    
    def _update_plot_elements(self):
        """Update plot elements with new data."""
        self.ax.clear()
        self.create_plot()


class CO2PerRTKComparisonPlot(MultiScenarioPlot):
    """
    Compare CO2 emissions per revenue tonne kilometer across scenarios.
    
    Shows carbon intensity evolution for freight transport.
    """
    
    required_outputs = ["co2_emissions_per_rtk"]
    
    def _get_default_figsize(self):
        """Return default figure size."""
        return (12, 6)
    
    def create_plot(self):
        """Create the CO2 per RTK comparison plot."""
        if isinstance(self.scenario_data, dict):
            for scenario_name, data in self.scenario_data.items():
                # Get style from parent class
                style = self.get_scenario_style(scenario_name)
                
                if data["df"] is not None and "co2_emissions_per_rtk" in data["df"].columns:
                    years = data["years"]
                    intensity = data["df"].loc[years, "co2_emissions_per_rtk"]
                    
                    self.ax.plot(
                        years, 
                        intensity, 
                        label=scenario_name,
                        color=style['color'],
                        linestyle=style['linestyle'],
                        linewidth=2
                    )
        else:
            for idx, data in enumerate(self.scenario_data):
                scenario_name = f"scenario_{idx}"
                style = self.get_scenario_style(scenario_name)
                
                if data["df"] is not None and "co2_emissions_per_rtk" in data["df"].columns:
                    years = data["years"]
                    intensity = data["df"].loc[years, "co2_emissions_per_rtk"]
                    
                    self.ax.plot(
                        years, 
                        intensity, 
                        label=f"Scenario {idx+1}",
                        color=style['color'],
                        linestyle=style['linestyle'],
                        linewidth=2
                    )
        
        self.ax.set_xlabel("Year", fontsize=12)
        self.ax.set_ylabel("CO2 per RTK [gCO2/RTK]", fontsize=12)
        self.ax.set_title("Carbon Intensity per Revenue Tonne Kilometer", fontsize=14)
        self.ax.legend(loc='best')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_ylim(bottom=0)
    
    def _update_plot_elements(self):
        """Update plot elements with new data."""
        self.ax.clear()
        self.create_plot()


class EnergyPerASKComparisonPlot(MultiScenarioPlot):
    """
    Compare energy consumption per available seat kilometer across scenarios.
    
    Shows energy intensity evolution for passenger capacity.
    """
    
    required_outputs = ["energy_per_ask_mean"]
    
    def _get_default_figsize(self):
        """Return default figure size."""
        return (12, 6)
    
    def create_plot(self):
        """Create the energy per ASK comparison plot."""
        if isinstance(self.scenario_data, dict):
            for scenario_name, data in self.scenario_data.items():
                # Get style from parent class
                style = self.get_scenario_style(scenario_name)
                
                if data["df"] is not None and "energy_per_ask_mean" in data["df"].columns:
                    years = data["years"]
                    intensity = data["df"].loc[years, "energy_per_ask_mean"]
                    
                    self.ax.plot(
                        years, 
                        intensity, 
                        label=scenario_name,
                        color=style['color'],
                        linestyle=style['linestyle'],
                        linewidth=2
                    )
        else:
            for idx, data in enumerate(self.scenario_data):
                scenario_name = f"scenario_{idx}"
                style = self.get_scenario_style(scenario_name)
                
                if data["df"] is not None and "energy_per_ask_mean" in data["df"].columns:
                    years = data["years"]
                    intensity = data["df"].loc[years, "energy_per_ask_mean"]
                    
                    self.ax.plot(
                        years, 
                        intensity, 
                        label=f"Scenario {idx+1}",
                        color=style['color'],
                        linestyle=style['linestyle'],
                        linewidth=2
                    )
        
        self.ax.set_xlabel("Year", fontsize=12)
        self.ax.set_ylabel("Energy per ASK [MJ/ASK]", fontsize=12)
        self.ax.set_title("Energy Intensity per Available Seat Kilometer", fontsize=14)
        self.ax.legend(loc='best')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_ylim(bottom=0)
    
    def _update_plot_elements(self):
        """Update plot elements with new data."""
        self.ax.clear()
        self.create_plot()


class EnergyPerRTKComparisonPlot(MultiScenarioPlot):
    """
    Compare energy consumption per revenue tonne kilometer across scenarios.
    
    Shows energy intensity evolution for freight operations.
    """
    
    required_outputs = ["energy_per_rtk_mean"]
    
    def _get_default_figsize(self):
        """Return default figure size."""
        return (12, 6)
    
    def create_plot(self):
        """Create the energy per RTK comparison plot."""
        if isinstance(self.scenario_data, dict):
            for scenario_name, data in self.scenario_data.items():
                # Get style from parent class
                style = self.get_scenario_style(scenario_name)
                
                if data["df"] is not None and "energy_per_rtk_mean" in data["df"].columns:
                    years = data["years"]
                    intensity = data["df"].loc[years, "energy_per_rtk_mean"]
                    
                    self.ax.plot(
                        years, 
                        intensity, 
                        label=scenario_name,
                        color=style['color'],
                        linestyle=style['linestyle'],
                        linewidth=2
                    )
        else:
            for idx, data in enumerate(self.scenario_data):
                scenario_name = f"scenario_{idx}"
                style = self.get_scenario_style(scenario_name)
                
                if data["df"] is not None and "energy_per_rtk_mean" in data["df"].columns:
                    years = data["years"]
                    intensity = data["df"].loc[years, "energy_per_rtk_mean"]
                    
                    self.ax.plot(
                        years, 
                        intensity, 
                        label=f"Scenario {idx+1}",
                        color=style['color'],
                        linestyle=style['linestyle'],
                        linewidth=2
                    )
        
        self.ax.set_xlabel("Year", fontsize=12)
        self.ax.set_ylabel("Energy per RTK [MJ/RTK]", fontsize=12)
        self.ax.set_title("Energy Intensity per Revenue Tonne Kilometer", fontsize=14)
        self.ax.legend(loc='best')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_ylim(bottom=0)
    
    def _update_plot_elements(self):
        """Update plot elements with new data."""
        self.ax.clear()
        self.create_plot()
