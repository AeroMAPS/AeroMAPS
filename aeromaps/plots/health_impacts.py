"""
Health impacts plotting module for visualizing DALYs from climate change,
surface ozone, and particulate matter contributions over time.
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.widgets import Slider
import numpy as np
import collections
from .constants import plot_1_x, plot_1_y


class HealthImpactsClimateChangePlot:
    """Plot stacked DALYs from climate change broken down by species."""

    def __init__(self, process):
        data = process.data
        self.df = data["vector_outputs"]
        self.years = data["years"]["full_years"]
        self.baseline_climate_years = [year for year in data['years']['climate_historic_years'] if year <= data['years']['historic_years'][0]]

        self.fig, self.ax = plt.subplots(figsize=(plot_1_x, plot_1_y))
        self.create_plot()

    def create_plot(self):
        """Create the stacked area plot for climate change impacts."""
        # Extract cumulative data for each species
        co2 = self.df.loc[self.years, "dalys_climate_change_co2"].values
        contrails = self.df.loc[self.years, "dalys_climate_change_contrails"].values
        nox = self.df.loc[self.years, "dalys_climate_change_nox"].values
        h2o = self.df.loc[self.years, "dalys_climate_change_h2o"].values
        soot = self.df.loc[self.years, "dalys_climate_change_soot"].values
        sulfur = self.df.loc[self.years, "dalys_climate_change_sulfur"].values

        # Handle negative values
        co2_pos = np.where(co2 > 0, co2, 0)
        co2_neg = np.where(co2 < 0, co2, 0)
        contrails_pos = np.where(contrails > 0, contrails, 0)
        contrails_neg = np.where(contrails < 0, contrails, 0)
        nox_pos = np.where(nox > 0, nox, 0)
        nox_neg = np.where(nox < 0, nox, 0)
        h2o_pos = np.where(h2o > 0, h2o, 0)
        h2o_neg = np.where(h2o < 0, h2o, 0)
        soot_pos = np.where(soot > 0, soot, 0)
        soot_neg = np.where(soot < 0, soot, 0)
        sulfur_pos = np.where(sulfur > 0, sulfur, 0)
        sulfur_neg = np.where(sulfur < 0, sulfur, 0)

        # Positive stack
        self.ax.stackplot(
            self.years,
            co2_pos,
            contrails_pos,
            nox_pos,
            h2o_pos,
            soot_pos,
            sulfur_pos,
            labels=["CO$_2$", "Contrails", "NO$_x$", "H$_2$O", "Soot", "Sulfur"],
            colors=["#adb5bd", "#e9c46a", "#e76f51", "#3f88c5", "#7b2cbf", "#a7c957"],
            alpha=0.8,
            linewidth=0.5,
        )

        # Negative stack
        self.ax.stackplot(
            self.years,
            co2_neg,
            contrails_neg,
            nox_neg,
            h2o_neg,
            soot_neg,
            sulfur_neg,
            colors=["#adb5bd", "#e9c46a", "#e76f51", "#3f88c5", "#7b2cbf", "#a7c957"],
            alpha=0.8,
            linewidth=0.5,
        )

        self.ax.grid(linestyle='--')
        self.ax.set_axisbelow(True)
        self.ax.set_title(f"Health Impacts Attributable to Aviation-Induced Climate Change\n"
                          f"(baseline climate state: "
                          f"[{self.baseline_climate_years[0]} - {self.baseline_climate_years[-1]}]"
                          f")")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Aviation-attributable DALYs per year")
        self.ax.legend()
        self.ax.set_xlim(self.years[0], self.years[-1])
        self.ax.yaxis.set_major_formatter(ticker.FuncFormatter(sci_notation))

        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        self.fig.tight_layout()

    def update(self, data):
        """Update plot with new data."""
        self.df = data["vector_outputs"]
        self.years = data["years"]["full_years"]
        self.baseline_climate_years = [year for year in data['years']['climate_historic_years'] if year <= data['years']['historic_years'][0]]

        for collection in self.ax.collections:
            collection.remove()

        self.create_plot()
        self.fig.canvas.draw()


class HealthImpactsAirQualityPlot:
    """Plot stacked DALYs from surface ozone and fine particulate matter."""

    def __init__(self, process):
        data = process.data
        self.df = data["vector_outputs"]
        self.years = data["years"]["full_years"]

        self.fig, (self.ax1, self.ax2) = plt.subplots(
            1,
            2,
            figsize=(plot_1_x, plot_1_y),
            sharey=True,
        )
        self.create_plot()

    def create_air_quality_plot(self, ax, pollutant: str):
        # Extract data for each source
        fuel = self.df.loc[self.years, f"dalys_{pollutant}"].values
        nox = self.df.loc[self.years, f"dalys_{pollutant}_nox"].values

        # Define non-NOx impacts as the difference between total and NOx-attributable impacts
        non_nox = fuel - nox

        # Handle negative values
        nox_pos = np.where(nox > 0, nox, 0)
        nox_neg = np.where(nox < 0, nox, 0)
        non_nox_pos = np.where(non_nox > 0, non_nox, 0)
        non_nox_neg = np.where(non_nox < 0, non_nox, 0)

        # Positive stack
        ax.stackplot(
            self.years,
            nox_pos,
            non_nox_pos,
            labels=["NO$_x$", "non-NO$_x$"],
            colors=["#e76f51", "#e3d5ca"],
            hatch=["", "//"],
            alpha=0.8,
            linewidth=0.5,
        )

        # Negative stack
        ax.stackplot(
            self.years,
            nox_neg,
            non_nox_neg,
            colors=["#e76f51", "#e3d5ca"],
            hatch=["", "//"],
            alpha=0.8,
            linewidth=0.5,
        )

        ax.grid(linestyle='--')
        ax.set_axisbelow(True)
        ax.set_xlabel("Year")
        ax.legend()
        ax.set_xlim(self.years[0], self.years[-1])
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(sci_notation))

    def create_plot(self):
        """Create the stacked area plots for surface ozone and particulate matter impacts."""
        self.create_air_quality_plot(self.ax1, "surface_ozone")
        self.ax1.set_title("Health Impacts - Surface O$_3$")
        self.ax1.set_ylabel("Aviation-attributable DALYs per year")

        self.create_air_quality_plot(self.ax2, "particulate_matter")
        self.ax2.set_title("Health Impacts - PM$_{2.5}$")
        self.ax2.yaxis.tick_right()
        self.ax2.tick_params(axis="y", which="both", labelright=True)
        # self.ax2.yaxis.set_label_position("right")

        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        self.fig.tight_layout()

    def update(self, data):
        """Update plot with new data."""
        self.df = data["vector_outputs"]
        self.years = data["years"]["full_years"]

        for collection in self.ax1.collections:
            collection.remove()
        for collection in self.ax2.collections:
            collection.remove()

        self.create_plot()
        self.fig.canvas.draw()


class HealthImpactsTotalPlot:
    """Interactive plot showing time evolution of annual health impacts (climate change, surface ozone,
    and fine particulate matter), and the detailed breakdown by species (e.g., contrails, NOx, CO2...)
    for the year selected by the user.
    """

    def __init__(self, process):
        # Data
        data = process.data
        self.df = data["vector_outputs"]
        self.years = data["years"]["full_years"]

        # Create figure with two subplots
        self.fig, (self.ax1, self.ax2) = plt.subplots(
            1, 2, figsize=(plot_1_x * 1.3, plot_1_y), sharey=False
        )

        # Define color and hatch patterns
        self.palette_dict = {
            "CO2": ("#adb5bd", ""),
            "Contrails": ("#e9c46a", ""),
            "NOx": ("#e76f51", ""),
            "H2O": ("#3f88c5", ""),
            "Soot": ("#7b2cbf", ""),
            "Sulfur": ("#a7c957", ""),
            "non-NOx": ("#e3d5ca", "//"),
        }

        # Create year selector widget
        ax_year = plt.axes([0.35, 0.0, 0.3, 0.03])
        self.year_slider = Slider(ax_year, 'Year', self.years[0], self.years[-1],
                                  valinit=data["years"]["prospective_years"][0], valstep=1)
        self.year_slider.on_changed(self.update_plot)

        self.create_plot()

    def create_plot(self):
        """Create both subplots for the selected year."""
        selected_year = int(self.year_slider.val)

        # Left subplot: Total health impacts over time
        self.create_total_plot()

        # Right subplot: Cascade plot for selected year
        self.create_cascade_plot(selected_year)

        #self.fig.suptitle(f"Aviation-Attributable Health Impacts", fontsize=14)

        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        self.fig.subplots_adjust(bottom=0.15)

    def create_total_plot(self):
        """Create the total health impacts time series plot."""
        # Extract data for each pathway
        climate = self.df.loc[self.years, "dalys_climate_change"].values
        ozone = self.df.loc[self.years, "dalys_surface_ozone"].values
        pm = self.df.loc[self.years, "dalys_particulate_matter"].values

        # Handle negative values
        climate_pos = np.where(climate > 0, climate, 0)
        climate_neg = np.where(climate < 0, climate, 0)
        ozone_pos = np.where(ozone > 0, ozone, 0)
        ozone_neg = np.where(ozone < 0, ozone, 0)
        pm_pos = np.where(pm > 0, pm, 0)
        pm_neg = np.where(pm < 0, pm, 0)

        # Positive stack
        self.ax1.stackplot(
            self.years,
            climate_pos,
            ozone_pos,
            pm_pos,
            labels=["Climate Change", "Surface O$_3$", "PM$_{2.5}$"],
            colors=["#1f77b4", "#ff7f0e", "#2ca02c"],
            alpha=0.8,
            linewidth=0.5,
            edgecolor="0.2"
        )

        # Negative stack
        self.ax1.stackplot(
            self.years,
            climate_neg,
            ozone_neg,
            pm_neg,
            colors=["#1f77b4", "#ff7f0e", "#2ca02c"],
            alpha=0.8,
            linewidth=0.5,
            edgecolor="0.2"
        )

        # Add vertical line for selected year
        selected_year = int(self.year_slider.val)
        self.vline = self.ax1.axvline(x=selected_year, linestyle='--', color='k', linewidth=1.5, alpha=0.8)

        self.ax1.grid(linestyle='--')
        self.ax1.set_axisbelow(True)
        self.ax1.set_title("Annual Health Impacts")
        #self.ax1.set_xlabel("Year")
        self.ax1.set_ylabel("DALYs per year")
        self.ax1.legend(loc='upper left')
        self.ax1.set_xlim(self.years[0], self.years[-1])
        self.ax1.yaxis.set_major_formatter(ticker.FuncFormatter(sci_notation))

    def create_cascade_plot(self, selected_year):
        """Create the cascade plot for the selected year."""
        # Extract data for the selected year
        climate_co2 = self.df.loc[selected_year, "dalys_climate_change_co2"]
        climate_contrails = self.df.loc[selected_year, "dalys_climate_change_contrails"]
        climate_nox = self.df.loc[selected_year, "dalys_climate_change_nox"]
        climate_h2o = self.df.loc[selected_year, "dalys_climate_change_h2o"]
        climate_soot = self.df.loc[selected_year, "dalys_climate_change_soot"]
        climate_sulfur = self.df.loc[selected_year, "dalys_climate_change_sulfur"]

        ozone_fuel = self.df.loc[selected_year, "dalys_surface_ozone"]
        ozone_nox = self.df.loc[selected_year, "dalys_surface_ozone_nox"]
        ozone_non_nox = ozone_fuel - ozone_nox

        pm_fuel = self.df.loc[selected_year, "dalys_particulate_matter"]
        pm_nox = self.df.loc[selected_year, "dalys_particulate_matter_nox"]
        pm_non_nox = pm_fuel - pm_nox

        # Create data structure
        impacts_data = {
            "Climate Change": {
                "CO2": climate_co2,
                "Contrails": climate_contrails,
                "NOx": climate_nox,
                "H2O": climate_h2o,
                "Soot": climate_soot,
                "Sulfur": climate_sulfur,
            },
            "Surface O$_3$": {
                "NOx": ozone_nox,
                "non-NOx": ozone_non_nox,
            },
            "PM$_{2.5}$": {
                "NOx": pm_nox,
                "non-NOx": pm_non_nox,
            }
        }

        impacts = list(impacts_data.keys())
        order = ["CO2", "Contrails", "NOx", "H2O", "Soot", "Sulfur", "non-NOx"]

        cumulative = 0
        bar_width = 0.65

        for i, impact in enumerate(impacts):
            contributor = impacts_data[impact]
            values = [contributor.get(p, 0) for p in order if p in contributor]
            names = [n for n in order if n in contributor]

            impact_total = sum(values)

            pos_bottom = cumulative
            neg_bottom = cumulative

            for name, value in zip(names, values):
                color, hatch = self.palette_dict.get(name, ("gray", ""))

                if value >= 0:
                    bar = self.ax2.bar(i, value, bottom=pos_bottom,
                                     width=bar_width, color=color, linewidth=0.5, edgecolor="0.2")
                    pos_bottom += value
                else:
                    bar = self.ax2.bar(i, value, bottom=neg_bottom,
                                     width=bar_width, color=color, linewidth=0.5, edgecolor="0.2")
                    neg_bottom += value

                if hatch:
                    bar[0].set_hatch(hatch)

            # true visible bar limits
            top = max(pos_bottom, neg_bottom)
            bottom = min(pos_bottom, neg_bottom)

            # connector at top of bar
            if i < len(impacts) - 1:
                self.ax2.plot(
                    [i + bar_width/2, i + 1 - bar_width/2],
                    [top, top],
                    color="black",
                    linewidth=1
                )

            # place label at bar extremity
            label_y = top + abs(top) * 0.05 if impact_total >= 0 else bottom - abs(bottom) * 0.05

            if abs(impact_total) > 0:
                exponent = int(np.floor(np.log10(abs(impact_total))))
                coeff = impact_total / 10**exponent
                self.ax2.text(
                    i,
                    label_y,
                    r"${:.1f}\times10^{{{}}}$".format(coeff, exponent),
                    ha="center",
                    va="bottom" if impact_total >= 0 else "top",
                    fontsize=10.5
                )

            cumulative = max(pos_bottom, neg_bottom)

        # Y-axis
        ymin, ymax = self.ax2.get_ylim()
        self.ax2.set_ylim(ymin, ymax * 1.1)
        self.ax2.yaxis.tick_right()
        self.ax2.tick_params(axis="y", which="both", labelright=True)
        self.ax2.yaxis.set_label_position("right")
        self.ax2.set_ylabel("DALYs per year")
        self.ax2.yaxis.set_major_formatter(ticker.FuncFormatter(sci_notation))

        # X-axis and grid
        self.ax2.set_xticks(range(len(impacts)))
        self.ax2.set_xticklabels(impacts)
        self.ax2.axhline(0, color="black", linewidth=0.8)
        self.ax2.grid(axis="y", alpha=0.3)
        self.ax2.set_axisbelow(True)
        self.ax2.set_facecolor("white")

        # Title
        self.ax2.set_title(f"Impacts Breakdown for Year {selected_year}")

        # Legend
        entries = collections.OrderedDict()
        for key, (color, hatch) in self.palette_dict.items():
            patch = plt.Rectangle(
                (0, 0), 1, 1,
                facecolor=color,
                edgecolor="0.2",
                linewidth=0.5,
                hatch=hatch
            )
            label = (key.replace("CO2","CO$_2$")
                     .replace("NOx","NO$_x$")
                     .replace("H2O","H$_2$O")
                     .replace("non-NOx","non-NO$_x$"))
            entries[label] = patch
        self.ax2.legend(
            entries.values(),
            entries.keys(),
            loc="lower center",
            bbox_to_anchor=(0.82, 0.03),
            ncol=1,
            fontsize=10,
        )

    def update_plot(self, val):
        """Update plot when year slider changes."""
        selected_year = int(val)

        # Update vertical line position
        self.vline.set_xdata([selected_year, selected_year])

        # Clear and recreate cascade plot
        self.ax2.clear()
        self.create_cascade_plot(selected_year)

        self.fig.canvas.draw()


def sci_notation(x, pos):
    if x == 0:
        return "0"
    exponent = int(np.floor(np.log10(abs(x))))
    coeff = x / 10 ** exponent
    return r"${:.1f}\times10^{{{}}}$".format(coeff, exponent)
