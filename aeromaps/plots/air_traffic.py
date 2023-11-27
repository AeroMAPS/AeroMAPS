import matplotlib.pyplot as plt
from .constants import plot_3_x, plot_3_y


class RevenuePassengerKilometerPlot:
    def __init__(self, data):
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
        self.ax = plt.gca()
        self.ax.set_xlim(2000, 2050)

        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        # self.fig.canvas.layout.width = "auto"
        # self.fig.canvas.layout.height = "auto"
        self.fig.tight_layout()

    def update(self, data):
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.line_rpk.set_ydata(self.df.loc[self.prospective_years, "rpk"])

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class RevenueTonneKilometerPlot:
    def __init__(self, data):
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
        self.ax = plt.gca()
        self.ax.set_xlim(2000, 2050)

        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        # self.fig.canvas.layout.width = "auto"
        # self.fig.canvas.layout.height = "auto"
        self.fig.tight_layout()

    def update(self, data):
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.line_rtk.set_ydata(self.df.loc[self.prospective_years, "rtk"])

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class AvailableSeatKilometerPlot:
    def __init__(self, data):
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
        self.ax = plt.gca()
        self.ax.set_xlim(2000, 2050)

        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        # self.fig.canvas.layout.width = "auto"
        # self.fig.canvas.layout.height = "auto"
        self.fig.tight_layout()

    def update(self, data):
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.line_ask.set_ydata(self.df.loc[self.prospective_years, "ask"])

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class TotalAircraftDistancePlot:
    def __init__(self, data):
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
            self.df.loc[self.historic_years, "total_aircraft_distance"] / 10**9,
            color="black",
            linestyle="-",
            label="History",
            linewidth=2,
        )

        (self.line_total_aircraft_distance,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "total_aircraft_distance"] / 10**9,
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
        self.ax = plt.gca()
        self.ax.set_xlim(2000, 2050)

        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        # self.fig.canvas.layout.width = "auto"
        # self.fig.canvas.layout.height = "auto"
        self.fig.tight_layout()

    def update(self, data):
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.line_total_aircraft_distance.set_ydata(
            self.df.loc[self.prospective_years, "total_aircraft_distance"] / 10**9
        )

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()
