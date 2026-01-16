from aeromaps.plots.single_scenario_plot import SingleScenarioPlot
from aeromaps.plots.single_scenario_plot import plot_3_x
from aeromaps.plots.single_scenario_plot import plot_3_y


class RevenuePassengerKilometerPlot(SingleScenarioPlot):
    def __init__(self, process, figsize=None):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize)

    def _get_default_figsize(self):
        return (plot_3_x, plot_3_y)

    def create_plot(self):
        self.ax.plot(
            self.historic_years,
            self.df.loc[self.historic_years, "rpk"],
            color="black",
            linestyle="-",
            label="History",
            linewidth=2,
        )

        (self.line_rpk,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "rpk"],
            color="blue",
            linestyle="-",
            label="Projections",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title("Evolution of the Revenue\nPassenger Kilometer (RPK) for air transport")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Revenue Passenger Kilometer [RPK]")
        self.ax.legend()
        
        self.ax.set_xlim(self.years[0], self.years[-1])

    def _update_plot_elements(self):
        self.line_rpk.set_ydata(self.df.loc[self.prospective_years, "rpk"])


class RevenueTonneKilometerPlot(SingleScenarioPlot):
    def __init__(self, process, figsize=None):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize)

    def _get_default_figsize(self):
        return (plot_3_x, plot_3_y)

    def create_plot(self):
        self.ax.plot(
            self.historic_years,
            self.df.loc[self.historic_years, "rtk"],
            color="black",
            linestyle="-",
            label="History",
            linewidth=2,
        )

        (self.line_rtk,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "rtk"],
            color="blue",
            linestyle="-",
            label="Projections",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title("Evolution of the Revenue\nTonne Kilometer (RTK) for air transport")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Revenue Tonne Kilometer [RTK]")
        self.ax.legend()
        
        self.ax.set_xlim(self.years[0], self.years[-1])

    def _update_plot_elements(self):
        self.line_rtk.set_ydata(self.df.loc[self.prospective_years, "rtk"])


class AvailableSeatKilometerPlot(SingleScenarioPlot):
    def __init__(self, process, figsize=None):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize)

    def _get_default_figsize(self):
        return (plot_3_x, plot_3_y)

    def create_plot(self):
        self.ax.plot(
            self.historic_years,
            self.df.loc[self.historic_years, "ask"],
            color="black",
            linestyle="-",
            label="History",
            linewidth=2,
        )

        (self.line_ask,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "ask"],
            color="blue",
            linestyle="-",
            label="Projections",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title("Evolution of the Available\nSeat Kilometer (ASK) for air transport")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Available Seat Kilometer [ASK]")
        self.ax.legend()
        
        self.ax.set_xlim(self.years[0], self.years[-1])

    def _update_plot_elements(self):
        self.line_ask.set_ydata(self.df.loc[self.prospective_years, "ask"])


class TotalAircraftDistancePlot(SingleScenarioPlot):
    def __init__(self, process, figsize=None):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize)

    def _get_default_figsize(self):
        return (plot_3_x, plot_3_y)

    def create_plot(self):
        self.ax.plot(
            self.historic_years,
            self.df_climate.loc[self.historic_years, "total_aircraft_distance"] / 10**9,
            color="black",
            linestyle="-",
            label="History",
            linewidth=2,
        )

        (self.line_total_aircraft_distance,) = self.ax.plot(
            self.prospective_years,
            self.df_climate.loc[self.prospective_years, "total_aircraft_distance"] / 10**9,
            color="blue",
            linestyle="-",
            label="Projections",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title("Evolution of the total distance\ntravelled by aircraft")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Total distance travelled by aircraft [in billions of km]")
        self.ax.legend()
        
        self.ax.set_xlim(self.years[0], self.years[-1])

    def _update_plot_elements(self):
        self.line_total_aircraft_distance.set_ydata(
            self.df_climate.loc[self.prospective_years, "total_aircraft_distance"] / 10**9
        )
