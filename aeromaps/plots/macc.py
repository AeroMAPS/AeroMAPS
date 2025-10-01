import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from ipywidgets import interact, widgets

from mpl_toolkits.axes_grid1 import make_axes_locatable


class AnnualMACC:
    def __init__(self, process, fleet_model):
        data = process.data
        self.df = data["vector_outputs"]
        self.fleet_model = fleet_model
        self.float_outputs = data["float_outputs"]
        self.float_inputs = data["float_inputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]
        self.pathways_manager = process.pathways_manager

        try:
            self.fig, self.ax = plt.subplots(
                figsize=(10, 7),
            )
            self.ax2 = self.ax.twiny()
            self.create_plot_data()
            self.plot_interact()

        except Exception as e:
            raise RuntimeError(
                "Error in creating plot. Possible cause: this plot requires top-down fleet model, "
                "abatement cost and complex energy cost models. Be sure to select them in the scenario settings."
            ) from e

    def plot_interact(self):
        year_widget = widgets.IntSlider(
            min=self.prospective_years[0],
            max=self.prospective_years[-1],
            step=1,
            description="Year:",
            value=2035,
        )

        metric_widget = widgets.Dropdown(
            options=[
                ("Instantaneous Carbon Abatement Cost", "carbon_abatement_cost"),
                ("Specific Carbon Abatement Cost", "specific_carbon_abatement_cost"),
                (
                    "Generic Specific Carbon Abatement Cost",
                    "generic_specific_carbon_abatement_cost",
                ),
            ],
            description="Metric:",
            value="generic_specific_carbon_abatement_cost",
        )

        scc_widget = widgets.FloatText(description="Base year SCC (Specific CAC ONLY):")

        def update_numeric_widget(change):
            if change["new"] == "specific_carbon_abatement_cost":
                scc_widget.disabled = False
            else:
                scc_widget.disabled = True
                scc_widget.value = 0

        metric_widget.observe(update_numeric_widget, names="value")

        interact(self.update, year=year_widget, metric=metric_widget, scc_start=scc_widget)

    def create_plot_data(self):
        self.macc_dict = {}

        for year in range(self.prospective_years[0], self.prospective_years[-1] + 1):
            name = []
            vol = []
            cost = []
            spe_cost = []
            g_spe_cost = []

            colors = []

            # Start with discrete aircraft from the fleet model
            for category, sets in self.fleet_model.fleet.all_aircraft_elements.items():
                for aircraft_var in sets:
                    if hasattr(aircraft_var, "parameters"):
                        aircraft_var_name = aircraft_var.parameters.full_name
                    else:
                        aircraft_var_name = aircraft_var.full_name

                    vol.append(
                        self.fleet_model.df.loc[
                            year, aircraft_var_name + ":aircraft_carbon_abatement_volume"
                        ]
                        / 1000000
                    )
                    cost.append(
                        self.fleet_model.df.loc[
                            year, aircraft_var_name + ":aircraft_carbon_abatement_cost"
                        ]
                    )

                    spe_cost.append(
                        self.fleet_model.df.loc[
                            year, aircraft_var_name + ":aircraft_specific_carbon_abatement_cost"
                        ]
                    )

                    g_spe_cost.append(
                        self.fleet_model.df.loc[
                            year,
                            aircraft_var_name + ":aircraft_generic_specific_carbon_abatement_cost",
                        ]
                    )
                    if category == "Short Range":
                        colors.append("gold")
                    elif category == "Medium Range":
                        colors.append("goldenrod")
                    else:
                        colors.append("darkgoldenrod")
                    name.append(aircraft_var_name.split(":")[-1])

            # continue with generic energy production pathways

            for pathway in self.pathways_manager.get_all():
                if (
                    pathway.name != "fossil_kerosene"
                ):  # hard coded for cac now, may be parametrized later
                    name.append(pathway.name)
                    abatement_col = f"{pathway.name}_abatement_effective"
                    if abatement_col not in self.df.columns:
                        raise ValueError(
                            f"Pathway {pathway.name} abatement is not defined. Pathways must be defined with bottom-up model."
                        )
                    vol.append(self.df[f"{pathway.name}_abatement_effective"][year] / 1000000)
                    cac_col = f"{pathway.name}_carbon_abatement_cost"
                    if cac_col not in self.df.columns:
                        raise ValueError(
                            f"Pathway {pathway.name} carbon abatement cost is not defined. Pathways must be defined with bottom-up model."
                        )
                    cost.append(self.df[f"{pathway.name}_carbon_abatement_cost"][year])
                    spe_cac_col = f"{pathway.name}_specific_carbon_abatement_cost"
                    if spe_cac_col not in self.df.columns:
                        raise ValueError(
                            f"Pathway {pathway.name} specific carbon abatement cost is not defined. Pathways must be defined with bottom-up model."
                        )
                    spe_cost.append(self.df[f"{pathway.name}_specific_carbon_abatement_cost"][year])
                    g_spe_cac_col = f"{pathway.name}_generic_specific_carbon_abatement_cost"
                    if g_spe_cac_col not in self.df.columns:
                        raise ValueError(
                            f"Pathway {pathway.name} generic specific carbon abatement cost is not defined. Pathways must be defined with bottom-up model."
                        )
                    g_spe_cost.append(
                        self.df[f"{pathway.name}_generic_specific_carbon_abatement_cost"][year]
                    )
                    colors.append("yellowgreen")

            name.extend(
                [
                    el
                    for el in [
                        "Freighter - Drop in",
                        "Freighter - Hydrogen",
                        "Freighter - Electric",
                        "OPS",
                        "OPS - Freight",
                        "Load Factor",
                    ]
                ]
            )

            # Abatement effective in MtCO2e
            vol.extend(
                [
                    elt / 1000000
                    for elt in [
                        self.df.aircraft_carbon_abatement_volume_freight_dropin[year],
                        self.df.aircraft_carbon_abatement_volume_freight_hydrogen[year],
                        self.df.aircraft_carbon_abatement_volume_freight_electric[year],
                        self.df.operations_abatement_effective[year],
                        self.df.operations_abatement_effective_freight[year],
                        self.df.load_factor_abatement_effective[year],
                    ]
                ]
            )

            # carbon abatement cost in (€/tCO2e)
            cost.extend(
                [
                    el
                    for el in [
                        self.df.aircraft_carbon_abatement_cost_freight_dropin[year],
                        self.df.aircraft_carbon_abatement_cost_freight_hydrogen[year],
                        self.df.aircraft_carbon_abatement_cost_freight_electric[year],
                        self.df.operations_abatement_cost[year],
                        self.df.operations_abatement_cost_freight[year],
                        self.df.load_factor_abatement_cost[year],
                    ]
                ]
            )

            spe_cost.extend(
                [
                    el
                    for el in [
                        self.df.aircraft_specific_carbon_abatement_cost_freight_dropin[year],
                        self.df.aircraft_specific_carbon_abatement_cost_freight_hydrogen[year],
                        self.df.aircraft_specific_carbon_abatement_cost_freight_electric[year],
                        self.df.operations_specific_abatement_cost[year],
                        self.df.operations_specific_abatement_cost_freight[year],
                        self.df.load_factor_specific_abatement_cost[year],
                    ]
                ]
            )

            g_spe_cost.extend(
                [
                    el
                    for el in [
                        self.df.aircraft_generic_specific_carbon_abatement_cost_freight_dropin[
                            year
                        ],
                        self.df.aircraft_generic_specific_carbon_abatement_cost_freight_hydrogen[
                            year
                        ],
                        self.df.aircraft_generic_specific_carbon_abatement_cost_freight_electric[
                            year
                        ],
                        self.df.operations_generic_specific_abatement_cost[year],
                        self.df.operations_generic_specific_abatement_cost_freight[year],
                        self.df.load_factor_generic_specific_abatement_cost[year],
                    ]
                ]
            )

            colors.extend(
                [
                    el
                    for el in [
                        "khaki",
                        "khaki",
                        "khaki",
                        "orange",
                        "orange",
                        "orange",
                    ]
                ]
            )

            macc_df = pd.DataFrame(
                data=[vol, cost, spe_cost, g_spe_cost, colors],
                columns=name,
                index=[
                    "abatement_effective",
                    "carbon_abatement_cost",
                    "specific_carbon_abatement_cost",
                    "generic_specific_carbon_abatement_cost",
                    "colors",
                ],
            )

            macc_df = macc_df.transpose()

            self.macc_dict[year] = macc_df

    def update(self, year, scc_start, metric):
        self.ax.cla()

        macc_df = self.macc_dict[year]

        macc_df = macc_df.sort_values(by=metric)

        # Dropping NaN on costs or abatements
        macc_df = macc_df.dropna(subset=metric)

        maccneg_df = macc_df[macc_df["abatement_effective"] < -0]
        maccpos_df = macc_df[macc_df["abatement_effective"] > 0]

        ##### POS ######

        heights_pos = maccpos_df[metric].to_list()
        names_pos = maccpos_df.index.to_list()
        heights_pos.insert(0, 0)
        heights_pos.append(0)

        # # MAx effective maccpos
        widths_effective_pos = maccpos_df["abatement_effective"].to_list()
        widths_effective_pos.insert(0, 0)
        widths_effective_pos.append(widths_effective_pos[-1])

        cumwidths_effective_pos = np.cumsum(widths_effective_pos)

        colors_pos = maccpos_df["colors"].to_list()

        scc_year = None
        if metric == "specific_carbon_abatement_cost":
            scc_year = scc_start * (
                (1 + self.float_inputs["social_discount_rate"])
                ** (year - self.prospective_years[0])
            )
        elif metric == "generic_specific_carbon_abatement_cost":
            scc_year = self.df.loc[year, "exogenous_carbon_price_trajectory"]

        ### POS

        self.ax.step(
            cumwidths_effective_pos - widths_effective_pos,
            heights_pos,
            where="post",
            color="black",
            label="Marginal abatement cost",
            linewidth=1,
            zorder=10,  # ensure top level
        )

        # custom_annotation_height_for_nice_plot = [
        #     70,
        #     220,
        #     130,
        #     100,
        #     100,
        #     130,
        #     150,
        #     180,
        #     100,
        #     100,
        #     100,
        #     180,
        #     240,
        #     220,
        #     300,
        #     380,
        #     460,
        #     520,
        #     580,
        #     670,
        # ]

        for i in range(len(widths_effective_pos) - 2):
            x_position = (cumwidths_effective_pos[i] + cumwidths_effective_pos[i + 1]) / 2
            y_position = min(heights_pos[i + 1], 2000)
            if heights_pos[i + 1] >= 0:
                if heights_pos[i + 1] >= 2000:
                    text = f"{names_pos[i]}\n {int(heights_pos[i + 1])}"
                else:
                    text = f"{names_pos[i]}"
                self.ax.annotate(
                    text,
                    (x_position, y_position),
                    xycoords="data",
                    xytext=(x_position, y_position + 50),
                    # xytext=(x_position, custom_annotation_height_for_nice_plot[i]),
                    textcoords="data",
                    arrowprops=dict(width=0.5, headwidth=0),
                    rotation=-60,
                    fontsize=9,
                    ha="right",
                    va="bottom",
                )
            else:
                self.ax.annotate(
                    f"{names_pos[i]}",
                    (x_position, 0),
                    xycoords="data",
                    xytext=(x_position, min(50, max(heights_pos) - 50) + 30 * (i % 3)),
                    # xytext=(x_position, custom_annotation_height_for_nice_plot[i]),
                    textcoords="data",
                    arrowprops=dict(width=0.5, headwidth=0),
                    rotation=-60,
                    fontsize=9,
                    ha="right",
                    va="bottom",
                )

        # Fill under the step plot with different colors for each step
        for i in range(0, (len(widths_effective_pos) - 2)):
            # Create a polygon for each step
            polygon = plt.Polygon(
                [
                    (cumwidths_effective_pos[i], 0),
                    (cumwidths_effective_pos[i], heights_pos[i + 1]),
                    (cumwidths_effective_pos[i + 1], heights_pos[i + 1]),
                    (cumwidths_effective_pos[i + 1], 0),
                ],
                closed=True,
                alpha=1,
                facecolor=colors_pos[i],
                edgecolor="black",
                linewidth=0.5,
                linestyle="dotted",
            )
            self.ax.add_patch(polygon)

        ### NEG

        ##### NEG #####

        heights_neg = maccneg_df[metric].to_list()
        names_neg = maccneg_df.index.to_list()

        heights_neg.append(0)
        heights_neg.insert(0, 0)

        # # MAx effective maccneg
        widths_effective_neg = maccneg_df["abatement_effective"].to_list()

        widths_effective_neg.insert(0, 0)
        widths_effective_neg.append(0)

        cumwidths_effective_neg = np.cumsum(widths_effective_neg)

        colors_neg = maccneg_df["colors"].to_list()

        self.ax.step(
            cumwidths_effective_neg[-1] - cumwidths_effective_neg + widths_effective_neg,
            heights_neg,
            where="post",
            color="#335C67",
            label="Marginal emission cost",
            linewidth=1,
            zorder=9,
        )

        # custom_annotation_height_for_nice_plot = [15,70,120,170,220]

        for i in range(len(widths_effective_neg) - 2):
            x_position = (
                cumwidths_effective_neg[-1]
                - (cumwidths_effective_neg[i] + cumwidths_effective_neg[i + 1]) / 2
            )
            self.ax.annotate(
                f"{names_neg[i]}",
                (x_position, 0),
                xycoords="data",
                xytext=(x_position, 50 + 30 * (i % 3)),
                # xytext=(x_position, custom_annotation_height_for_nice_plot[i]),
                textcoords="data",
                arrowprops=dict(width=0.5, headwidth=0),
                rotation=-60,
                fontsize=9,
                ha="right",
                va="bottom",
            )

        # Fill under the step plot with different colors for each step
        for i in range(0, (len(widths_effective_neg) - 2)):
            # Create a polygon for each step
            polygon = plt.Polygon(
                [
                    (cumwidths_effective_neg[-1] - cumwidths_effective_neg[i], 0),
                    (
                        cumwidths_effective_neg[-1] - cumwidths_effective_neg[i],
                        heights_neg[i + 1],
                    ),
                    (
                        cumwidths_effective_neg[-1] - cumwidths_effective_neg[i + 1],
                        heights_neg[i + 1],
                    ),
                    (cumwidths_effective_neg[-1] - cumwidths_effective_neg[i + 1], 0),
                ],
                closed=True,
                alpha=1,
                facecolor=colors_neg[i],
                edgecolor="black",
                linewidth=0.5,
                linestyle="dotted",
            )
            self.ax.add_patch(polygon)

        if scc_year is not None:
            self.ax.axhline(scc_year, color="firebrick", linestyle="--", linewidth=1)
            self.ax.text(
                10, scc_year * 1.02, "Reference carbon value", color="firebrick", fontsize=8
            )

        self.ax.set_ylabel("Carbon Abatement Cost (€/t$\mathregular{CO_2}$)")
        self.ax.set_xlabel("$\mathregular{CO_2}$ abatted (Mt)")

        self.ax.axhline(0, color="black", linestyle="--", linewidth=1)

        self.ax.axvline(0, color="black", linestyle="--", linewidth=1)

        legend_patches_1 = [
            Line2D(
                [0], [0], color="black", linewidth=1, linestyle="-", label="Marginal Abatement Cost"
            ),
            mpatches.Patch(color="gold", alpha=1, label="Short-Range Efficiency"),
            mpatches.Patch(color="goldenrod", alpha=1, label="Medium-Range Efficiency"),
            mpatches.Patch(color="darkgoldenrod", alpha=1, label="Long-Range Efficiency"),
            mpatches.Patch(color="khaki", alpha=1, label="Freighter Efficiency"),
            mpatches.Patch(color="orange", alpha=1, label="Operations"),
            mpatches.Patch(color="yellowgreen", alpha=1, label="Energy"),
        ]

        self.ax.add_artist(
            self.ax.legend(
                handles=legend_patches_1,
                fontsize=9,
                title="Type of lever",
                loc="upper left",
                bbox_to_anchor=(60 / self.ax.figure.bbox.width, 1),
            )
        )

        self.ax.set_xlim(
            cumwidths_effective_neg[-1] - 100,
            cumwidths_effective_pos[-1] - widths_effective_pos[-1] + 50,
        )
        self.ax.set_ylim(
            max(-300, min(min(heights_pos), min(heights_neg)) - 50),
            min(2000, max(max(heights_neg), max(heights_pos)) + 300),
        )

        # Add abatement and emission zones
        self.ax.axvspan(
            xmin=self.ax.get_xlim()[0],
            xmax=0,
            facecolor="#ff70a6",
            alpha=0.1,
            clip_on=True,
            zorder=-1,
        )
        self.ax.axvspan(
            xmin=0,
            xmax=self.ax.get_xlim()[1],
            facecolor="#70d6ff",
            alpha=0.15,
            clip_on=True,
            zorder=-1,
        )

        self.ax.text(
            -1,
            self.ax.get_ylim()[1] / 2.8,
            "Extra carbon emissions",
            rotation=90,
            va="bottom",
            ha="right",
            fontsize=10,
            color="dimgrey",
        )
        self.ax.text(
            5,
            self.ax.get_ylim()[1] / 2.8,
            "Carbon abatement",
            rotation=90,
            va="bottom",
            ha="left",
            fontsize=10,
            color="dimgrey",
        )

        self.ax.grid()
        self.ax.set_title(f"Marginal abatement cost curve for year {year}")

        self.ax2.xaxis.set_label_position("bottom")
        self.ax2.set_xlabel("Annual $\mathregular{CO_2}$ emissions (Mt)")

        self.ax2.spines["bottom"].set_position(("axes", -0.1))  # Move spine below the plot
        self.ax2.xaxis.set_ticks_position("bottom")

        self.ax2.set_xlim(
            self.df.co2_emissions_2019technology[year]
            - self.ax.get_xlim()[0]
            - cumwidths_effective_neg[-1],
            self.df.co2_emissions_2019technology[year]
            - self.ax.get_xlim()[1]
            - cumwidths_effective_neg[-1],
        )

        self.fig.tight_layout()
        self.fig.canvas.draw()


class CumulativeMACC:
    def __init__(self, process, fleet_model):
        data = process.data
        self.df = data["vector_outputs"]
        self.fleet_model = fleet_model
        self.float_outputs = data["float_outputs"]
        self.float_inputs = data["float_inputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]
        self.pathways_manager = process.pathways_manager

        try:
            self.fig, self.ax = plt.subplots(
                figsize=(10, 7),
            )
            self.ax2 = self.ax.twiny()
            self.create_plot_data()
            self.update()
        except Exception as e:
            raise RuntimeError(
                "Error in creating plot. Possible cause: this plot requires top-down fleet model, "
                "abatement cost and complex energy cost models. Be sure to select them in the scenario settings."
            ) from e

    def create_plot_data(self):
        social_discount_rate = self.float_inputs["social_discount_rate"]
        start_year = self.prospective_years[1]  # not 2019
        end_year = self.prospective_years[-1]

        # macc_dict = {}

        name_list = []
        cumvol_list = []
        cumcost_list = []
        discounted_cumcost_list = []
        # undiscounted_cac_list = []
        # discounted_cac_list = []

        colors_list = []

        for category, sets in self.fleet_model.fleet.all_aircraft_elements.items():
            for aircraft_var in sets:
                if hasattr(aircraft_var, "parameters"):
                    aircraft_var_name = aircraft_var.parameters.full_name
                else:
                    aircraft_var_name = aircraft_var.full_name

                cumvol = 0
                cumcost = 0
                discountedcumcost = 0
                for year in range(start_year, end_year + 1):
                    year_vol = (
                        self.fleet_model.df.loc[
                            year, aircraft_var_name + ":aircraft_carbon_abatement_volume"
                        ]
                        / 1000000
                    )

                    year_cost = (
                        year_vol
                        * 1000000
                        * self.fleet_model.df.loc[
                            year, aircraft_var_name + ":aircraft_carbon_abatement_cost"
                        ]
                    )

                    cumvol += year_vol
                    cumcost += year_cost
                    discountedcumcost += year_cost / (1 + social_discount_rate) ** (
                        year - start_year
                    )
                cumvol_list.append(cumvol)
                cumcost_list.append(cumcost)
                discounted_cumcost_list.append(discountedcumcost)

                if category == "Short Range":
                    colors_list.append("gold")
                elif category == "Medium Range":
                    colors_list.append("goldenrod")
                else:
                    colors_list.append("darkgoldenrod")
                name_list.append(aircraft_var_name.split(":")[-1])

        name_list.extend(
            [
                el
                for el in [
                    "Freighter - Dropin",
                    "Freighter - Hydrogen",
                    "Freighter - Electric",
                    "OPS",
                    "OPS - Freighter",
                    "LF",
                ]
            ]
        )

        # Abatement effective in MtCO2e
        cumvol_list.extend(
            [
                elt / 1000000
                for elt in [
                    self.df.aircraft_carbon_abatement_volume_freight_dropin.loc[
                        start_year:end_year
                    ].sum(),
                    self.df.aircraft_carbon_abatement_volume_freight_hydrogen.loc[
                        start_year:end_year
                    ].sum(),
                    self.df.aircraft_carbon_abatement_volume_freight_electric.loc[
                        start_year:end_year
                    ].sum(),
                    self.df.operations_abatement_effective.loc[start_year:end_year].sum(),
                    self.df.operations_abatement_effective_freight.loc[start_year:end_year].sum(),
                    self.df.load_factor_abatement_effective.loc[start_year:end_year].sum(),
                ]
            ]
        )

        # carbon abatement cost in (€/tCO2e)
        cumcost_list.extend(
            [
                el
                for el in [
                    (
                        self.df.aircraft_carbon_abatement_cost_freight_dropin.loc[
                            start_year:end_year
                        ]
                        * self.df.aircraft_carbon_abatement_volume_freight_dropin.loc[
                            start_year:end_year
                        ]
                    ).sum(),
                    (
                        self.df.aircraft_carbon_abatement_cost_freight_hydrogen.loc[
                            start_year:end_year
                        ]
                        * self.df.aircraft_carbon_abatement_volume_freight_hydrogen.loc[
                            start_year:end_year
                        ]
                    ).sum(),
                    (
                        self.df.aircraft_carbon_abatement_cost_freight_electric.loc[
                            start_year:end_year
                        ]
                        * self.df.aircraft_carbon_abatement_volume_freight_electric.loc[
                            start_year:end_year
                        ]
                    ).sum(),
                    (
                        self.df.operations_abatement_cost.loc[start_year:end_year]
                        * self.df.operations_abatement_effective.loc[start_year:end_year]
                    ).sum(),
                    (
                        self.df.operations_abatement_cost_freight.loc[start_year:end_year]
                        * self.df.operations_abatement_effective_freight.loc[start_year:end_year]
                    ).sum(),
                    (
                        self.df.load_factor_abatement_cost.loc[start_year:end_year]
                        * self.df.load_factor_abatement_effective.loc[start_year:end_year]
                    ).sum(),
                ]
            ]
        )

        power_series = pd.Series(
            [
                (1 + social_discount_rate) ** (year - start_year)
                for year in range(start_year, end_year + 1)
            ],
            index=range(start_year, end_year + 1),
        )

        discounted_cumcost_list.extend(
            [
                el
                for el in [
                    (
                        self.df.aircraft_carbon_abatement_cost_freight_dropin.loc[
                            start_year:end_year
                        ]
                        * self.df.aircraft_carbon_abatement_volume_freight_dropin.loc[
                            start_year:end_year
                        ]
                        / power_series
                    ).sum(),
                    (
                        self.df.aircraft_carbon_abatement_cost_freight_hydrogen.loc[
                            start_year:end_year
                        ]
                        * self.df.aircraft_carbon_abatement_volume_freight_hydrogen.loc[
                            start_year:end_year
                        ]
                        / power_series
                    ).sum(),
                    (
                        self.df.aircraft_carbon_abatement_cost_freight_electric.loc[
                            start_year:end_year
                        ]
                        * self.df.aircraft_carbon_abatement_volume_freight_electric.loc[
                            start_year:end_year
                        ]
                        / power_series
                    ).sum(),
                    (
                        self.df.operations_abatement_cost.loc[start_year:end_year]
                        * self.df.operations_abatement_effective.loc[start_year:end_year]
                        / power_series
                    ).sum(),
                    (
                        self.df.operations_abatement_cost_freight.loc[start_year:end_year]
                        * self.df.operations_abatement_effective_freight.loc[start_year:end_year]
                        / power_series
                    ).sum(),
                    (
                        self.df.load_factor_abatement_cost.loc[start_year:end_year]
                        * self.df.load_factor_abatement_effective.loc[start_year:end_year]
                        / power_series
                    ).sum(),
                ]
            ]
        )

        colors_list.extend(
            [
                el
                for el in [
                    "khaki",
                    "khaki",
                    "khaki",
                    "orange",
                    "orange",
                    "orange",
                ]
            ]
        )

        # now add generic energy production pathways
        for pathway in self.pathways_manager.get_all():
            if pathway.name != "fossil_kerosene":
                name_list.append(pathway.name)
                abatement_col = f"{pathway.name}_abatement_effective"
                if abatement_col not in self.df.columns:
                    raise ValueError(
                        f"Pathway {pathway.name} abatement is not defined. Pathways must be defined with bottom-up model."
                    )
                cumvol = self.df[abatement_col].loc[start_year:end_year].sum() / 1000000
                cumvol_list.append(cumvol)

                cac_col = f"{pathway.name}_carbon_abatement_cost"
                if cac_col not in self.df.columns:
                    raise ValueError(
                        f"Pathway {pathway.name} carbon abatement cost is not defined. Pathways must be defined with bottom-up model."
                    )
                cumcost = (
                    self.df[cac_col].loc[start_year:end_year]
                    * self.df[abatement_col].loc[start_year:end_year]
                ).sum()
                cumcost_list.append(cumcost)

                discounted_cumcost = (
                    self.df[cac_col].loc[start_year:end_year]
                    * self.df[abatement_col].loc[start_year:end_year]
                    / power_series
                ).sum()
                discounted_cumcost_list.append(discounted_cumcost)

                colors_list.append("yellowgreen")

        undiscounted_cac_list = [
            a / (b * 1000000) if (b != 0 and not np.isnan(b)) else np.NaN
            for a, b in zip(cumcost_list, cumvol_list)
        ]
        discounted_cac_list = [
            a / (b * 1000000) if (b != 0 and not np.isnan(b)) else np.NaN
            for a, b in zip(discounted_cumcost_list, cumvol_list)
        ]

        macc_df = pd.DataFrame(
            data=[
                cumvol_list,
                cumcost_list,
                discounted_cumcost_list,
                undiscounted_cac_list,
                discounted_cac_list,
                colors_list,
            ],
            columns=name_list,
            index=[
                "abatement_effective",
                "cumulative_abatement_cost",
                "discoutend_cumulative_abatement_cost",
                "undiscounted_carbon_abatement_cost",
                "carbon_abatement_cost",
                "colors",
            ],
        )
        self.macc_df = (
            macc_df.transpose()
            .sort_values(by="carbon_abatement_cost")
            .dropna(subset="carbon_abatement_cost")
        )

    def update(self):
        self.ax.cla()

        maccneg_df = self.macc_df[self.macc_df["abatement_effective"] < 0]
        maccpos_df = self.macc_df[self.macc_df["abatement_effective"] > 0]

        ##### POS ######

        heights_pos = maccpos_df["carbon_abatement_cost"].to_list()
        names_pos = maccpos_df.index.to_list()
        heights_pos.insert(0, 0)
        heights_pos.append(0)

        # # Max effective maccpos
        widths_effective_pos = maccpos_df["abatement_effective"].to_list()
        widths_effective_pos.insert(0, 0)
        widths_effective_pos.append(widths_effective_pos[-1])

        cumwidths_effective_pos = np.cumsum(widths_effective_pos)

        colors_pos = maccpos_df["colors"].to_list()

        self.ax.step(
            cumwidths_effective_pos - widths_effective_pos,
            heights_pos,
            where="post",
            color="black",
            label="Marginal abatement cost",
            linewidth=1,
            zorder=10,  # ensure top level
        )

        # custom_annotation_height_for_nice_plot = [100, 80, 80, 80, 80, 80, 80, 80, 20, 20, 50, 100, 120, 140, 170, 200,
        #                                           180, 180, 250, 300, 350, 400]

        for i in range(len(widths_effective_pos) - 2):
            x_position = (cumwidths_effective_pos[i] + cumwidths_effective_pos[i + 1]) / 2
            y_position = min(heights_pos[i + 1], 2000)
            if heights_pos[i + 1] >= 0:
                if heights_pos[i + 1] >= 2000:
                    text = f"{names_pos[i]}\n {int(heights_pos[i + 1])}"
                else:
                    text = f"{names_pos[i]}"
                self.ax.annotate(
                    text,
                    (x_position, y_position),
                    xycoords="data",
                    xytext=(x_position, y_position + 50),
                    # xytext=(x_position, custom_annotation_height_for_nice_plot[i]),
                    textcoords="data",
                    arrowprops=dict(width=0.3, headwidth=0),
                    rotation=-60,
                    fontsize=9,
                    ha="right",
                    va="bottom",
                )
            else:
                self.ax.annotate(
                    f"{names_pos[i]}",
                    (x_position, 0),
                    xycoords="data",
                    xytext=(x_position, min(50, max(heights_pos) - 50) + 30 * (i % 3)),
                    # xytext=(x_position, custom_annotation_height_for_nice_plot[i]),
                    textcoords="data",
                    arrowprops=dict(width=0.3, headwidth=0),
                    rotation=-60,
                    fontsize=9,
                    ha="right",
                    va="bottom",
                )

        # Fill under the step plot with different colors for each step
        for i in range(0, (len(widths_effective_pos) - 2)):
            # Create a polygon for each step
            polygon = plt.Polygon(
                [
                    (cumwidths_effective_pos[i], 0),
                    (cumwidths_effective_pos[i], heights_pos[i + 1]),
                    (cumwidths_effective_pos[i + 1], heights_pos[i + 1]),
                    (cumwidths_effective_pos[i + 1], 0),
                ],
                closed=True,
                alpha=1,
                facecolor=colors_pos[i],
                edgecolor="black",
                linewidth=0.5,
                linestyle="dotted",
            )
            self.ax.add_patch(polygon)

        ##### NEG #####

        heights_neg = maccneg_df["carbon_abatement_cost"].to_list()
        names_neg = maccneg_df.index.to_list()

        heights_neg.append(0)
        heights_neg.insert(0, 0)

        # # Mself.ax effective maccneg
        widths_effective_neg = maccneg_df["abatement_effective"].to_list()

        widths_effective_neg.insert(0, 0)
        widths_effective_neg.append(0)

        cumwidths_effective_neg = np.cumsum(widths_effective_neg)

        colors_neg = maccneg_df["colors"].to_list()

        self.ax.step(
            np.cumsum(widths_effective_neg)[-1]
            - np.cumsum(widths_effective_neg)
            + widths_effective_neg,
            heights_neg,
            where="post",
            color="#335C67",
            label="Marginal emission cost",
            linewidth=1,
            zorder=9,
        )

        # custom_annotation_height_for_nice_plot = [20,45,70,95,120]

        for i in range(len(widths_effective_neg) - 2):
            x_position = (
                cumwidths_effective_neg[-1]
                - (cumwidths_effective_neg[i] + cumwidths_effective_neg[i + 1]) / 2
            )
            self.ax.annotate(
                f"{names_neg[i]}",
                (x_position, 0),
                xycoords="data",
                # xytext=(x_position, custom_annotation_height_for_nice_plot[i]),
                xytext=(x_position, 50 + 30 * (i % 3)),
                textcoords="data",
                arrowprops=dict(width=0.3, headwidth=0),
                rotation=-60,
                fontsize=9,
                ha="right",
                va="bottom",
            )

        # Fill under the step plot with different colors for each step
        for i in range(0, (len(widths_effective_neg) - 2)):
            # Create a polygon for each step
            polygon = plt.Polygon(
                [
                    (cumwidths_effective_neg[-1] - cumwidths_effective_neg[i], 0),
                    (
                        cumwidths_effective_neg[-1] - cumwidths_effective_neg[i],
                        heights_neg[i + 1],
                    ),
                    (
                        cumwidths_effective_neg[-1] - cumwidths_effective_neg[i + 1],
                        heights_neg[i + 1],
                    ),
                    (cumwidths_effective_neg[-1] - cumwidths_effective_neg[i + 1], 0),
                ],
                closed=True,
                alpha=1,
                facecolor=colors_neg[i],
                edgecolor="black",
                linewidth=0.5,
                linestyle="dotted",
            )
            self.ax.add_patch(polygon)

        self.ax.set_ylabel("Carbon Abatement Cost (€/t$\mathregular{CO_2}$)")
        self.ax.set_xlabel("Cumulative $\mathregular{CO_2}$ abatted (Mt)")

        self.ax.axhline(0, color="black", linestyle="--", linewidth=1)

        self.ax.axvline(0, color="black", linestyle="--", linewidth=1)

        legend_patches_1 = [
            Line2D(
                [0], [0], color="black", linewidth=1, linestyle="-", label="Marginal Abatement Cost"
            ),
            mpatches.Patch(color="gold", alpha=1, label="Short-Range Efficiency"),
            mpatches.Patch(color="goldenrod", alpha=1, label="Medium-Range Efficiency"),
            mpatches.Patch(color="darkgoldenrod", alpha=1, label="Long-Range Efficiency"),
            mpatches.Patch(color="khaki", alpha=1, label="Freighter Efficiency"),
            mpatches.Patch(color="orange", alpha=1, label="Operations"),
            mpatches.Patch(color="yellowgreen", alpha=1, label="Energy"),
        ]

        self.ax.legend(
            handles=legend_patches_1,
            title="Type of lever",
            loc="upper left",
            bbox_to_anchor=(90 / self.ax.figure.bbox.width, 1),
        )

        self.ax.set_xlim(
            cumwidths_effective_neg[-1] - 1500,
            cumwidths_effective_pos[-1] - widths_effective_pos[-1] + 500,
        )
        self.ax.set_ylim(
            max(-300, min(min(heights_pos), min(heights_neg)) - 50),
            min(2000, max(max(heights_neg), max(heights_pos)) + 230),
        )

        # Add abatement and emission zones
        self.ax.axvspan(
            xmin=self.ax.get_xlim()[0],
            xmax=0,
            facecolor="#ff70a6",
            alpha=0.1,
            clip_on=True,
            zorder=-1,
        )
        self.ax.axvspan(
            xmin=0,
            xmax=self.ax.get_xlim()[1],
            facecolor="#70d6ff",
            alpha=0.15,
            clip_on=True,
            zorder=-1,
        )

        self.ax.text(
            -5,
            self.ax.get_ylim()[1] / 2.4,
            "Extra carbon emissions",
            rotation=90,
            va="bottom",
            ha="right",
            fontsize=10,
            color="dimgrey",
        )
        self.ax.text(
            30,
            self.ax.get_ylim()[1] / 2.4,
            "Carbon abatement",
            rotation=90,
            va="bottom",
            ha="left",
            fontsize=10,
            color="dimgrey",
        )

        self.ax.grid()
        self.ax.set_title(
            f"Cumulative marginal abatement cost curve, for starting year {self.prospective_years[1]}"
        )

        self.ax2.xaxis.set_label_position("bottom")
        self.ax2.set_xlabel("cumulative $\mathregular{CO_2}$ emissions (Mt)")

        self.ax2.spines["bottom"].set_position(("axes", -0.1))  # Move spine below the plot
        self.ax2.xaxis.set_ticks_position("bottom")

        self.ax2.set_xlim(
            self.df.cumulative_co2_emissions_2019technology[self.prospective_years[-1]] * 1000
            - self.ax.get_xlim()[0]
            - cumwidths_effective_neg[-1],
            self.df.cumulative_co2_emissions_2019technology[self.prospective_years[-1]] * 1000
            - self.ax.get_xlim()[1]
            - cumwidths_effective_neg[-1],
        )

        self.fig.tight_layout()
        self.fig.canvas.draw()


class ScenarioMACC:
    def __init__(self, process, fleet_model):
        data = process.data
        self.df = data["vector_outputs"]
        self.fleet_model = fleet_model
        self.float_outputs = data["float_outputs"]
        self.float_inputs = data["float_inputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]
        self.pathways_manager = process.pathways_manager

        self.fig, (self.ax, self.ax_scc) = plt.subplots(
            2, 1, figsize=(10, 7), sharex=True, gridspec_kw={"height_ratios": [20, 1]}
        )
        divider = make_axes_locatable(self.ax)
        dummy_divider = make_axes_locatable(self.ax_scc)

        try:
            # Create ax2 for the colorbar
            self.ax2 = divider.append_axes("right", size="3%", pad=0.1)
            # Create a dummy ax to keep sharex
            self.dummy_ax = dummy_divider.append_axes("right", size="3%", pad=0.1)
            self.dummy_ax.set_visible(False)

            self.create_plot_data()
            self.plot_interact()
        except Exception as e:
            raise RuntimeError(
                "Error in creating plot. Possible cause: this plot requires top-down fleet model, "
                "abatement cost and complex energy cost models. Be sure to select them in the scenario settings."
            ) from e

    def plot_interact(self):
        metric_widget = widgets.Dropdown(
            options=[
                ("Instantaneous Carbon Abatement Cost", "carbon_abatement_cost"),
                ("Specific Carbon Abatement Cost", "specific_carbon_abatement_cost"),
                (
                    "Generic Specific Carbon Abatement Cost",
                    "generic_specific_carbon_abatement_cost",
                ),
            ],
            value="specific_carbon_abatement_cost",
            description="Metric:",
        )

        scc_widget = widgets.FloatText(description="Base year SCC (Specific CAC ONLY):")

        def update_numeric_widget(change):
            if change["new"] == "specific_carbon_abatement_cost":
                scc_widget.disabled = False
            else:
                scc_widget.disabled = True
                scc_widget.value = 0

        metric_widget.observe(update_numeric_widget, names="value")

        interact(self.update, metric=metric_widget, scc_start=scc_widget)

    def create_plot_data(self):
        self.macc_dict = {}

        for year in range(self.prospective_years[0], self.prospective_years[-1] + 1):
            name = []
            vol = []
            cost = []
            spe_cost = []
            g_spe_cost = []

            colors = []

            # Start with discrete aircraft from the fleet model
            for category, sets in self.fleet_model.fleet.all_aircraft_elements.items():
                for aircraft_var in sets:
                    if hasattr(aircraft_var, "parameters"):
                        aircraft_var_name = aircraft_var.parameters.full_name
                    else:
                        aircraft_var_name = aircraft_var.full_name

                    vol.append(
                        self.fleet_model.df.loc[
                            year, aircraft_var_name + ":aircraft_carbon_abatement_volume"
                        ]
                        / 1000000
                    )
                    cost.append(
                        self.fleet_model.df.loc[
                            year, aircraft_var_name + ":aircraft_carbon_abatement_cost"
                        ]
                    )

                    spe_cost.append(
                        self.fleet_model.df.loc[
                            year, aircraft_var_name + ":aircraft_specific_carbon_abatement_cost"
                        ]
                    )

                    g_spe_cost.append(
                        self.fleet_model.df.loc[
                            year,
                            aircraft_var_name + ":aircraft_generic_specific_carbon_abatement_cost",
                        ]
                    )
                    if category == "Short Range":
                        colors.append("gold")
                    elif category == "Medium Range":
                        colors.append("goldenrod")
                    else:
                        colors.append("darkgoldenrod")
                    name.append(aircraft_var_name.split(":")[-1])

            # continue with generic energy production pathways

            for pathway in self.pathways_manager.get_all():
                if (
                    pathway.name != "fossil_kerosene"
                ):  # hard coded for cac now, may be parametrized later
                    name.append(pathway.name)
                    abatement_col = f"{pathway.name}_abatement_effective"
                    if abatement_col not in self.df.columns:
                        raise ValueError(
                            f"Pathway {pathway.name} abatement is not defined. Pathways must be defined with bottom-up model."
                        )
                    vol.append(self.df[f"{pathway.name}_abatement_effective"][year] / 1000000)
                    cac_col = f"{pathway.name}_carbon_abatement_cost"
                    if cac_col not in self.df.columns:
                        raise ValueError(
                            f"Pathway {pathway.name} carbon abatement cost is not defined. Pathways must be defined with bottom-up model."
                        )
                    cost.append(self.df[f"{pathway.name}_carbon_abatement_cost"][year])
                    spe_cac_col = f"{pathway.name}_specific_carbon_abatement_cost"
                    if spe_cac_col not in self.df.columns:
                        raise ValueError(
                            f"Pathway {pathway.name} specific carbon abatement cost is not defined. Pathways must be defined with bottom-up model."
                        )
                    spe_cost.append(self.df[f"{pathway.name}_specific_carbon_abatement_cost"][year])
                    g_spe_cac_col = f"{pathway.name}_generic_specific_carbon_abatement_cost"
                    if g_spe_cac_col not in self.df.columns:
                        raise ValueError(
                            f"Pathway {pathway.name} generic specific carbon abatement cost is not defined. Pathways must be defined with bottom-up model."
                        )
                    g_spe_cost.append(
                        self.df[f"{pathway.name}_generic_specific_carbon_abatement_cost"][year]
                    )
                    colors.append("yellowgreen")

            name.extend(
                [
                    el
                    for el in [
                        "Freighter - Drop in",
                        "Freighter - Hydrogen",
                        "Freighter - Electric",
                        "OPS",
                        "OPS - Freight",
                        "Load Factor",
                    ]
                ]
            )

            # Abatement effective in MtCO2e
            vol.extend(
                [
                    elt / 1000000
                    for elt in [
                        self.df.aircraft_carbon_abatement_volume_freight_dropin[year],
                        self.df.aircraft_carbon_abatement_volume_freight_hydrogen[year],
                        self.df.aircraft_carbon_abatement_volume_freight_electric[year],
                        self.df.operations_abatement_effective[year],
                        self.df.operations_abatement_effective_freight[year],
                        self.df.load_factor_abatement_effective[year],
                    ]
                ]
            )

            # carbon abatement cost in (€/tCO2e)
            cost.extend(
                [
                    el
                    for el in [
                        self.df.aircraft_carbon_abatement_cost_freight_dropin[year],
                        self.df.aircraft_carbon_abatement_cost_freight_hydrogen[year],
                        self.df.aircraft_carbon_abatement_cost_freight_electric[year],
                        self.df.operations_abatement_cost[year],
                        self.df.operations_abatement_cost_freight[year],
                        self.df.load_factor_abatement_cost[year],
                    ]
                ]
            )

            spe_cost.extend(
                [
                    el
                    for el in [
                        self.df.aircraft_specific_carbon_abatement_cost_freight_dropin[year],
                        self.df.aircraft_specific_carbon_abatement_cost_freight_hydrogen[year],
                        self.df.aircraft_specific_carbon_abatement_cost_freight_electric[year],
                        self.df.operations_specific_abatement_cost[year],
                        self.df.operations_specific_abatement_cost_freight[year],
                        self.df.load_factor_specific_abatement_cost[year],
                    ]
                ]
            )

            g_spe_cost.extend(
                [
                    el
                    for el in [
                        self.df.aircraft_generic_specific_carbon_abatement_cost_freight_dropin[
                            year
                        ],
                        self.df.aircraft_generic_specific_carbon_abatement_cost_freight_hydrogen[
                            year
                        ],
                        self.df.aircraft_generic_specific_carbon_abatement_cost_freight_electric[
                            year
                        ],
                        self.df.operations_generic_specific_abatement_cost[year],
                        self.df.operations_generic_specific_abatement_cost_freight[year],
                        self.df.load_factor_generic_specific_abatement_cost[year],
                    ]
                ]
            )

            colors.extend(
                [
                    el
                    for el in [
                        "khaki",
                        "khaki",
                        "khaki",
                        "orange",
                        "orange",
                        "orange",
                    ]
                ]
            )

            macc_df = pd.DataFrame(
                data=[vol, cost, spe_cost, g_spe_cost, colors],
                columns=name,
                index=[
                    "abatement_effective",
                    "carbon_abatement_cost",
                    "specific_carbon_abatement_cost",
                    "generic_specific_carbon_abatement_cost",
                    "colors",
                ],
            )

            macc_df = macc_df.transpose()

            self.macc_dict[year] = macc_df

    def update(self, metric, scc_start):
        self.ax.cla()
        self.ax_scc.cla()
        self.ax2.cla()
        self.dummy_ax.cla()
        scc_list = []

        for year in range(self.prospective_years[0], self.prospective_years[-1] + 1):
            macc_df = self.macc_dict[year]

            macc_df = macc_df.sort_values(by=metric)

            macc_df = macc_df.dropna(subset=metric)

            maccneg_df = macc_df[macc_df["abatement_effective"] < 0]
            maccpos_df = macc_df[macc_df["abatement_effective"] > 0]

            ##### POS ######

            heights_pos = maccpos_df[metric].to_numpy()
            widths_effective_pos = maccpos_df["abatement_effective"].to_numpy()

            cumwidths_pos = np.cumsum(widths_effective_pos)

            if metric == "specific_carbon_abatement_cost":
                scc_year = scc_start * (
                    (1 + self.float_inputs["social_discount_rate"])
                    ** (year - self.prospective_years[0])
                )
                scc_list.append(scc_year)
                hatch_list = []
                for value in heights_pos:
                    # Check if the value is above the threshold
                    if value > scc_year:
                        hatch_list.append("..")
                    else:
                        hatch_list.append("")

            elif metric == "generic_specific_carbon_abatement_cost":
                scc_year = self.df.loc[year, "exogenous_carbon_price_trajectory"]
                scc_list.append(scc_year)
                hatch_list = []
                for value in heights_pos:
                    # Check if the value is above the threshold
                    if value > scc_year:
                        hatch_list.append("..")
                    else:
                        hatch_list.append("")

            else:
                hatch_list = ["" for val in heights_pos]

            norm = Normalize(vmin=-300, vmax=1000)

            for i in range(len(heights_pos)):
                self.ax.bar(
                    year,
                    widths_effective_pos[i],
                    color=plt.cm.RdBu_r(norm(heights_pos[i])),
                    bottom=cumwidths_pos[i] - widths_effective_pos[i],
                    edgecolor="black",
                    hatch=hatch_list[i],
                    width=1,
                )

            ##### NEG ######
            heights_neg = maccneg_df[metric].to_numpy()
            widths_effective_neg = maccneg_df["abatement_effective"].to_numpy()

            cumwidths_neg = np.cumsum(widths_effective_neg)

            for i in range(len(heights_neg)):
                self.ax.bar(
                    year,
                    -widths_effective_neg[i],
                    color=plt.cm.RdBu_r(norm(heights_neg[i])),
                    bottom=cumwidths_neg[-1] - cumwidths_neg[i] + widths_effective_neg[i],
                    edgecolor="black",
                    hatch="xx",
                    width=1,
                )

            # colorbar ssc
            if metric != "carbon_abatement_cost":
                self.ax_scc.set_visible(True)
                self.ax_scc.bar(
                    year,
                    1,
                    color=plt.cm.RdBu_r(norm(scc_year)),
                    bottom=0,
                    edgecolor="black",
                    width=1,
                )

                self.ax.legend(
                    handles=[
                        mpatches.Patch(facecolor="none", edgecolor="black", hatch=".."),
                        mpatches.Patch(facecolor="none", edgecolor="black"),
                        mpatches.Patch(facecolor="none", edgecolor="black", hatch="xx"),
                    ],
                    labels=["Above SCC", "Below or Equal to SCC", "Extra Emissions"],
                )
            else:
                self.ax_scc.set_visible(False)

                self.ax.legend(
                    handles=[
                        mpatches.Patch(facecolor="none", edgecolor="black", hatch="xx"),
                    ],
                    labels=["Extra Emissions"],
                )

        # Create a ScalarMappable to display the colormap as a legend

        sm = ScalarMappable(cmap=plt.cm.RdBu_r, norm=norm)
        sm.set_array([])  # Set an empty array since we don't have specific data values

        self.fig.colorbar(
            sm, cax=self.ax2, label="Carbon Abatement Cost (€/t$\mathregular{CO_2}$)", norm=norm
        )

        # Hatch legedn

        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Abatement Effective (Mt)")
        self.ax.tick_params(labelbottom=True)

        self.ax_scc.set_xlim(
            (2 * self.prospective_years[0] - 1) / 2, (2 * self.prospective_years[-1] + 1) / 2
        )
        self.ax_scc.set_ylim(0, 1)
        self.ax_scc.yaxis.set_visible(False)
        self.ax_scc.tick_params(top=True, bottom=False, labelbottom=False)
        self.ax_scc.set_xlabel("Reference carbon value (€/t$\mathregular{CO_2}$)")

        self.ax.set_title("Scenario Carbon Abatement Cost Evolution")
        self.ax.yaxis.grid(True)
        self.fig.tight_layout()
        self.fig.canvas.draw()


class ShadowCarbonPrice:
    def __init__(self, process, fleet_model):
        data = process.data
        self.df = data["vector_outputs"]
        self.fleet_model = fleet_model
        self.float_outputs = data["float_outputs"]
        self.float_inputs = data["float_inputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]
        self.pathways_manager = process.pathways_manager

        try:
            self.fig, self.ax = plt.subplots(figsize=(10, 7))

            self.create_plot_data()
            self.plot_interact()
        except Exception as e:
            raise RuntimeError(
                "Error in creating plot. Possible cause: this plot requires top-down fleet model, "
                "abatement cost and complex energy cost models. Be sure to select them in the scenario settings."
            ) from e

    def plot_interact(self):
        metric_widget = widgets.Dropdown(
            options=[
                ("Specific Carbon Abatement Cost", "specific_carbon_abatement_cost"),
                (
                    "Generic Specific Carbon Abatement Cost",
                    "generic_specific_carbon_abatement_cost",
                ),
            ],
            value="generic_specific_carbon_abatement_cost",
            description="Metric:",
        )

        scc_widget = widgets.FloatText(description="Base year SCC (Specific CAC ONLY):")

        def update_numeric_widget(change):
            if change["new"] == "specific_carbon_abatement_cost":
                scc_widget.disabled = False
            else:
                scc_widget.disabled = True
                scc_widget.value = 0

        metric_widget.observe(update_numeric_widget, names="value")

        interact(self.update, metric=metric_widget, scc_start=scc_widget)

    def create_plot_data(self):
        self.macc_dict = {}

        for year in range(self.prospective_years[0], self.prospective_years[-1] + 1):
            name = []
            vol = []
            cost = []
            spe_cost = []
            g_spe_cost = []

            colors = []
            # Start with discrete aircraft from the fleet model
            for category, sets in self.fleet_model.fleet.all_aircraft_elements.items():
                for aircraft_var in sets:
                    if hasattr(aircraft_var, "parameters"):
                        aircraft_var_name = aircraft_var.parameters.full_name
                    else:
                        aircraft_var_name = aircraft_var.full_name

                    vol.append(
                        self.fleet_model.df.loc[
                            year, aircraft_var_name + ":aircraft_carbon_abatement_volume"
                        ]
                        / 1000000
                    )
                    cost.append(
                        self.fleet_model.df.loc[
                            year, aircraft_var_name + ":aircraft_carbon_abatement_cost"
                        ]
                    )

                    spe_cost.append(
                        self.fleet_model.df.loc[
                            year, aircraft_var_name + ":aircraft_specific_carbon_abatement_cost"
                        ]
                    )

                    g_spe_cost.append(
                        self.fleet_model.df.loc[
                            year,
                            aircraft_var_name + ":aircraft_generic_specific_carbon_abatement_cost",
                        ]
                    )
                    if category == "Short Range":
                        colors.append("gold")
                    elif category == "Medium Range":
                        colors.append("goldenrod")
                    else:
                        colors.append("darkgoldenrod")
                    name.append(aircraft_var_name.split(":")[-1])

            # continue with generic energy production pathways

            for pathway in self.pathways_manager.get_all():
                if (
                    pathway.name != "fossil_kerosene"
                ):  # hard coded for cac now, may be parametrized later
                    name.append(pathway.name)
                    abatement_col = f"{pathway.name}_abatement_effective"
                    if abatement_col not in self.df.columns:
                        raise ValueError(
                            f"Pathway {pathway.name} abatement is not defined. Pathways must be defined with bottom-up model."
                        )
                    vol.append(self.df[f"{pathway.name}_abatement_effective"][year] / 1000000)
                    cac_col = f"{pathway.name}_carbon_abatement_cost"
                    if cac_col not in self.df.columns:
                        raise ValueError(
                            f"Pathway {pathway.name} carbon abatement cost is not defined. Pathways must be defined with bottom-up model."
                        )
                    cost.append(self.df[f"{pathway.name}_carbon_abatement_cost"][year])
                    spe_cac_col = f"{pathway.name}_specific_carbon_abatement_cost"
                    if spe_cac_col not in self.df.columns:
                        raise ValueError(
                            f"Pathway {pathway.name} specific carbon abatement cost is not defined. Pathways must be defined with bottom-up model."
                        )
                    spe_cost.append(self.df[f"{pathway.name}_specific_carbon_abatement_cost"][year])
                    g_spe_cac_col = f"{pathway.name}_generic_specific_carbon_abatement_cost"
                    if g_spe_cac_col not in self.df.columns:
                        raise ValueError(
                            f"Pathway {pathway.name} generic specific carbon abatement cost is not defined. Pathways must be defined with bottom-up model."
                        )
                    g_spe_cost.append(
                        self.df[f"{pathway.name}_generic_specific_carbon_abatement_cost"][year]
                    )
                    colors.append("yellowgreen")

            name.extend(
                [
                    el
                    for el in [
                        "Freighter - Drop in",
                        "Freighter - Hydrogen",
                        "Freighter - Electric",
                        "OPS",
                        "OPS - Freight",
                        "Load Factor",
                    ]
                ]
            )

            # Abatement effective in MtCO2e
            vol.extend(
                [
                    elt / 1000000
                    for elt in [
                        self.df.aircraft_carbon_abatement_volume_freight_dropin[year],
                        self.df.aircraft_carbon_abatement_volume_freight_hydrogen[year],
                        self.df.aircraft_carbon_abatement_volume_freight_electric[year],
                        self.df.operations_abatement_effective[year],
                        self.df.operations_abatement_effective_freight[year],
                        self.df.load_factor_abatement_effective[year],
                    ]
                ]
            )

            # carbon abatement cost in (€/tCO2e)
            cost.extend(
                [
                    el
                    for el in [
                        self.df.aircraft_carbon_abatement_cost_freight_dropin[year],
                        self.df.aircraft_carbon_abatement_cost_freight_hydrogen[year],
                        self.df.aircraft_carbon_abatement_cost_freight_electric[year],
                        self.df.operations_abatement_cost[year],
                        self.df.operations_abatement_cost_freight[year],
                        self.df.load_factor_abatement_cost[year],
                    ]
                ]
            )

            spe_cost.extend(
                [
                    el
                    for el in [
                        self.df.aircraft_specific_carbon_abatement_cost_freight_dropin[year],
                        self.df.aircraft_specific_carbon_abatement_cost_freight_hydrogen[year],
                        self.df.aircraft_specific_carbon_abatement_cost_freight_electric[year],
                        self.df.operations_specific_abatement_cost[year],
                        self.df.operations_specific_abatement_cost_freight[year],
                        self.df.load_factor_specific_abatement_cost[year],
                    ]
                ]
            )

            g_spe_cost.extend(
                [
                    el
                    for el in [
                        self.df.aircraft_generic_specific_carbon_abatement_cost_freight_dropin[
                            year
                        ],
                        self.df.aircraft_generic_specific_carbon_abatement_cost_freight_hydrogen[
                            year
                        ],
                        self.df.aircraft_generic_specific_carbon_abatement_cost_freight_electric[
                            year
                        ],
                        self.df.operations_generic_specific_abatement_cost[year],
                        self.df.operations_generic_specific_abatement_cost_freight[year],
                        self.df.load_factor_generic_specific_abatement_cost[year],
                    ]
                ]
            )

            colors.extend(
                [
                    el
                    for el in [
                        "khaki",
                        "khaki",
                        "khaki",
                        "orange",
                        "orange",
                        "orange",
                    ]
                ]
            )

            macc_df = pd.DataFrame(
                data=[vol, cost, spe_cost, g_spe_cost, colors],
                columns=name,
                index=[
                    "abatement_effective",
                    "carbon_abatement_cost",
                    "specific_carbon_abatement_cost",
                    "generic_specific_carbon_abatement_cost",
                    "colors",
                ],
            )

            macc_df = macc_df.transpose()

            self.macc_dict[year] = macc_df

    def update(self, metric, scc_start):
        self.ax.cla()
        scc_list = []

        marginal_cac = []
        marginal_cac09 = []
        marginal_cac08 = []
        marginal_cac05 = []
        scc_list = []
        years = range(self.prospective_years[0], self.prospective_years[-1] + 1)

        for year in years:
            macc_df = self.macc_dict[year]

            macc_df = macc_df.sort_values(by=metric)

            macc_df = macc_df.dropna(subset=metric)

            # Plot only made for positive abatements
            maccpos_df = macc_df[macc_df["abatement_effective"] > 0]

            ##### POS ######

            heights_pos = maccpos_df[metric].to_numpy()
            widths_effective_pos = maccpos_df["abatement_effective"].to_numpy()

            if metric == "specific_carbon_abatement_cost":
                scc_year = scc_start * (
                    (1 + self.float_inputs["social_discount_rate"])
                    ** (year - self.prospective_years[0])
                )
                scc_list.append(scc_year)
            elif metric == "generic_specific_carbon_abatement_cost":
                scc_year = self.df.loc[year, "exogenous_carbon_price_trajectory"]
                scc_list.append(scc_year)

            if len(widths_effective_pos > 0):
                cumwidths_pos = np.cumsum(widths_effective_pos)

                target_value = 0.9 * cumwidths_pos[-1]
                index_val = np.searchsorted(cumwidths_pos, target_value, side="right")
                marginal_cac09.append(heights_pos[min(index_val, len(heights_pos))])

                target_value = 0.8 * cumwidths_pos[-1]
                index_val = np.searchsorted(cumwidths_pos, target_value, side="right")
                marginal_cac08.append(heights_pos[min(index_val, len(heights_pos))])

                target_value = 0.5 * cumwidths_pos[-1]
                index_val = np.searchsorted(cumwidths_pos, target_value, side="right")
                marginal_cac05.append(heights_pos[min(index_val, len(heights_pos))])

                marginal_cac.append(max(heights_pos))

            else:
                marginal_cac.append(np.NaN)
                marginal_cac09.append(np.NaN)
                marginal_cac08.append(np.NaN)
                marginal_cac05.append(np.NaN)

        self.ax.plot(
            years,
            marginal_cac,
            color="navy",
            linestyle="-",
            label="Initial Marginal Abatement Cost",
        )
        self.ax.plot(years, marginal_cac09, color="navy", linestyle="--", label="90% Abatement")
        self.ax.plot(years, marginal_cac08, color="navy", linestyle="-.", label="80% Abatement")
        self.ax.plot(years, marginal_cac05, color="navy", linestyle=":", label="50% Abatement")
        self.ax.plot(
            years,
            scc_list,
            color="orangered",
            linestyle="-",
            label="SCC",
        )
        # self.ax.plot(
        #     [2020,2025,2050],
        #     [43.3,51,108],
        #     color="orangered",
        #     linestyle="--",
        #     label="SCC-Low",
        # )

        self.ax.set_title("Shadow carbon price in the scenario")

        self.ax.set_ylabel("Carbon Abatement Cost (€/tCO$\mathregular{2}$)")
        self.ax.set_xlabel("Year")

        self.ax.grid()
        self.ax.legend()
        self.fig.tight_layout()
        self.fig.canvas.draw()


class AnnualMACCSimple:
    def __init__(self, process):
        data = process.data
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.float_inputs = data["float_inputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]
        self.pathways_manager = process.pathways_manager

        try:
            self.fig, self.ax = plt.subplots(
                figsize=(10, 7),
            )
            self.ax2 = self.ax.twiny()
            self.create_plot_data()
            self.plot_interact()

        except Exception as e:
            raise RuntimeError("Error in creating plot") from e

    def plot_interact(self):
        year_widget = widgets.IntSlider(
            min=self.prospective_years[0],
            max=self.prospective_years[-1],
            step=1,
            description="Year:",
            value=2050,
        )

        metric_widget = widgets.Dropdown(
            options=[
                ("Instantaneous Carbon Abatement Cost", "carbon_abatement_cost"),
                ("Specific Carbon Abatement Cost", "specific_carbon_abatement_cost"),
                (
                    "Generic Specific Carbon Abatement Cost",
                    "generic_specific_carbon_abatement_cost",
                ),
            ],
            description="Metric:",
        )

        scc_widget = widgets.FloatText(description="Base year SCC (Specific CAC ONLY):")

        def update_numeric_widget(change):
            if change["new"] == "specific_carbon_abatement_cost":
                scc_widget.disabled = False
            else:
                scc_widget.disabled = True
                scc_widget.value = 0

        metric_widget.observe(update_numeric_widget, names="value")

        interact(self.update, year=year_widget, metric=metric_widget, scc_start=scc_widget)

    def create_plot_data(self):
        self.macc_dict = {}

        for year in range(self.prospective_years[0], self.prospective_years[-1] + 1):
            name = []
            vol = []
            cost = []
            spe_cost = []
            g_spe_cost = []

            colors = []
            name.extend(
                [
                    el
                    for el in [
                        "Passenger - Mean",
                        "Freighter - Drop in",
                        "Freighter - Hydrogen",
                        "Freighter - Electric",
                        "OPS",
                        "OPS - Freight",
                        "Load Factor",
                    ]
                ]
            )

            # Abatement effective in MtCO2e
            vol.extend(
                [
                    elt / 1000000
                    for elt in [
                        self.df.aircraft_carbon_abatement_volume_passenger_mean[year],
                        self.df.aircraft_carbon_abatement_volume_freight_dropin[year],
                        self.df.aircraft_carbon_abatement_volume_freight_hydrogen[year],
                        self.df.aircraft_carbon_abatement_volume_freight_electric[year],
                        self.df.operations_abatement_effective[year],
                        self.df.operations_abatement_effective_freight[year],
                        self.df.load_factor_abatement_effective[year],
                    ]
                ]
            )

            # carbon abatement cost in (€/tCO2e)
            cost.extend(
                [
                    el
                    for el in [
                        self.df.aircraft_carbon_abatement_cost_passenger_mean[year],
                        self.df.aircraft_carbon_abatement_cost_freight_dropin[year],
                        self.df.aircraft_carbon_abatement_cost_freight_hydrogen[year],
                        self.df.aircraft_carbon_abatement_cost_freight_electric[year],
                        self.df.operations_abatement_cost[year],
                        self.df.operations_abatement_cost_freight[year],
                        self.df.load_factor_abatement_cost[year],
                    ]
                ]
            )

            spe_cost.extend(
                [
                    el
                    for el in [
                        self.df.aircraft_specific_carbon_abatement_cost_passenger_mean[year],
                        self.df.aircraft_specific_carbon_abatement_cost_freight_dropin[year],
                        self.df.aircraft_specific_carbon_abatement_cost_freight_hydrogen[year],
                        self.df.aircraft_specific_carbon_abatement_cost_freight_electric[year],
                        self.df.operations_specific_abatement_cost[year],
                        self.df.operations_specific_abatement_cost_freight[year],
                        self.df.load_factor_specific_abatement_cost[year],
                    ]
                ]
            )

            g_spe_cost.extend(
                [
                    el
                    for el in [
                        self.df.aircraft_generic_specific_carbon_abatement_cost_passenger_mean[
                            year
                        ],
                        self.df.aircraft_generic_specific_carbon_abatement_cost_freight_dropin[
                            year
                        ],
                        self.df.aircraft_generic_specific_carbon_abatement_cost_freight_hydrogen[
                            year
                        ],
                        self.df.aircraft_generic_specific_carbon_abatement_cost_freight_electric[
                            year
                        ],
                        self.df.operations_generic_specific_abatement_cost[year],
                        self.df.operations_generic_specific_abatement_cost_freight[year],
                        self.df.load_factor_generic_specific_abatement_cost[year],
                    ]
                ]
            )

            colors.extend(
                [
                    el
                    for el in [
                        "goldenrod",
                        "khaki",
                        "khaki",
                        "khaki",
                        "orange",
                        "orange",
                        "orange",
                    ]
                ]
            )

            for pathway in self.pathways_manager.get_all():
                if (
                    pathway.name != "fossil_kerosene"
                ):  # hard coded for cac now, may be parametrized later
                    name.append(pathway.name)
                    abatement_col = f"{pathway.name}_abatement_effective"
                    if abatement_col not in self.df.columns:
                        raise ValueError(
                            f"Pathway {pathway.name} abatement is not defined. Pathways must be defined with bottom-up model."
                        )
                    vol.append(self.df[f"{pathway.name}_abatement_effective"][year] / 1000000)
                    cac_col = f"{pathway.name}_carbon_abatement_cost"
                    if cac_col not in self.df.columns:
                        raise ValueError(
                            f"Pathway {pathway.name} carbon abatement cost is not defined. Pathways must be defined with bottom-up model."
                        )
                    cost.append(self.df[f"{pathway.name}_carbon_abatement_cost"][year])
                    spe_cac_col = f"{pathway.name}_specific_carbon_abatement_cost"
                    if spe_cac_col not in self.df.columns:
                        raise ValueError(
                            f"Pathway {pathway.name} specific carbon abatement cost is not defined. Pathways must be defined with bottom-up model."
                        )
                    spe_cost.append(self.df[f"{pathway.name}_specific_carbon_abatement_cost"][year])
                    g_spe_cac_col = f"{pathway.name}_generic_specific_carbon_abatement_cost"
                    if g_spe_cac_col not in self.df.columns:
                        raise ValueError(
                            f"Pathway {pathway.name} generic specific carbon abatement cost is not defined. Pathways must be defined with bottom-up model."
                        )
                    g_spe_cost.append(
                        self.df[f"{pathway.name}_generic_specific_carbon_abatement_cost"][year]
                    )
                    colors.append("yellowgreen")

            macc_df = pd.DataFrame(
                data=[vol, cost, spe_cost, g_spe_cost, colors],
                columns=name,
                index=[
                    "abatement_effective",
                    "carbon_abatement_cost",
                    "specific_carbon_abatement_cost",
                    "generic_specific_carbon_abatement_cost",
                    "colors",
                ],
            )

            macc_df = macc_df.transpose()

            self.macc_dict[year] = macc_df

    def update(self, year, scc_start, metric):
        self.ax.cla()

        macc_df = self.macc_dict[year]

        macc_df = macc_df.sort_values(by=metric)

        # dropping NaN on costs or abatements
        macc_df = macc_df.dropna(subset=metric)

        maccneg_df = macc_df[macc_df["abatement_effective"] < -0]
        maccpos_df = macc_df[macc_df["abatement_effective"] > 0]

        ##### POS ######

        heights_pos = maccpos_df[metric].to_list()
        names_pos = maccpos_df.index.to_list()
        heights_pos.insert(0, 0)
        heights_pos.append(0)

        # # MAx effective maccpos
        widths_effective_pos = maccpos_df["abatement_effective"].to_list()
        widths_effective_pos.insert(0, 0)
        widths_effective_pos.append(widths_effective_pos[-1])

        cumwidths_effective_pos = np.cumsum(widths_effective_pos)

        colors_pos = maccpos_df["colors"].to_list()

        scc_year = None
        if metric == "specific_carbon_abatement_cost":
            scc_year = scc_start * (
                (1 + self.float_inputs["social_discount_rate"])
                ** (year - self.prospective_years[0])
            )
        elif metric == "generic_specific_carbon_abatement_cost":
            scc_year = self.df.loc[year, "exogenous_carbon_price_trajectory"]

        ### POS

        self.ax.step(
            cumwidths_effective_pos - widths_effective_pos,
            heights_pos,
            where="post",
            color="black",
            label="Marginal abatement cost",
            linewidth=1,
            zorder=10,  # ensure top level
        )

        # custom_annotation_height_for_nice_plot = [100, 100, 130,100,100,130,150,180,100,100,100,150,200,220,300,380,380,420,600,720,800,840,10]

        for i in range(len(widths_effective_pos) - 2):
            x_position = (cumwidths_effective_pos[i] + cumwidths_effective_pos[i + 1]) / 2
            y_position = min(heights_pos[i + 1], 2000)
            if heights_pos[i + 1] >= 0:
                if heights_pos[i + 1] >= 2000:
                    text = f"{names_pos[i]}\n {int(heights_pos[i + 1])}"
                else:
                    text = f"{names_pos[i]}"
                self.ax.annotate(
                    text,
                    (x_position, y_position),
                    xycoords="data",
                    xytext=(x_position, y_position + 50),
                    # xytext=(x_position, custom_annotation_height_for_nice_plot[i]),
                    textcoords="data",
                    arrowprops=dict(width=0.5, headwidth=0),
                    rotation=-60,
                    fontsize=9,
                    ha="right",
                    va="bottom",
                )
            else:
                self.ax.annotate(
                    f"{names_pos[i]}",
                    (x_position, 0),
                    xycoords="data",
                    xytext=(x_position, min(50, max(heights_pos) - 50) + 30 * (i % 3)),
                    # xytext=(x_position, custom_annotation_height_for_nice_plot[i]),
                    textcoords="data",
                    arrowprops=dict(width=0.5, headwidth=0),
                    rotation=-60,
                    fontsize=9,
                    ha="right",
                    va="bottom",
                )

        # Fill under the step plot with different colors for each step
        for i in range(0, (len(widths_effective_pos) - 2)):
            # Create a polygon for each step
            polygon = plt.Polygon(
                [
                    (cumwidths_effective_pos[i], 0),
                    (cumwidths_effective_pos[i], heights_pos[i + 1]),
                    (cumwidths_effective_pos[i + 1], heights_pos[i + 1]),
                    (cumwidths_effective_pos[i + 1], 0),
                ],
                closed=True,
                alpha=1,
                facecolor=colors_pos[i],
                edgecolor="black",
                linewidth=0.5,
                linestyle="dotted",
            )
            self.ax.add_patch(polygon)

        ### NEG

        ##### NEG #####

        heights_neg = maccneg_df[metric].to_list()
        names_neg = maccneg_df.index.to_list()

        heights_neg.append(0)
        heights_neg.insert(0, 0)

        # # MAx effective maccneg
        widths_effective_neg = maccneg_df["abatement_effective"].to_list()

        widths_effective_neg.insert(0, 0)
        widths_effective_neg.append(0)

        cumwidths_effective_neg = np.cumsum(widths_effective_neg)

        colors_neg = maccneg_df["colors"].to_list()

        self.ax.step(
            cumwidths_effective_neg[-1] - cumwidths_effective_neg + widths_effective_neg,
            heights_neg,
            where="post",
            color="#335C67",
            label="Marginal emission cost",
            linewidth=1,
            zorder=9,
        )

        # custom_annotation_height_for_nice_plot = [15,70,120,170,220]

        for i in range(len(widths_effective_neg) - 2):
            x_position = (
                cumwidths_effective_neg[-1]
                - (cumwidths_effective_neg[i] + cumwidths_effective_neg[i + 1]) / 2
            )
            self.ax.annotate(
                f"{names_neg[i]}",
                (x_position, 0),
                xycoords="data",
                xytext=(x_position, 50 + 30 * (i % 3)),
                # xytext=(x_position, custom_annotation_height_for_nice_plot[i]),
                textcoords="data",
                arrowprops=dict(width=0.5, headwidth=0),
                rotation=-60,
                fontsize=9,
                ha="right",
                va="bottom",
            )

        # Fill under the step plot with different colors for each step
        for i in range(0, (len(widths_effective_neg) - 2)):
            # Create a polygon for each step
            polygon = plt.Polygon(
                [
                    (cumwidths_effective_neg[-1] - cumwidths_effective_neg[i], 0),
                    (
                        cumwidths_effective_neg[-1] - cumwidths_effective_neg[i],
                        heights_neg[i + 1],
                    ),
                    (
                        cumwidths_effective_neg[-1] - cumwidths_effective_neg[i + 1],
                        heights_neg[i + 1],
                    ),
                    (cumwidths_effective_neg[-1] - cumwidths_effective_neg[i + 1], 0),
                ],
                closed=True,
                alpha=1,
                facecolor=colors_neg[i],
                edgecolor="black",
                linewidth=0.5,
                linestyle="dotted",
            )
            self.ax.add_patch(polygon)

        if scc_year is not None:
            self.ax.axhline(scc_year, color="firebrick", linestyle="--", linewidth=1)
            self.ax.text(
                10, scc_year * 1.02, "Reference carbon value", color="firebrick", fontsize=8
            )

        self.ax.set_ylabel("Carbon Abatement Cost (€/t$\mathregular{CO_2}$)")
        self.ax.set_xlabel("$\mathregular{CO_2}$ abatted (Mt)")

        self.ax.axhline(0, color="black", linestyle="--", linewidth=1)

        self.ax.axvline(0, color="black", linestyle="--", linewidth=1)

        legend_patches_1 = [
            Line2D(
                [0], [0], color="black", linewidth=1, linestyle="-", label="Marginal Abatement Cost"
            ),
            mpatches.Patch(color="gold", alpha=1, label="Short-Range Efficiency"),
            mpatches.Patch(color="goldenrod", alpha=1, label="Medium-Range Efficiency"),
            mpatches.Patch(color="darkgoldenrod", alpha=1, label="Long-Range Efficiency"),
            mpatches.Patch(color="khaki", alpha=1, label="Freighter Efficiency"),
            mpatches.Patch(color="orange", alpha=1, label="Operations"),
            mpatches.Patch(color="yellowgreen", alpha=1, label="Energy"),
        ]

        self.ax.add_artist(
            self.ax.legend(
                handles=legend_patches_1,
                fontsize=9,
                title="Type of lever",
                loc="upper left",
                bbox_to_anchor=(60 / self.ax.figure.bbox.width, 1),
            )
        )

        self.ax.set_xlim(
            cumwidths_effective_neg[-1] - 100,
            cumwidths_effective_pos[-1] - widths_effective_pos[-1] + 50,
        )
        self.ax.set_ylim(
            max(-300, min(min(heights_pos), min(heights_neg)) - 50),
            min(2000, max(max(heights_neg), max(heights_pos)) + 300),
        )

        # Add abatement and emission zones
        self.ax.axvspan(
            xmin=self.ax.get_xlim()[0],
            xmax=0,
            facecolor="#ff70a6",
            alpha=0.1,
            clip_on=True,
            zorder=-1,
        )
        self.ax.axvspan(
            xmin=0,
            xmax=self.ax.get_xlim()[1],
            facecolor="#70d6ff",
            alpha=0.15,
            clip_on=True,
            zorder=-1,
        )

        self.ax.text(
            -1,
            self.ax.get_ylim()[1] / 2.8,
            "Extra carbon emissions",
            rotation=90,
            va="bottom",
            ha="right",
            fontsize=10,
            color="dimgrey",
        )
        self.ax.text(
            5,
            self.ax.get_ylim()[1] / 2.8,
            "Carbon abatement",
            rotation=90,
            va="bottom",
            ha="left",
            fontsize=10,
            color="dimgrey",
        )

        self.ax.grid()
        self.ax.set_title(f"Marginal abatement cost curve for year {year}")

        self.ax2.xaxis.set_label_position("bottom")
        self.ax2.set_xlabel("Annual $\mathregular{CO_2}$ emissions (Mt)")

        self.ax2.spines["bottom"].set_position(("axes", -0.1))  # Move spine below the plot
        self.ax2.xaxis.set_ticks_position("bottom")

        self.ax2.set_xlim(
            self.df.co2_emissions_2019technology[year]
            - self.ax.get_xlim()[0]
            - cumwidths_effective_neg[-1],
            self.df.co2_emissions_2019technology[year]
            - self.ax.get_xlim()[1]
            - cumwidths_effective_neg[-1],
        )

        self.fig.tight_layout()
        self.fig.canvas.draw()


class ShadowCarbonPriceSimple:
    def __init__(self, process):
        data = process.data
        self.df = data["vector_outputs"]
        self.float_outputs = data["float_outputs"]
        self.float_inputs = data["float_inputs"]
        self.years = data["years"]["full_years"]
        self.historic_years = data["years"]["historic_years"]
        self.prospective_years = data["years"]["prospective_years"]
        self.pathways_manager = process.pathways_manager

        try:
            self.fig, self.ax = plt.subplots(figsize=(10, 7))

            self.create_plot_data()
            self.plot_interact()
        except Exception as e:
            raise RuntimeError(
                "Error in creating plot. Possible cause: this plot requires top-down fleet model, "
                "abatement cost and complex energy cost models. Be sure to select them in the scenario settings."
            ) from e

    def plot_interact(self):
        metric_widget = widgets.Dropdown(
            options=[
                ("Specific Carbon Abatement Cost", "specific_carbon_abatement_cost"),
                (
                    "Generic Specific Carbon Abatement Cost",
                    "generic_specific_carbon_abatement_cost",
                ),
            ],
            value="generic_specific_carbon_abatement_cost",
            description="Metric:",
        )

        scc_widget = widgets.FloatText(description="Base year SCC (Specific CAC ONLY):")

        def update_numeric_widget(change):
            if change["new"] == "specific_carbon_abatement_cost":
                scc_widget.disabled = False
            else:
                scc_widget.disabled = True
                scc_widget.value = 0

        metric_widget.observe(update_numeric_widget, names="value")

        interact(self.update, metric=metric_widget, scc_start=scc_widget)

    def create_plot_data(self):
        self.macc_dict = {}

        for year in range(self.prospective_years[0], self.prospective_years[-1] + 1):
            name = []
            vol = []
            cost = []
            spe_cost = []
            g_spe_cost = []

            colors = []

            name.extend(
                [
                    el
                    for el in [
                        "Passenger - Mean",
                        "Freighter - Drop in",
                        "Freighter - Hydrogen",
                        "Freighter - Electric",
                        "OPS",
                        "OPS - Freight",
                        "Load Factor",
                    ]
                ]
            )

            # Abatement effective in MtCO2e
            vol.extend(
                [
                    elt / 1000000
                    for elt in [
                        self.df.aircraft_carbon_abatement_volume_passenger_mean[year],
                        self.df.aircraft_carbon_abatement_volume_freight_dropin[year],
                        self.df.aircraft_carbon_abatement_volume_freight_hydrogen[year],
                        self.df.aircraft_carbon_abatement_volume_freight_electric[year],
                        self.df.operations_abatement_effective[year],
                        self.df.operations_abatement_effective_freight[year],
                        self.df.load_factor_abatement_effective[year],
                    ]
                ]
            )

            # carbon abatement cost in (€/tCO2e)
            cost.extend(
                [
                    el
                    for el in [
                        self.df.aircraft_carbon_abatement_cost_passenger_mean[year],
                        self.df.aircraft_carbon_abatement_cost_freight_dropin[year],
                        self.df.aircraft_carbon_abatement_cost_freight_hydrogen[year],
                        self.df.aircraft_carbon_abatement_cost_freight_electric[year],
                        self.df.operations_abatement_cost[year],
                        self.df.operations_abatement_cost_freight[year],
                        self.df.load_factor_abatement_cost[year],
                    ]
                ]
            )

            spe_cost.extend(
                [
                    el
                    for el in [
                        self.df.aircraft_specific_carbon_abatement_cost_passenger_mean[year],
                        self.df.aircraft_specific_carbon_abatement_cost_freight_dropin[year],
                        self.df.aircraft_specific_carbon_abatement_cost_freight_hydrogen[year],
                        self.df.aircraft_specific_carbon_abatement_cost_freight_electric[year],
                        self.df.operations_specific_abatement_cost[year],
                        self.df.operations_specific_abatement_cost_freight[year],
                        self.df.load_factor_specific_abatement_cost[year],
                    ]
                ]
            )

            g_spe_cost.extend(
                [
                    el
                    for el in [
                        self.df.aircraft_generic_specific_carbon_abatement_cost_passenger_mean[
                            year
                        ],
                        self.df.aircraft_generic_specific_carbon_abatement_cost_freight_dropin[
                            year
                        ],
                        self.df.aircraft_generic_specific_carbon_abatement_cost_freight_hydrogen[
                            year
                        ],
                        self.df.aircraft_generic_specific_carbon_abatement_cost_freight_electric[
                            year
                        ],
                        self.df.operations_generic_specific_abatement_cost[year],
                        self.df.operations_generic_specific_abatement_cost_freight[year],
                        self.df.load_factor_generic_specific_abatement_cost[year],
                    ]
                ]
            )

            colors.extend(
                [
                    el
                    for el in [
                        "goldenrod",
                        "khaki",
                        "khaki",
                        "khaki",
                        "orange",
                        "orange",
                        "orange",
                    ]
                ]
            )

            for pathway in self.pathways_manager.get_all():
                if (
                    pathway.name != "fossil_kerosene"
                ):  # hard coded for cac now, may be parametrized later
                    name.append(pathway.name)
                    abatement_col = f"{pathway.name}_abatement_effective"
                    if abatement_col not in self.df.columns:
                        raise ValueError(
                            f"Pathway {pathway.name} abatement is not defined. Pathways must be defined with bottom-up model."
                        )
                    vol.append(self.df[f"{pathway.name}_abatement_effective"][year] / 1000000)
                    cac_col = f"{pathway.name}_carbon_abatement_cost"
                    if cac_col not in self.df.columns:
                        raise ValueError(
                            f"Pathway {pathway.name} carbon abatement cost is not defined. Pathways must be defined with bottom-up model."
                        )
                    cost.append(self.df[f"{pathway.name}_carbon_abatement_cost"][year])
                    spe_cac_col = f"{pathway.name}_specific_carbon_abatement_cost"
                    if spe_cac_col not in self.df.columns:
                        raise ValueError(
                            f"Pathway {pathway.name} specific carbon abatement cost is not defined. Pathways must be defined with bottom-up model."
                        )
                    spe_cost.append(self.df[f"{pathway.name}_specific_carbon_abatement_cost"][year])
                    g_spe_cac_col = f"{pathway.name}_generic_specific_carbon_abatement_cost"
                    if g_spe_cac_col not in self.df.columns:
                        raise ValueError(
                            f"Pathway {pathway.name} generic specific carbon abatement cost is not defined. Pathways must be defined with bottom-up model."
                        )
                    g_spe_cost.append(
                        self.df[f"{pathway.name}_generic_specific_carbon_abatement_cost"][year]
                    )
                    colors.append("yellowgreen")

            macc_df = pd.DataFrame(
                data=[vol, cost, spe_cost, g_spe_cost, colors],
                columns=name,
                index=[
                    "abatement_effective",
                    "carbon_abatement_cost",
                    "specific_carbon_abatement_cost",
                    "generic_specific_carbon_abatement_cost",
                    "colors",
                ],
            )

            macc_df = macc_df.transpose()

            self.macc_dict[year] = macc_df

    def update(self, metric, scc_start):
        self.ax.cla()
        scc_list = []

        marginal_cac = []
        marginal_cac09 = []
        marginal_cac08 = []
        marginal_cac05 = []
        scc_list = []
        years = range(self.prospective_years[0], self.prospective_years[-1] + 1)

        for year in years:
            macc_df = self.macc_dict[year]

            macc_df = macc_df.sort_values(by=metric)

            macc_df = macc_df.dropna(subset=metric)

            # Plot only made for positive abatements
            maccpos_df = macc_df[macc_df["abatement_effective"] > 0]

            ##### POS ######

            heights_pos = maccpos_df[metric].to_numpy()
            widths_effective_pos = maccpos_df["abatement_effective"].to_numpy()

            if metric == "specific_carbon_abatement_cost":
                scc_year = scc_start * (
                    (1 + self.float_inputs["social_discount_rate"])
                    ** (year - self.prospective_years[0])
                )
                scc_list.append(scc_year)
            elif metric == "generic_specific_carbon_abatement_cost":
                scc_year = self.df.loc[year, "exogenous_carbon_price_trajectory"]
                scc_list.append(scc_year)

            if len(widths_effective_pos > 0):
                cumwidths_pos = np.cumsum(widths_effective_pos)

                target_value = 0.9 * cumwidths_pos[-1]
                index_val = np.searchsorted(cumwidths_pos, target_value, side="right")
                marginal_cac09.append(heights_pos[min(index_val, len(heights_pos))])

                target_value = 0.8 * cumwidths_pos[-1]
                index_val = np.searchsorted(cumwidths_pos, target_value, side="right")
                marginal_cac08.append(heights_pos[min(index_val, len(heights_pos))])

                target_value = 0.5 * cumwidths_pos[-1]
                index_val = np.searchsorted(cumwidths_pos, target_value, side="right")
                marginal_cac05.append(heights_pos[min(index_val, len(heights_pos))])

                marginal_cac.append(max(heights_pos))

            else:
                marginal_cac.append(np.NaN)
                marginal_cac09.append(np.NaN)
                marginal_cac08.append(np.NaN)
                marginal_cac05.append(np.NaN)

        self.ax.plot(
            years,
            marginal_cac,
            color="navy",
            linestyle="-",
            label="Initial Marginal Abatement Cost",
        )
        self.ax.plot(years, marginal_cac09, color="navy", linestyle="--", label="90% Abatement")
        self.ax.plot(years, marginal_cac08, color="navy", linestyle="-.", label="80% Abatement")
        self.ax.plot(years, marginal_cac05, color="navy", linestyle=":", label="50% Abatement")
        self.ax.plot(
            years,
            scc_list,
            color="orangered",
            linestyle="-",
            label="SCC",
        )
        # self.ax.plot(
        #     [2020,2025,2050],
        #     [43.3,51,108],
        #     color="orangered",
        #     linestyle="--",
        #     label="SCC-Low",
        # )

        self.ax.set_title("Shadow carbon price in the scenario")

        self.ax.set_ylabel("Carbon Abatement Cost (€/tCO$\mathregular{2}$)")
        self.ax.set_xlabel("Year")

        self.ax.grid()
        self.ax.legend()
        self.fig.tight_layout()
        self.fig.canvas.draw()
