import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, LogNorm
import seaborn as sns
import math
import pandas as pd
import collections
import numpy as np

pb_methods = {
    ("PBLCIA", "climate change", "climate change radiative forcing"),
    ("PBLCIA", "biosphere integrity", "biosphere integrity"),
    ("PBLCIA", "biogeochemical", "nitrogen cycle"),
    ("PBLCIA", "biogeochemical", "phosphorus cycle"),
    ("PBLCIA", "freshwater change", "freshwater use"),
    ("PBLCIA", "stratospheric ozone depletion", "ozone depletion"),
}


def plot_stacked_evolution_subplots(xarray_data, start_year: int = 2020, end_year: int = None):
    """
    Plots a stacked evolution of the LCA results provided as an xarray
    """

    # Convert to dataframe
    df = xarray_data.to_dataframe().reset_index()

    # Keep only years >= start_year
    if start_year:
        df = df[df["year"] >= start_year]
    if end_year:
        df = df[df["year"] <= end_year]

    # Set the desired columns as a MultiIndex
    df = df.set_index(["impacts", "axis", "year"])

    # Pivot the DataFrame to have years as columns
    df = df.pivot_table(values="lca", index=["impacts", "axis"], columns="year")

    # Remove phases containing 'sum'
    df_filtered = df[~df.index.get_level_values("axis").str.contains("sum")]

    # df_filtered = df_filtered[
    #    ~df_filtered.index.get_level_values("axis").str.contains("_other_")
    # ]  # make sure it is equal to zero before deleting

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
        "lcaf_production": (palette[4], ""),
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
        colors = [palette_dict.get(key, ["gray"])[0] for key in df_method.index]
        stacks = axes[i].stackplot(
            years, df_method, labels=df_method.index, alpha=0.8, colors=colors, linewidth=0.2
        )

        # Customize the subplot
        name = method[2]
        # name = name.replace('- ', '\n').replace('(', '\n(')
        # name = name.replace("(with non-CO2)", "")
        name = name.replace("total", "")
        name = name.split("- ")[0]
        name = name.replace(":", "\n")
        name = "".join([a if a.isupper() else b for a, b in zip(name, name.title())])

        unit = xarray_data.coords["impacts"].attrs["units"][
            method
        ]  # bw.Method(method).metadata.get("unit")
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
        hatches = [palette_dict.get(key, ["", ""])[1] for key in df_method.index]
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
            # if label == "Others":
            #    continue
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


def plot_stacked_evolution_pb_subplots(xarray_data, scaling_factors=None, label_y="Impact"):
    """
    Affiche un stacked evolution plot pour les PBLCIA ciblés.

    scaling_factors : dict | float | None
        - dict : {pb_tuple: facteur, ...}
        - float : coefficient global
        - None : équivalent à 1
    """

    # ---- Préparer DataFrame ----
    df = xarray_data.to_dataframe().reset_index()
    df = df.set_index(["impacts", "axis", "year"])
    df = df.pivot_table(values="lca", index=["impacts", "axis"], columns="year")

    df_filtered = df.loc[df.index.get_level_values("impacts").isin(pb_methods)]

    # ---- Préparer variables ----
    methods = df_filtered.index.get_level_values("impacts").unique()
    years = sorted(df_filtered.columns)

    n_methods = len(methods)
    n_cols = 3
    n_rows = math.ceil(n_methods / n_cols)

    palette = sns.color_palette("Set2", len(df_filtered.index.levels[1]))
    palette_dict = {
        "aircraft_production": (palette[3], ""),
        "airport": (palette[1], ""),
        "kerosene_production": (palette[2], ""),
        "lcaf_production": (palette[4], ""),
        "biofuel_production": (palette[5], ""),
        "e_fuel_production": (palette[8], ""),
        "hydrogen_production": (palette[6], ""),
        "CO2 from combustion": (palette[7], ""),
        "Non-CO2 from combustion": ("0.8", "//"),
    }

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(12, n_rows * 4), constrained_layout=False)
    axes = axes.flatten()

    for i, method in enumerate(methods):
        df_method = df_filtered.xs(method, level="impacts")
        df_method.index = df_method.index.str.replace("_other_", "Others")

        # Regroupements CO2 / non-CO2
        co2_rows = df_method.index.str.startswith("CO2")
        if co2_rows.any():
            co2_aggregated = df_method[co2_rows].sum()
            co2_aggregated.name = "CO2 from combustion"
            df_method = pd.concat([df_method[~co2_rows], co2_aggregated.to_frame().T])

        nonco2_rows = df_method.index.str.startswith("non_CO2")
        if nonco2_rows.any():
            nonco2_aggregated = df_method[nonco2_rows].sum()
            nonco2_aggregated.name = "Non-CO2 from combustion"
            df_method = pd.concat([df_method[~nonco2_rows], nonco2_aggregated.to_frame().T])

        df_method = df_method.loc[~(df_method.eq(0).all(axis=1))]

        # 🔑 Facteur d’échelle
        if scaling_factors is None:
            factor = 1.0
        elif isinstance(scaling_factors, dict):
            factor = scaling_factors.get(method, 1.0)  # par défaut 1 si absent
        else:  # scalaire global
            factor = scaling_factors

        df_method = (df_method / factor) * 100

        # Tracé
        colors = [palette_dict[key][0] for key in df_method.index]
        stacks = axes[i].stackplot(
            years,
            df_method,
            labels=df_method.index,
            alpha=0.8,
            colors=colors,
            linewidth=0.2,
        )

        # Nom du subplot
        name = method[2]
        name = name.replace("(with non-CO2)", "").replace("total", "").split("- ")[0]
        name = name.replace(":", "\n")
        name = "".join([a if a.isupper() else b for a, b in zip(name, name.title())])

        if i == 0:
            name = f"Biogeochemical flows\n{name}"
        if i == 1:
            name = f"Biogeochemical flows\n{name}"
        if i == 2:
            name = f"{name}\nLand use + Radiative Forcing*"
        if i == 3:
            name = "Climate change\nRadiative forcing*"

        axes[i].set_title(name, fontsize=12)
        axes[i].set_xlabel("Year")
        axes[i].set_ylabel(label_y)
        axes[i].grid(True)
        axes[i].set_axisbelow(True)
        axes[i].ticklabel_format(axis="y", scilimits=(0, 4))
        axes[i].set_facecolor("white")

        hatches = [palette_dict[key][1] for key in df_method.index]
        for stack, hatch, values in zip(stacks, hatches, df_method.values):
            if np.any(values != 0):
                stack.set_edgecolor("0.1")
            if hatch:
                stack.set_hatch(hatch)

    # Légende commune
    all_handles, all_labels = [], []
    for ax in axes[:n_methods]:
        handles, labels = ax.get_legend_handles_labels()
        all_handles.extend(handles)
        all_labels.extend(labels)

    entries = collections.OrderedDict()
    for handle, label in zip(all_handles, all_labels):
        if label == "Others":
            continue
        if label == "CO2 from combustion":
            label_name = label.replace(
                "CO2 from combustion", r"CO$_2$ from combustion (and production if *)"
            )
        elif "CO2" in label:
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
        title="Contribution",
        title_fontsize=12,
    )

    bbox = legend.get_window_extent(fig.canvas.get_renderer()).transformed(
        fig.transFigure.inverted()
    )
    fig.tight_layout(rect=(0, bbox.y1, 1, 1), h_pad=0.5, w_pad=0.5)

    plt.show()


def plot_planetary_radar(xarray_data, scaling_factors=None, chosen_year=2050):
    """
    Planetary Boundaries radar – dégradé par impact
    (version avec lignes radiales et labels lisibles)
    """
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap, LogNorm

    # ==========================
    # Préparation des données
    # ==========================
    df = xarray_data.to_dataframe().reset_index()
    df = df.set_index(["impacts", "axis"])
    df = df.pivot_table(values="lca", index=["impacts", "axis"], columns="year")
    df = df.loc[df.index.get_level_values("impacts").isin(pb_methods)]

    year = chosen_year
    df_agg = df[year].groupby(level=0).sum()
    df_agg = df_agg[df_agg > 0]

    if scaling_factors is not None:
        if isinstance(scaling_factors, dict):
            scale = pd.Series({k: scaling_factors.get(k, 1.0) for k in df_agg.index})
            df_agg /= scale
        else:
            df_agg /= scaling_factors

    df_agg *= 100  # Conversion en %

    categories = [c[2] if isinstance(c, tuple) else c for c in df_agg.index]
    values = df_agg.values

    # ==========================
    # Paramètres radar
    # ==========================
    N = len(categories)
    theta = np.linspace(0, 2 * np.pi, N, endpoint=False)
    width = 2 * np.pi / N  # * 0.82

    # Rotation des arcs colorés pour aligner
    theta_color = theta - width / 2

    # ==========================
    # Figure
    # ==========================
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")

    # ==========================
    # Colormap Planetary Boundaries
    # ==========================
    safe_green = "#1a9850"

    colors = [
        "#fee391",
        "#fdb863",
        "#f46d43",
        "#d73027",
        "#cc0000",
    ]

    pb_cmap = LinearSegmentedColormap.from_list("pb", colors)
    norm = LogNorm(vmin=100, vmax=1000)

    # ==========================
    # Dégradé radial PAR IMPACT
    # ==========================
    r_steps = np.logspace(0, np.log10(max(values) * 1.1), 500)

    for ang, val in zip(theta_color, values):
        if val < 1:
            continue  # saute cet impact
        for r0, r1 in zip(r_steps[:-1], r_steps[1:]):
            if r0 >= val:
                break
            if r1 > val:
                r1 = val
            ax.bar(
                ang,
                r1 - r0,
                bottom=r0,
                width=width,
                color=pb_cmap(norm(r1)),
                edgecolor=None,
                align="edge",
                log=True,
                zorder=2,
            )

    for ang, val in zip(theta_color, values):
        if val <= 1:
            continue

        safe_top = min(val, 100)

        ax.bar(
            ang,
            safe_top - 1,
            bottom=1,
            width=width,
            color=safe_green,
            edgecolor=None,
            align="edge",
            log=True,
            zorder=3,  # au-dessus du dégradé
        )

    # ==========================
    # Contours noirs
    # ==========================
    for ang, val in zip(theta, values):
        if val < 1:
            continue
        ax.bar(
            ang,
            val - 1,
            bottom=1,
            width=width,
            color="none",
            edgecolor="black",
            linewidth=1,
            log=True,
            zorder=4,
        )

    # ==========================
    # Lignes radiales fines
    # ==========================
    radial_ticks = [10, 100, 1000, 10000]
    for rt in radial_ticks:
        ax.plot(
            np.linspace(0, 2 * np.pi, 400),
            [rt] * 400,
            color="gray",
            linewidth=0.7,
            linestyle="--",
            zorder=6,
        )
    ax.plot(
        np.linspace(0, 2 * np.pi, 400),
        [100] * 400,
        color="white",
        linewidth=3,
        linestyle="-",
        zorder=5,
    )

    # ==========================
    # Axes & labels
    # ==========================

    max_radius = 100000

    arc_width = 2 * np.pi / N  # * 0.82
    theta_sep = theta + arc_width / 2  # décalage pour aligner sur le bord de l'arc

    for ang in theta_sep:
        ax.plot([ang, ang], [1, max_radius], color="gray", linewidth=0.8, linestyle="--", zorder=7)

    ax.set_xticks(theta)
    labels = [c.replace("_", " ").title() for c in categories]
    labels[0] = "Nitrogen\nCycle"
    labels[3] = "Climate\nChange"
    ax.set_xticklabels(labels, fontsize=11, fontweight="bold")
    ax.tick_params(axis="x", pad=20)

    ax.set_ylim(1, max_radius)
    ax.set_yticks([])
    ax.spines["polar"].set_visible(False)

    for rt in radial_ticks:
        ax.text(
            np.deg2rad(270),
            rt,
            f"{rt} %",  # texte
            fontsize=10,
            fontweight="bold",
            color="black",
            ha="center",
            va="bottom",  # aligne le texte au-dessus du cercle
            zorder=5,  # au-dessus des arcs colorés
        )

    ax.grid(False)
    plt.tight_layout()
    plt.show()


def plot_planetary_radar_all(xarray_data, scaling_factors=None, chosen_year=2050):
    """
    Planetary Boundaries radar – dégradé par impact
    (version avec lignes radiales et labels lisibles)
    """
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt

    # ==========================
    # Préparation des données
    # ==========================
    values = []
    for i in range(0, len(xarray_data)):
        df = xarray_data[i].to_dataframe().reset_index()
        df = df.set_index(["impacts", "axis"])
        df = df.pivot_table(values="lca", index=["impacts", "axis"], columns="year")
        df = df.loc[df.index.get_level_values("impacts").isin(pb_methods)]

        year = chosen_year
        df_agg = df[year].groupby(level=0).sum()
        df_agg = df_agg[df_agg > 0]

        if scaling_factors is not None:
            if isinstance(scaling_factors, dict):
                scale = pd.Series({k: scaling_factors.get(k, 1.0) for k in df_agg.index})
                df_agg /= scale
            else:
                df_agg /= scaling_factors

        df_agg *= 100  # Conversion en %

        categories = [c[2] if isinstance(c, tuple) else c for c in df_agg.index]
        values.append(df_agg.values)

    # ==========================
    # Paramètres radar
    # ==========================
    N = len(categories)
    theta = np.linspace(0, 2 * np.pi, N, endpoint=False)
    width = 2 * np.pi / N  # * 0.82

    # ==========================
    # Figure
    # ==========================
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")

    # ==========================
    # Contours noirs
    # ==========================
    for i in range(0, len(values)):
        if i == 0:
            chosen_edgecolor = "grey"
        elif i == 1:
            chosen_edgecolor = "orangered"
        elif i == 2:
            chosen_edgecolor = "limegreen"
        else:
            chosen_edgecolor = "royalblue"
        for ang, val in zip(theta, values[i]):
            if val < 1:
                continue
            ax.bar(
                ang,
                val - 1,
                bottom=1,
                width=width,
                color="none",
                edgecolor=chosen_edgecolor,
                linewidth=1,
                log=True,
                zorder=5,
            )

    # ==========================
    # Lignes radiales fines
    # ==========================
    radial_ticks = [10, 100, 1000, 10000]
    ax.plot(
        np.linspace(0, 2 * np.pi, 400),
        [100] * 400,
        color="white",
        linewidth=3,
        linestyle="-",
        zorder=4,
    )
    for rt in radial_ticks:
        ax.plot(
            np.linspace(0, 2 * np.pi, 400),
            [rt] * 400,
            color="gray",
            linewidth=0.7,
            linestyle="--",
            zorder=4,
        )

    # ==========================
    # Axes & labels
    # ==========================

    max_radius = 100000

    arc_width = 2 * np.pi / N  # * 0.82
    theta_sep = theta + arc_width / 2  # décalage pour aligner sur le bord de l'arc

    for ang in theta_sep:
        ax.plot([ang, ang], [1, max_radius], color="gray", linewidth=0.8, linestyle="--", zorder=7)

    ax.set_xticks(theta)
    labels = [c.replace("_", " ").title() for c in categories]
    labels[0] = "Nitrogen\nCycle"
    labels[3] = "Climate\nChange"
    ax.set_xticklabels(labels, fontsize=11, fontweight="bold")
    ax.tick_params(axis="x", pad=20)

    ax.set_ylim(1, max_radius)
    ax.set_yticks([])
    ax.spines["polar"].set_visible(False)

    for rt in radial_ticks:
        ax.text(
            np.deg2rad(270),
            rt,
            f"{rt} %",  # texte
            fontsize=10,
            fontweight="bold",
            color="black",
            ha="center",
            va="bottom",  # aligne le texte au-dessus du cercle
            zorder=5,  # au-dessus des arcs colorés
        )

    ax.grid(False)
    plt.tight_layout()
    plt.show()


def plot_planetary_table_all(xarray_data, scaling_factors=None, chosen_year=2050):
    values = []
    for i in range(0, len(xarray_data)):
        df = xarray_data[i].to_dataframe().reset_index()
        df = df.set_index(["impacts", "axis"])
        df = df.pivot_table(values="lca", index=["impacts", "axis"], columns="year")
        df = df.loc[df.index.get_level_values("impacts").isin(pb_methods)]

        year = chosen_year
        df_agg = df[year].groupby(level=0).sum()
        df_agg = df_agg[df_agg > 0]

        scaling_factors = scaling_factors
        if scaling_factors is not None:
            if isinstance(scaling_factors, dict):
                scale = pd.Series({k: scaling_factors.get(k, 1.0) for k in df_agg.index})
                df_agg /= scale
            else:
                df_agg /= scaling_factors

        df_agg *= 100  # Conversion en %

        categories = [c[2] if isinstance(c, tuple) else c for c in df_agg.index]
        values.append(df_agg.values)

    # Plot heatmap

    pb_labels = [c.replace("_", " ").title() for c in categories]
    pb_labels[0] = "Nitrogen\nCycle"
    pb_labels[3] = "Climate\nChange"
    scenario_labels = ["IS0", "IS1", "IS2", "IS3"]

    plt.figure(figsize=(12, 6))

    # Exemple de données
    values_clip = np.array(values)  # ton array exact

    def format_sci(v):
        if v < 10:
            return f"{v:.1f}"
        elif v < 100:
            return f"{v:.0f}"
        else:
            return f"{v:.1e}"

    annot_sci = np.vectorize(format_sci)(values_clip)

    # ---------------- Colormap
    colors = [
        "#fee391",
        "#fdb863",
        "#f46d43",
        "#d73027",
        "#cc0000",
    ]
    cmap = LinearSegmentedColormap.from_list("pb_log", colors)
    cmap.set_under("#1a9850")  # vert fixe pour <100
    cmap.set_over("#cc0000")  # rouge fixe pour >1000

    # ---------------- Norme log
    norm = LogNorm(vmin=100, vmax=10000)

    # ---------------- Heatmap
    plt.figure(figsize=(12, 6))
    ax = sns.heatmap(
        values_clip,
        annot=annot_sci,
        fmt="",
        cmap=cmap,
        norm=norm,
        xticklabels=pb_labels,
        yticklabels=scenario_labels,
        cbar=True,
        linewidths=0.5,
        linecolor="black",
        cbar_kws={
            "label": "Share of aviation planetary boundary [%]",
            "ticks": [100, 1000, 10000],
            "format": "%d",
        },
    )

    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(1.0)
        spine.set_color("black")

    cbar = ax.collections[0].colorbar

    # --- Flèche verte pour <100 (sous l'échelle) ---
    cbar.ax.annotate(
        "",  # pas de texte
        xy=(0.5, -0.05),  # pointe de la flèche, sous le cbar
        xytext=(0.5, 0.0),  # base de la flèche (en haut du vert)
        xycoords="axes fraction",
        arrowprops=dict(
            facecolor="#1a9850",
            edgecolor="#1a9850",
            width=15,
            headwidth=25,
            headlength=15,
            shrink=0,
        ),
        ha="center",
        va="center",
    )
    cbar.ax.annotate(
        "",  # pas de texte
        xy=(0.5, 1.05),  # pointe de la flèche, au-dessus du cbar
        xytext=(0.5, 1.0),  # base de la flèche (en bas du rouge)
        xycoords="axes fraction",
        arrowprops=dict(
            facecolor="#cc0000",
            edgecolor="#cc0000",
            width=15,
            headwidth=25,
            headlength=15,
            shrink=0,
        ),
        ha="center",
        va="center",
    )

    ax.grid(False)
    plt.tight_layout()
    plt.show()
    plt.savefig("test")
