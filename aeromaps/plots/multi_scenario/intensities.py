"""Multi-scenario comparison plots for intensity metrics."""

import matplotlib.pyplot as plt
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
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                  '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        if isinstance(self.scenario_data, dict):
            for idx, (scenario_name, data) in enumerate(self.scenario_data.items()):
                color = colors[idx % len(colors)]
                
                if data["df"] is not None and "co2_emissions_per_rpk" in data["df"].columns:
                    years = data["years"]
                    intensity = data["df"].loc[years, "co2_emissions_per_rpk"]
                    
                    self.ax.plot(
                        years, 
                        intensity, 
                        label=scenario_name,
                        color=color,
                        linewidth=2
                    )
        else:
            for idx, data in enumerate(self.scenario_data):
                color = colors[idx % len(colors)]
                
                if data["df"] is not None and "co2_emissions_per_rpk" in data["df"].columns:
                    years = data["years"]
                    intensity = data["df"].loc[years, "co2_emissions_per_rpk"]
                    
                    self.ax.plot(
                        years, 
                        intensity, 
                        label=f"Scenario {idx+1}",
                        color=color,
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
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                  '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        if isinstance(self.scenario_data, dict):
            for idx, (scenario_name, data) in enumerate(self.scenario_data.items()):
                color = colors[idx % len(colors)]
                
                if data["df"] is not None and "co2_emissions_per_rtk" in data["df"].columns:
                    years = data["years"]
                    intensity = data["df"].loc[years, "co2_emissions_per_rtk"]
                    
                    self.ax.plot(
                        years, 
                        intensity, 
                        label=scenario_name,
                        color=color,
                        linewidth=2
                    )
        else:
            for idx, data in enumerate(self.scenario_data):
                color = colors[idx % len(colors)]
                
                if data["df"] is not None and "co2_emissions_per_rtk" in data["df"].columns:
                    years = data["years"]
                    intensity = data["df"].loc[years, "co2_emissions_per_rtk"]
                    
                    self.ax.plot(
                        years, 
                        intensity, 
                        label=f"Scenario {idx+1}",
                        color=color,
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
    
    required_outputs = ["energy_per_ask"]
    
    def _get_default_figsize(self):
        """Return default figure size."""
        return (12, 6)
    
    def create_plot(self):
        """Create the energy per ASK comparison plot."""
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                  '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        if isinstance(self.scenario_data, dict):
            for idx, (scenario_name, data) in enumerate(self.scenario_data.items()):
                color = colors[idx % len(colors)]
                
                if data["df"] is not None and "energy_per_ask" in data["df"].columns:
                    years = data["years"]
                    intensity = data["df"].loc[years, "energy_per_ask"]
                    
                    self.ax.plot(
                        years, 
                        intensity, 
                        label=scenario_name,
                        color=color,
                        linewidth=2
                    )
        else:
            for idx, data in enumerate(self.scenario_data):
                color = colors[idx % len(colors)]
                
                if data["df"] is not None and "energy_per_ask" in data["df"].columns:
                    years = data["years"]
                    intensity = data["df"].loc[years, "energy_per_ask"]
                    
                    self.ax.plot(
                        years, 
                        intensity, 
                        label=f"Scenario {idx+1}",
                        color=color,
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
    
    required_outputs = ["energy_per_rtk"]
    
    def _get_default_figsize(self):
        """Return default figure size."""
        return (12, 6)
    
    def create_plot(self):
        """Create the energy per RTK comparison plot."""
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                  '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        if isinstance(self.scenario_data, dict):
            for idx, (scenario_name, data) in enumerate(self.scenario_data.items()):
                color = colors[idx % len(colors)]
                
                if data["df"] is not None and "energy_per_rtk" in data["df"].columns:
                    years = data["years"]
                    intensity = data["df"].loc[years, "energy_per_rtk"]
                    
                    self.ax.plot(
                        years, 
                        intensity, 
                        label=scenario_name,
                        color=color,
                        linewidth=2
                    )
        else:
            for idx, data in enumerate(self.scenario_data):
                color = colors[idx % len(colors)]
                
                if data["df"] is not None and "energy_per_rtk" in data["df"].columns:
                    years = data["years"]
                    intensity = data["df"].loc[years, "energy_per_rtk"]
                    
                    self.ax.plot(
                        years, 
                        intensity, 
                        label=f"Scenario {idx+1}",
                        color=color,
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
