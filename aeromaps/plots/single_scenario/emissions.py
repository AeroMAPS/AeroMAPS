import matplotlib.pyplot as plt
import numpy as np
from aeromaps.plots.single_scenario_plot import SingleScenarioPlot, plot_3_x, plot_3_y


class CumulativeCO2EmissionsPlot(SingleScenarioPlot):
    def __init__(self, process, figsize=None):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize)

    def _get_default_figsize(self):
        return (plot_3_x, plot_3_y)

    def create_plot(self):
        (self.line_cumulative_co2_emissions,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "cumulative_co2_emissions"],
            color="blue",
            linestyle="-",
            label="Cumulative CO₂ emissions",
            linewidth=2,
        )

        (self.line_aviation_carbon_budget,) = self.ax.plot(
            self.prospective_years,
            np.ones(len(self.prospective_years)) * self.float_outputs["aviation_carbon_budget"],
            color="black",
            linestyle="--",
            label="Aviation carbon budget",
            linewidth=1,
        )

        self.ax.grid()
        self.ax.set_title(
            "Comparison of cumulative CO₂ emissions from air transport\nwith allocated carbon budget (from 2019)"
        )
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Cumulative CO₂ emissions [GtCO₂]")
        self.ax.legend()
        self.ax.set_xlim(2019, self.years[-1])

    def _update_plot_elements(self):
        self.line_cumulative_co2_emissions.set_ydata(
            self.df.loc[self.prospective_years, "cumulative_co2_emissions"]
        )

        self.line_aviation_carbon_budget.set_ydata(
            np.ones(len(self.prospective_years)) * self.float_outputs["aviation_carbon_budget"]
        )

        for collection in self.ax.collections:
            collection.remove()


class DirectH2OEmissionsPlot(SingleScenarioPlot):
    def __init__(self, process, figsize=None):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize)

    def _get_default_figsize(self):
        return (plot_3_x, plot_3_y)

    def create_plot(self):
        self.ax.plot(
            self.historic_years,
            self.df_climate.loc[self.historic_years, "h2o_emissions"],
            color="black",
            linestyle="-",
            label="History",
            linewidth=2,
        )

        (self.line_h2o_emissions,) = self.ax.plot(
            self.prospective_years,
            self.df_climate.loc[self.prospective_years, "h2o_emissions"],
            color="blue",
            linestyle="-",
            label="Projections",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title("Evolution of direct H₂O emissions\nfrom air transport")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Direct H₂O emissions [MtH₂O]")
        self.ax.legend()
        self.ax.set_xlim(self.years[0], self.years[-1])

    def _update_plot_elements(self):
        self.line_h2o_emissions.set_ydata(
            self.df_climate.loc[self.prospective_years, "h2o_emissions"]
        )

        for collection in self.ax.collections:
            collection.remove()


class DirectNOxEmissionsPlot(SingleScenarioPlot):
    def __init__(self, process, figsize=None):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize)

    def _get_default_figsize(self):
        return (plot_3_x, plot_3_y)

    def create_plot(self):
        self.ax.plot(
            self.historic_years,
            self.df_climate.loc[self.historic_years, "nox_emissions"],
            color="black",
            linestyle="-",
            label="History",
            linewidth=2,
        )

        (self.line_nox_emissions,) = self.ax.plot(
            self.prospective_years,
            self.df_climate.loc[self.prospective_years, "nox_emissions"],
            color="blue",
            linestyle="-",
            label="Projections",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title("Evolution of direct NOx emissions\nfrom air transport")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Direct NOx emissions [MtNOx]")
        self.ax.legend()
        self.ax.set_xlim(self.years[0], self.years[-1])

    def _update_plot_elements(self):
        self.line_nox_emissions.set_ydata(
            self.df_climate.loc[self.prospective_years, "nox_emissions"]
        )

        for collection in self.ax.collections:
            collection.remove()


class DirectSulfurEmissionsPlot(SingleScenarioPlot):
    def __init__(self, process, figsize=None):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize)

    def _get_default_figsize(self):
        return (plot_3_x, plot_3_y)

    def create_plot(self):
        self.ax.plot(
            self.historic_years,
            self.df_climate.loc[self.historic_years, "sulfur_emissions"],
            color="black",
            linestyle="-",
            label="History",
            linewidth=2,
        )

        (self.line_sulfur_emissions,) = self.ax.plot(
            self.prospective_years,
            self.df_climate.loc[self.prospective_years, "sulfur_emissions"],
            color="blue",
            linestyle="-",
            label="Projections",
            linewidth=2,
        )

        self.ax.grid()
        self.ax.set_title("Evolution of direct sulfur emissions\nfrom air transport")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Direct sulfur emissions [MtSO2]")
        self.ax.set_xlim(self.years[0], self.years[-1])

    def _update_plot_elements(self):
        self.line_sulfur_emissions.set_ydata(
            self.df_climate.loc[self.prospective_years, "sulfur_emissions"]
        )

        for collection in self.ax.collections:
            collection.remove()


class DirectSootEmissionsPlot(SingleScenarioPlot):
    def __init__(self, process, figsize=None):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize)

    def _get_default_figsize(self):
        return (plot_3_x, plot_3_y)

    def create_plot(self):
        self.ax.plot(
            self.historic_years,
            self.df_climate.loc[self.historic_years, "soot_emissions"],
            color="black",
            linestyle="-",
            label="History",
            linewidth=2,
        )

        (self.line_soot_emissions,) = self.ax.plot(
            self.prospective_years,
            self.df_climate.loc[self.prospective_years, "soot_emissions"],
            color="blue",
            linestyle="-",
            label="Projections",
            linewidth=2,
        )

        self._setup_grid_and_labels(
            "Evolution of direct soot emissions\nfrom air transport",
            "Year",
            "Direct soot emissions [MtBC]"
        )
        self._set_x_limits()

    def _update_plot_elements(self):
        self.line_soot_emissions.set_ydata(
            self.df_climate.loc[self.prospective_years, "soot_emissions"]
        )


class CarbonOffsetPlot(SingleScenarioPlot):
    def __init__(self, process, figsize=None):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize)

    def _get_default_figsize(self):
        return (plot_3_x, plot_3_y)

    def create_plot(self):
        self.ax.plot(
            self.historic_years,
            self.df.loc[self.historic_years, "carbon_offset"],
            color="black",
            linestyle="-",
            label="History",
            linewidth=2,
        )

        (self.line_carbon_offset,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "carbon_offset"],
            color="blue",
            linestyle="-",
            label="Projections",
            linewidth=2,
        )

        self._setup_grid_and_labels(
            "Evolution of carbon offset\nfrom air transport",
            "Year",
            "Carbon offset [MtCO₂]"
        )
        self._set_x_limits()

    def _update_plot_elements(self):
        self.line_carbon_offset.set_ydata(self.df.loc[self.prospective_years, "carbon_offset"])


class CumulativeCarbonOffsetPlot(SingleScenarioPlot):
    def __init__(self, process, figsize=None):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize)

    def _get_default_figsize(self):
        return (plot_3_x, plot_3_y)

    def create_plot(self):
        (self.line_cumulative_carbon_offset,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "cumulative_carbon_offset"],
            color="blue",
            linestyle="-",
            label="Cumulative carbon offset",
            linewidth=2,
        )

        self._setup_grid_and_labels(
            "Cumulative carbon offset from air transport",
            "Year",
            "Cumulative carbon offset [GtCO₂]"
        )
        self.ax.legend()

    def _update_plot_elements(self):
        self.line_cumulative_carbon_offset.set_ydata(
            self.df.loc[self.prospective_years, "cumulative_carbon_offset"]
        )
