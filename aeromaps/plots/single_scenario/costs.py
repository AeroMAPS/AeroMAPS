# @Time : 15/06/2023 09:06
# @Author : a.salgas
# @File : costs.py
# @Software: PyCharm
import numpy as np
from matplotlib.patches import Patch

from aeromaps.plots.single_scenario_plot import SingleScenarioPlot
from aeromaps.plots.single_scenario_plot import plot_2_x
from aeromaps.plots.single_scenario_plot import plot_2_y
from aeromaps.plots.single_scenario_plot import plot_3_x
from aeromaps.plots.single_scenario_plot import plot_3_y


class ScenarioEnergyExpensesComparison(SingleScenarioPlot):
    required_outputs = [
        "non_discounted_energy_expenses",
        "non_discounted_net_energy_expenses",
        "non_discounted_bau_energy_expenses",
        "carbon_tax_bau",
        "non_discounted_full_kero_energy_expenses",
        "carbon_tax_full_kero",
    ]

    def __init__(self, process, figsize=None, **kwargs):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize, **kwargs)

    def _get_default_figsize(self):
        return (plot_2_x, plot_2_y)

    def create_plot(self):
        (self.line_energy_expenses,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "non_discounted_energy_expenses"],
            label="Scenario energy expenses",
            linestyle="-",
            color="#0c9e30",
        )

        (self.line_energy_expenses_carb_tax,) = self.ax.plot(
            self.prospective_years,
            (self.df.loc[self.prospective_years, "non_discounted_net_energy_expenses"]),
            label="Scenario net energy expenses",
            linestyle="--",
            color="#0c9e30",
        )
        (self.line_bau_energy_expenses,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "non_discounted_bau_energy_expenses"],
            label="Business as usual energy expenses",
            linestyle="-",
            color="#2A3438",
        )
        (self.line_bau_energy_expenses_carbon_tax,) = self.ax.plot(
            self.prospective_years,
            (
                self.df.loc[self.prospective_years, "non_discounted_bau_energy_expenses"]
                + self.df.loc[self.prospective_years, "carbon_tax_bau"]
            ),
            label="Business as usual energy expenses incl. carbon tax",
            linestyle="--",
            color="#2A3438",
        )

        (self.line_full_kero_energy_expenses,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "non_discounted_full_kero_energy_expenses"],
            label="Efficiency only energy expenses",
            linestyle="-",
            color="#A64253",
        )
        (self.line_full_kero_energy_expenses_carbon_tax,) = self.ax.plot(
            self.prospective_years,
            (
                self.df.loc[self.prospective_years, "non_discounted_full_kero_energy_expenses"]
                + self.df.loc[self.prospective_years, "carbon_tax_full_kero"]
            ),
            label="Efficiency only energy expenses incl. carbon tax",
            linestyle="--",
            color="#A64253",
        )

        self.ax.grid(axis="y")
        self.ax.legend(loc="upper left")
        self.ax.set_title("Annual energy expenses per pathway")
        self.ax.set_ylabel("Energy expenses [M€]")


        self.ax.set_xlim(2020, self.years[-1])
        # #

    def _update_plot_elements(self):
        self.line_energy_expenses.set_ydata(
            self.df.loc[self.prospective_years, "non_discounted_energy_expenses"]
        )

        self.line_energy_expenses_carb_tax.set_ydata(
            (self.df.loc[self.prospective_years, "non_discounted_net_energy_expenses"])
        )

        self.line_bau_energy_expenses.set_ydata(
            self.df.loc[self.prospective_years, "non_discounted_bau_energy_expenses"]
        )

        self.line_bau_energy_expenses_carbon_tax.set_ydata(
            (
                self.df.loc[self.prospective_years, "non_discounted_bau_energy_expenses"]
                + self.df.loc[self.prospective_years, "carbon_tax_bau"]
            )
        )

        self.line_full_kero_energy_expenses.set_ydata(
            self.df.loc[self.prospective_years, "non_discounted_full_kero_energy_expenses"]
        )

        self.line_full_kero_energy_expenses_carbon_tax.set_ydata(
            (
                self.df.loc[self.prospective_years, "non_discounted_full_kero_energy_expenses"]
                + self.df.loc[self.prospective_years, "carbon_tax_full_kero"]
            )
        )

    def update(self, df_data):
        self.df = df_data["vector_outputs"]

        self.line_energy_expenses.set_ydata(
            self.df.loc[self.prospective_years, "non_discounted_energy_expenses"]
        )

        self.line_energy_expenses_carb_tax.set_ydata(
            (
                self.df.loc[self.prospective_years, "non_discounted_energy_expenses"]
                + self.df.loc[self.prospective_years, "kerosene_carbon_tax_cost"]
                + self.df.loc[self.prospective_years, "biofuel_carbon_tax_hefa_fog"]
                + self.df.loc[self.prospective_years, "biofuel_carbon_tax_hefa_others"]
                + self.df.loc[self.prospective_years, "biofuel_carbon_tax_atj"]
                + self.df.loc[self.prospective_years, "biofuel_carbon_tax_ft_others"]
                + self.df.loc[self.prospective_years, "biofuel_carbon_tax_ft_msw"]
                + self.df.loc[self.prospective_years, "electrolysis_h2_carbon_tax"]
                + self.df.loc[self.prospective_years, "gas_ccs_h2_carbon_tax"]
                + self.df.loc[self.prospective_years, "gas_h2_carbon_tax"]
                + self.df.loc[self.prospective_years, "coal_ccs_h2_carbon_tax"]
                + self.df.loc[self.prospective_years, "coal_h2_carbon_tax"]
                + self.df.loc[self.prospective_years, "electrofuel_carbon_tax"]
                + self.df.loc[self.prospective_years, "electricity_direct_use_carbon_tax"]
            )
        )

        self.line_bau_energy_expenses.set_ydata(
            self.df.loc[self.prospective_years, "non_discounted_bau_energy_expenses"]
        )

        self.line_bau_energy_expenses_carbon_tax.set_ydata(
            (
                self.df.loc[self.prospective_years, "non_discounted_bau_energy_expenses"]
                + self.df.loc[self.prospective_years, "carbon_tax_bau"]
            )
        )

        for collection in self.ax.collections:
            collection.remove()
        self.fig.canvas.draw()


class DiscountEffect(SingleScenarioPlot):
    required_outputs = [
        "non_discounted_energy_expenses",
        "discounted_energy_expenses",
    ]

    def __init__(self, process, figsize=None, **kwargs):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize, **kwargs)

    def _get_default_figsize(self):
        return (plot_3_x, plot_3_y)

    def create_plot(self):
        (self.line_non_discounted,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "non_discounted_energy_expenses"],
            color="#2A3438",
            linestyle="-",
            label="Non-discounted expenses",
            linewidth=2,
        )

        (self.line_discounted,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "discounted_energy_expenses"],
            color="red",
            linestyle="-",
            label="Discounted expenses at r={}%".format(self.parameters["social_discount_rate"]),
            linewidth=2,
        )

        self.ax.grid(axis="y")
        self.ax.set_title("Total (energy) expenses (M€)")
        self.ax.set_ylabel("M€ / year")

        self.ax.legend()
        self.ax.set_xlim(2020, self.years[-1])

    def _update_plot_elements(self):
        self.line_non_discounted.set_ydata(
            self.df.loc[self.prospective_years, "non_discounted_energy_expenses"]
        )

        self.line_discounted.set_ydata(
            self.df.loc[self.prospective_years, "discounted_energy_expenses"]
        )


class DOCEvolutionBreakdown(SingleScenarioPlot):
    required_outputs = [
        "doc_total_per_ask_mean",
        "doc_non_energy_per_ask_mean",
        "doc_energy_per_ask_mean",
        "doc_energy_tax_per_ask_mean",
        "doc_energy_carbon_tax_per_ask_mean",
        "doc_energy_subsidy_per_ask_mean",
        "doc_carbon_tax_lowering_offset_per_ask_mean",
    ]

    def __init__(self, process, figsize=None, **kwargs):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize, **kwargs)

    def _get_default_figsize(self):
        return (plot_3_x, plot_3_y)

    def create_plot(self):
        (self.line_total,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_total_per_ask_mean"],
            color="blue",
            linestyle="-",
            label="Total DOC (Net)",
            linewidth=2,
            zorder=3,
        )

        (self.line_total_gross,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_total_per_ask_mean"]
            - self.df.loc[self.prospective_years, "doc_energy_carbon_tax_per_ask_mean"]
            - self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_subsidy_per_ask_mean"],
            color="blue",
            linestyle=":",
            label="Total DOC (Gross)",
            linewidth=2,
            zorder=3,
        )

        (self.line_total_adjusted,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            - self.df.loc[self.prospective_years, "doc_energy_subsidy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"],
            color="blue",
            linestyle="--",
            label="Total DOC (Net, with offset)",
            linewidth=2,
            zorder=3,
        )

        # start with energy subsidies
        self.ax.fill_between(
            self.prospective_years,
            -self.df.loc[self.prospective_years, "doc_energy_subsidy_per_ask_mean"],
            np.zeros(len(self.prospective_years)),
            color="cornflowerblue",
            hatch="xx",
            label="Energy subsidy",
            edgecolor="dimgray",
            linewidth=0.5,
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"],
            np.zeros(len(self.prospective_years)),
            color="royalblue",
            label="Non-energy",
            edgecolor="dimgray",
            linewidth=0.5,
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"],
            color="cornflowerblue",
            label="Energy",
            edgecolor="dimgray",
            linewidth=0.5,
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"],
            color="cornflowerblue",
            hatch="//",
            linewidth=0.5,
            edgecolor="dimgray",
            label="Energy taxes (non-carbon)",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_carbon_tax_per_ask_mean"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"],
            color="cornflowerblue",
            hatch="..",
            linewidth=0.5,
            edgecolor="dimgray",
            label="Carbon tax",
        )

        self.ax.grid()
        self.ax.set_title("Direct Operating Costs breakdown")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Direct Operating Costs [€/ASK]")


        components_handles = [
            Patch(facecolor="cornflowerblue", edgecolor="black", label="Energy"),
            Patch(facecolor="royalblue", edgecolor="black", label="Non-energy"),
        ]

        self.ax.add_artist(
            self.ax.legend(
                handles=components_handles,
                loc="upper left",
                prop={"size": 8},
            )
        )

        tax_handles = [
            Patch(facecolor="none", edgecolor="black", hatch="//", label="Tax"),
            Patch(
                facecolor="none",
                edgecolor="black",
                hatch="xx",
                label="Subsidy",
            ),
            Patch(
                facecolor="none",
                edgecolor="black",
                hatch="..",
                label="Carbon tax",
            ),
        ]

        self.ax.add_artist(
            self.ax.legend(
                handles=tax_handles,
                loc="upper right",
                prop={"size": 8},
            )
        )

        self.ax.set_xlim(self.prospective_years[0], self.prospective_years[-1])
        # self.ax.set_ylim(0,)


class DOCEvolutionCategory(SingleScenarioPlot):
    required_outputs = [
        "doc_total_per_ask_short_range_dropin_fuel",
        "doc_total_per_ask_medium_range_dropin_fuel",
        "doc_total_per_ask_long_range_dropin_fuel",
        "doc_total_per_ask_short_range_hydrogen",
        "doc_total_per_ask_medium_range_hydrogen",
        "doc_total_per_ask_long_range_hydrogen",
        "doc_total_per_ask_short_range_electric",
        "doc_total_per_ask_medium_range_electric",
        "doc_total_per_ask_long_range_electric",
        "doc_total_per_ask_mean",
    ]

    def __init__(self, process, figsize=None, **kwargs):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize, **kwargs)

    def _get_default_figsize(self):
        return (plot_2_x, plot_2_y)

    def create_plot(self):
        (self.line_srdi,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_total_per_ask_short_range_dropin_fuel"],
            linestyle="-",
            label="Short range-D.in",
            linewidth=2,
        )

        (self.line_mrdi,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_total_per_ask_medium_range_dropin_fuel"],
            linestyle="-",
            label="Medium range-D.in",
            linewidth=2,
        )

        (self.line_lrdi,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_total_per_ask_long_range_dropin_fuel"],
            linestyle="-",
            label="Long range-D.in",
            linewidth=2,
        )

        (self.line_srh,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_total_per_ask_short_range_hydrogen"],
            linestyle="-",
            label="Short range-H2",
            linewidth=2,
        )

        (self.line_mrh,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_total_per_ask_medium_range_hydrogen"],
            linestyle="-",
            label="Medium range-H2",
            linewidth=2,
        )

        (self.line_lrh,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_total_per_ask_long_range_hydrogen"],
            linestyle="-",
            label="Long range-H2",
            linewidth=2,
        )

        (self.line_sre,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_total_per_ask_short_range_electric"],
            linestyle="-",
            label="Short range-battery electric",
            linewidth=2,
        )

        (self.line_mre,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_total_per_ask_medium_range_electric"],
            linestyle="-",
            label="Medium range-battery electric",
            linewidth=2,
        )

        (self.line_lre,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_total_per_ask_long_range_electric"],
            linestyle="-",
            label="Long range-battery electric",
            linewidth=2,
        )

        (self.line_tot,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_total_per_ask_mean"],
            color="red",
            linestyle="-",
            label="Fleet average",
            linewidth=2,
        )

        self.ax.grid(axis="y")
        self.ax.set_title("Average direct operating cost by aircraft category")
        self.ax.set_ylabel("€ / ASK")

        self.ax.legend(title="Direct Operating Cost")
        self.ax.set_xlim(2020, self.years[-1])

    def _update_plot_elements(self):
        self.line_lrh.set_ydata(
            self.df.loc[self.prospective_years, "doc_total_per_ask_long_range_hydrogen"]
        )

        self.line_lrdi.set_ydata(
            self.df.loc[self.prospective_years, "doc_total_per_ask_long_range_dropin_fuel"]
        )

        self.line_lre.set_ydata(
            self.df.loc[self.prospective_years, "doc_total_per_ask_long_range_electric"]
        )

        self.line_mrh.set_ydata(
            self.df.loc[self.prospective_years, "doc_total_per_ask_medium_range_hydrogen"]
        )

        self.line_mrdi.set_ydata(
            self.df.loc[self.prospective_years, "doc_total_per_ask_medium_range_dropin_fuel"]
        )

        self.line_mre.set_ydata(
            self.df.loc[self.prospective_years, "doc_total_per_ask_medium_range_electric"]
        )

        self.line_srh.set_ydata(
            self.df.loc[self.prospective_years, "doc_total_per_ask_short_range_hydrogen"]
        )

        self.line_srdi.set_ydata(
            self.df.loc[self.prospective_years, "doc_total_per_ask_short_range_dropin_fuel"]
        )

        self.line_sre.set_ydata(
            self.df.loc[self.prospective_years, "doc_total_per_ask_short_range_electric"]
        )

        self.line_tot.set_ydata(self.df.loc[self.prospective_years, "doc_total_per_ask_mean"])


class AirfareEvolutionBreakdown(SingleScenarioPlot):
    required_outputs = [
        "doc_total_per_ask_mean",
        "doc_non_energy_per_ask_mean",
        "doc_energy_per_ask_mean",
        "doc_energy_tax_per_ask_mean",
        "doc_energy_carbon_tax_per_ask_mean",
        "doc_energy_subsidy_per_ask_mean",
        "doc_carbon_tax_lowering_offset_per_ask_mean",
        "noc_carbon_offset_per_ask",
        "non_operating_cost_per_ask",
        "passenger_tax_per_ask",
        "indirect_operating_cost_per_ask",
        "operational_profit_per_ask",
    ]

    def __init__(self, process, figsize=None, **kwargs):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize, **kwargs)

    def _get_default_figsize(self):
        return (plot_2_x, plot_2_y)

    def create_plot(self):
        (self.line_total_airfare,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            - self.df.loc[self.prospective_years, "doc_energy_subsidy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "non_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "passenger_tax_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "operational_profit_per_ask"],
            color="grey",
            linestyle="-",
            label="Airfare",
            linewidth=2,
        )

        (self.line_total_gross,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_total_per_ask_mean"]
            - self.df.loc[self.prospective_years, "doc_energy_carbon_tax_per_ask_mean"]
            - self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_subsidy_per_ask_mean"],
            color="blue",
            linestyle=":",
            label="Total DOC (Gross)",
            linewidth=2,
            zorder=3,
        )

        (self.line_total_adjusted,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            - self.df.loc[self.prospective_years, "doc_energy_subsidy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"],
            color="blue",
            linestyle="--",
            label="Total DOC (Net, with offset)",
            linewidth=2,
            zorder=3,
        )

        # start with energy subsidies
        self.ax.fill_between(
            self.prospective_years,
            -self.df.loc[self.prospective_years, "doc_energy_subsidy_per_ask_mean"],
            np.zeros(len(self.prospective_years)),
            color="cornflowerblue",
            hatch="xx",
            label="Energy subsidy",
            edgecolor="dimgray",
            linewidth=0.5,
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"],
            np.zeros(len(self.prospective_years)),
            color="royalblue",
            label="Non-energy",
            edgecolor="dimgray",
            linewidth=0.5,
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"],
            color="cornflowerblue",
            label="Energy",
            edgecolor="dimgray",
            linewidth=0.5,
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"],
            color="cornflowerblue",
            hatch="//",
            linewidth=0.5,
            edgecolor="dimgray",
            label="Energy taxes (non-carbon)",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"],
            color="cornflowerblue",
            hatch="..",
            linewidth=0.5,
            edgecolor="dimgray",
            label="Carbon tax (adjusted for offsets)",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"],
            color="#848482",
            alpha=0.8,
            label="Carbon offset",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"],
            color="#FF8800",
            alpha=0.8,
            label="Indirect-Operating Costs",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "non_operating_cost_per_ask"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"],
            color="#FFAA00",
            alpha=0.8,
            label="Non-Operating Costs",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "non_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "passenger_tax_per_ask"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "non_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"],
            color="#FFD000",
            alpha=0.8,
            label="Passenger Tax",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "non_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "passenger_tax_per_ask"]
            + self.df.loc[self.prospective_years, "operational_profit_per_ask"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "non_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "passenger_tax_per_ask"],
            color="#FFEA00",
            alpha=0.8,
            label="Operating Profit",
        )

        self.ax.grid()
        self.ax.set_title("Airfare breakdown")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Airfare [€/ASK]")

        self.ax.legend(fontsize="8", loc="upper left")
        self.ax.set_xlim(self.prospective_years[0], self.prospective_years[-1])

    def _update_plot_elements(self):
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        for collection in self.ax.collections:
            collection.remove()

        self.line_total_airfare.set_ydata(
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            - self.df.loc[self.prospective_years, "doc_energy_subsidy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "non_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "passenger_tax_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "operational_profit_per_ask"]
        )

        self.line_total_gross.set_ydata(
            self.df.loc[self.prospective_years, "doc_total_per_ask_mean"]
            - self.df.loc[self.prospective_years, "doc_energy_carbon_tax_per_ask_mean"]
            - self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_subsidy_per_ask_mean"]
        )

        self.line_total_adjusted.set_ydata(
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            - self.df.loc[self.prospective_years, "doc_energy_subsidy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
        )

        self.ax.fill_between(
            self.prospective_years,
            -self.df.loc[self.prospective_years, "doc_energy_subsidy_per_ask_mean"],
            np.zeros(len(self.prospective_years)),
            color="cornflowerblue",
            hatch="xx",
            label="Energy subsidy",
            edgecolor="dimgray",
            linewidth=0.5,
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"],
            np.zeros(len(self.prospective_years)),
            color="royalblue",
            label="Non-energy",
            edgecolor="dimgray",
            linewidth=0.5,
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"],
            color="cornflowerblue",
            label="Energy",
            edgecolor="dimgray",
            linewidth=0.5,
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"],
            color="cornflowerblue",
            hatch="//",
            linewidth=0.5,
            edgecolor="dimgray",
            label="Energy taxes (non-carbon)",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"],
            color="cornflowerblue",
            hatch="..",
            linewidth=0.5,
            edgecolor="dimgray",
            label="Carbon tax (adjusted for offsets)",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"],
            color="#848482",
            alpha=0.8,
            label="Carbon offset",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"],
            color="#FF8800",
            alpha=0.8,
            label="Indirect-Operating Costs",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "non_operating_cost_per_ask"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"],
            color="#FFAA00",
            alpha=0.8,
            label="Non-Operating Costs",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "non_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "passenger_tax_per_ask"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "non_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"],
            color="#FFD000",
            alpha=0.8,
            label="Passenger Tax",
        )

        self.ax.fill_between(
            self.prospective_years,
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "non_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "passenger_tax_per_ask"]
            + self.df.loc[self.prospective_years, "operational_profit_per_ask"],
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
            + self.df.loc[self.prospective_years, "noc_carbon_offset_per_ask"]
            + self.df.loc[self.prospective_years, "non_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "indirect_operating_cost_per_ask"]
            + self.df.loc[self.prospective_years, "passenger_tax_per_ask"],
            color="#FFEA00",
            alpha=0.8,
            label="Operating Profit",
        )
        self.fig.canvas.draw()
