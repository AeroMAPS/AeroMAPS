import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from ipywidgets import interact, widgets


class ScenarioEnergyExpensesPlot:
    def __init__(self, process):
        data = process.data
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]
        self.pathways_manager = process.pathways_manager

        self.fig, self.ax = plt.subplots(
            figsize=(15, 9),
        )
        self.hatch_map = {
            "mfsp": "",
            "tax": "//",
            "carbon_tax": "..",
            "subsidy": "--",
        }
        self.label_map = {
            "mfsp": "Gross expenses",
            "tax": "Other taxes",
            "carbon_tax": "Carbon tax",
            "subsidy": "Subventions",
        }
        self.marker_map = {
            "mfsp": "o",
            "tax": "s",
            "carbon_tax": "D",
            "subsidy": "v",
        }
        self.linestyle_map = {
            "mfsp": "--",
            "tax": ":",
            "carbon_tax": ":",
            "subsidy": ":",
        }
        self.plot_interact()
        self.create_plot()

    def plot_interact(self):
        pathway_widget = widgets.SelectMultiple(
            options=[("All pathways", "all")]
            + [(pathway.name, pathway) for pathway in self.pathways_manager.get_all()],
            description="Energy carrier:",
            value=["all"],
        )

        detail_level = widgets.ToggleButtons(
            options=["Overview", "Pathways (Stacked)", "Pathways (no stack)"],
            description="Detail level:",
            disabled=False,
            button_style="success",
            value="Pathways",
        )

        mfsp_checkbox = widgets.Checkbox(value=True, description="Gross Expenses", disabled=False)
        net_mfsp_checkbox = widgets.Checkbox(
            value=False, description="Net Airlines Expenses", disabled=False
        )
        subsidies_checkbox = widgets.Checkbox(value=False, description="Subsidies", disabled=False)
        carbon_tax_checbox = widgets.Checkbox(
            value=False, description="Carbon Taxes", disabled=False
        )
        other_taxes_checkbox = widgets.Checkbox(
            value=False, description="Other Taxes", disabled=False
        )

        interact(
            self.update,
            pathway_selected=pathway_widget,
            detail_level_selected=detail_level,
            subsidies=subsidies_checkbox,
            carbon_tax=carbon_tax_checbox,
            other_taxes=other_taxes_checkbox,
            gross_expenses=mfsp_checkbox,
            net_expenses=net_mfsp_checkbox,
        )

    def create_plot(self):
        pass

    def update(
        self,
        pathway_selected,
        detail_level_selected,
        subsidies,
        carbon_tax,
        other_taxes,
        gross_expenses,
        net_expenses,
    ):
        self.ax.cla()

        pathways = self.pathways_manager.get_all()
        colors = plt.cm.get_cmap("tab20", len(pathways))
        pathway_colors = {p.name: colors(i) for i, p in enumerate(pathways)}

        if "all" in pathway_selected:
            pathways = self.pathways_manager.get_all()
        else:
            pathways = pathway_selected

        # Préparation des données par filière et composante
        components = []
        if gross_expenses:
            components.append("mfsp")
        if other_taxes:
            components.append("tax")
        if carbon_tax:
            components.append("carbon_tax")
        # On ne met pas "subsidy" ici pour le stack principal

        # Construction des matrices de données [pathway][component][année]
        data_dict = {}
        for p in pathways:
            data_dict[p.name] = {}
            if "mfsp" in components:
                data_dict[p.name]["mfsp"] = (
                    self.df.loc[self.prospective_years, f"{p.name}_mfsp"].fillna(0).values
                    * self.df.loc[self.prospective_years, f"{p.name}_energy_consumption"]
                    .fillna(0)
                    .values
                    / 1e6
                )
            if "tax" in components:
                data_dict[p.name]["tax"] = (
                    self.df.loc[self.prospective_years, f"{p.name}_unit_tax"].fillna(0).values
                    * self.df.loc[self.prospective_years, f"{p.name}_energy_consumption"]
                    .fillna(0)
                    .values
                    / 1e6
                )
            if "carbon_tax" in components:
                data_dict[p.name]["carbon_tax"] = (
                    self.df.loc[self.prospective_years, f"{p.name}_unit_carbon_tax"]
                    .fillna(0)
                    .values
                    * self.df.loc[self.prospective_years, f"{p.name}_energy_consumption"]
                    .fillna(0)
                    .values
                    / 1e6
                )
            if subsidies:
                data_dict[p.name]["subsidy"] = (
                    self.df.loc[self.prospective_years, f"{p.name}_unit_subsidy"].fillna(0).values
                    * self.df.loc[self.prospective_years, f"{p.name}_energy_consumption"]
                    .fillna(0)
                    .values
                    / 1e6
                )

        if detail_level_selected == "Pathways":
            bottom = np.zeros(len(self.prospective_years))
            for i, p in enumerate(pathways):
                comp_bottom = bottom.copy()
                for comp in components:
                    vals = data_dict[p.name].get(comp, np.zeros(len(self.prospective_years)))
                    comp_top = comp_bottom + vals
                    self.ax.fill_between(
                        self.prospective_years,
                        comp_bottom,
                        comp_top,
                        facecolor=pathway_colors[p.name],
                        hatch=self.hatch_map[comp],
                        edgecolor="black",
                        linewidth=0.5,
                        alpha=0.5,
                        label=f"{p.name} - {self.label_map[comp]}" if (i == 0) else None,
                    )
                    comp_bottom = comp_top
                bottom = comp_bottom
            if subsidies:
                bottom_neg = np.zeros(len(self.prospective_years))
                for i, p in enumerate(pathways):
                    vals = data_dict[p.name].get("subsidy", np.zeros(len(self.prospective_years)))
                    comp_top = bottom_neg - vals
                    self.ax.fill_between(
                        self.prospective_years,
                        bottom_neg,
                        comp_top,
                        facecolor=pathway_colors[p.name],
                        hatch=self.hatch_map["subsidy"],
                        edgecolor="black",
                        linewidth=0.5,
                        alpha=0.5,
                        label=f"{p.name} - {self.label_map['subsidy']}" if (i == 0) else None,
                    )
                    bottom_neg = comp_top
            if net_expenses:
                net_overlay = np.array(
                    [
                        self.df.loc[self.prospective_years, f"{p.name}_net_mfsp"].fillna(0).values
                        * self.df.loc[self.prospective_years, f"{p.name}_energy_consumption"]
                        .fillna(0)
                        .values
                        / 1e6
                        for p in pathways
                    ]
                )
                net_total = np.sum(net_overlay, axis=0)
                self.ax.plot(
                    self.prospective_years,
                    net_total,
                    color="black",
                    linewidth=2,
                    alpha=1,
                    linestyle="--",
                    label="Net airlines expenses",
                )
        elif detail_level_selected == "Overview":
            # Stack positif (hors subventions) par composant (somme sur toutes les filières)
            comp_bottom = np.zeros(len(self.prospective_years))
            for comp in components:
                vals = np.sum(
                    [
                        data_dict[p.name].get(comp, np.zeros(len(self.prospective_years)))
                        for p in pathways
                    ],
                    axis=0,
                )
                comp_top = comp_bottom + vals
                self.ax.fill_between(
                    self.prospective_years,
                    comp_bottom,
                    comp_top,
                    facecolor="grey",
                    hatch=self.hatch_map[comp],
                    edgecolor="black",
                    linewidth=0.5,
                    alpha=0.5,
                    label=self.label_map[comp] if comp_bottom.sum() == 0 else None,
                )
                comp_bottom = comp_top
            # Stack négatif pour subventions (somme sur toutes les filières)
            if subsidies:
                comp_bottom = np.zeros(len(self.prospective_years))
                vals = np.sum(
                    [
                        data_dict[p.name].get("subsidy", np.zeros(len(self.prospective_years)))
                        for p in pathways
                    ],
                    axis=0,
                )
                comp_top = comp_bottom - vals
                self.ax.fill_between(
                    self.prospective_years,
                    comp_bottom,
                    comp_top,
                    facecolor="grey",
                    hatch=self.hatch_map["subsidy"],
                    edgecolor="black",
                    linewidth=0.5,
                    alpha=0.5,
                    label=self.label_map["subsidy"],
                )
            if net_expenses:
                vals = np.sum(
                    [
                        self.df.loc[self.prospective_years, f"{p.name}_net_mfsp"].fillna(0).values
                        * self.df.loc[self.prospective_years, f"{p.name}_energy_consumption"]
                        .fillna(0)
                        .values
                        / 1e6
                        for p in pathways
                    ],
                    axis=0,
                )
                self.ax.plot(
                    self.prospective_years,
                    vals,
                    color="black",
                    linewidth=4,
                    alpha=1,
                    linestyle="solid",
                )
        elif detail_level_selected == "Lines (no stack)":
            # Affichage non stacké : chaque filière = couleur, chaque composant = marqueur + linestyle
            for i, p in enumerate(pathways):
                for comp in ["mfsp", "tax", "carbon_tax", "subsidy"]:
                    if (
                        (comp == "mfsp" and gross_expenses)
                        or (comp == "tax" and other_taxes)
                        or (comp == "carbon_tax" and carbon_tax)
                        or (comp == "subsidy" and subsidies)
                    ):
                        vals = data_dict[p.name].get(comp, np.zeros(len(self.prospective_years)))
                        # Subventions négatives
                        if comp == "subsidy":
                            vals = -vals
                        self.ax.plot(
                            self.prospective_years,
                            vals,
                            color=pathway_colors[p.name],
                            marker=self.marker_map[comp],
                            linestyle=self.linestyle_map[comp],
                            linewidth=1.5,
                            alpha=0.5,
                            markersize=4,
                            label=f"{p.name} - {self.label_map[comp]}",
                        )
            # Net expenses en surimpression (no stack)
            if net_expenses:
                for i, p in enumerate(pathways):
                    vals = (
                        self.df.loc[self.prospective_years, f"{p.name}_net_mfsp"].fillna(0).values
                        * self.df.loc[self.prospective_years, f"{p.name}_energy_consumption"]
                        .fillna(0)
                        .values
                        / 1e6
                    )
                    self.ax.plot(
                        self.prospective_years,
                        vals,
                        color=pathway_colors[p.name],
                        linestyle="solid",
                        linewidth=2,
                        label=f"{p.name} - Net expenses",
                    )

        # Légendes adaptées
        if detail_level_selected == "Lines (no stack)":
            pathway_legend_handles = [
                Patch(facecolor=pathway_colors[p.name], edgecolor="black", alpha=0.5, label=p.name)
                for p in pathways
            ]
            marker_legend_handles = [
                Line2D(
                    [0],
                    [0],
                    color="black",
                    marker=self.marker_map[comp],
                    linestyle=self.linestyle_map[comp],
                    markersize=4,
                    label=self.label_map[comp],
                )
                for comp in ["mfsp", "tax", "carbon_tax", "subsidy"]
                if (
                    (comp == "mfsp" and gross_expenses)
                    or (comp == "tax" and other_taxes)
                    or (comp == "carbon_tax" and carbon_tax)
                    or (comp == "subsidy" and subsidies)
                )
            ]
            net_legend_handle = Line2D(
                [0],
                [0],
                color="black",
                linestyle="solid",
                linewidth=2,
                label="Net airlines expenses",
            )
            legend1 = self.ax.legend(
                handles=pathway_legend_handles,
                title="Energy carriers",
                loc="upper left",
                prop={"size": 8},
            )
            legend2 = self.ax.legend(
                handles=marker_legend_handles + [net_legend_handle],
                loc="upper right",
                prop={"size": 8},
            )
            self.ax.add_artist(legend1)
            self.ax.add_artist(legend2)
        else:
            pathway_legend_handles = [
                Patch(facecolor=pathway_colors[p.name], edgecolor="black", label=p.name, alpha=0.5)
                for p in pathways
            ]
            overlay_legend_handles = [
                Patch(edgecolor="black", facecolor="none", label=self.label_map["mfsp"]),
                Patch(
                    edgecolor="black",
                    facecolor="none",
                    hatch=self.hatch_map["tax"],
                    label=self.label_map["tax"],
                ),
                Patch(
                    edgecolor="black",
                    facecolor="none",
                    hatch=self.hatch_map["carbon_tax"],
                    label=self.label_map["carbon_tax"],
                ),
                Patch(
                    edgecolor="black",
                    facecolor="none",
                    hatch=self.hatch_map["subsidy"],
                    label=self.label_map["subsidy"],
                ),
                Line2D(
                    [0],
                    [0],
                    color="black",
                    linewidth=2,
                    linestyle="solid",
                    label="Net airlines expenses",
                ),
            ]

            legend1 = self.ax.legend(
                title="Energy carrier selected"
                if len(pathway_legend_handles) < 2
                else "Energy carriers selected",
                handles=pathway_legend_handles,
                loc="upper left",
                prop={"size": 7},
            )
            legend2 = self.ax.legend(
                handles=overlay_legend_handles,
                loc="upper right",
                prop={"size": 7},
            )
            self.ax.add_artist(legend1)
            self.ax.add_artist(legend2)

        self.ax.grid(axis="x")
        self.ax.set_title("Annual energy expenses per pathway")
        self.ax.set_ylabel("Energy expenses [M€]")
        self.ax.set_xlim(2020, self.years[-1])
        self.ax.set_ylim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()
