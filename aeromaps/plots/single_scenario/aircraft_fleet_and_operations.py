import matplotlib.pyplot as plt

from aeromaps.plots.single_scenario_plot import SingleScenarioPlot
from aeromaps.plots.single_scenario_plot import plot_3_x
from aeromaps.plots.single_scenario_plot import plot_3_y


class DropinFuelConsumptionLiterPerPAX100kmPlot(SingleScenarioPlot):
    def __init__(self, process, figsize=None):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize)

    def _get_default_figsize(self):
        return (plot_3_x, plot_3_y)
        data = process.data
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.fig, self.ax = plt.subplots(
            figsize=(plot_3_x, plot_3_y),
        )
        self.create_plot()

    def create_plot(self):
        self.ax.plot(
            self.historic_years,
            self.df.loc[self.historic_years, "dropin_fuel_consumption_liter_per_pax_100km"],
            color="black",
            linestyle="-",
            label="History",
            linewidth=2,
        )

        (self.line_fuel_consumption_l100km,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "dropin_fuel_consumption_liter_per_pax_100km"],
            color="blue",
            linestyle="-",
            label="Projections",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title(
            "Evolution of (drop-in) fuel consumption\nper passenger for air transport"
        )
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Fuel consumption per passenger [L/100km]")
        
        self.ax.legend()
        self.ax.set_xlim(self.years[0], self.years[-1])

    def _update_plot_elements(self):
        self.line_fuel_consumption_l100km.set_ydata(
            self.df.loc[self.prospective_years, "dropin_fuel_consumption_liter_per_pax_100km"]
        )


class MeanLoadFactorPlot(SingleScenarioPlot):
    def __init__(self, process, figsize=None):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize)

    def _get_default_figsize(self):
        return (plot_3_x, plot_3_y)
        data = process.data
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.fig, self.ax = plt.subplots(
            figsize=(plot_3_x, plot_3_y),
        )
        self.create_plot()

    def create_plot(self):
        self.ax.plot(
            self.historic_years,
            self.df.loc[self.historic_years, "load_factor"],
            color="black",
            linestyle="-",
            label="History",
            linewidth=2,
        )

        (self.line_load_factor,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "load_factor"],
            color="blue",
            linestyle="-",
            label="Projections",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title("Evolution of the aircraft load factor")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Aircraft load factor [%]")
        
        self.ax.legend()
        self.ax.set_xlim(self.years[0], self.years[-1])

    def _update_plot_elements(self):
        self.line_load_factor.set_ydata(self.df.loc[self.prospective_years, "load_factor"])


class MeanEnergyPerASKPlot(SingleScenarioPlot):
    def __init__(self, process, figsize=None):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize)

    def _get_default_figsize(self):
        return (plot_3_x, plot_3_y)

    def create_plot(self):
        self.ax.plot(
            self.historic_years,
            self.df.loc[self.historic_years, "energy_per_ask_mean"],
            color="black",
            linestyle="-",
            label="History",
            linewidth=2,
        )

        (self.line_energy_per_ask,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "energy_per_ask_mean"],
            color="blue",
            linestyle="-",
            label="Projections",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title(
            "Evolution of the mean energy consumed\nper Available Seat Kilometer (ASK)"
        )
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Energy per Available Seat Kilometer [MJ/ASK]")
        
        self.ax.legend()
        self.ax.set_xlim(self.years[0], self.years[-1])

    def _update_plot_elements(self):
        self.line_energy_per_ask.set_ydata(
            self.df.loc[self.prospective_years, "energy_per_ask_mean"]
        )


class MeanEnergyPerRTKPlot(SingleScenarioPlot):
    def __init__(self, process, figsize=None):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize)

    def _get_default_figsize(self):
        return (plot_3_x, plot_3_y)

    def create_plot(self):
        self.ax.plot(
            self.historic_years,
            self.df.loc[self.historic_years, "energy_per_rtk_mean"],
            color="black",
            linestyle="-",
            label="History",
            linewidth=2,
        )

        (self.line_energy_per_rtk,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "energy_per_rtk_mean"],
            color="blue",
            linestyle="-",
            label="Projections",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title(
            "Evolution of the mean energy consumed\nper Revenue Tonne Kilometer (RTK)"
        )
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Energy per Revenue Tonne Kilometer [MJ/RTK]")
        
        self.ax.legend()
        self.ax.set_xlim(self.years[0], self.years[-1])

    def _update_plot_elements(self):
        self.line_energy_per_rtk.set_ydata(
            self.df.loc[self.prospective_years, "energy_per_rtk_mean"]
        )
