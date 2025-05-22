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
            "subsidy": "xx",
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

        # Prepare data by pathway and component
        components = []
        if gross_expenses:
            components.append("mfsp")
        if other_taxes:
            components.append("tax")
        if carbon_tax:
            components.append("carbon_tax")
        # Do not add "subsidy" here for the main stack

        # Build data matrices [pathway][component][year]
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
            # Positive stack (excluding subsidies) by component (sum over all pathways)
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
            # Negative stack for subsidies (sum over all pathways)
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
            # Non-stacked display: each pathway = color, each component = marker + linestyle
            for i, p in enumerate(pathways):
                for comp in ["mfsp", "tax", "carbon_tax", "subsidy"]:
                    if (
                        (comp == "mfsp" and gross_expenses)
                        or (comp == "tax" and other_taxes)
                        or (comp == "carbon_tax" and carbon_tax)
                        or (comp == "subsidy" and subsidies)
                    ):
                        vals = data_dict[p.name].get(comp, np.zeros(len(self.prospective_years)))
                        # Negative for subsidies
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
            # Net expenses overlay (not stacked)
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

        # Adapted legends
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


class DetailledMFSPBreakdown:
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

        self.resource_color_map = self._create_color_map()
        self.hatch_map = {
            "cost": "",
            "tax": "//",
            "carbon_tax": "..",
            "subsidy": "xx",
        }

        self.fig, self.ax = plt.subplots()
        self.create_plot()
        self.plot_interact()

    def _create_color_map(self):
        # Color mapping for each (process, resource) pair
        pathways = self.pathways_manager.get_all()
        process_resource_pairs = set()
        for p in pathways:
            for resource in p.resources_used:
                process_resource_pairs.add(("main", resource))
            for process_name, resource in p.resources_used_processes.items():
                process_resource_pairs.add((process_name, resource))
            for process_name in p.resources_used_processes.keys():
                process_resource_pairs.add((process_name, "without_resources_unit_cost"))
        process_resource_pairs.add(("main", "mfsp_without_resource"))
        pairs_sorted = sorted(process_resource_pairs)
        cmap = plt.get_cmap("tab20")
        color_map = {pair: cmap(i % 20) for i, pair in enumerate(pairs_sorted)}
        color_map[("main", "mfsp_without_resource")] = (0.7, 0.7, 0.7, 1.0)
        return color_map

    def create_plot(self):
        pass

    def plot_interact(self):
        mode_widget = widgets.ToggleButtons(
            options=[
                ("All pathways for a year", "per_year"),
                ("One pathway over time", "pathway_over_time"),
            ],
            description="Mode:",
            value="per_year",
        )
        year_widget = widgets.IntSlider(
            min=self.prospective_years[0],
            max=self.prospective_years[-1],
            step=1,
            description="Year:",
            value=2035,
        )
        pathway_widget = widgets.Dropdown(
            options=[(p.name, p) for p in self.pathways_manager.get_all()],
            description="Pathway:",
        )

        def _update(mode, year, pathway):
            if mode == "per_year":
                year_widget.layout.display = ""
                pathway_widget.layout.display = "none"
                self.update_per_year(year)
            else:
                year_widget.layout.display = "none"
                pathway_widget.layout.display = ""
                self.update_pathway_over_time(pathway)

        widgets.interact(_update, mode=mode_widget, year=year_widget, pathway=pathway_widget)

    def update_per_year(self, year):
        self.ax.cla()
        pathways = self.pathways_manager.get_all()
        pathway_handles = []

        for p in pathways:
            if not (
                pd.isna(self.df.loc[year, f"{p.name}_energy_consumption"])
                or self.df.loc[year, f"{p.name}_energy_consumption"] < 1e-9
            ):
                color = self.resource_color_map.get(("main", "mfsp_without_resource"), "grey")
                mfsp_col = p.name + "_mfsp_without_resource"
                mfsp_val = self.df.loc[year, mfsp_col] if mfsp_col in self.df.columns else 0
                if mfsp_val != 0:
                    self.ax.bar(
                        p.name,
                        mfsp_val,
                        linewidth=0.5,
                        edgecolor="black",
                        color=color,
                        hatch=self.hatch_map["cost"],
                    )
                    base = self.df.loc[year, mfsp_col]
                else:
                    base = 0

                # Taxes and subsidies on the base
                tax_col = p.name + "_unit_tax_without_resource"
                tax_val = self.df.loc[year, tax_col] if tax_col in self.df.columns else 0
                if tax_val != 0:
                    self.ax.bar(
                        p.name,
                        tax_val,
                        bottom=base,
                        linewidth=0.5,
                        edgecolor="black",
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
                        edgecolor="black",
                        color=color,
                        hatch=self.hatch_map["subsidy"],
                    )

                neg_base = -subsidy_val
                if mfsp_val != 0 or subsidy_val != 0 or tax_val != 0:
                    pathway_handles.append(
                        Patch(facecolor=color, edgecolor="black", label="Base, excluding resource")
                    )

                # Pathway-specific resources
                for resource in p.resources_used:
                    color = self.resource_color_map.get(("main", resource), None)
                    cost_col = p.name + "_excluding_processes_" + resource + "_unit_cost"
                    cost_val = self.df.loc[year, cost_col] if cost_col in self.df.columns else 0
                    if cost_val != 0:
                        self.ax.bar(
                            p.name,
                            cost_val,
                            bottom=base,
                            linewidth=0.5,
                            edgecolor="black",
                            color=color,
                            hatch=self.hatch_map["cost"],
                        )
                    base += cost_val
                    # Taxes and subsidies on the resource
                    tax_col = p.name + "_excluding_processes_" + resource + "_unit_tax"
                    tax_val = self.df.loc[year, tax_col] if tax_col in self.df.columns else 0
                    if tax_val != 0:
                        self.ax.bar(
                            p.name,
                            tax_val,
                            bottom=base,
                            linewidth=0.5,
                            edgecolor="black",
                            color=color,
                            hatch=self.hatch_map["tax"],
                        )
                        base += tax_val
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
                            edgecolor="black",
                            color=color,
                            hatch=self.hatch_map["subsidy"],
                        )
                    neg_base = -subsidy_val
                    if cost_val != 0 or tax_val != 0 or subsidy_val != 0:
                        pathway_handles.append(
                            Patch(
                                facecolor=color,
                                edgecolor="black",
                                label=f"Base - {resource}",
                            )
                        )

                # Resources used by each process
                process_resources = p.resources_used_processes
                for process_name, resource in process_resources.items():
                    color = self.resource_color_map.get((process_name, resource), None)
                    cost_col = p.name + "_" + process_name + "_" + resource + "_unit_cost"
                    cost_val = self.df.loc[year, cost_col] if cost_col in self.df.columns else 0
                    if cost_val != 0:
                        self.ax.bar(
                            p.name,
                            cost_val,
                            bottom=base,
                            linewidth=0.5,
                            edgecolor="black",
                            color=color,
                            hatch=self.hatch_map["cost"],
                        )
                    base += cost_val
                    # Taxes and subsidies on this process/resource
                    tax_col = p.name + "_" + process_name + "_" + resource + "_unit_tax"
                    tax_val = self.df.loc[year, tax_col] if tax_col in self.df.columns else 0
                    if tax_val != 0:
                        self.ax.bar(
                            p.name,
                            tax_val,
                            bottom=base,
                            linewidth=0.5,
                            edgecolor="black",
                            color=color,
                            hatch=self.hatch_map["tax"],
                        )
                        base += tax_val
                    subsidy_col = p.name + "_" + process_name + "_" + resource + "_unit_subsidy"
                    subsidy_val = (
                        self.df.loc[year, subsidy_col] if subsidy_col in self.df.columns else 0
                    )
                    if subsidy_val != 0:
                        self.ax.bar(
                            p.name,
                            -subsidy_val,
                            bottom=neg_base,
                            linewidth=0.5,
                            edgecolor="black",
                            color=color,
                            hatch=self.hatch_map["subsidy"],
                        )
                    neg_base = -subsidy_val
                    if cost_val != 0 or tax_val != 0 or subsidy_val != 0:
                        pathway_handles.append(
                            Patch(
                                facecolor=color,
                                edgecolor="black",
                                label=f"{process_name}, {resource}",
                            )
                        )

                # Cost without resource for each process
                for process_name in process_resources.keys():
                    color = self.resource_color_map.get(
                        (process_name, "without_resources_unit_cost"), None
                    )
                    cost_col = p.name + "_" + process_name + "_without_resources_unit_cost"
                    cost_val = self.df.loc[year, cost_col] if cost_col in self.df.columns else 0
                    if cost_val != 0:
                        self.ax.bar(
                            p.name,
                            cost_val,
                            bottom=base,
                            linewidth=0.5,
                            edgecolor="black",
                            color=color,
                            hatch=self.hatch_map["cost"],
                        )
                    base += cost_val
                    # Taxes and subsidies on this process without resource
                    tax_col = p.name + "_" + process_name + "_without_resources_unit_tax"
                    tax_val = self.df.loc[year, tax_col] if tax_col in self.df.columns else 0
                    if tax_val != 0:
                        self.ax.bar(
                            p.name,
                            tax_val,
                            bottom=base,
                            linewidth=0.5,
                            edgecolor="black",
                            color=color,
                            hatch=self.hatch_map["tax"],
                        )
                        base += tax_val
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
                            edgecolor="black",
                            color=color,
                            hatch=self.hatch_map["subsidy"],
                        )
                    neg_base = -subsidy_val
                    if cost_val != 0 or tax_val != 0 or subsidy_val != 0:
                        pathway_handles.append(
                            Patch(
                                facecolor=color,
                                edgecolor="black",
                                label=f"{process_name}, excluding resource",
                            )
                        )

                # Add carbon tax (per pathway only)
                carbon_tax_col = f"{p.name}_unit_carbon_tax"
                carbon_tax_val = (
                    self.df.loc[year, carbon_tax_col] if carbon_tax_col in self.df.columns else 0
                )
                if carbon_tax_val != 0:
                    self.ax.bar(
                        p.name,
                        carbon_tax_val,
                        bottom=base,
                        edgecolor="black",
                        linewidth=0.5,
                        color="none",
                        hatch=self.hatch_map["carbon_tax"],
                    )
                    base += carbon_tax_val

                net_col = f"{p.name}_net_mfsp"
                if net_col in self.df.columns:
                    net_val = self.df.loc[year, net_col]
                    self.ax.bar(
                        p.name,
                        net_val,
                        linewidth=2,
                        color="none",
                        edgecolor="black",
                        alpha=0.7,
                        zorder=2,
                        fill=False,
                        hatch=None,
                    )

        # Unique handles for legend
        unique_labels = set()
        unique_pathway_handles = []
        for handle in pathway_handles:
            if handle.get_label() not in unique_labels:
                unique_pathway_handles.append(handle)
                unique_labels.add(handle.get_label())
        pathway_handles = unique_pathway_handles

        bar_type_handles = [
            Patch(facecolor="none", edgecolor="black", hatch=self.hatch_map["cost"], label="MFSP"),
            Patch(facecolor="none", edgecolor="black", hatch=self.hatch_map["tax"], label="Tax"),
            Patch(
                facecolor="none",
                edgecolor="black",
                hatch=self.hatch_map["subsidy"],
                label="Subsidy",
            ),
            Patch(
                facecolor="none",
                edgecolor="black",
                hatch=self.hatch_map["carbon_tax"],
                label="Carbon tax",
            ),
            Patch(facecolor="none", edgecolor="black", linewidth=2, label="Net MFSP"),
        ]

        legend1 = self.ax.legend(
            handles=pathway_handles,
            title="Pathways",
            loc="upper left",
            prop={"size": 8},
        )
        legend2 = self.ax.legend(
            handles=bar_type_handles,
            title="Bar types",
            loc="upper right",
            prop={"size": 8},
        )
        self.ax.add_artist(legend1)
        self.ax.add_artist(legend2)

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

    def update_pathway_over_time(self, pathway):
        self.ax.cla()
        years = self.prospective_years
        p = pathway

        energy_col = f"{p.name}_energy_consumption"
        if energy_col not in self.df.columns:
            return

        active_mask = (self.df.loc[years, energy_col] >= 1e-9) & (
            ~self.df.loc[years, energy_col].isna()
        )
        if not active_mask.any():
            return

        years = active_mask[active_mask].index

        base = np.zeros(len(years))
        neg_base = np.zeros(len(years))
        pathway_handles = []

        # Base cost (excluding resource)
        color = self.resource_color_map.get(("main", "mfsp_without_resource"), "grey")
        mfsp_col = p.name + "_mfsp_without_resource"
        mfsp_vals = (
            self.df.loc[years, mfsp_col].fillna(0).values
            if mfsp_col in self.df.columns
            else np.zeros(len(years))
        )
        if np.any(mfsp_vals != 0):
            self.ax.fill_between(
                years,
                base,
                base + mfsp_vals,
                facecolor=color,
                hatch=self.hatch_map["cost"],
                edgecolor="black",
                linewidth=0.5,
                alpha=0.8,
                zorder=2,
            )
            base += mfsp_vals
            pathway_handles.append(
                Patch(facecolor=color, edgecolor="black", label="Base, excluding resource")
            )

        # Taxes on base
        tax_col = p.name + "_unit_tax_without_resource"
        tax_vals = (
            self.df.loc[years, tax_col].fillna(0).values
            if tax_col in self.df.columns
            else np.zeros(len(years))
        )
        if np.any(tax_vals != 0):
            self.ax.fill_between(
                years,
                base,
                base + tax_vals,
                facecolor=color,
                hatch=self.hatch_map["tax"],
                edgecolor="black",
                linewidth=0.5,
                alpha=0.8,
                zorder=2,
            )
            base += tax_vals

        # Subsidy on base
        subsidy_col = p.name + "_unit_subsidy_without_resource"
        subsidy_vals = (
            self.df.loc[years, subsidy_col].fillna(0).values
            if subsidy_col in self.df.columns
            else np.zeros(len(years))
        )
        if np.any(subsidy_vals != 0):
            neg_top = neg_base - subsidy_vals
            color = self.resource_color_map.get(("main", "mfsp_without_resource"), "grey")
            self.ax.fill_between(
                years,
                neg_base,
                neg_top,
                facecolor=color,
                hatch=self.hatch_map["subsidy"],
                edgecolor="black",
                linewidth=0.5,
                alpha=0.8,
                zorder=2,
            )
            neg_base = neg_top

        if np.any(mfsp_vals != 0) or np.any(subsidy_vals != 0) or np.any(tax_vals != 0):
            pathway_handles.append(
                Patch(facecolor=color, edgecolor="black", label="Base, excluding resource")
            )

        # Pathway-specific resources
        for resource in p.resources_used:
            color = self.resource_color_map.get(("main", resource), None)
            cost_col = p.name + "_excluding_processes_" + resource + "_unit_cost"
            cost_vals = (
                self.df.loc[years, cost_col].fillna(0).values
                if cost_col in self.df.columns
                else np.zeros(len(years))
            )
            if np.any(cost_vals != 0):
                self.ax.fill_between(
                    years,
                    base,
                    base + cost_vals,
                    facecolor=color,
                    hatch=self.hatch_map["cost"],
                    edgecolor="black",
                    linewidth=0.5,
                    alpha=0.8,
                    zorder=2,
                )
                base += cost_vals
                pathway_handles.append(
                    Patch(facecolor=color, edgecolor="black", label=f"Base - {resource}")
                )
            tax_col = p.name + "_excluding_processes_" + resource + "_unit_tax"
            tax_vals = (
                self.df.loc[years, tax_col].fillna(0).values
                if tax_col in self.df.columns
                else np.zeros(len(years))
            )
            if np.any(tax_vals != 0):
                self.ax.fill_between(
                    years,
                    base,
                    base + tax_vals,
                    facecolor=color,
                    hatch=self.hatch_map["tax"],
                    edgecolor="black",
                    linewidth=0.5,
                    alpha=0.8,
                    zorder=2,
                )
                base += tax_vals
                # Subsidy on resources

            subsidy_col = p.name + "_excluding_processes_" + resource + "_unit_subsidy"
            subsidy_vals = (
                self.df.loc[years, subsidy_col].fillna(0).values
                if subsidy_col in self.df.columns
                else np.zeros(len(years))
            )
            if np.any(subsidy_vals != 0):
                neg_top = neg_base - subsidy_vals
                self.ax.fill_between(
                    years,
                    neg_base,
                    neg_top,
                    facecolor=color,
                    hatch=self.hatch_map["subsidy"],
                    edgecolor="black",
                    linewidth=0.5,
                    alpha=0.8,
                    zorder=2,
                )
                neg_base = neg_top
            if np.any(cost_vals != 0) or np.any(tax_vals != 0) or np.any(subsidy_vals != 0):
                pathway_handles.append(
                    Patch(facecolor=color, edgecolor="black", label=f"Base - {resource}")
                )

        # Resources used by each process
        process_resources = p.resources_used_processes
        for process_name, resource in process_resources.items():
            color = self.resource_color_map.get((process_name, resource), None)
            cost_col = p.name + "_" + process_name + "_" + resource + "_unit_cost"
            cost_vals = (
                self.df.loc[years, cost_col].fillna(0).values
                if cost_col in self.df.columns
                else np.zeros(len(years))
            )
            if np.any(cost_vals != 0):
                self.ax.fill_between(
                    years,
                    base,
                    base + cost_vals,
                    facecolor=color,
                    hatch=self.hatch_map["cost"],
                    edgecolor="black",
                    linewidth=0.5,
                    alpha=0.8,
                    zorder=2,
                )
                base += cost_vals

            tax_col = p.name + "_" + process_name + "_" + resource + "_unit_tax"
            tax_vals = (
                self.df.loc[years, tax_col].fillna(0).values
                if tax_col in self.df.columns
                else np.zeros(len(years))
            )
            if np.any(tax_vals != 0):
                self.ax.fill_between(
                    years,
                    base,
                    base + tax_vals,
                    facecolor=color,
                    hatch=self.hatch_map["tax"],
                    edgecolor="black",
                    linewidth=0.5,
                    alpha=0.8,
                    zorder=2,
                )
                base += tax_vals
            subsidy_col = p.name + "_" + process_name + "_" + resource + "_unit_subsidy"
            subsidy_vals = (
                self.df.loc[years, subsidy_col].fillna(0).values
                if subsidy_col in self.df.columns
                else np.zeros(len(years))
            )
            if np.any(subsidy_vals != 0):
                neg_top = neg_base - subsidy_vals
                self.ax.fill_between(
                    years,
                    neg_base,
                    neg_top,
                    facecolor=color,
                    hatch=self.hatch_map["subsidy"],
                    edgecolor="black",
                    linewidth=0.5,
                    alpha=0.8,
                    label=f"Subsidy - {process_name}, {resource}",
                    zorder=2,
                )
                neg_base = neg_top
            if np.any(tax_vals != 0) or np.any(subsidy_vals != 0) or np.any(cost_vals != 0):
                pathway_handles.append(
                    Patch(facecolor=color, edgecolor="black", label=f"{process_name}, {resource}")
                )

        # Cost without resource for each process
        for process_name in process_resources.keys():
            color = self.resource_color_map.get((process_name, "without_resources_unit_cost"), None)
            cost_col = p.name + "_" + process_name + "_without_resources_unit_cost"
            cost_vals = (
                self.df.loc[years, cost_col].fillna(0).values
                if cost_col in self.df.columns
                else np.zeros(len(years))
            )
            if np.any(cost_vals != 0):
                self.ax.fill_between(
                    years,
                    base,
                    base + cost_vals,
                    facecolor=color,
                    hatch=self.hatch_map["cost"],
                    edgecolor="black",
                    linewidth=0.5,
                    alpha=0.8,
                    zorder=2,
                )
                base += cost_vals

            tax_col = p.name + "_" + process_name + "_without_resources_unit_tax"
            tax_vals = (
                self.df.loc[years, tax_col].fillna(0).values
                if tax_col in self.df.columns
                else np.zeros(len(years))
            )
            if np.any(tax_vals != 0):
                self.ax.fill_between(
                    years,
                    base,
                    base + tax_vals,
                    facecolor=color,
                    hatch=self.hatch_map["tax"],
                    edgecolor="black",
                    linewidth=0.5,
                    alpha=0.8,
                    zorder=2,
                )
                base += tax_vals

            subsidy_col = p.name + "_" + process_name + "_without_resources_unit_subsidy"
            subsidy_vals = (
                self.df.loc[years, subsidy_col].fillna(0).values
                if subsidy_col in self.df.columns
                else np.zeros(len(years))
            )
            if np.any(subsidy_vals != 0):
                neg_top = neg_base - subsidy_vals
                self.ax.fill_between(
                    years,
                    neg_base,
                    neg_top,
                    facecolor=color,
                    hatch=self.hatch_map["subsidy"],
                    edgecolor="black",
                    linewidth=0.5,
                    alpha=0.8,
                    zorder=2,
                )
                neg_base = neg_top
            if np.any(tax_vals != 0) or np.any(subsidy_vals != 0) or np.any(cost_vals != 0):
                pathway_handles.append(
                    Patch(
                        facecolor=color,
                        edgecolor="black",
                        label=f"{process_name}, excluding resource",
                    )
                )

        # Carbon tax (per pathway only)
        carbon_tax_col = f"{p.name}_unit_carbon_tax"
        carbon_tax_vals = (
            self.df.loc[years, carbon_tax_col].fillna(0).values
            if carbon_tax_col in self.df.columns
            else np.zeros(len(years))
        )
        if np.any(carbon_tax_vals != 0):
            self.ax.fill_between(
                years,
                base,
                base + carbon_tax_vals,
                facecolor="none",
                hatch=self.hatch_map["carbon_tax"],
                edgecolor="black",
                linewidth=0.5,
                alpha=0.8,
                zorder=2,
            )
            base += carbon_tax_vals

        # Net MFSP overlay
        net_col = f"{p.name}_net_mfsp"
        if net_col in self.df.columns:
            net_vals = self.df.loc[years, net_col].fillna(0).values
            if np.any(net_vals != 0):
                self.ax.plot(
                    years,
                    net_vals,
                    color="black",
                    linewidth=2,
                    alpha=0.7,
                    zorder=2,
                    label="Net MFSP",
                )

        # Remove duplicate labels in legend
        seen = set()
        unique_pathway_handles = []
        for h in pathway_handles:
            if h.get_label() not in seen and h.get_label() is not None:
                unique_pathway_handles.append(h)
                seen.add(h.get_label())

        bar_type_handles = [
            Patch(facecolor="none", edgecolor="black", hatch=self.hatch_map["cost"], label="Cost"),
            Patch(facecolor="none", edgecolor="black", hatch=self.hatch_map["tax"], label="Tax"),
            Patch(
                facecolor="none",
                edgecolor="black",
                hatch=self.hatch_map["subsidy"],
                label="Subsidy",
            ),
            Patch(
                facecolor="none",
                edgecolor="black",
                hatch=self.hatch_map["carbon_tax"],
                label="Carbon tax",
            ),
            Line2D([0], [0], color="black", linewidth=2, label="Net MFSP"),
        ]

        legend1 = self.ax.legend(
            handles=unique_pathway_handles,
            title="Components",
            loc="upper left",
            prop={"size": 8},
        )
        legend2 = self.ax.legend(
            handles=bar_type_handles,
            title="Bar types",
            loc="upper right",
            prop={"size": 8},
        )
        self.ax.add_artist(legend1)
        self.ax.add_artist(legend2)

        self.ax.grid(axis="y")
        self.ax.set_title(f"MFSP breakdown over time for {p.name}")
        self.ax.set_ylabel("MFSP [€/MJ]")
        self.ax.set_xlabel("Year")
        self.ax.set_xlim(self.prospective_years[0], self.prospective_years[-1])
        self.ax.set_ylim(
            self.ax.get_ylim()[0],
            self.ax.get_ylim()[1] * 1.1,
        )

        # self.ax.set_xticklabels(years, rotation=-30, ha="left")
        self.fig.tight_layout()
        self.fig.canvas.draw()
