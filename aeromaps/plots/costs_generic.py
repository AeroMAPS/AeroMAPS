import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from ipywidgets import interact, widgets


class ScenarioEnergyCapitalPlot:
    def __init__(self, process):
        data = process.data
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]
        self.pathways_manager = process.pathways_manager

        self.fig, self.ax = plt.subplots(
            figsize=(12, 7),
        )

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

        interact(
            self.update,
            pathway_selected=pathway_widget,
            detail_level_selected=detail_level,
        )

    def create_plot(self):
        pass

    def update(
        self,
        pathway_selected,
        detail_level_selected,
    ):
        self.ax.cla()

        pathways = self.pathways_manager.get_all()

        def first_usage_year(p):
            energy_col = f"{p.name}_energy_consumption"
            if energy_col not in self.df.columns:
                return max(self.prospective_years) + 1
            series = self.df.loc[self.prospective_years, energy_col]
            valid_years = series[~(series.isna() | (series == 0.0))].index.tolist()
            return min(valid_years) if valid_years else max(self.prospective_years) + 1

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

        # --- MODE STACKED_PATHWAYS ---
        if detail_level_selected == "stacked_pathways":
            bottom = np.zeros(len(self.prospective_years))
            for i, p in enumerate(pathways):
                # core capex
                col = f"{p.name}_capex_cost"
                vals = (
                    self.df.loc[self.prospective_years, col].fillna(0).values
                    if col in self.df.columns
                    else np.zeros(len(self.prospective_years))
                )
                top = bottom + vals
                self.ax.fill_between(
                    self.prospective_years,
                    bottom,
                    top,
                    facecolor=pathway_colors[p.name],
                    edgecolor="black",
                    linewidth=0.5,
                    alpha=0.5,
                    linestyle=":",
                    label=p.name,
                )
                bottom = top

                # associated process_capex
                for process_name in p.resources_used_processes.keys():
                    col_proc = f"{p.name}_{process_name}_capex_cost"
                    vals = (
                        self.df.loc[self.prospective_years, col_proc].fillna(0).values
                        if col_proc in self.df.columns
                        else np.zeros(len(self.prospective_years))
                    )
                    top = bottom + vals
                    self.ax.fill_between(
                        self.prospective_years,
                        bottom,
                        top,
                        facecolor=pathway_colors[p.name],
                        edgecolor="black",
                        linewidth=0.5,
                        alpha=0.5,
                        linestyle=":",
                        label=f"{p.name} - {process_name}",
                    )
                    bottom = top

        elif detail_level_selected == "overview":
            bottom = np.zeros(len(self.prospective_years))
            vals = np.zeros(len(self.prospective_years))
            for i, p in enumerate(pathways):
                # core capex
                col = f"{p.name}_capex_cost"
                vals += (
                    self.df.loc[self.prospective_years, col].fillna(0).values
                    if col in self.df.columns
                    else 0
                )

                # associated process_capex
                for process_name in p.resources_used_processes.keys():
                    col_proc = f"{p.name}_{process_name}_capex_cost"
                    vals += (
                        self.df.loc[self.prospective_years, col_proc].fillna(0).values
                        if col_proc in self.df.columns
                        else 0
                    )

            top = bottom + vals
            self.ax.fill_between(
                self.prospective_years,
                bottom,
                top,
                facecolor="grey",
                edgecolor="black",
                linewidth=0.5,
                alpha=0.5,
                label="Total capital expenses",
            )

        elif detail_level_selected == "line_pathways":
            for i, p in enumerate(pathways):
                # core capex
                col = f"{p.name}_capex_cost"
                vals = (
                    self.df.loc[self.prospective_years, col].fillna(0).values
                    if col in self.df.columns
                    else np.zeros(len(self.prospective_years))
                )
                self.ax.plot(
                    self.prospective_years,
                    vals,
                    color=pathway_colors[p.name],
                    linewidth=1.5,
                    alpha=0.5,
                    label=p.name,
                )
                # associated process_capex
                for process_name in p.resources_used_processes.keys():
                    col_proc = f"{p.name}_{process_name}_capex_cost"
                    vals = (
                        self.df.loc[self.prospective_years, col_proc].fillna(0).values
                        if col_proc in self.df.columns
                        else np.zeros(len(self.prospective_years))
                    )
                    self.ax.plot(
                        self.prospective_years,
                        vals,
                        color=pathway_colors[p.name],
                        linewidth=1.5,
                        alpha=0.5,
                        label=f"{p.name} - {process_name}",
                    )

        # Légende adaptée avec mention bottom-up
        handles, labels = self.ax.get_legend_handles_labels()
        seen = set()
        new_handles = []
        new_labels = []
        for ha, la in zip(handles, labels):
            if la not in seen and la is not None:
                new_handles.append(ha)
                new_labels.append(la)
                seen.add(la)
        # Ajout de la mention bottom-up
        self.ax.legend(new_handles, new_labels, loc="upper right")
        self.ax.grid(axis="x")
        self.ax.set_title("Annual capital expenses (bottom-up pathways only)")
        self.ax.set_ylabel("Capital expenses [M€]")
        self.ax.set_xlim(2020, self.years[-1])
        self.ax.set_ylim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()


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
            figsize=(12, 7),
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
                    self.df.loc[self.prospective_years, f"{p.name}_mean_mfsp"].fillna(0).values
                    * self.df.loc[self.prospective_years, f"{p.name}_energy_consumption"]
                    .fillna(0)
                    .values
                    / 1e6
                )
            if "tax" in components:
                data_dict[p.name]["tax"] = (
                    self.df.loc[self.prospective_years, f"{p.name}_mean_unit_tax"].fillna(0).values
                    * self.df.loc[self.prospective_years, f"{p.name}_energy_consumption"]
                    .fillna(0)
                    .values
                    / 1e6
                )
            if "carbon_tax" in components:
                data_dict[p.name]["carbon_tax"] = (
                    self.df.loc[self.prospective_years, f"{p.name}_mean_unit_carbon_tax"]
                    .fillna(0)
                    .values
                    * self.df.loc[self.prospective_years, f"{p.name}_energy_consumption"]
                    .fillna(0)
                    .values
                    / 1e6
                )
            if subsidies:
                data_dict[p.name]["subsidy"] = (
                    self.df.loc[self.prospective_years, f"{p.name}_mean_unit_subsidy"]
                    .fillna(0)
                    .values
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
        if detail_level_selected == "line_pathways":
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
            if detail_level_selected == "stacked_pathways":
                pathway_legend_handles = [
                    Patch(
                        facecolor=pathway_colors[p.name], edgecolor="black", label=p.name, alpha=0.5
                    )
                    for p in pathways
                ]
            else:
                pathway_legend_handles = [
                    Patch(
                        facecolor="grey",
                        edgecolor="black",
                        label="All pathways selected",
                        alpha=0.5,
                    )
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
        self.ax.set_title("Annual energy expenses")
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

        self.fig, self.ax = plt.subplots(
            figsize=(10, 7),
        )
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
        process_resource_pairs.add(("main", "mean_mfsp_without_resource"))
        pairs_sorted = sorted(process_resource_pairs)
        cmap = plt.get_cmap("tab20b")
        color_map = {pair: cmap(i % 20) for i, pair in enumerate(pairs_sorted)}
        return color_map

    @staticmethod
    def _is_nonzero_or_notnan(*args):
        """Check if any of the arguments is non-zero or not null. TODO generalize this for the whole project."""
        return any(
            (v is not None and not (isinstance(v, float) and np.isnan(v)) and v != 0) for v in args
        )

    def create_plot(self):
        pass

    def plot_interact(self):
        mode_widget = widgets.ToggleButtons(
            options=[
                ("All pathways - 1 year", "per_year"),
                ("1 pathway", "pathway_over_time"),
            ],
            description="Visualisation mode:",
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
        show_used_widget = widgets.ToggleButtons(
            options=[
                ("Used pathways only", True),
                ("All pathways defined", False),
            ],
            description="Display option:",
            value=True,
        )

        show_vintage_mean_widget = widgets.ToggleButtons(
            options=[
                ("EIS vintage values (V)", "vintage"),
                ("Mean values (M)", "mean"),
            ],
            description="Value displayed for bottom-up pathways:",
            value="mean",
        )

        def _update(mode, year, pathway, show_only_used, show_vintage_mean):
            self.show_only_used = show_only_used
            self.show_vintage_mean = show_vintage_mean
            if mode == "per_year":
                year_widget.layout.display = ""
                pathway_widget.layout.display = "none"
                self.update_per_year(year)
            else:
                year_widget.layout.display = "none"
                pathway_widget.layout.display = ""
                self.update_pathway_over_time(pathway)

        widgets.interact(
            _update,
            mode=mode_widget,
            year=year_widget,
            pathway=pathway_widget,
            show_only_used=show_used_widget,
            show_vintage_mean=show_vintage_mean_widget,
        )

    def update_per_year(self, year):
        self.ax.cla()
        pathways = self.pathways_manager.get_all()
        pathway_handles = []

        # Split pathways into used and unused
        used_pathways = []
        unused_pathways = []
        for p in pathways:
            is_used = not (
                pd.isna(self.df.loc[year, f"{p.name}_energy_consumption"])
                or self.df.loc[year, f"{p.name}_energy_consumption"] < 1e-9
            )
            if is_used:
                used_pathways.append(p)
            else:
                unused_pathways.append(p)

        if self.show_only_used:
            display_pathways = used_pathways
            unused_pathways = []
        else:
            display_pathways = used_pathways + unused_pathways

        for p in display_pathways:
            if p.cost_model == "top-down":
                is_used = p in used_pathways
                alpha = 1.0 if is_used else 0.3
                color = self.resource_color_map.get(("main", "mean_mfsp_without_resource"), "grey")
                mfsp_col = p.name + "_mean_mfsp_without_resource"
                mfsp_val = self.df.loc[year, mfsp_col] if mfsp_col in self.df.columns else 0
                if self._is_nonzero_or_notnan(mfsp_val):
                    self.ax.bar(
                        p.name,
                        mfsp_val,
                        linewidth=0.5,
                        edgecolor="black",
                        color=color,
                        hatch=self.hatch_map["cost"],
                        alpha=alpha,
                    )
                    base = self.df.loc[year, mfsp_col]
                else:
                    base = 0

                # Taxes and subsidies on the base
                tax_col = p.name + "_mean_unit_tax_without_resource"
                tax_val = self.df.loc[year, tax_col] if tax_col in self.df.columns else 0
                if self._is_nonzero_or_notnan(tax_val):
                    self.ax.bar(
                        p.name,
                        tax_val,
                        bottom=base,
                        linewidth=0.5,
                        edgecolor="black",
                        color=color,
                        hatch=self.hatch_map["tax"],
                        alpha=alpha,
                    )
                    base += tax_val

                subsidy_col = p.name + "_mean_unit_subsidy_without_resource"
                subsidy_val = (
                    self.df.loc[year, subsidy_col] if subsidy_col in self.df.columns else 0
                )
                if self._is_nonzero_or_notnan(subsidy_val):
                    self.ax.bar(
                        p.name,
                        -subsidy_val,
                        bottom=0,
                        linewidth=0.5,
                        edgecolor="black",
                        color=color,
                        hatch=self.hatch_map["subsidy"],
                        alpha=alpha,
                    )

                neg_base = -subsidy_val
                if self._is_nonzero_or_notnan(mfsp_val, tax_val, subsidy_val):
                    pathway_handles.append(
                        Patch(
                            facecolor=color,
                            edgecolor="black",
                            label="Pathway base",
                            alpha=0.8,
                            hatch=self.hatch_map["cost"],
                        )
                    )

                # Pathway-specific resources
                for resource in p.resources_used:
                    color = self.resource_color_map.get(("main", resource), None)
                    cost_col = p.name + "_excluding_processes_" + resource + "_mean_unit_cost"
                    cost_val = self.df.loc[year, cost_col] if cost_col in self.df.columns else 0
                    if self._is_nonzero_or_notnan(cost_val):
                        self.ax.bar(
                            p.name,
                            cost_val,
                            bottom=base,
                            linewidth=0.5,
                            edgecolor="black",
                            color=color,
                            hatch=self.hatch_map["cost"],
                            alpha=alpha,
                        )
                    base += cost_val
                    # Taxes and subsidies on the resource
                    tax_col = p.name + "_excluding_processes_" + resource + "_mean_unit_tax"
                    tax_val = self.df.loc[year, tax_col] if tax_col in self.df.columns else 0
                    if self._is_nonzero_or_notnan(tax_val):
                        self.ax.bar(
                            p.name,
                            tax_val,
                            bottom=base,
                            linewidth=0.5,
                            edgecolor="black",
                            color=color,
                            hatch=self.hatch_map["tax"],
                            alpha=alpha,
                        )
                        base += tax_val
                    subsidy_col = p.name + "_excluding_processes_" + resource + "_mean_unit_subsidy"
                    subsidy_val = (
                        self.df.loc[year, subsidy_col] if subsidy_col in self.df.columns else 0
                    )
                    if self._is_nonzero_or_notnan(subsidy_val):
                        self.ax.bar(
                            p.name,
                            -subsidy_val,
                            bottom=neg_base,
                            linewidth=0.5,
                            edgecolor="black",
                            color=color,
                            hatch=self.hatch_map["subsidy"],
                            alpha=alpha,
                        )
                    neg_base = -subsidy_val
                    if self._is_nonzero_or_notnan(cost_val, tax_val, subsidy_val):
                        pathway_handles.append(
                            Patch(
                                facecolor=color,
                                edgecolor="black",
                                label=resource,
                                alpha=0.8,
                                hatch=self.hatch_map["cost"],
                            )
                        )

                # Resources used by each process
                process_resources = p.resources_used_processes
                for process_name, resource in process_resources.items():
                    color = self.resource_color_map.get((process_name, resource), None)
                    cost_col = p.name + "_" + process_name + "_" + resource + "_mean_unit_cost"
                    cost_val = self.df.loc[year, cost_col] if cost_col in self.df.columns else 0
                    if self._is_nonzero_or_notnan(cost_val):
                        self.ax.bar(
                            p.name,
                            cost_val,
                            bottom=base,
                            linewidth=0.5,
                            edgecolor="black",
                            color=color,
                            hatch=self.hatch_map["cost"],
                            alpha=alpha,
                        )
                    base += cost_val
                    # Taxes and subsidies on this process/resource
                    tax_col = p.name + "_" + process_name + "_" + resource + "_mean_unit_tax"
                    tax_val = self.df.loc[year, tax_col] if tax_col in self.df.columns else 0
                    if self._is_nonzero_or_notnan(tax_val):
                        self.ax.bar(
                            p.name,
                            tax_val,
                            bottom=base,
                            linewidth=0.5,
                            edgecolor="black",
                            color=color,
                            hatch=self.hatch_map["tax"],
                            alpha=alpha,
                        )
                        base += tax_val
                    subsidy_col = (
                        p.name + "_" + process_name + "_" + resource + "_mean_unit_subsidy"
                    )
                    subsidy_val = (
                        self.df.loc[year, subsidy_col] if subsidy_col in self.df.columns else 0
                    )
                    if self._is_nonzero_or_notnan(subsidy_val):
                        self.ax.bar(
                            p.name,
                            -subsidy_val,
                            bottom=neg_base,
                            linewidth=0.5,
                            edgecolor="black",
                            color=color,
                            hatch=self.hatch_map["subsidy"],
                            alpha=alpha,
                        )
                    neg_base = -subsidy_val
                    if self._is_nonzero_or_notnan(cost_val, tax_val, subsidy_val):
                        pathway_handles.append(
                            Patch(
                                facecolor=color,
                                edgecolor="black",
                                label=f"{process_name}, {resource}",
                                alpha=0.8,
                                hatch=self.hatch_map["cost"],
                            )
                        )

                # Cost without resource for each process
                for process_name in process_resources.keys():
                    color = self.resource_color_map.get(
                        (process_name, "without_resources_unit_cost"), None
                    )
                    cost_col = p.name + "_" + process_name + "_mean_unit_cost_without_resources"
                    cost_val = self.df.loc[year, cost_col] if cost_col in self.df.columns else 0
                    if self._is_nonzero_or_notnan(cost_val):
                        self.ax.bar(
                            p.name,
                            cost_val,
                            bottom=base,
                            linewidth=0.5,
                            edgecolor="black",
                            color=color,
                            hatch=self.hatch_map["cost"],
                            alpha=alpha,
                        )
                    base += cost_val
                    # Taxes and subsidies on this process without resource
                    tax_col = p.name + "_" + process_name + "_mean_unit_tax_without_resources"
                    tax_val = self.df.loc[year, tax_col] if tax_col in self.df.columns else 0
                    if self._is_nonzero_or_notnan(tax_val):
                        self.ax.bar(
                            p.name,
                            tax_val,
                            bottom=base,
                            linewidth=0.5,
                            edgecolor="black",
                            color=color,
                            hatch=self.hatch_map["tax"],
                            alpha=alpha,
                        )
                        base += tax_val
                    subsidy_col = (
                        p.name + "_" + process_name + "_mean_unit_subsidy_without_resources"
                    )
                    subsidy_val = (
                        self.df.loc[year, subsidy_col] if subsidy_col in self.df.columns else 0
                    )
                    if self._is_nonzero_or_notnan(subsidy_val):
                        self.ax.bar(
                            p.name,
                            -subsidy_val,
                            bottom=neg_base,
                            linewidth=0.5,
                            edgecolor="black",
                            color=color,
                            hatch=self.hatch_map["subsidy"],
                            alpha=alpha,
                        )
                    neg_base = -subsidy_val
                    if self._is_nonzero_or_notnan(cost_val, tax_val, subsidy_val):
                        pathway_handles.append(
                            Patch(
                                facecolor=color,
                                edgecolor="black",
                                label=process_name,
                                alpha=0.8,
                                hatch=self.hatch_map["cost"],
                            )
                        )

                # Add carbon tax (per pathway only)
                carbon_tax_col = f"{p.name}_mean_unit_carbon_tax"
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
                        alpha=alpha,
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
                        alpha=alpha,
                        zorder=2,
                        fill=False,
                        hatch=None,
                    )
            elif p.cost_model == "bottom-up" and self.show_vintage_mean == "vintage":
                is_used = p in used_pathways
                alpha = 1.0 if is_used else 0.3
                variable_opex_alpha = 0.8
                fixed_opex_alpha = 0.6

                base = 0
                neg_base = 0

                # Couleurs
                color_capex = self.resource_color_map.get(
                    ("main", "mean_mfsp_without_resource"), "grey"
                )
                color_fixed_opex = color_capex
                color_variable_opex = color_capex

                # Capex vintage
                capex_col = f"{p.name}_vintage_unit_capex"
                capex_val = self.df.loc[year, capex_col] if capex_col in self.df.columns else 0
                if self._is_nonzero_or_notnan(capex_val):
                    self.ax.bar(
                        p.name,
                        capex_val,
                        bottom=base,
                        linewidth=0.5,
                        edgecolor="black",
                        color=color_capex,
                        hatch=self.hatch_map["cost"],
                        alpha=alpha,
                        label=None,
                    )
                    base += capex_val
                    pathway_handles.append(
                        Patch(
                            facecolor=color_capex,
                            edgecolor="black",
                            label="Pathway, Capex (V)",
                            alpha=0.8,
                            hatch=self.hatch_map["cost"],
                        )
                    )

                # Fixed opex vintage
                fixed_opex_col = f"{p.name}_vintage_unit_fixed_opex"
                fixed_opex_val = (
                    self.df.loc[year, fixed_opex_col] if fixed_opex_col in self.df.columns else 0
                )
                if self._is_nonzero_or_notnan(fixed_opex_val):
                    self.ax.bar(
                        p.name,
                        fixed_opex_val,
                        bottom=base,
                        linewidth=0.5,
                        edgecolor="black",
                        color=color_fixed_opex,
                        hatch=self.hatch_map["cost"],
                        alpha=alpha * fixed_opex_alpha,
                        label=None,
                    )
                    base += fixed_opex_val
                    pathway_handles.append(
                        Patch(
                            facecolor=color_fixed_opex,
                            edgecolor="black",
                            label="Pathway, fixed Opex (V)",
                            alpha=0.8 * fixed_opex_alpha,
                            hatch=self.hatch_map["cost"],
                        )
                    )

                # Variable opex vintage
                variable_opex_col = f"{p.name}_vintage_unit_variable_opex"
                variable_opex_val = (
                    self.df.loc[year, variable_opex_col]
                    if variable_opex_col in self.df.columns
                    else 0
                )
                if self._is_nonzero_or_notnan(variable_opex_val):
                    self.ax.bar(
                        p.name,
                        variable_opex_val,
                        bottom=base,
                        linewidth=0.5,
                        edgecolor="black",
                        color=color_variable_opex,
                        hatch=self.hatch_map["cost"],
                        alpha=alpha * variable_opex_alpha,
                        label=None,
                    )
                    base += variable_opex_val
                    pathway_handles.append(
                        Patch(
                            facecolor=color_variable_opex,
                            edgecolor="black",
                            label="Pathway, variable Opex (V)",
                            alpha=0.8 * variable_opex_alpha,
                            hatch=self.hatch_map["cost"],
                        )
                    )

                # Resources vintage
                for resource in p.resources_used:
                    color = self.resource_color_map.get(("main", resource), None)
                    res_col = f"{p.name}_excluding_processes_{resource}_vintage_unit_cost"
                    res_val = self.df.loc[year, res_col] if res_col in self.df.columns else 0
                    if self._is_nonzero_or_notnan(res_val):
                        self.ax.bar(
                            p.name,
                            res_val,
                            bottom=base,
                            linewidth=0.5,
                            edgecolor="black",
                            color=color,
                            hatch=self.hatch_map["cost"],
                            alpha=alpha,
                            label=None,
                        )
                        base += res_val
                        pathway_handles.append(
                            Patch(
                                facecolor=color,
                                edgecolor="black",
                                label=f"Pathway, {resource} (V)",
                                alpha=0.8,
                                hatch=self.hatch_map["cost"],
                            )
                        )

                # Processus vintage
                for process_name, resource in p.resources_used_processes.items():
                    color = self.resource_color_map.get((process_name, resource), None)
                    proc_col = f"{p.name}_{process_name}_{resource}_vintage_unit_cost"
                    proc_val = self.df.loc[year, proc_col] if proc_col in self.df.columns else 0
                    if self._is_nonzero_or_notnan(proc_val):
                        self.ax.bar(
                            p.name,
                            proc_val,
                            bottom=base,
                            linewidth=0.5,
                            edgecolor="black",
                            color=color,
                            hatch=self.hatch_map["cost"],
                            alpha=alpha,
                            label=None,
                        )
                        base += proc_val
                        pathway_handles.append(
                            Patch(
                                facecolor=color,
                                edgecolor="black",
                                label=f"{process_name}, {resource} (V)",
                                alpha=0.8,
                                hatch=self.hatch_map["cost"],
                            )
                        )

                # Capex, opex process vintage (sans Resource)
                for process_name in p.resources_used_processes.keys():
                    color = self.resource_color_map.get(
                        (process_name, "without_resources_unit_cost"), None
                    )
                    capex_col = f"{p.name}_{process_name}_vintage_unit_capex"
                    capex_val = self.df.loc[year, capex_col] if capex_col in self.df.columns else 0
                    if self._is_nonzero_or_notnan(capex_val):
                        self.ax.bar(
                            p.name,
                            capex_val,
                            bottom=base,
                            linewidth=0.5,
                            edgecolor="black",
                            color=color,
                            hatch=self.hatch_map["cost"],
                            alpha=alpha,
                            label=None,
                        )
                        base += capex_val
                        pathway_handles.append(
                            Patch(
                                facecolor=color,
                                edgecolor="black",
                                label=f"{process_name}, Capex (V)",
                                alpha=0.8,
                                hatch=self.hatch_map["cost"],
                            )
                        )
                    fixed_opex_col = f"{p.name}_{process_name}_vintage_unit_fixed_opex"
                    fixed_opex_val = (
                        self.df.loc[year, fixed_opex_col]
                        if fixed_opex_col in self.df.columns
                        else 0
                    )
                    if self._is_nonzero_or_notnan(fixed_opex_val):
                        self.ax.bar(
                            p.name,
                            fixed_opex_val,
                            bottom=base,
                            linewidth=0.5,
                            edgecolor="black",
                            color=color,
                            hatch=self.hatch_map["cost"],
                            alpha=alpha * fixed_opex_alpha,
                            label=None,
                        )
                        base += fixed_opex_val
                        pathway_handles.append(
                            Patch(
                                facecolor=color,
                                edgecolor="black",
                                label=f"{process_name}, fixed Opex (V)",
                                alpha=0.8 * fixed_opex_alpha,
                                hatch=self.hatch_map["cost"],
                            )
                        )
                    variable_opex_col = f"{p.name}_{process_name}_vintage_unit_variable_opex"
                    variable_opex_val = (
                        self.df.loc[year, variable_opex_col]
                        if variable_opex_col in self.df.columns
                        else 0
                    )
                    if self._is_nonzero_or_notnan(variable_opex_val):
                        self.ax.bar(
                            p.name,
                            variable_opex_val,
                            bottom=base,
                            linewidth=0.5,
                            edgecolor="black",
                            color=color,
                            hatch=self.hatch_map["cost"],
                            alpha=alpha * variable_opex_alpha,
                            label=None,
                        )
                        base += variable_opex_val
                        pathway_handles.append(
                            Patch(
                                facecolor=color,
                                edgecolor="black",
                                label=f"{process_name}, variable Opex (V)",
                                alpha=0.8 * variable_opex_alpha,
                                hatch=self.hatch_map["cost"],
                            )
                        )

                # Carbon tax vintage
                carbon_tax_col = f"{p.name}_vintage_eis_carbon_tax"
                carbon_tax_val = (
                    self.df.loc[year, carbon_tax_col] if carbon_tax_col in self.df.columns else 0
                )
                if self._is_nonzero_or_notnan(carbon_tax_val):
                    self.ax.bar(
                        p.name,
                        carbon_tax_val,
                        bottom=base,
                        edgecolor="black",
                        linewidth=0.5,
                        color="none",
                        hatch=self.hatch_map["carbon_tax"],
                        alpha=alpha,
                        label=None,
                    )
                    base += carbon_tax_val

                # Unit taxes and subsidies
                tax_col = f"{p.name}_mean_unit_tax"
                tax_val = self.df.loc[year, tax_col] if tax_col in self.df.columns else 0
                if self._is_nonzero_or_notnan(tax_val):
                    self.ax.bar(
                        p.name,
                        tax_val,
                        bottom=base,
                        linewidth=0.5,
                        edgecolor="black",
                        color="none",
                        hatch=self.hatch_map["tax"],
                        alpha=alpha,
                        label=None,
                    )
                    base += tax_val

                subsidy_col = f"{p.name}_mean_unit_subsidy"
                subsidy_val = (
                    self.df.loc[year, subsidy_col] if subsidy_col in self.df.columns else 0
                )
                if self._is_nonzero_or_notnan(subsidy_val):
                    self.ax.bar(
                        p.name,
                        -subsidy_val,
                        bottom=neg_base,
                        linewidth=0.5,
                        edgecolor="black",
                        color="none",
                        hatch=self.hatch_map["subsidy"],
                        alpha=alpha,
                        label=None,
                    )

                # Net MFSP overlay
                net_col = f"{p.name}_net_mfsp"
                if net_col in self.df.columns:
                    net_val = self.df.loc[year, net_col]
                    self.ax.bar(
                        p.name,
                        net_val,
                        linewidth=2,
                        color="none",
                        edgecolor="black",
                        alpha=alpha,
                        zorder=2,
                        fill=False,
                        hatch=None,
                    )
            elif p.cost_model == "bottom-up" and self.show_vintage_mean == "mean":
                is_used = p in used_pathways
                alpha = 1.0 if is_used else 0.3
                variable_opex_alpha = 0.8
                fixed_opex_alpha = 0.6

                base = 0
                neg_base = 0

                # Couleurs
                color_capex = self.resource_color_map.get(
                    ("main", "mean_mfsp_without_resource"), "grey"
                )
                color_fixed_opex = color_capex
                color_variable_opex = color_capex

                # Capex mean
                capex_col = f"{p.name}_mean_unit_capex"
                capex_val = self.df.loc[year, capex_col] if capex_col in self.df.columns else 0
                if self._is_nonzero_or_notnan(capex_val):
                    self.ax.bar(
                        p.name,
                        capex_val,
                        bottom=base,
                        linewidth=0.5,
                        edgecolor="black",
                        color=color_capex,
                        hatch=self.hatch_map["cost"],
                        alpha=alpha,
                        label=None,
                    )
                    base += capex_val
                    pathway_handles.append(
                        Patch(
                            facecolor=color_capex,
                            edgecolor="black",
                            label="Pathway, Capex (M)",
                            alpha=0.8,
                            hatch=self.hatch_map["cost"],
                        )
                    )

                # Fixed opex mean
                fixed_opex_col = f"{p.name}_mean_unit_fixed_opex"
                fixed_opex_val = (
                    self.df.loc[year, fixed_opex_col] if fixed_opex_col in self.df.columns else 0
                )
                if self._is_nonzero_or_notnan(fixed_opex_val):
                    self.ax.bar(
                        p.name,
                        fixed_opex_val,
                        bottom=base,
                        linewidth=0.5,
                        edgecolor="black",
                        color=color_fixed_opex,
                        hatch=self.hatch_map["cost"],
                        alpha=alpha * fixed_opex_alpha,
                        label=None,
                    )
                    base += fixed_opex_val
                    pathway_handles.append(
                        Patch(
                            facecolor=color_fixed_opex,
                            edgecolor="black",
                            label="Pathway, fixed Opex (M)",
                            alpha=0.8 * fixed_opex_alpha,
                            hatch=self.hatch_map["cost"],
                        )
                    )

                # Variable opex mean
                variable_opex_col = f"{p.name}_mean_unit_variable_opex"
                variable_opex_val = (
                    self.df.loc[year, variable_opex_col]
                    if variable_opex_col in self.df.columns
                    else 0
                )
                if self._is_nonzero_or_notnan(variable_opex_val):
                    self.ax.bar(
                        p.name,
                        variable_opex_val,
                        bottom=base,
                        linewidth=0.5,
                        edgecolor="black",
                        color=color_variable_opex,
                        hatch=self.hatch_map["cost"],
                        alpha=alpha * variable_opex_alpha,
                        label=None,
                    )
                    base += variable_opex_val
                    pathway_handles.append(
                        Patch(
                            facecolor=color_variable_opex,
                            edgecolor="black",
                            label="Pathway, variable Opex (M)",
                            alpha=0.8 * variable_opex_alpha,
                            hatch=self.hatch_map["cost"],
                        )
                    )

                # Resources mean
                for resource in p.resources_used:
                    color = self.resource_color_map.get(("main", resource), None)
                    res_col = f"{p.name}_excluding_processes_{resource}_mean_unit_cost"
                    res_val = self.df.loc[year, res_col] if res_col in self.df.columns else 0
                    if self._is_nonzero_or_notnan(res_val):
                        self.ax.bar(
                            p.name,
                            res_val,
                            bottom=base,
                            linewidth=0.5,
                            edgecolor="black",
                            color=color,
                            hatch=self.hatch_map["cost"],
                            alpha=alpha,
                            label=None,
                        )
                        base += res_val
                        pathway_handles.append(
                            Patch(
                                facecolor=color,
                                edgecolor="black",
                                label=f"Pathway, {resource} (M)",
                                alpha=0.8,
                                hatch=self.hatch_map["cost"],
                            )
                        )

                # Processus mean
                for process_name, resource in p.resources_used_processes.items():
                    color = self.resource_color_map.get((process_name, resource), None)
                    proc_col = f"{p.name}_{process_name}_{resource}_mean_unit_cost"
                    proc_val = self.df.loc[year, proc_col] if proc_col in self.df.columns else 0
                    if self._is_nonzero_or_notnan(proc_val):
                        self.ax.bar(
                            p.name,
                            proc_val,
                            bottom=base,
                            linewidth=0.5,
                            edgecolor="black",
                            color=color,
                            hatch=self.hatch_map["cost"],
                            alpha=alpha,
                            label=None,
                        )
                        base += proc_val
                        pathway_handles.append(
                            Patch(
                                facecolor=color,
                                edgecolor="black",
                                label=f"{process_name}, {resource} (M)",
                                alpha=0.8,
                                hatch=self.hatch_map["cost"],
                            )
                        )

                # Capex, opex process mean
                for process_name in p.resources_used_processes.keys():
                    color = self.resource_color_map.get(
                        (process_name, "without_resources_unit_cost"), None
                    )
                    capex_col = f"{p.name}_{process_name}_mean_unit_capex"
                    capex_val = self.df.loc[year, capex_col] if capex_col in self.df.columns else 0
                    if self._is_nonzero_or_notnan(capex_val):
                        self.ax.bar(
                            p.name,
                            capex_val,
                            bottom=base,
                            linewidth=0.5,
                            edgecolor="black",
                            color=color,
                            hatch=self.hatch_map["cost"],
                            alpha=alpha,
                            label=None,
                        )
                        base += capex_val
                        pathway_handles.append(
                            Patch(
                                facecolor=color,
                                edgecolor="black",
                                label=f"{process_name}, Capex (M)",
                                alpha=0.8,
                                hatch=self.hatch_map["cost"],
                            )
                        )
                    fixed_opex_col = f"{p.name}_{process_name}_mean_unit_fixed_opex"
                    fixed_opex_val = (
                        self.df.loc[year, fixed_opex_col]
                        if fixed_opex_col in self.df.columns
                        else 0
                    )
                    if self._is_nonzero_or_notnan(fixed_opex_val):
                        self.ax.bar(
                            p.name,
                            fixed_opex_val,
                            bottom=base,
                            linewidth=0.5,
                            edgecolor="black",
                            color=color,
                            hatch=self.hatch_map["cost"],
                            alpha=alpha * fixed_opex_alpha,
                            label=None,
                        )
                        base += fixed_opex_val
                        pathway_handles.append(
                            Patch(
                                facecolor=color,
                                edgecolor="black",
                                label=f"{process_name}, fixed Opex (M)",
                                alpha=0.8 * fixed_opex_alpha,
                                hatch=self.hatch_map["cost"],
                            )
                        )
                    variable_opex_col = f"{p.name}_{process_name}_mean_unit_variable_opex"
                    variable_opex_val = (
                        self.df.loc[year, variable_opex_col]
                        if variable_opex_col in self.df.columns
                        else 0
                    )
                    if self._is_nonzero_or_notnan(variable_opex_val):
                        self.ax.bar(
                            p.name,
                            variable_opex_val,
                            bottom=base,
                            linewidth=0.5,
                            edgecolor="black",
                            color=color,
                            hatch=self.hatch_map["cost"],
                            alpha=alpha * variable_opex_alpha,
                            label=None,
                        )
                        base += variable_opex_val
                        pathway_handles.append(
                            Patch(
                                facecolor=color,
                                edgecolor="black",
                                label=f"{process_name}, variable Opex (M)",
                                alpha=0.8 * variable_opex_alpha,
                                hatch=self.hatch_map["cost"],
                            )
                        )

                # Carbon tax mean
                carbon_tax_col = f"{p.name}_mean_unit_carbon_tax"
                carbon_tax_val = (
                    self.df.loc[year, carbon_tax_col] if carbon_tax_col in self.df.columns else 0
                )
                if self._is_nonzero_or_notnan(carbon_tax_val):
                    self.ax.bar(
                        p.name,
                        carbon_tax_val,
                        bottom=base,
                        edgecolor="black",
                        linewidth=0.5,
                        color="none",
                        hatch=self.hatch_map["carbon_tax"],
                        alpha=alpha,
                        label=None,
                    )
                    base += carbon_tax_val

                # Unit taxes and subsidies
                tax_col = f"{p.name}_mean_unit_tax"
                tax_val = self.df.loc[year, tax_col] if tax_col in self.df.columns else 0
                if self._is_nonzero_or_notnan(tax_val):
                    self.ax.bar(
                        p.name,
                        tax_val,
                        bottom=base,
                        linewidth=0.5,
                        edgecolor="black",
                        color="none",
                        hatch=self.hatch_map["tax"],
                        alpha=alpha,
                        label=None,
                    )
                    base += tax_val

                subsidy_col = f"{p.name}_mean_unit_subsidy"
                subsidy_val = (
                    self.df.loc[year, subsidy_col] if subsidy_col in self.df.columns else 0
                )
                if self._is_nonzero_or_notnan(subsidy_val):
                    self.ax.bar(
                        p.name,
                        -subsidy_val,
                        bottom=neg_base,
                        linewidth=0.5,
                        edgecolor="black",
                        color="none",
                        hatch=self.hatch_map["subsidy"],
                        alpha=alpha,
                        label=None,
                    )

                # Net MFSP overlay (ligne)
                net_col = f"{p.name}_net_mfsp"
                if net_col in self.df.columns:
                    net_val = self.df.loc[year, net_col]
                    self.ax.bar(
                        p.name,
                        net_val,
                        linewidth=2,
                        color="none",
                        edgecolor="black",
                        alpha=alpha,
                        zorder=2,
                        fill=False,
                        hatch=None,
                    )

        # Draw vertical dashed line to separate used and unused options if needed
        if not self.show_only_used and len(unused_pathways) > 0 and len(used_pathways) > 0:
            # Find the x position after the last used pathway
            xticks = [p.name for p in display_pathways]
            used_count = len(used_pathways)
            # Get the tick positions

            if used_count < len(xticks):
                # Draw a vertical line between used and unused
                # The bar centers are at integer positions, so draw at (used_count - 0.5)
                self.ax.axvline(
                    x=used_count - 0.5,
                    color="black",
                    linestyle="dashed",
                    linewidth=1,
                    alpha=0.7,
                    zorder=10,
                )
                # Add vertical text annotations
                ylim = self.ax.get_ylim()
                ymid = ylim[1] * 0.99
                self.ax.text(
                    used_count - 0.7,
                    ymid,
                    "Used",
                    rotation=90,
                    va="top",
                    ha="right",
                    fontsize=10,
                    color="black",
                    alpha=0.7,
                    backgroundcolor="none",
                )
                self.ax.text(
                    used_count - 0.3,
                    ymid,
                    "Not (yet) used",
                    rotation=90,
                    va="top",
                    ha="left",
                    fontsize=10,
                    color="black",
                    alpha=0.7,
                    backgroundcolor="none",
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
            Patch(
                facecolor="none", edgecolor="black", hatch=self.hatch_map["cost"], label="Cost/MFSP"
            ),
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
            handles=pathway_handles,
            title="Cost components",
            loc="upper left",
            prop={"size": 8},
        )
        legend2 = self.ax.legend(
            handles=bar_type_handles,
            loc="upper right",
            prop={"size": 8},
        )
        self.ax.add_artist(legend1)
        self.ax.add_artist(legend2)

        self.ax.grid(axis="y")
        self.ax.set_title("Mean MFSP breakdown for year " + str(year))
        self.ax.set_ylabel("MFSP/Cost [€/MJ]")

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
        if getattr(pathway, "cost_model", None) == "bottom-up":
            self.update_pathway_over_time_bottomup(pathway)
        else:
            self.update_pathway_over_time_topdown(pathway)

    def update_pathway_over_time_topdown(self, pathway):
        self.ax.cla()
        years = self.prospective_years[1:]
        p = pathway

        energy_col = f"{p.name}_energy_consumption"
        if energy_col not in self.df.columns:
            return

        # Active mask: years with energy consumption >= 1e-9 and not NaN
        active_mask = (self.df.loc[years, energy_col] >= 1e-9) & (
            ~self.df.loc[years, energy_col].isna()
        )
        years_active = np.array(years)[active_mask.values]
        years_inactive = np.array([y for y in years if y not in years_active])
        years_inactive = np.append(
            years_inactive,
            years_active[0]
            if len(years_active) > 0 and years_active[0] < self.prospective_years[-1]
            else [],
        )

        pathway_handles = []

        def plot_for_years(years_subset, alpha):
            if len(years_subset) == 0:
                return
            base = np.zeros(len(years_subset))
            neg_base = np.zeros(len(years_subset))

            def get_vals(col):
                if col in self.df.columns:
                    return self.df.loc[years_subset, col].fillna(0).values
                else:
                    return np.zeros(len(years_subset))

            # Base cost (excluding resource)
            color = self.resource_color_map.get(("main", "mean_mfsp_without_resource"), "grey")
            mfsp_col = p.name + "_mean_mfsp_without_resource"
            mfsp_vals = get_vals(mfsp_col)
            if np.any(mfsp_vals != 0):
                self.ax.fill_between(
                    years_subset,
                    base,
                    base + mfsp_vals,
                    facecolor=color,
                    hatch=self.hatch_map["cost"],
                    edgecolor="black",
                    linewidth=0.5,
                    alpha=alpha,
                    zorder=2,
                )
                base += mfsp_vals
                pathway_handles.append(Patch(facecolor=color, edgecolor="black", label="Base cost"))

            # Taxes on base
            tax_col = p.name + "_mean_unit_tax_without_resource"
            tax_vals = get_vals(tax_col)
            if np.any(tax_vals != 0):
                self.ax.fill_between(
                    years_subset,
                    base,
                    base + tax_vals,
                    facecolor=color,
                    hatch=self.hatch_map["tax"],
                    edgecolor="black",
                    linewidth=0.5,
                    alpha=alpha,
                    zorder=2,
                )
                base += tax_vals

            # Subsidy on base
            subsidy_col = p.name + "_mean_unit_subsidy_without_resource"
            subsidy_vals = get_vals(subsidy_col)
            if np.any(subsidy_vals != 0):
                neg_top = neg_base - subsidy_vals
                self.ax.fill_between(
                    years_subset,
                    neg_base,
                    neg_top,
                    facecolor=color,
                    hatch=self.hatch_map["subsidy"],
                    edgecolor="black",
                    linewidth=0.5,
                    alpha=alpha,
                    zorder=2,
                )
                neg_base = neg_top

            if np.any(mfsp_vals != 0) or np.any(subsidy_vals != 0) or np.any(tax_vals != 0):
                pathway_handles.append(
                    Patch(facecolor=color, edgecolor="black", label="Pathway base")
                )

            # Pathway-specific resources
            for resource in p.resources_used:
                color = self.resource_color_map.get(("main", resource), None)
                cost_col = p.name + "_excluding_processes_" + resource + "_mean_unit_cost"
                cost_vals = get_vals(cost_col)
                if np.any(cost_vals != 0):
                    self.ax.fill_between(
                        years_subset,
                        base,
                        base + cost_vals,
                        facecolor=color,
                        hatch=self.hatch_map["cost"],
                        edgecolor="black",
                        linewidth=0.5,
                        alpha=alpha,
                        zorder=2,
                    )
                    base += cost_vals
                tax_col = p.name + "_excluding_processes_" + resource + "_mean_unit_tax"
                tax_vals = get_vals(tax_col)
                if np.any(tax_vals != 0):
                    self.ax.fill_between(
                        years_subset,
                        base,
                        base + tax_vals,
                        facecolor=color,
                        hatch=self.hatch_map["tax"],
                        edgecolor="black",
                        linewidth=0.5,
                        alpha=alpha,
                        zorder=2,
                    )
                    base += tax_vals

                subsidy_col = p.name + "_excluding_processes_" + resource + "_mean_unit_subsidy"
                subsidy_vals = get_vals(subsidy_col)
                if np.any(subsidy_vals != 0):
                    neg_top = neg_base - subsidy_vals
                    self.ax.fill_between(
                        years_subset,
                        neg_base,
                        neg_top,
                        facecolor=color,
                        hatch=self.hatch_map["subsidy"],
                        edgecolor="black",
                        linewidth=0.5,
                        alpha=alpha,
                        zorder=2,
                    )
                    neg_base = neg_top
                if np.any(cost_vals != 0) or np.any(tax_vals != 0) or np.any(subsidy_vals != 0):
                    pathway_handles.append(
                        Patch(facecolor=color, edgecolor="black", label=resource)
                    )

            # Resources used by each process
            process_resources = p.resources_used_processes
            for process_name, resource in process_resources.items():
                color = self.resource_color_map.get((process_name, resource), None)
                cost_col = p.name + "_" + process_name + "_" + resource + "_mean_unit_cost"
                cost_vals = get_vals(cost_col)
                if np.any(cost_vals != 0):
                    self.ax.fill_between(
                        years_subset,
                        base,
                        base + cost_vals,
                        facecolor=color,
                        hatch=self.hatch_map["cost"],
                        edgecolor="black",
                        linewidth=0.5,
                        alpha=alpha,
                        zorder=2,
                    )
                    base += cost_vals

                tax_col = p.name + "_" + process_name + "_" + resource + "_mean_unit_tax"
                tax_vals = get_vals(tax_col)
                if np.any(tax_vals != 0):
                    self.ax.fill_between(
                        years_subset,
                        base,
                        base + tax_vals,
                        facecolor=color,
                        hatch=self.hatch_map["tax"],
                        edgecolor="black",
                        linewidth=0.5,
                        alpha=alpha,
                        zorder=2,
                    )
                    base += tax_vals
                subsidy_col = p.name + "_" + process_name + "_" + resource + "_mean_unit_subsidy"
                subsidy_vals = get_vals(subsidy_col)
                if np.any(subsidy_vals != 0):
                    neg_top = neg_base - subsidy_vals
                    self.ax.fill_between(
                        years_subset,
                        neg_base,
                        neg_top,
                        facecolor=color,
                        hatch=self.hatch_map["subsidy"],
                        edgecolor="black",
                        linewidth=0.5,
                        alpha=alpha,
                        zorder=2,
                    )
                    neg_base = neg_top
                if np.any(tax_vals != 0) or np.any(subsidy_vals != 0) or np.any(cost_vals != 0):
                    pathway_handles.append(
                        Patch(
                            facecolor=color, edgecolor="black", label=f"{process_name}, {resource}"
                        )
                    )

            # Cost without resource for each process
            for process_name in process_resources.keys():
                color = self.resource_color_map.get(
                    (process_name, "without_resources_unit_cost"), None
                )
                cost_col = p.name + "_" + process_name + "_mean_unit_cost_without_resources"
                cost_vals = get_vals(cost_col)
                if np.any(cost_vals != 0):
                    self.ax.fill_between(
                        years_subset,
                        base,
                        base + cost_vals,
                        facecolor=color,
                        hatch=self.hatch_map["cost"],
                        edgecolor="black",
                        linewidth=0.5,
                        alpha=alpha,
                        zorder=2,
                    )
                    base += cost_vals
                subsidy_col = p.name + "_" + process_name + "_mean_unit_subsidy_without_resources"
                subsidy_vals = get_vals(subsidy_col)
                if np.any(subsidy_vals != 0):
                    neg_top = neg_base - subsidy_vals
                    self.ax.fill_between(
                        years_subset,
                        neg_base,
                        neg_top,
                        facecolor=color,
                        hatch=self.hatch_map["subsidy"],
                        edgecolor="black",
                        linewidth=0.5,
                        alpha=alpha,
                        zorder=2,
                    )
                    neg_base = neg_top
                tax_col = p.name + "_" + process_name + "_mean_unit_tax_without_resources"
                tax_vals = get_vals(tax_col)
                if np.any(tax_vals != 0):
                    self.ax.fill_between(
                        years_subset,
                        base,
                        base + tax_vals,
                        facecolor=color,
                        hatch=self.hatch_map["tax"],
                        edgecolor="black",
                        linewidth=0.5,
                        alpha=alpha,
                        zorder=2,
                    )
                    base += tax_vals
                if np.any(cost_vals != 0) or np.any(tax_vals != 0) or np.any(subsidy_vals != 0):
                    pathway_handles.append(
                        Patch(
                            facecolor=color,
                            edgecolor="black",
                            label=process_name,
                        )
                    )

        # Plot inactive years (alpha=0.3) only if self.show_only_used is False
        if not self.show_only_used:
            plot_for_years(years_inactive, 0.3)
        plot_for_years(years_active, 0.8)

        # Add vertical dashed line to separate used and unused years
        if not self.show_only_used and len(years_active) > 0 and len(years_inactive) > 0:
            first_active_year = years_active[0]
            # Draw a vertical dashed line between last unused and first used year
            self.ax.axvline(
                x=first_active_year,
                color="black",
                linestyle="dashed",
                linewidth=1,
                alpha=0.7,
                zorder=3,
            )
            # Add vertical text annotations
            ylim = self.ax.get_ylim()
            ymid = (ylim[0] + ylim[1]) / 2
            self.ax.text(
                first_active_year - 0.2,
                ymid,
                "Not used",
                rotation=90,
                va="center",
                ha="right",
                fontsize=10,
                color="black",
                alpha=0.7,
                backgroundcolor="none",
            )
            self.ax.text(
                first_active_year + 0.2,
                ymid,
                "Used",
                rotation=90,
                va="center",
                ha="left",
                fontsize=10,
                color="black",
                alpha=0.7,
                backgroundcolor="none",
            )

        # Remove duplicate labels in legend
        seen = set()
        unique_pathway_handles = []
        for h in pathway_handles:
            if h.get_label() not in seen and h.get_label() is not None:
                unique_pathway_handles.append(h)
                seen.add(h.get_label())

        bar_type_handles = [
            Patch(
                facecolor="none", edgecolor="black", hatch=self.hatch_map["cost"], label="MFSP/Cost"
            ),
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
            Line2D([0], [0], color="black", linewidth=2, label="Net MFSP/Cost"),
        ]

        legend1 = self.ax.legend(
            handles=unique_pathway_handles,
            title="Components",
            loc="upper left",
            prop={"size": 8},
        )
        legend2 = self.ax.legend(
            handles=bar_type_handles,
            loc="upper right",
            prop={"size": 8},
        )
        self.ax.add_artist(legend1)
        self.ax.add_artist(legend2)

        self.ax.grid(axis="y")
        self.ax.set_title(f"MFSP breakdown over time for {p.name}")
        self.ax.set_ylabel("MFSP [€/MJ]")
        self.ax.set_xlabel("Year")
        self.ax.set_xlim(self.prospective_years[1], self.prospective_years[-1])
        self.ax.set_ylim(
            self.ax.get_ylim()[0],
            self.ax.get_ylim()[1] * 1.1,
        )

        self.fig.tight_layout()
        self.fig.canvas.draw()

    def update_pathway_over_time_bottomup(self, pathway):
        self.ax.cla()
        years = self.prospective_years[1:]
        p = pathway

        energy_col = f"{p.name}_energy_consumption"
        if energy_col not in self.df.columns:
            return

        active_mask = (self.df.loc[years, energy_col] >= 1e-9) & (
            ~self.df.loc[years, energy_col].isna()
        )
        years_active = np.array(years)[active_mask.values]
        years_inactive = np.array([y for y in years if y not in years_active])
        years_inactive = np.append(
            years_inactive,
            years_active[0]
            if len(years_active) > 0 and years_active[0] < self.prospective_years[-1]
            else [],
        )

        pathway_handles = []

        variable_opex_alpha = 0.8
        fixed_opex_alpha = 0.6

        def plot_for_years_vintage(years_subset, alpha):
            if len(years_subset) == 0:
                return
            base = np.zeros(len(years_subset))

            def get_vals(col):
                if col in self.df.columns:
                    return self.df.loc[years_subset, col].fillna(0).values
                else:
                    return np.zeros(len(years_subset))

            # Capex vintage
            color_capex = self.resource_color_map.get(
                ("main", "mean_mfsp_without_resource"), "grey"
            )
            capex_col = f"{p.name}_vintage_unit_capex"
            capex_vals = get_vals(capex_col)
            if np.any(capex_vals != 0):
                self.ax.fill_between(
                    years_subset,
                    base,
                    base + capex_vals,
                    facecolor=color_capex,
                    hatch=self.hatch_map["cost"],
                    edgecolor="black",
                    linewidth=0.5,
                    alpha=alpha,
                    zorder=2,
                )
                base += capex_vals
                pathway_handles.append(
                    Patch(
                        facecolor=color_capex,
                        edgecolor="black",
                        label="Pathway, Capex (V)",
                        alpha=0.8,
                        hatch=self.hatch_map["cost"],
                    )
                )

            # Fixed opex vintage
            color_fixed_opex = color_capex
            fixed_opex_col = f"{p.name}_vintage_unit_fixed_opex"
            fixed_opex_vals = get_vals(fixed_opex_col)
            if np.any(fixed_opex_vals != 0):
                self.ax.fill_between(
                    years_subset,
                    base,
                    base + fixed_opex_vals,
                    facecolor=color_fixed_opex,
                    hatch=self.hatch_map["cost"],
                    edgecolor="black",
                    linewidth=0.5,
                    alpha=alpha * fixed_opex_alpha,
                    zorder=2,
                )
                base += fixed_opex_vals
                pathway_handles.append(
                    Patch(
                        facecolor=color_fixed_opex,
                        edgecolor="black",
                        label="Pathway, fixed Opex (V)",
                        alpha=0.8 * fixed_opex_alpha,
                        hatch=self.hatch_map["cost"],
                    )
                )

            # Variable opex vintage
            color_variable_opex = color_capex
            variable_opex_col = f"{p.name}_vintage_unit_variable_opex"
            variable_opex_vals = get_vals(variable_opex_col)
            if np.any(variable_opex_vals != 0):
                self.ax.fill_between(
                    years_subset,
                    base,
                    base + variable_opex_vals,
                    facecolor=color_variable_opex,
                    hatch=self.hatch_map["cost"],
                    edgecolor="black",
                    linewidth=0.5,
                    alpha=alpha * variable_opex_alpha,
                    zorder=2,
                )
                base += variable_opex_vals
                pathway_handles.append(
                    Patch(
                        facecolor=color_variable_opex,
                        edgecolor="black",
                        label="Pathway, variable Opex (V)",
                        alpha=0.8 * variable_opex_alpha,
                        hatch=self.hatch_map["cost"],
                    )
                )

            # Resources vintage
            for resource in p.resources_used:
                color = self.resource_color_map.get(("main", resource), None)
                res_col = f"{p.name}_excluding_processes_{resource}_vintage_unit_cost"
                res_vals = get_vals(res_col)
                if np.any(res_vals != 0):
                    self.ax.fill_between(
                        years_subset,
                        base,
                        base + res_vals,
                        facecolor=color,
                        hatch=self.hatch_map["cost"],
                        edgecolor="black",
                        linewidth=0.5,
                        alpha=alpha,
                        zorder=2,
                    )
                    base += res_vals
                    pathway_handles.append(
                        Patch(
                            facecolor=color,
                            edgecolor="black",
                            label=f"Pathway, {resource} (V)",
                            alpha=0.8,
                            hatch=self.hatch_map["cost"],
                        )
                    )

            # Processus vintage
            for process_name, resource in p.resources_used_processes.items():
                color = self.resource_color_map.get((process_name, resource), None)
                proc_col = f"{p.name}_{process_name}_{resource}_vintage_unit_cost"
                proc_vals = get_vals(proc_col)
                if np.any(proc_vals != 0):
                    self.ax.fill_between(
                        years_subset,
                        base,
                        base + proc_vals,
                        facecolor=color,
                        hatch=self.hatch_map["cost"],
                        edgecolor="black",
                        linewidth=0.5,
                        alpha=alpha,
                        zorder=2,
                    )
                    base += proc_vals
                    pathway_handles.append(
                        Patch(
                            facecolor=color,
                            edgecolor="black",
                            label=f"{process_name}, {resource} (V)",
                            alpha=0.8,
                            hatch=self.hatch_map["cost"],
                        )
                    )

            # Capex, opex process vintage (sans Resource)
            for process_name in p.resources_used_processes.keys():
                color = self.resource_color_map.get(
                    (process_name, "without_resources_unit_cost"), None
                )
                capex_col = f"{p.name}_{process_name}_vintage_unit_capex"
                capex_vals = get_vals(capex_col)
                if np.any(capex_vals != 0):
                    self.ax.fill_between(
                        years_subset,
                        base,
                        base + capex_vals,
                        facecolor=color,
                        hatch=self.hatch_map["cost"],
                        edgecolor="black",
                        linewidth=0.5,
                        alpha=alpha,
                        zorder=2,
                    )
                    base += capex_vals
                    pathway_handles.append(
                        Patch(
                            facecolor=color,
                            edgecolor="black",
                            label=f"{process_name}, Capex (V)",
                            alpha=0.8,
                            hatch=self.hatch_map["cost"],
                        )
                    )
                fixed_opex_col = f"{p.name}_{process_name}_vintage_unit_fixed_opex"
                fixed_opex_vals = get_vals(fixed_opex_col)
                if np.any(fixed_opex_vals != 0):
                    self.ax.fill_between(
                        years_subset,
                        base,
                        base + fixed_opex_vals,
                        facecolor=color,
                        hatch=self.hatch_map["cost"],
                        edgecolor="black",
                        linewidth=0.5,
                        alpha=alpha * fixed_opex_alpha,
                        zorder=2,
                    )
                    base += fixed_opex_vals
                    pathway_handles.append(
                        Patch(
                            facecolor=color,
                            edgecolor="black",
                            label=f"{process_name}, fixed Opex (V)",
                            alpha=0.8 * fixed_opex_alpha,
                            hatch=self.hatch_map["cost"],
                        )
                    )
                variable_opex_col = f"{p.name}_{process_name}_vintage_unit_variable_opex"
                variable_opex_vals = get_vals(variable_opex_col)
                if np.any(variable_opex_vals != 0):
                    self.ax.fill_between(
                        years_subset,
                        base,
                        base + variable_opex_vals,
                        facecolor=color,
                        hatch=self.hatch_map["cost"],
                        edgecolor="black",
                        linewidth=0.5,
                        alpha=alpha * variable_opex_alpha,
                        zorder=2,
                    )
                    base += variable_opex_vals
                    pathway_handles.append(
                        Patch(
                            facecolor=color,
                            edgecolor="black",
                            label=f"{process_name}, variable Opex (V)",
                            alpha=0.8 * variable_opex_alpha,
                            hatch=self.hatch_map["cost"],
                        )
                    )

            # Carbon tax vintage
            carbon_tax_col = f"{p.name}_vintage_eis_carbon_tax"
            carbon_tax_vals = get_vals(carbon_tax_col)
            if np.any(carbon_tax_vals != 0):
                self.ax.fill_between(
                    years_subset,
                    base,
                    base + carbon_tax_vals,
                    facecolor="none",
                    hatch=self.hatch_map["carbon_tax"],
                    edgecolor="black",
                    linewidth=0.5,
                    alpha=alpha,
                    zorder=2,
                )
                base += carbon_tax_vals

            # Net MFSP overlay (ligne)
            net_col = f"{p.name}_net_mfsp"
            if net_col in self.df.columns:
                net_vals = self.df.loc[years_subset, net_col].fillna(0).values
                self.ax.plot(
                    years_subset,
                    net_vals,
                    color="black",
                    linewidth=2,
                    alpha=alpha,
                    linestyle="solid",
                    zorder=3,
                    label="Net MFSP",
                )

        def plot_for_years_mean(years_subset, alpha):
            if len(years_subset) == 0:
                return
            base = np.zeros(len(years_subset))

            def get_vals(col):
                if col in self.df.columns:
                    return self.df.loc[years_subset, col].fillna(0).values
                else:
                    return np.zeros(len(years_subset))

            # Capex mean
            color_capex = self.resource_color_map.get(
                ("main", "mean_mfsp_without_resource"), "grey"
            )
            capex_col = f"{p.name}_mean_unit_capex"
            capex_vals = get_vals(capex_col)
            if np.any(capex_vals != 0):
                self.ax.fill_between(
                    years_subset,
                    base,
                    base + capex_vals,
                    facecolor=color_capex,
                    hatch=self.hatch_map["cost"],
                    edgecolor="black",
                    linewidth=0.5,
                    alpha=alpha,
                    zorder=2,
                )
                base += capex_vals
                pathway_handles.append(
                    Patch(
                        facecolor=color_capex,
                        edgecolor="black",
                        label="Pathway, Capex (M)",
                        alpha=0.8,
                        hatch=self.hatch_map["cost"],
                    )
                )

            # Fixed opex mean
            color_fixed_opex = color_capex
            fixed_opex_col = f"{p.name}_mean_unit_fixed_opex"
            fixed_opex_vals = get_vals(fixed_opex_col)
            if np.any(fixed_opex_vals != 0):
                self.ax.fill_between(
                    years_subset,
                    base,
                    base + fixed_opex_vals,
                    facecolor=color_fixed_opex,
                    hatch=self.hatch_map["cost"],
                    edgecolor="black",
                    linewidth=0.5,
                    alpha=alpha,
                    zorder=2,
                )
                base += fixed_opex_vals
                pathway_handles.append(
                    Patch(
                        facecolor=color_fixed_opex,
                        edgecolor="black",
                        label="Pathway, fixed Opex (M)",
                        alpha=0.8,
                        hatch=self.hatch_map["cost"],
                    )
                )

            # Variable opex mean
            color_variable_opex = color_capex
            variable_opex_col = f"{p.name}_mean_unit_variable_opex"
            variable_opex_vals = get_vals(variable_opex_col)
            if np.any(variable_opex_vals != 0):
                self.ax.fill_between(
                    years_subset,
                    base,
                    base + variable_opex_vals,
                    facecolor=color_variable_opex,
                    hatch=self.hatch_map["cost"],
                    edgecolor="black",
                    linewidth=0.5,
                    alpha=alpha,
                    zorder=2,
                )
                base += variable_opex_vals
                pathway_handles.append(
                    Patch(
                        facecolor=color_variable_opex,
                        edgecolor="black",
                        label="Pathway, variable Opex (M)",
                        alpha=0.8,
                        hatch=self.hatch_map["cost"],
                    )
                )

            # Resources mean
            for resource in p.resources_used:
                color = self.resource_color_map.get(("main", resource), None)
                res_col = f"{p.name}_excluding_processes_{resource}_mean_unit_cost"
                res_vals = get_vals(res_col)
                if np.any(res_vals != 0):
                    self.ax.fill_between(
                        years_subset,
                        base,
                        base + res_vals,
                        facecolor=color,
                        hatch=self.hatch_map["cost"],
                        edgecolor="black",
                        linewidth=0.5,
                        alpha=alpha,
                        zorder=2,
                    )
                    base += res_vals
                    pathway_handles.append(
                        Patch(
                            facecolor=color,
                            edgecolor="black",
                            label=f"Pathway, {resource} (M)",
                            alpha=0.8,
                            hatch=self.hatch_map["cost"],
                        )
                    )

            # Processus mean
            for process_name, resource in p.resources_used_processes.items():
                color = self.resource_color_map.get((process_name, resource), None)
                proc_col = f"{p.name}_{process_name}_{resource}_mean_unit_cost"
                proc_vals = get_vals(proc_col)
                if np.any(proc_vals != 0):
                    self.ax.fill_between(
                        years_subset,
                        base,
                        base + proc_vals,
                        facecolor=color,
                        hatch=self.hatch_map["cost"],
                        edgecolor="black",
                        linewidth=0.5,
                        alpha=alpha,
                        zorder=2,
                    )
                    base += proc_vals
                    pathway_handles.append(
                        Patch(
                            facecolor=color,
                            edgecolor="black",
                            label=f"{process_name}, {resource} (M)",
                            alpha=0.8,
                            hatch=self.hatch_map["cost"],
                        )
                    )

            # Capex, opex process mean (sans Resource)
            for process_name in p.resources_used_processes.keys():
                color = self.resource_color_map.get(
                    (process_name, "without_resources_unit_cost"), None
                )
                capex_col = f"{p.name}_{process_name}_mean_unit_capex"
                capex_vals = get_vals(capex_col)
                if np.any(capex_vals != 0):
                    self.ax.fill_between(
                        years_subset,
                        base,
                        base + capex_vals,
                        facecolor=color,
                        hatch=self.hatch_map["cost"],
                        edgecolor="black",
                        linewidth=0.5,
                        alpha=alpha,
                        zorder=2,
                    )
                    base += capex_vals
                    pathway_handles.append(
                        Patch(
                            facecolor=color,
                            edgecolor="black",
                            label=f"{process_name}, Capex (M)",
                            alpha=0.8,
                            hatch=self.hatch_map["cost"],
                        )
                    )
                fixed_opex_col = f"{p.name}_{process_name}_mean_unit_fixed_opex"
                fixed_opex_vals = get_vals(fixed_opex_col)
                if np.any(fixed_opex_vals != 0):
                    self.ax.fill_between(
                        years_subset,
                        base,
                        base + fixed_opex_vals,
                        facecolor=color,
                        hatch=self.hatch_map["cost"],
                        edgecolor="black",
                        linewidth=0.5,
                        alpha=alpha,
                        zorder=2,
                    )
                    base += fixed_opex_vals
                    pathway_handles.append(
                        Patch(
                            facecolor=color,
                            edgecolor="black",
                            label=f"{process_name}, fixed Opex (M)",
                            alpha=0.8,
                            hatch=self.hatch_map["cost"],
                        )
                    )
                variable_opex_col = f"{p.name}_{process_name}_mean_unit_variable_opex"
                variable_opex_vals = get_vals(variable_opex_col)
                if np.any(variable_opex_vals != 0):
                    self.ax.fill_between(
                        years_subset,
                        base,
                        base + variable_opex_vals,
                        facecolor=color,
                        hatch=self.hatch_map["cost"],
                        edgecolor="black",
                        linewidth=0.5,
                        alpha=alpha,
                        zorder=2,
                    )
                    base += variable_opex_vals
                    pathway_handles.append(
                        Patch(
                            facecolor=color,
                            edgecolor="black",
                            label=f"{process_name}, variable Opex (M)",
                            alpha=0.8,
                            hatch=self.hatch_map["cost"],
                        )
                    )

            # Carbon tax mean
            carbon_tax_col = f"{p.name}_mean_unit_carbon_tax"
            carbon_tax_vals = get_vals(carbon_tax_col)
            if np.any(carbon_tax_vals != 0):
                self.ax.fill_between(
                    years_subset,
                    base,
                    base + carbon_tax_vals,
                    facecolor="none",
                    hatch=self.hatch_map["carbon_tax"],
                    edgecolor="black",
                    linewidth=0.5,
                    alpha=alpha,
                    zorder=2,
                )
                base += carbon_tax_vals

            # Net MFSP overlay (ligne)
            net_col = f"{p.name}_net_mfsp"
            if net_col in self.df.columns:
                net_vals = self.df.loc[years_subset, net_col].fillna(0).values
                self.ax.plot(
                    years_subset,
                    net_vals,
                    color="black",
                    linewidth=2,
                    alpha=alpha,
                    linestyle="solid",
                    zorder=3,
                    label="Net MFSP",
                )

        # Plot inactive years (alpha=0.3) only if self.show_only_used is False
        if not self.show_only_used:
            if self.show_vintage_mean == "vintage":
                plot_for_years_vintage(years_inactive, 0.3)
            else:
                plot_for_years_mean(years_active, 0.3)

        if self.show_vintage_mean == "vintage":
            plot_for_years_vintage(years_active, 0.8)
        else:
            plot_for_years_mean(years_active, 0.8)

        # Add vertical dashed line to separate used and unused years
        if not self.show_only_used and len(years_active) > 0 and len(years_inactive) > 0:
            first_active_year = years_active[0]
            self.ax.axvline(
                x=first_active_year,
                color="black",
                linestyle="dashed",
                linewidth=1,
                alpha=0.7,
                zorder=3,
            )
            ylim = self.ax.get_ylim()
            ymid = (ylim[0] + ylim[1]) / 2
            self.ax.text(
                first_active_year - 0.2,
                ymid,
                "Not used",
                rotation=90,
                va="center",
                ha="right",
                fontsize=10,
                color="black",
                alpha=0.7,
                backgroundcolor="none",
            )
            self.ax.text(
                first_active_year + 0.2,
                ymid,
                "Used",
                rotation=90,
                va="center",
                ha="left",
                fontsize=10,
                color="black",
                alpha=0.7,
                backgroundcolor="none",
            )

        # Remove duplicate labels in legend
        seen = set()
        unique_pathway_handles = []
        for h in pathway_handles:
            if h.get_label() not in seen and h.get_label() is not None:
                unique_pathway_handles.append(h)
                seen.add(h.get_label())

        bar_type_handles = [
            Patch(
                facecolor="none", edgecolor="black", hatch=self.hatch_map["cost"], label="MFSP/Cost"
            ),
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
            Line2D([0], [0], color="black", linewidth=2, label="Net MFSP/Cost"),
        ]

        legend1 = self.ax.legend(
            handles=unique_pathway_handles,
            title="Components",
            loc="upper left",
            prop={"size": 8},
        )
        legend2 = self.ax.legend(
            handles=bar_type_handles,
            loc="upper right",
            prop={"size": 8},
        )
        self.ax.add_artist(legend1)
        self.ax.add_artist(legend2)

        self.ax.grid(axis="y")
        self.ax.set_title(f"MFSP breakdown over time for {p.name}")
        self.ax.set_ylabel("MFSP [€/MJ]")
        self.ax.set_xlabel("Year")
        self.ax.set_xlim(self.prospective_years[1], self.prospective_years[-1])
        self.ax.set_ylim(
            self.ax.get_ylim()[0],
            self.ax.get_ylim()[1] * 1.1,
        )

        self.fig.tight_layout()
        self.fig.canvas.draw()


class SimpleMFSP:
    def __init__(self, process):
        data = process.data
        self.df = data["vector_outputs"]
        self.years = data["years"]["full_years"]
        self.prospective_years = data["years"]["prospective_years"]
        self.pathways_manager = process.pathways_manager

        self.fig, self.ax = plt.subplots(figsize=(12, 7))
        self.plot_interact()

    def plot_interact(self):
        mfsp_toggle = widgets.ToggleButtons(
            options=[
                ("Net MFSP", "net_mfsp"),
                ("MFSP", "mean_mfsp"),
            ],
            description="MFSP type:",
            value="net_mfsp",
        )
        interact(self.create_plot, mfsp_type=mfsp_toggle)

    def create_plot(self, mfsp_type="net_mfsp"):
        self.ax.cla()
        pathways = self.pathways_manager.get_all()
        colors = plt.cm.get_cmap("tab20", len(pathways))
        aircraft_linestyles = {
            "dropin_fuel": "-",
            "hydrogen": "--",
            "electric": "-.",
        }
        dashed_line_needed = False
        used_labels = set()
        for i, p in enumerate(pathways):
            col = f"{p.name}_{mfsp_type}"
            energy_col = f"{p.name}_energy_consumption"
            if col in self.df.columns and energy_col in self.df.columns:
                years = np.array(self.prospective_years)
                vals = self.df.loc[self.prospective_years, col].fillna(np.nan).values
                energy = self.df.loc[self.prospective_years, energy_col].fillna(0).values
                linestyle = aircraft_linestyles.get(getattr(p, "aircraft_type", ""), "solid")

                used_mask = energy > 1e-9
                color_used = colors(i)
                color_unused = "grey"
                linewidth = 2

                seg_start = 0
                current_used = used_mask[0]
                for idx in range(1, len(years)):
                    if used_mask[idx] != current_used:
                        seg_years = years[seg_start : idx + 1]
                        seg_vals = vals[seg_start : idx + 1]
                        if current_used:
                            label = p.name if p.name not in used_labels else None
                            self.ax.plot(
                                seg_years,
                                seg_vals,
                                color=color_used,
                                linewidth=linewidth,
                                linestyle=linestyle,
                                label=label,
                            )
                            if label:
                                used_labels.add(label)
                        else:
                            label = "Not used" if not dashed_line_needed else None
                            self.ax.plot(
                                seg_years,
                                seg_vals,
                                color=color_unused,
                                linewidth=1.5,
                                linestyle="dotted",
                                alpha=0.7,
                                label=label,
                            )
                            if label:
                                dashed_line_needed = True
                        seg_start = idx
                        current_used = used_mask[idx]
                seg_years = years[seg_start:]
                seg_vals = vals[seg_start:]
                if current_used:
                    label = p.name if p.name not in used_labels else None
                    self.ax.plot(
                        seg_years,
                        seg_vals,
                        color=color_used,
                        linewidth=linewidth,
                        linestyle=linestyle,
                        label=label,
                    )
                    if label:
                        used_labels.add(label)
                else:
                    label = "Not used" if not dashed_line_needed else None
                    self.ax.plot(
                        seg_years,
                        seg_vals,
                        color=color_unused,
                        linewidth=1.5,
                        linestyle="dotted",
                        alpha=0.7,
                        label=label,
                    )
                    if label:
                        dashed_line_needed = True

        handles, labels = self.ax.get_legend_handles_labels()
        # Remove duplicate labels
        seen = set()
        new_handles = []
        new_labels = []
        for ha, lb in zip(handles, labels):
            if lb not in seen and lb is not None:
                new_handles.append(ha)
                new_labels.append(lb)
                seen.add(lb)
        # Add "Not used" if needed and not present
        if dashed_line_needed and "Not used" not in new_labels:
            new_handles.append(
                Line2D(
                    [0],
                    [0],
                    color="grey",
                    linestyle="dotted",
                    linewidth=1.5,
                    alpha=0.7,
                    label="Not used",
                )
            )
            new_labels.append("Not used")
        self.ax.set_title("Net MFSP by fuel" if mfsp_type == "net_mfsp" else "MFSP by fuel")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Net MFSP [€/MJ]" if mfsp_type == "net_mfsp" else "MFSP [€/MJ]")
        self.ax.legend(new_handles, new_labels)
        self.ax.grid(True)
        self.fig.tight_layout()
        self.fig.canvas.draw()

    def update(self, data):
        self.df = data["vector_outputs"]
        self.years = data["years"]["full_years"]
        self.prospective_years = data["years"]["prospective_years"]
        self.pathways_manager = data["pathways_manager"]

        # Clear the current axes
        self.ax.cla()

        # Recreate the plot with updated data
        self.create_plot()

        # Redraw the canvas
        self.fig.canvas.draw()
