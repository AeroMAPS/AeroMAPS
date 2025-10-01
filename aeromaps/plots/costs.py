# @Time : 15/06/2023 09:06
# @Author : a.salgas
# @File : costs.py
# @Software: PyCharm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch


from .constants import plot_3_x, plot_3_y


class ScenarioEnergyExpensesComparison:
    def __init__(self, process):
        data = process.data
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.fig, self.ax = plt.subplots(
            # figsize=(plot_3_x, plot_3_y),
        )
        self.create_plot()

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
        self.ax = plt.gca()

        self.ax.set_xlim(2020, self.years[-1])
        # #
        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        # self.fig.canvas.layout.width = "auto"
        # self.fig.canvas.layout.height = "auto"
        self.fig.tight_layout()

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
        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class DiscountEffect:
    def __init__(self, process):
        data = process.data
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.float_inputs = data["float_inputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.fig, self.ax = plt.subplots(
            figsize=(plot_3_x, plot_3_y),
        )
        self.create_plot()

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
            label="Discounted expenses at r={}%".format(self.float_inputs["social_discount_rate"]),
            linewidth=2,
        )

        self.ax.grid(axis="y")
        self.ax.set_title("Total (energy) expenses (M€)")
        self.ax.set_ylabel("M€ / year")
        self.ax = plt.gca()
        self.ax.legend()
        self.ax.set_xlim(2020, self.years[-1])
        # #
        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        # self.fig.canvas.layout.width = "auto"
        # self.fig.canvas.layout.height = "auto"
        self.fig.tight_layout()

    def update(self, df_data):
        self.df = df_data["vector_outputs"]

        self.line_non_discounted.set_ydata(
            self.df.loc[self.prospective_years, "non_discounted_energy_expenses"]
        )

        self.line_discounted.set_ydata(
            self.df.loc[self.prospective_years, "discounted_energy_expenses"]
        )

        for collection in self.ax.collections:
            collection.remove()

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class DropInMACC:
    # TODO DEPRECATE THIS CLASS
    def __init__(self, process):
        data = process.data
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        try:
            self.fig, self.ax = plt.subplots(
                figsize=(plot_3_x, plot_3_y),
            )
            self.create_plot()
        except Exception as e:
            raise RuntimeError(
                "Error in creating plot. Possible cause: this plot requires complex energy cost and abatement models. "
                "Be sure to select them in the scenario settings."
            ) from e

    def create_plot(self):
        # Select year at which the MACC is plotted
        year = self.years[-1]

        # create a dataframe for the various pathways
        # (usage: sorting the values by increasing carbon abatement cost)

        pathways = [
            "Bio - HEFA FOG",
            "Bio - HEFA Others",
            "Bio - Alcohol to Jet",
            "Bio - FT MSW",
            "Bio - FT Others",
            "Electrofuel",
        ]

        # Abatement potential in MtCO2e
        abatement_potential = [
            elt / 1000000
            for elt in [
                self.df.abatement_potential_hefa_fog[year],
                self.df.abatement_potential_hefa_others[year],
                self.df.abatement_potential_atj[year],
                self.df.abatement_potential_ft_msw[year],
                self.df.abatement_potential_ft_others[year],
                self.df.abatement_potential_electrofuel[year],
            ]
        ]

        # Energy available in EJ
        energy_avail = [
            elt / 1000000000000
            for elt in [
                self.df.energy_avail_hefa_fog[year],
                self.df.energy_avail_hefa_others[year],
                self.df.energy_avail_atj[year],
                self.df.energy_avail_ft_msw[year],
                self.df.energy_avail_ft_others[year],
                self.df.energy_avail_electrofuel[year],
            ]
        ]

        # carbon abatement cost in (€/tCO2e)
        carbon_abatement_cost = [
            self.df.carbon_abatement_cost_hefa_fog[year],
            self.df.carbon_abatement_cost_hefa_others[year],
            self.df.carbon_abatement_cost_atj[year],
            self.df.carbon_abatement_cost_ft_msw[year],
            self.df.carbon_abatement_cost_ft_others[year],
            self.df.carbon_abatement_cost_electrofuel[year],
        ]

        colors = ["#ee9b00", "#ffbf47", "#bb3e03", "#097223", "#0c9e30", "#828782"]

        macc_df = pd.DataFrame(
            data=[abatement_potential, energy_avail, carbon_abatement_cost, colors],
            columns=pathways,
            index=["abatement_potential", "energy_avail", "carbon_abatement_cost", "colors"],
        )

        macc_df = macc_df.transpose().sort_values(by="carbon_abatement_cost")

        macc_df = macc_df[macc_df["abatement_potential"] > 0]

        heights = macc_df["carbon_abatement_cost"].to_list()
        names = macc_df.index.to_list()
        heights.insert(0, 0)
        heights.append(heights[-1])

        # MAx potential MACC
        widths_potential = macc_df["abatement_potential"].to_list()
        widths_potential.insert(0, 0)
        widths_potential.append(widths_potential[-1])

        colors = macc_df["colors"].to_list()

        self.macc_curve = self.ax.step(
            np.cumsum(widths_potential) - widths_potential,
            heights,
            where="post",
            color="#335C67",
            label="Marginal abatement cost",
            linewidth=1.5,
        )

        # Fill under the step plot with different colors for each step
        for i in range(0, (len(widths_potential) - 2)):
            # Create a polygon for each step
            polygon = plt.Polygon(
                [
                    (np.cumsum(widths_potential)[i], 0),
                    (np.cumsum(widths_potential)[i], heights[i + 1]),
                    (np.cumsum(widths_potential)[i + 1], heights[i + 1]),
                    (np.cumsum(widths_potential)[i + 1], 0),
                ],
                closed=True,
                color=colors[i],
                alpha=0.5,
            )
            self.ax.add_patch(polygon)

        fuel = macc_df.energy_avail.to_list()
        fuel.insert(0, 0)
        widths_potential.pop()
        self.ax2 = self.ax.twinx()
        self.ax2.plot(
            np.cumsum(widths_potential),
            np.cumsum(fuel),
            color="#9E2A2B",
            linestyle=":",
            label="Energy potential",
            marker="x",
        )

        self.ax2.axhline(
            y=self.df.energy_consumption_dropin_fuel[year] / 1e12
            - self.df.energy_consumption_kerosene[year] / 1e12,
            color="black",
            linewidth=1,
            linestyle="-.",
        )
        self.ax2.text(
            0,
            1.02
            * (
                self.df.energy_consumption_dropin_fuel[year] / 1e12
                - self.df.energy_consumption_kerosene[year] / 1e12
            ),
            "Air transport sustainable drop-in fuels use, final year",
        )

        self.ax2.axhline(
            y=self.df.energy_consumption_dropin_fuel[year] / 1e12,
            color="black",
            linewidth=1,
            linestyle="-",
        )
        self.ax2.text(
            0,
            1.02 * (self.df.energy_consumption_dropin_fuel[year] / 1e12),
            "Air transport total drop-in fuels use, final year",
        )

        self.ax.grid(True, which="both", ls=":")
        self.ax.set_ylabel("Carbon Abatement Cost (€/t$\mathregular{CO_2}$)")
        self.ax2.set_ylabel("Energy potential under current allocation (EJ)")
        self.ax.set_xlabel("$\mathregular{CO_2}$ abatted (Mt)")

        for i in range(len(widths_potential) - 1):
            self.ax.text(np.cumsum(widths_potential)[i] + 10, heights[i + 1] - 50, names[i])

        self.ax.legend(
            fancybox=True,
            shadow=True,
            loc="lower left",
            bbox_to_anchor=[0.00, -0.2],
            prop={"size": 8},
        )
        self.ax2.legend(
            fancybox=True,
            shadow=True,
            loc="lower right",
            bbox_to_anchor=[1, -0.2],
            prop={"size": 8},
        )

        self.ax.set_title("Marginal abatement cost curve for drop-in fuels")

        # #
        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        # self.fig.canvas.layout.width = "auto"
        # self.fig.canvas.layout.height = "auto"
        self.fig.tight_layout()

    def update(self, df_data):
        self.df = df_data["vector_outputs"]
        self.float_outputs = df_data["float_outputs"]
        self.years = df_data["years"]["full_years"]
        self.historic_years = df_data["years"]["historic_years"]
        self.prospective_years = df_data["years"]["prospective_years"]

        self.ax.cla()
        self.ax2.cla()

        # Select year at which the MACC is plotted
        year = self.years[-1]

        # create a dataframe for the various pathways
        # (usage: sorting the values by increasing carbon abatement cost)

        pathways = [
            "Bio - HEFA FOG",
            "Bio - HEFA Others",
            "Bio - Alcohol to Jet",
            "Bio - FT MSW",
            "Bio - FT Others",
            "Electrofuel",
        ]

        # Abatement potential in MtCO2e
        abatement_potential = [
            elt / 1000000
            for elt in [
                self.df.abatement_potential_hefa_fog[year],
                self.df.abatement_potential_hefa_others[year],
                self.df.abatement_potential_atj[year],
                self.df.abatement_potential_ft_msw[year],
                self.df.abatement_potential_ft_others[year],
                self.df.abatement_potential_electrofuel[year],
            ]
        ]

        # Energy available in EJ
        energy_avail = [
            elt / 1000000000000
            for elt in [
                self.df.energy_avail_hefa_fog[year],
                self.df.energy_avail_hefa_others[year],
                self.df.energy_avail_atj[year],
                self.df.energy_avail_ft_msw[year],
                self.df.energy_avail_ft_others[year],
                self.df.energy_avail_electrofuel[year],
            ]
        ]

        # carbon abatement cost in (€/tCO2e)
        carbon_abatement_cost = [
            self.df.carbon_abatement_cost_hefa_fog[year],
            self.df.carbon_abatement_cost_hefa_others[year],
            self.df.carbon_abatement_cost_atj[year],
            self.df.carbon_abatement_cost_ft_msw[year],
            self.df.carbon_abatement_cost_ft_others[year],
            self.df.carbon_abatement_cost_electrofuel[year],
        ]

        colors = ["#ee9b00", "#ffbf47", "#bb3e03", "#097223", "#0c9e30", "#828782"]

        macc_df = pd.DataFrame(
            data=[abatement_potential, energy_avail, carbon_abatement_cost, colors],
            columns=pathways,
            index=["abatement_potential", "energy_avail", "carbon_abatement_cost", "colors"],
        )

        macc_df = macc_df.transpose().sort_values(by="carbon_abatement_cost")

        macc_df = macc_df[macc_df["abatement_potential"] > 0]

        heights = macc_df["carbon_abatement_cost"].to_list()
        names = macc_df.index.to_list()
        heights.insert(0, 0)
        heights.append(heights[-1])

        # MAx potential MACC
        widths_potential = macc_df["abatement_potential"].to_list()
        widths_potential.insert(0, 0)
        widths_potential.append(widths_potential[-1])

        colors = macc_df["colors"].to_list()

        self.macc_curve = self.ax.step(
            np.cumsum(widths_potential) - widths_potential,
            heights,
            where="post",
            color="#335C67",
            label="Marginal abatement cost",
            linewidth=1.5,
        )

        # Fill under the step plot with different colors for each step
        for i in range(0, (len(widths_potential) - 2)):
            # Create a polygon for each step
            polygon = plt.Polygon(
                [
                    (np.cumsum(widths_potential)[i], 0),
                    (np.cumsum(widths_potential)[i], heights[i + 1]),
                    (np.cumsum(widths_potential)[i + 1], heights[i + 1]),
                    (np.cumsum(widths_potential)[i + 1], 0),
                ],
                closed=True,
                color=colors[i],
                alpha=0.5,
            )
            self.ax.add_patch(polygon)

        fuel = macc_df.energy_avail.to_list()
        fuel.insert(0, 0)
        widths_potential.pop()

        self.ax2.plot(
            np.cumsum(widths_potential),
            np.cumsum(fuel),
            color="#9E2A2B",
            linestyle=":",
            label="Energy potential",
            marker="x",
        )

        self.ax2.axhline(
            y=self.df.energy_consumption_dropin_fuel[year] / 1e12
            - self.df.energy_consumption_kerosene[year] / 1e12,
            color="black",
            linewidth=1,
            linestyle="-.",
        )
        self.ax2.text(
            0,
            1.02
            * (
                self.df.energy_consumption_dropin_fuel[year] / 1e12
                - self.df.energy_consumption_kerosene[year] / 1e12
            ),
            "Air transport sustainable drop-in fuels use, final year",
        )

        self.ax2.axhline(
            y=self.df.energy_consumption_dropin_fuel[year] / 1e12,
            color="black",
            linewidth=1,
            linestyle="-",
        )
        self.ax2.text(
            0,
            1.02 * (self.df.energy_consumption_dropin_fuel[year] / 1e12),
            "Air transport total drop-in fuels use, final year",
        )

        self.ax.grid(True, which="both", ls=":")
        self.ax.set_ylabel("Carbon Abatement Cost (€/t$\mathregular{CO_2}$)")
        self.ax2.set_ylabel("Energy potential under current allocation (EJ)")
        self.ax.set_xlabel("$\mathregular{CO_2}$ abatted (Mt)")

        for i in range(len(widths_potential) - 1):
            self.ax.text(np.cumsum(widths_potential)[i] + 10, heights[i + 1] - 50, names[i])

        self.fig.tight_layout()
        self.fig.canvas.draw()


class DOCEvolutionBreakdown:
    def __init__(self, process):
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
        self.ax = plt.gca()

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

        for collection in self.ax.collections:
            collection.remove()

        self.line_total.set_ydata(self.df.loc[self.prospective_years, "doc_total_per_ask_mean"])

        self.line_total_adjusted.set_ydata(
            self.df.loc[self.prospective_years, "doc_non_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            - self.df.loc[self.prospective_years, "doc_energy_subsidy_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_carbon_tax_lowering_offset_per_ask_mean"]
        )

        self.line_total_gross.set_ydata(
            self.df.loc[self.prospective_years, "doc_total_per_ask_mean"]
            - self.df.loc[self.prospective_years, "doc_energy_per_ask_mean"]
            - self.df.loc[self.prospective_years, "doc_energy_tax_per_ask_mean"]
            + self.df.loc[self.prospective_years, "doc_energy_subsidy_per_ask_mean"]
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

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class DOCEvolutionCategory:
    def __init__(self, process):
        data = process.data
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.float_inputs = data["float_inputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.fig, self.ax = plt.subplots(
            figsize=(plot_3_x, plot_3_y),
        )
        self.create_plot()

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
        self.ax = plt.gca()
        self.ax.legend(title="Direct Operating Cost")
        self.ax.set_xlim(2020, self.years[-1])
        # #
        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        # self.fig.canvas.layout.width = "auto"
        # self.fig.canvas.layout.height = "auto"
        self.fig.tight_layout()

    def update(self, df_data):
        for collection in self.ax.collections:
            collection.remove()

        self.df = df_data["vector_outputs"]

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

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


class AirfareEvolutionBreakdown:
    def __init__(self, process):
        data = process.data
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]

        self.fig, self.ax = plt.subplots(
            # figsize=(plot_3_x, plot_3_y),
        )
        self.create_plot()

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
        self.ax = plt.gca()
        self.ax.legend(fontsize="8", loc="upper left")
        self.ax.set_xlim(self.prospective_years[0], self.prospective_years[-1])

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

        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()
