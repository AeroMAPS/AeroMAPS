import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
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
            options=[
                ("Overview", "overview"),
                ("Pathways (Stacked)", "stacked_pathways"),
                ("Pathways (no stack)", "line_pathways"),
            ],
            description="Detail level:",
            disabled=False,
            button_style="success",
            value="stacked_pathways",
        )

        mfsp_checkbox = widgets.Checkbox(value=True, description="Gross Expenses", disabled=False)
        net_mfsp_checkbox = widgets.Checkbox(
            value=True, description="Net Airlines Expenses", disabled=False
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

        # Sort first pathways by the first year with a non-zero value
        # TODO move somewhere else?
        def first_usage_year(p):
            mfsp_series = self.df.loc[self.prospective_years, f"{p.name}_energy_consumption"]
            # First valid year (non-NaN and non-zero)
            valid_years = mfsp_series[~(mfsp_series.isna() | (mfsp_series == 0.0))].index.tolist()
            # If no valid years, return max year + 1
            first_valid_year = min(valid_years) if valid_years else max(self.prospective_years) + 1
            return first_valid_year

        colors = plt.cm.get_cmap("tab20", len(pathways))
        pathway_colors = {p.name: colors(i) for i, p in enumerate(pathways)}

        if "all" not in pathway_selected:
            pathways = pathway_selected

        # Sort pathways and filter out those that have no usage within prospective years
        pathways = [
            p
            for p in sorted(pathways, key=first_usage_year)
            if first_usage_year(p) <= max(self.prospective_years)
        ]

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

        if detail_level_selected == "stacked_pathways":
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
                        linestyle=":",
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
                        linestyle=":",
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
                    linestyle="solid",
                    label="Net airlines expenses",
                )
        elif detail_level_selected == "overview":
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
                    linewidth=2,
                    alpha=1,
                    linestyle="solid",
                )
        elif detail_level_selected == "line_pathways":
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


class DetailledMFSPBreakdownPerYear:
    def __init__(self, process):
        data = process.data
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.float_inputs = data["float_inputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]
        self.pathways_data = process.energy_carriers_data
        self.pathways_manager = process.pathways_manager

        # Création du mapping couleur pour chaque couple (process, resource)
        self.resource_color_map = self._create_color_map()
        self.hatch_map = {
            "cost": "",
            "tax": "//",
            "subsidy": "\\\\",
            "carbon_tax": "..",
        }

        self.fig, self.ax = plt.subplots(
            # figsize=(plot_3_x, plot_3_y),
        )

        self.create_plot()
        self.plot_interact()

    def _create_color_map(self):
        # Mapping couleur pour chaque couple (process, resource)
        pathways = self.pathways_manager.get_all()
        process_resource_pairs = set()
        for p in pathways:
            # Ressources propres à la filière (pas de process)
            for resource in p.resources_used:
                process_resource_pairs.add(("main", resource))
            # Ressources utilisées par chaque process
            for process_name, resource in p.resources_used_processes.items():
                process_resource_pairs.add((process_name, resource))
            # Pour les coûts sans ressource d'un process
            for process_name in p.resources_used_processes.keys():
                process_resource_pairs.add((process_name, "without_resources_unit_cost"))
        # Ajout d'une clé spéciale pour la barre "sans ressource"
        process_resource_pairs.add(("main", "mfsp_without_resource"))
        pairs_sorted = sorted(process_resource_pairs)
        cmap = plt.get_cmap("tab20")
        color_map = {pair: cmap(i % 20) for i, pair in enumerate(pairs_sorted)}
        # Couleur grise pour la barre "sans ressource"
        color_map[("main", "mfsp_without_resource")] = (0.7, 0.7, 0.7, 1.0)
        return color_map

    def create_plot(self):
        pass

    def plot_interact(self):
        year_widget = widgets.IntSlider(
            min=self.prospective_years[0],
            max=self.prospective_years[-1],
            step=1,
            description="Year:",
            value=2035,
        )

        interact(self.update, year=year_widget)

    def update(self, year):
        self.ax.cla()

        # this function must access outputs of teh process depending on what's inside the energy config file
        # get all pathways
        pathways = self.pathways_manager.get_all()

        for p in pathways:
            if not (
                pd.isna(self.df.loc[year, f"{p.name}_energy_consumption"])
                or self.df.loc[year, f"{p.name}_energy_consumption"] < 1e-9
            ):
                color = self.resource_color_map.get(("main", "mfsp_without_resource"), "grey")
                self.ax.bar(
                    p.name,
                    self.df.loc[year, p.name + "_mfsp_without_resource"],
                    label="Base, excluding resource",
                    linewidth=0.5,
                    color=color,
                    hatch=self.hatch_map["cost"],
                )
                base = self.df.loc[year, p.name + "_mfsp_without_resource"]

                # Taxes et subventions sur la base
                tax_col = p.name + "_unit_tax_without_resource"
                tax_val = self.df.loc[year, tax_col] if tax_col in self.df.columns else 0
                if tax_val != 0:
                    self.ax.bar(
                        p.name,
                        tax_val,
                        bottom=base,
                        linewidth=0.5,
                        color=color,
                        hatch=self.hatch_map["tax"],
                    )
                    base += tax_val

                subsidy_col = p.name + "_unit_subsidy_without_resource"
                subsidy_val = (
                    self.df.loc[year, subsidy_col] if subsidy_col in self.df.columns else 0
                )
                if subsidy_val != 0:
                    self.ax.bar(
                        p.name,
                        -subsidy_val,
                        bottom=0,
                        linewidth=0.5,
                        color=color,
                        hatch=self.hatch_map["subsidy"],
                    )

                neg_base = -subsidy_val
                # base ne change pas car subvention négative

                # Ressources propres à la filière
                for resource in p.resources_used:
                    resource_cost = self.df.loc[
                        year, p.name + "_excluding_processes_" + resource + "_unit_cost"
                    ]
                    color = self.resource_color_map.get(("main", resource), None)
                    self.ax.bar(
                        p.name,
                        resource_cost,
                        bottom=base,
                        label=f"Base - {resource}",
                        linewidth=0.5,
                        color=color,
                        hatch=self.hatch_map["cost"],
                    )
                    # Taxes et subventions sur la ressource
                    tax_col = p.name + "_excluding_processes_" + resource + "_unit_tax"
                    tax_val = self.df.loc[year, tax_col] if tax_col in self.df.columns else 0
                    if tax_val != 0:
                        self.ax.bar(
                            p.name,
                            tax_val,
                            bottom=base + resource_cost,
                            linewidth=0.5,
                            color=color,
                            hatch=self.hatch_map["tax"],
                        )
                        resource_cost += tax_val
                    subsidy_col = p.name + "_excluding_processes_" + resource + "_unit_subsidy"
                    subsidy_val = (
                        self.df.loc[year, subsidy_col] if subsidy_col in self.df.columns else 0
                    )
                    if subsidy_val != 0:
                        self.ax.bar(
                            p.name,
                            -subsidy_val,
                            bottom=neg_base,
                            linewidth=0.5,
                            color=color,
                            hatch=self.hatch_map["subsidy"],
                        )

                    base += resource_cost
                    neg_base = -subsidy_val

                # Ressources utilisées par chaque process
                process_resources = p.resources_used_processes
                for process_name, resource in process_resources.items():
                    process_cost = self.df.loc[
                        year, p.name + "_" + process_name + "_" + resource + "_unit_cost"
                    ]
                    color = self.resource_color_map.get((process_name, resource), None)
                    self.ax.bar(
                        p.name,
                        process_cost,
                        bottom=base,
                        label=f"{process_name}, {resource}",
                        linewidth=0.5,
                        color=color,
                        hatch=self.hatch_map["cost"],
                    )
                    # Taxes et subventions sur ce process/ressource
                    tax_col = p.name + "_" + process_name + "_" + resource + "_unit_tax"
                    tax_val = self.df.loc[year, tax_col] if tax_col in self.df.columns else 0
                    if tax_val != 0:
                        self.ax.bar(
                            p.name,
                            tax_val,
                            bottom=neg_base,
                            linewidth=0.5,
                            color=color,
                            hatch=self.hatch_map["tax"],
                        )
                        process_cost += tax_val
                    subsidy_col = p.name + "_" + process_name + "_" + resource + "_unit_subsidy"
                    subsidy_val = (
                        self.df.loc[year, subsidy_col] if subsidy_col in self.df.columns else 0
                    )
                    if subsidy_val != 0:
                        self.ax.bar(
                            p.name,
                            -subsidy_val,
                            bottom=base + process_cost,
                            linewidth=0.5,
                            color=color,
                            hatch=self.hatch_map["subsidy"],
                        )

                    base += process_cost
                    neg_base = -subsidy_val

                # Coût sans ressource pour chaque process
                for process_name in process_resources.keys():
                    process_cost = self.df.loc[
                        year, p.name + "_" + process_name + "_without_resources_unit_cost"
                    ]
                    color = self.resource_color_map.get(
                        (process_name, "without_resources_unit_cost"), None
                    )
                    self.ax.bar(
                        p.name,
                        process_cost,
                        bottom=base,
                        label=f"{process_name}, excluding resource",
                        linewidth=0.5,
                        color=color,
                        hatch=self.hatch_map["cost"],
                    )
                    # Taxes et subventions sur ce process sans ressource
                    tax_col = p.name + "_" + process_name + "_without_resources_unit_tax"
                    tax_val = self.df.loc[year, tax_col] if tax_col in self.df.columns else 0
                    if tax_val != 0:
                        self.ax.bar(
                            p.name,
                            tax_val,
                            bottom=base + process_cost,
                            linewidth=0.5,
                            color=color,
                            hatch=self.hatch_map["tax"],
                        )
                        process_cost += tax_val
                    subsidy_col = p.name + "_" + process_name + "_without_resources_unit_subsidy"
                    subsidy_val = (
                        self.df.loc[year, subsidy_col] if subsidy_col in self.df.columns else 0
                    )
                    if subsidy_val != 0:
                        self.ax.bar(
                            p.name,
                            -subsidy_val,
                            bottom=neg_base,
                            linewidth=0.5,
                            color=color,
                            hatch=self.hatch_map["subsidy"],
                        )
                        # process_cost ne change pas car subvention négative
                    base += process_cost
                    neg_base = -subsidy_val

                # Ajout de la carbon tax (par filière uniquement)
                carbon_tax_col = f"{p.name}_unit_carbon_tax"
                carbon_tax_val = (
                    self.df.loc[year, carbon_tax_col] if carbon_tax_col in self.df.columns else 0
                )
                if carbon_tax_val != 0:
                    self.ax.bar(
                        p.name,
                        carbon_tax_val,
                        bottom=base,
                        label="Carbon tax",
                        linewidth=1.5,
                        color="black",
                        alpha=0.3,
                        hatch=self.hatch_map["carbon_tax"],
                    )
                    base += carbon_tax_val

                net_col = f"{p.name}_net_mfsp"
                if net_col in self.df.columns:
                    net_val = self.df.loc[year, net_col]
                    self.ax.bar(
                        p.name,
                        net_val,
                        linewidth=2.5,
                        color="none",
                        edgecolor="black",
                        alpha=0.7,
                        zorder=10,
                        fill=False,
                        hatch=None,
                    )

        # Suppression des doublons dans la légende
        handles, labels = self.ax.get_legend_handles_labels()
        seen = set()
        unique = []
        for han, lbl in zip(handles, labels):
            if lbl not in seen:
                unique.append((han, lbl))
                seen.add(lbl)
        if unique:
            handles, labels = zip(*unique)
            self.ax.legend(handles, labels)
        else:
            self.ax.legend()

        self.ax.grid(axis="y")
        self.ax.set_title("Mean MFSP breakdown for year " + str(year))
        self.ax.set_ylabel("MFSP [€/MJ]")

        self.ax.set_xticks(self.ax.get_xticks())
        self.ax.set_xticklabels(self.ax.get_xticklabels(), rotation=-30, ha="left")

        self.ax.set_ylim(
            self.ax.get_ylim()[0],
            self.ax.get_ylim()[1] * 1.1,
        )

        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        self.fig.tight_layout()
        self.fig.canvas.draw()
