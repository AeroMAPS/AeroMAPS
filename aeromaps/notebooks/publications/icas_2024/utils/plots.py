import brightway2 as bw
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
import math
import collections


def plot_stacked_evolution_subplots(xarray_data):
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
        "aircraft_production": (palette[1], ""),
        "airport": (palette[2], ""),
        "combustion_biofuel": (palette[3], ""),
        "combustion_electrofuel": (palette[4], ""),
        "combustion_kerosene": (palette[5], ""),
        "production_biofuel": (palette[6], ""),
        "production_electrofuel": (palette[7], ""),
        # "Production Electrofuel\n(Fischer-Tropsch process)": (palette[7], "|"),
        "production_electrofuel_DAC": ("0.35", ""),
        "production_electrofuel_electrolysis": ("0.8", "\\"),
        "production_kerosene": (palette[8], ""),
    }

    # Create subplots
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(12, n_rows * 4), constrained_layout=False)
    axes = axes.flatten()  # Flatten the array of axes for easy iteration

    for i, method in enumerate(methods):
        df_method = df_filtered.xs(method, level="impacts")
        df_method.index = df_method.index.str.replace("_other_", "Others")

        # Remove elements with no contribution to score
        df_method = df_method.loc[~(df_method.eq(0).all(axis=1))]

        # Plot stacked area chart with custom colors
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

        unit = bw.Method(method).metadata.get("unit")
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


def plot_stacked_sensitivity_subplots(df, kerosene_scenario_values):
    # Remove phases containing 'sum'
    df_filtered = df[~df.index.get_level_values("phase").str.contains("sum")]

    methods = df_filtered.index.get_level_values("method").unique()  # [9:]
    years = df_filtered.columns

    # Determine the number of rows and columns for the subplots
    n_methods = len(methods)
    n_cols = 3  # 2 if n_methods % 2 == 0 else 3
    n_rows = math.ceil(n_methods / n_cols)

    # Use seaborn color palette for better aesthetics
    palette = sns.color_palette("Set2", len(df_filtered.index.levels[1]))
    palette_dict = {
        "aircraft_production": (palette[1], ""),
        "airport": (palette[2], ""),
        "combustion_biofuel": (palette[3], ""),
        "combustion_electrofuel": (palette[4], ""),
        "combustion_kerosene": (palette[5], ""),
        "production_biofuel": (palette[6], ""),
        "production_electrofuel": (palette[7], ""),
        "Production Electrofuel\n(Fischer-Tropsch process)": (palette[7], "|"),
        "Production Electrofuel\n(Direct Air Capture)": ("0.35", ""),
        "Production Electrofuel\n(Electrolysis)": ("0.8", "\\"),
        "production_kerosene": (palette[8], ""),
    }

    # Create subplots
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(12, n_rows * 4), constrained_layout=False)
    axes = axes.flatten()  # Flatten the array of axes for easy iteration

    for i, method in enumerate(methods):
        df_method = df_filtered.xs(method, level="method")
        df_method.index = df_method.index.str.replace(
            "_other_", "Production Electrofuel\n(Fischer-Tropsch process)"
        )
        df_method.index = df_method.index.str.replace(
            "production_electrofuel_DAC", "Production Electrofuel\n(Direct Air Capture)"
        )
        df_method.index = df_method.index.str.replace(
            "production_electrofuel_electrolysis", "Production Electrofuel\n(Electrolysis)"
        )

        # Rearrange columns order for plot order
        cols = df_method.index.tolist()
        cols = cols[1:-1] + cols[:1] + cols[-1:]
        df_method = df_method.reindex(index=cols)

        # Plot stacked area chart with custom colors
        stacks = axes[i].stackplot(
            years,
            df_method,
            labels=df_method.index,
            alpha=0.8,
            colors=[palette_dict[key][0] for key in df_method.index],
        )

        # Add reference line of kerosene scenario
        axes[i].hlines(
            y=kerosene_scenario_values[method], xmin=0, xmax=1, linewidth=2, color="r", ls="--"
        )
        axes[i].annotate(
            "scenario 1",
            (0.28, kerosene_scenario_values[method]),
            xycoords="data",
            xytext=(15, -18),
            textcoords="offset points",
            fontsize=11,
            va="bottom",
            ha="right",
            color="red",
            backgroundcolor="w",
        )

        # Customize the subplot
        name, unit = method.split("[", 1)
        # name = name.replace('- ', '\n').replace('(', '\n(')
        name = name.replace("total", "")
        name = name.split("- ")[0]
        name = name.replace(":", "\n")
        name = "".join([a if a.isupper() else b for a, b in zip(name, name.title())])
        unit = unit.replace("]", "")
        axes[i].set_title(name, fontsize=12)
        axes[i].set_xlabel("Share of Photovoltaic")
        axes[i].set_ylabel(unit)
        axes[i].grid(True)
        axes[i].set_axisbelow(True)
        axes[i].ticklabel_format(axis="y", scilimits=(0, 4))
        axes[i].xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        # if i == 0 or i == len(axes) - 1:
        # axes[i].legend()

        hatches = [palette_dict[key][1] for key in df_method.index]
        for stack, hatch in zip(stacks, hatches):
            if hatch:
                stack.set_hatch(hatch)

    # Remove any empty subplots
    # for j in range(i + 1, len(axes)):
    #    fig.delaxes(axes[j])

    # Add a single legend for all subplots
    # handles, labels = axes[0].get_legend_handles_labels()
    # fig.legend(handles, labels, title='Phase', loc='lower center', ncol=4, bbox_to_anchor = (0, -0.01, 1, 1))#, mode="expand") #, ncol=len(df_filtered.index.levels[1]))
    # plt.tight_layout()

    # Collect legend labels from all plots.
    entries = collections.OrderedDict()
    for ax in axes.flatten():
        for handle, label in zip(*axes[0].get_legend_handles_labels()):
            # if 'biofuel' in label or 'electrofuel' in label:
            #    continue
            label_name = label.replace("_", " ").title()
            entries[label_name] = handle
    legend = fig.legend(
        entries.values(),
        entries.keys(),
        loc="lower center",
        bbox_to_anchor=(0.5, 0),
        ncol=4,
        fontsize=11,
        title="Life-Cycle Phase",
        title_fontsize=12,
    )

    # Set tight layout while keeping legend in the screen
    bbox = legend.get_window_extent(fig.canvas.get_renderer()).transformed(
        fig.transFigure.inverted()
    )
    fig.tight_layout(rect=(0, bbox.y1, 1, 1), h_pad=0.5, w_pad=0.5)

    # show plot
    plt.show()

def plot_evolution_subplots_iams(df):
    iams = df.index.get_level_values("IAM Model - Scenario").unique()
    methods = df["impacts"].unique()  # [-3:]#.take([1,11,12])

    # Determine the number of rows and columns for the subplots
    n_methods = len(methods)
    n_cols = 3  # 2 if n_methods % 2 == 0 else 3
    n_rows = math.ceil(n_methods / n_cols)

    # Use seaborn color palette for better aesthetics
    palette = sns.color_palette("Set2", len(df.index.levels[1]))

    # Create subplots
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(12, n_rows * 4), constrained_layout=False)
    axes = axes.flatten()  # Flatten the array of axes for easy iteration

    for k, iam in enumerate(iams):
        df_iam = df.xs(iam, level="IAM Model - Scenario")

        for i, method in enumerate(methods):
            df_method = df_iam[df_iam["impacts"] == method]
            # df_method = df_iam.xs(method, level="impacts")
            df_method = df_method.set_index("year")
            # df_method['axis'] = df_method['axis'].str.replace(r'\*sum\*', iam, regex=True)

            # return df_method

            # Plot stacked area chart with custom colors
            df_method["lca"].plot(ax=axes[i], label=iam, color=palette[k], linewidth=2.5)
            # axes[i].plot(years, df_method, alpha=0.8)

            # Customize the subplot
            unit = bw.Method(eval(method)).metadata.get("unit")
            unit = unit.replace("]", "")
            unit = unit.replace("m2*a crop-Eq", r"m$^2\times$yr annual crop land")
            unit = unit.replace("-Eq", "-eq")
            unit = unit.replace("CO2", r"CO$_2$")

            name = eval(method)[2]
            # name = name.replace('- ', '\n').replace('(', '\n(')
            name = name.replace("(with non-CO2)", "")
            name = name.replace("total", "")
            name = name.split("- ")[0]
            name = name.replace(":", "\n")
            name = "".join([a if a.isupper() else b for a, b in zip(name, name.title())])

            axes[i].set_title(name, fontsize=12)
            axes[i].set_xlabel("Year")
            axes[i].set_ylabel(unit)
            axes[i].grid(True, alpha=0.5)
            axes[i].set_axisbelow(True)
            axes[i].ticklabel_format(axis="y", scilimits=(0, 4))
            axes[i].set_facecolor("white")

    # Collect legend labels from all plots.
    entries = collections.OrderedDict()
    for ax in axes.flatten():
        for handle, label in zip(*axes[0].get_legend_handles_labels()):
            # if 'biofuel' in label or 'electrofuel' in label:
            #    continue
            label_name = label.replace("_", " ").replace("1150Gt", "RCP2.6")  # .title()
            entries[label_name] = handle
    legend = fig.legend(
        entries.values(),
        entries.keys(),
        loc="lower center",
        bbox_to_anchor=(0.5, 0),
        ncol=4,
        fontsize=11,
        title="SSP - RCP (simulated with REMIND)",
        title_fontsize=12,
    )

    # Set tight layout while keeping legend in the screen
    bbox = legend.get_window_extent(fig.canvas.get_renderer()).transformed(
        fig.transFigure.inverted()
    )
    fig.tight_layout(rect=(0, bbox.y1, 1, 1), h_pad=0.5, w_pad=0.5)

    # show plot
    plt.show()