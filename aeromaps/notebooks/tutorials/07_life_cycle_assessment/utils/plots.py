import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import math
import collections


def plot_stacked_evolution_subplots(xarray_data):
    """
    Plots a stacked evolution of the LCA results provided as an xarray
    """

    df = xarray_data.to_dataframe().reset_index()

    # Set the desired columns as a MultiIndex
    df = df.set_index(["impacts", "axis", "year"])

    # Pivot the DataFrame to have years as columns
    df = df.pivot_table(values="lca", index=["impacts", "axis"], columns="year")

    # Remove phases containing 'sum'
    df_filtered = df[~df.index.get_level_values("axis").str.contains("sum")]
    df_filtered = df_filtered[
        ~df_filtered.index.get_level_values("axis").str.contains("_other_")
    ]  # make sure it is equal to zero before deleting

    methods = df_filtered.index.get_level_values("impacts").unique()  # [:9]
    years = df_filtered.columns

    # Determine the number of rows and columns for the subplots
    n_methods = len(methods)
    n_cols = 3  # 2 if n_methods % 2 == 0 else 3
    n_rows = math.ceil(n_methods / n_cols)

    # Use seaborn color palette for better aesthetics
    palette = sns.color_palette("Set2", len(df_filtered.index.levels[1]))
    palette_dict = {
        "aircraft_production": (palette[3], ""),
        "airport": (palette[1], ""),
        "kerosene_production": (palette[2], ""),
        "biofuel_production": (palette[5], ""),
        "e_fuel_production": (palette[8], ""),
        "hydrogen_production": (palette[6], ""),
        "CO2 from combustion": (palette[7], ""),
        "Non-CO2 from combustion": ("0.8", "//"),
    }

    # Create subplots
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(12, n_rows * 4), constrained_layout=False)
    axes = axes.flatten()  # Flatten the array of axes for easy iteration

    for i, method in enumerate(methods):
        df_method = df_filtered.xs(method, level="impacts")
        df_method.index = df_method.index.str.replace("_other_", "Others")

        # Group CO2 emissions together
        co2_rows = df_method.index.str.startswith("CO2")
        co2_aggregated = df_method[co2_rows].sum()
        co2_aggregated.name = "CO2 from combustion"
        df_method = pd.concat(
            [df_method[~co2_rows], co2_aggregated.to_frame().T], ignore_index=False
        )

        # Group non-CO2 emissions together
        nonco2_rows = df_method.index.str.startswith("non_CO2")
        nonco2_aggregated = df_method[nonco2_rows].sum()
        nonco2_aggregated.name = "Non-CO2 from combustion"
        df_method = pd.concat(
            [df_method[~nonco2_rows], nonco2_aggregated.to_frame().T], ignore_index=False
        )

        # Remove elements with no contribution to score
        df_method = df_method.loc[~(df_method.eq(0).all(axis=1))]

        # Plot stacked area chart with custom colors
        # stacks = axes[i].stackplot(years, df_method, labels=df_method.index, alpha=0.8, colors=palette)
        colors = [palette_dict[key][0] for key in df_method.index]
        stacks = axes[i].stackplot(
            years, df_method, labels=df_method.index, alpha=0.8, colors=colors, linewidth=0.2
        )

        # Customize the subplot
        name = method[2]
        # name = name.replace('- ', '\n').replace('(', '\n(')
        name = name.replace("(with non-CO2)", "")
        name = name.replace("total", "")
        name = name.split("- ")[0]
        name = name.replace(":", "\n")
        name = "".join([a if a.isupper() else b for a, b in zip(name, name.title())])

        unit = xarray_data.coords["impacts"].attrs["units"][method]
        unit = unit.replace("]", "")
        unit = unit.replace("m2*a crop-Eq", r"m$^2\times$yr annual crop land")
        unit = unit.replace("-Eq", "-eq")
        unit = unit.replace("CO2", r"CO$_2$")

        axes[i].set_title(name, fontsize=12)
        axes[i].set_xlabel("Year")
        axes[i].set_ylabel(unit)
        axes[i].grid(True)
        axes[i].set_axisbelow(True)
        axes[i].ticklabel_format(axis="y", scilimits=(0, 4))
        axes[i].set_facecolor("white")

        # Set hatches pattern
        hatches = [palette_dict[key][1] for key in df_method.index]
        for stack, hatch, values in zip(stacks, hatches, df_method.values):
            if np.any(values != 0):  # Check if the layer has non-zero values
                stack.set_edgecolor("0.1")
            # stack.set_edgecolor(color)
            if hatch:
                stack.set_hatch(hatch)

    # Collect legend labels from all plots.
    all_handles = []
    all_labels = []
    for ax in axes:
        handles, labels = ax.get_legend_handles_labels()
        all_handles.extend(handles)
        all_labels.extend(labels)

    entries = collections.OrderedDict()
    for ax in axes.flatten():
        for handle, label in zip(all_handles, all_labels):
            # if 'biofuel' in label or 'electrofuel' in label:
            #    continue
            if label == "Others":
                continue
            if "CO2" in label:
                label_name = label.replace("CO2", r"CO$_2$")
            elif "e_fuel" in label:
                label_name = label.replace("e_fuel", "E-Fuel").replace("_", " ").title()
            else:
                label_name = label.replace("_", " ").title()
            entries[label_name] = handle
    legend = fig.legend(
        entries.values(),
        entries.keys(),
        loc="lower center",
        bbox_to_anchor=(0.5, 0),
        ncol=4,
        fontsize=11,
        title="Contribution",  # title='Life-Cycle Phase',
        title_fontsize=12,
    )

    # Set tight layout while keeping legend in the screen
    bbox = legend.get_window_extent(fig.canvas.get_renderer()).transformed(
        fig.transFigure.inverted()
    )
    fig.tight_layout(rect=(0, bbox.y1, 1, 1), h_pad=0.5, w_pad=0.5)

    # show plot
    plt.show()