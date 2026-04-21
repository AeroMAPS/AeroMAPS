# @Time : 15/06/2023 09:06
# @Author : a.salgas
# @File : costs.py
# @Software: PyCharm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

from aeromaps.plots.single_scenario_plot import SingleScenarioPlot
from aeromaps.plots.single_scenario_plot import plot_1_x
from aeromaps.plots.single_scenario_plot import plot_1_y
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

    def __init__(self, process, figsize=None):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize)

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

    def __init__(self, process, figsize=None):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize)

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

    def __init__(self, process, figsize=None):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize)

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

    def __init__(self, process, figsize=None):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize)

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


class AllEnergyCostsPerRPKBreakdown(SingleScenarioPlot):
    """Stacked-area breakdown of energy-related costs per RPK by pathway.

    Inspired by :class:`ScenarioEnergyExpensesPlot`: uses the
    ``pathways_manager`` to dynamically discover energy carriers so that
    **only carriers with non-zero energy consumption** appear in the legend.
    Each carrier's cost is broken down (via hatch patterns) into:

    * Base energy cost (MFSP)
    * Carbon tax
    * Energy tax
    * Subsidy (shown as a negative area below zero)

    A black total line for ``doc_all_energy_costs_per_rpk`` is overlaid.
    """

    required_outputs = [
        "doc_all_energy_costs_per_rpk",
        "rpk_long_range",
        "rpk_medium_range",
        "rpk_short_range",
    ]

    # Hatch / label maps – same visual language as ScenarioEnergyExpensesPlot
    _HATCH_MAP = {
        "mfsp": "",
        "tax": "//",
        "carbon_tax": "..",
        "subsidy": "xx",
    }
    _LABEL_MAP = {
        "mfsp": "Energy cost",
        "tax": "Energy taxes",
        "carbon_tax": "Carbon tax",
        "subsidy": "Subsidies",
    }

    def __init__(self, process, figsize=None):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize)

    def _get_default_figsize(self):
        return (plot_2_x, plot_2_y)

    # -- helpers ----------------------------------------------------------

    def _get_active_pathways(self):
        """Return pathways with non-zero energy consumption, sorted by first usage year."""
        pathways = self.pathways_manager.get_all()

        def first_usage_year(p):
            col = f"{p.name}_energy_consumption"
            if col not in self.df.columns:
                return max(self.prospective_years) + 1
            series = self.df.loc[self.prospective_years, col]
            valid = series[~(series.isna() | (series == 0.0))].index.tolist()
            return min(valid) if valid else max(self.prospective_years) + 1

        return [
            p
            for p in sorted(pathways, key=first_usage_year)
            if first_usage_year(p) <= max(self.prospective_years)
        ]

    def _total_rpk(self):
        y = self.prospective_years
        return (
            self.df.loc[y, "rpk_long_range"]
            + self.df.loc[y, "rpk_medium_range"]
            + self.df.loc[y, "rpk_short_range"]
        ).values

    def _compute_pathway_data(self, pathways, total_rpk):
        """Build per-pathway cost-component arrays expressed in €/RPK.

        Uses only the **passenger** share of each pathway's energy consumption
        so that the stacked areas are consistent with ``doc_all_energy_costs_per_rpk``
        (which is derived from per-ASK costs × total_ASK / total_RPK and therefore
        excludes freight energy).
        """
        y = self.prospective_years

        # Pre-compute passenger-to-total energy ratios per aircraft type so
        # that each pathway's energy is scaled to passenger-only.
        pax_ratios = {}
        if self.pathways_manager is not None:
            for atype in self.pathways_manager.get_all_types("aircraft_type"):
                total_col = f"energy_consumption_{atype}"
                pax_col = f"energy_consumption_passenger_{atype}"
                if total_col in self.df.columns and pax_col in self.df.columns:
                    total_e = self.df.loc[y, total_col].fillna(0).values
                    pax_e = self.df.loc[y, pax_col].fillna(0).values
                    with np.errstate(divide="ignore", invalid="ignore"):
                        ratio = np.where(total_e > 0, pax_e / total_e, 0.0)
                    pax_ratios[atype] = ratio
                else:
                    pax_ratios[atype] = np.ones(len(y))

        data = {}
        for p in pathways:
            raw_energy = self.df.loc[y, f"{p.name}_energy_consumption"].fillna(0).values
            # Scale to passenger-only energy
            ratio = pax_ratios.get(p.aircraft_type, np.ones(len(y)))
            energy = raw_energy * ratio

            data[p.name] = {
                "mfsp": np.where(total_rpk > 0, energy
                * self.df.loc[y, f"{p.name}_mean_mfsp"].fillna(0).values
                / total_rpk, 0),
                "carbon_tax": np.where(total_rpk > 0, energy
                * self.df.loc[y, f"{p.name}_mean_unit_carbon_tax"].fillna(0).values
                / total_rpk, 0),
                "tax": np.where(total_rpk > 0, energy
                * self.df.loc[y, f"{p.name}_mean_unit_tax"].fillna(0).values
                / total_rpk, 0),
                "subsidy": np.where(total_rpk > 0, energy
                * self.df.loc[y, f"{p.name}_mean_unit_subsidy"].fillna(0).values
                / total_rpk, 0),
            }

        # Normalise so that the stacked net total exactly matches the model's
        # ``doc_all_energy_costs_per_rpk``.  In price-elastic MDA loops the
        # pathway shares used by EnergyCarriersMeans may lag behind the final
        # energy values, causing a small discrepancy.
        model_total = self.df.loc[y, "doc_all_energy_costs_per_rpk"].fillna(0).values
        stacked_total = np.zeros(len(y))
        for p in pathways:
            d = data[p.name]
            stacked_total += d["mfsp"] + d["carbon_tax"] + d["tax"] - d["subsidy"]
        with np.errstate(divide="ignore", invalid="ignore"):
            scale = np.where(
                np.abs(stacked_total) > 1e-12,
                model_total / stacked_total,
                1.0,
            )
        for p in pathways:
            for comp in ("mfsp", "carbon_tax", "tax", "subsidy"):
                data[p.name][comp] = data[p.name][comp] * scale

        return data

    # -- plotting ---------------------------------------------------------

    def _draw_stacked(self, pathways, data, pathway_colors):
        """Draw the stacked areas and total line; shared by create_plot / _update."""
        y = self.prospective_years
        positive_components = ["mfsp", "tax", "carbon_tax"]

        # --- positive stack (per pathway, per component) ---
        bottom = np.zeros(len(y))
        for idx, p in enumerate(pathways):
            comp_bottom = bottom.copy()
            for comp in positive_components:
                vals = data[p.name].get(comp, np.zeros(len(y)))
                comp_top = comp_bottom + vals
                self.ax.fill_between(
                    y,
                    comp_bottom,
                    comp_top,
                    facecolor=pathway_colors[p.name],
                    hatch=self._HATCH_MAP[comp],
                    edgecolor="black",
                    linewidth=0.5,
                    alpha=0.5,
                    linestyle=":",
                )
                comp_bottom = comp_top
            bottom = comp_bottom

        # --- negative stack for subsidies ---
        bottom_neg = np.zeros(len(y))
        for p in pathways:
            vals = data[p.name].get("subsidy", np.zeros(len(y)))
            comp_top = bottom_neg - vals
            self.ax.fill_between(
                y,
                bottom_neg,
                comp_top,
                facecolor=pathway_colors[p.name],
                hatch=self._HATCH_MAP["subsidy"],
                edgecolor="black",
                linewidth=0.5,
                linestyle=":",
                alpha=0.5,
            )
            bottom_neg = comp_top

        # --- total line ---
        self.ax.plot(
            y,
            self.df.loc[y, "doc_all_energy_costs_per_rpk"],
            color="black",
            linestyle="-",
            linewidth=2,
            zorder=4,
            label="Total energy costs per RPK",
        )

    def _draw_legends(self, pathways, pathway_colors):
        """Add two legends: one for carrier colours, one for component hatches."""
        from matplotlib.lines import Line2D
        # Left legend – active energy carriers
        carrier_handles = [
            Patch(
                facecolor=pathway_colors[p.name],
                edgecolor="black",
                alpha=0.5,
                label=p.name,
            )
            for p in pathways
        ]
        legend1 = self.ax.legend(
            handles=carrier_handles,
            title="Energy carrier" if len(carrier_handles) == 1 else "Energy carriers",
            loc="upper left",
            prop={"size": 7},
        )

        # Right legend – cost components (hatch) + total line
        overlay_handles = [
            Patch(edgecolor="black", facecolor="none", label=self._LABEL_MAP["mfsp"]),
            Patch(
                edgecolor="black",
                facecolor="none",
                hatch=self._HATCH_MAP["tax"],
                label=self._LABEL_MAP["tax"],
            ),
            Patch(
                edgecolor="black",
                facecolor="none",
                hatch=self._HATCH_MAP["carbon_tax"],
                label=self._LABEL_MAP["carbon_tax"],
            ),
            Patch(
                edgecolor="black",
                facecolor="none",
                hatch=self._HATCH_MAP["subsidy"],
                label=self._LABEL_MAP["subsidy"],
            ),
            Line2D(
                [0],
                [0],
                color="black",
                linewidth=2,
                linestyle="solid",
                label="Total energy costs per RPK",
            ),
        ]
        legend2 = self.ax.legend(
            handles=overlay_handles,
            loc="upper right",
            prop={"size": 7},
        )
        self.ax.add_artist(legend1)
        self.ax.add_artist(legend2)

    def create_plot(self):
        pathways = self._get_active_pathways()
        colors_cmap = plt.cm.get_cmap("tab20", max(len(self.pathways_manager.get_all()), 1))
        all_pathways = self.pathways_manager.get_all()
        pathway_colors = {p.name: colors_cmap(i) for i, p in enumerate(all_pathways)}

        total_rpk = self._total_rpk()
        data = self._compute_pathway_data(pathways, total_rpk)

        self._draw_stacked(pathways, data, pathway_colors)
        self._draw_legends(pathways, pathway_colors)

        self.ax.grid(axis="x")
        self.ax.set_title("Energy costs per RPK – Breakdown by carrier")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Energy costs [€/RPK]")
        self.ax.set_xlim(self.prospective_years[0], self.prospective_years[-1])

    def _update_plot_elements(self):
        for collection in list(self.ax.collections):
            collection.remove()
        for line in list(self.ax.lines):
            line.remove()

        pathways = self._get_active_pathways()
        colors_cmap = plt.cm.get_cmap("tab20", max(len(self.pathways_manager.get_all()), 1))
        all_pathways = self.pathways_manager.get_all()
        pathway_colors = {p.name: colors_cmap(i) for i, p in enumerate(all_pathways)}

        total_rpk = self._total_rpk()
        data = self._compute_pathway_data(pathways, total_rpk)

        self._draw_stacked(pathways, data, pathway_colors)
        self._draw_legends(pathways, pathway_colors)
        self.fig.canvas.draw()


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

    def __init__(self, process, figsize=None):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize)

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
