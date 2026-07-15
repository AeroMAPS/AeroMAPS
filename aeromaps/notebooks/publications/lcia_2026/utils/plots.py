import math
import collections
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as ticker


#palette = sns.color_palette("Set2", 10)
#palette_dict = {
#    "NOx": (palette[1], ""),
#    "soot": (palette[5], ""),
#    "CO2": (palette[7], ""),
#    "sulfur": (palette[4], ""),
#    "contrails": (palette[2], ""),
#    "water_vapour": (palette[6], ""),
#    "non_NOx": (palette[7], "//"),
#}

palette_dict = {
    "NOx": ("#e76f51", ""),
    "soot": ("#7b2cbf", ""),
    "CO2": ("#adb5bd", ""),
    "sulfur": ("#a7c957", ""),
    "contrails": ("#e9c46a", ""),
    "water_vapour": ("#3f88c5", ""),
    "non_NOx": ("#e3d5ca", "//"),
}

order = [
    "CO2",
    "contrails",
    "water_vapour",
    "NOx",
    "soot",
    "sulfur",
    "non_NOx"
]


def prepare_non_nox(da):
    """Create non_NOx pollutant from fuel_burn_air_quality - NOx"""

    targets = ["pm25: human health", "o3: human health"]
    mask = [imp[2] in targets for imp in da.impacts.values]

    non_nox = (
        da.loc[dict(axis="fuel_burn_air_quality", impacts=mask)]
        - da.loc[dict(axis="NOx", impacts=mask)]
    ).assign_coords(axis="non_NOx")

    da = xr.concat([da, non_nox], dim="axis")
    da = da.drop_sel(axis="fuel_burn_air_quality")

    return da


def merge_nox_axes(da):
    """
    Sum all axes containing 'NOx' into a single 'NOx' axis.
    """

    # select axes containing NOx but exclude non_NOx
    nox_axes = [ax for ax in da.axis.values if "NOx" in ax and ax != "non_NOx"]

    if not nox_axes:
        return da

    # sum all NOx axes
    nox_sum = da.sel(axis=nox_axes).sum(dim="axis")

    # reintroduce axis dimension
    nox_sum = nox_sum.expand_dims("axis").assign_coords(axis=["NOx"])

    # remove original NOx axes
    da = da.drop_sel(axis=nox_axes)

    # append merged NOx
    da = xr.concat([da, nox_sum], dim="axis")

    return da


def plot_stacked_evolution_subplots(xarray_data, start_year: int = 2019, end_year: int = None):
    """
    Plot stacked evolution of LCA results stored in an xarray.
    """

    # ------------------------------------------------------------------
    # 1. Prepare xarray data
    # ------------------------------------------------------------------

    da = xarray_data.copy()

    # --- Compute non-NOx contribution (fuel_burn_air_quality - NOx, excl. LH2)
    da = prepare_non_nox(da)
    
    # --- Merge NOx contributions (all fuels incl. LH2)
    da = merge_nox_axes(da)

    # --- Create new aggregated impact
    sum_targets = [
        "pm25: human health",
        "o3: human health",
        "climate change: human health",
    ]

    sum_mask = [imp[2] in sum_targets for imp in da.impacts.values]

    summed = da.sel(impacts=sum_mask).groupby("axis").sum("impacts")

    new_impact = ("LCIA Aviation", "human health", "total: human health")
    summed = summed.expand_dims(impacts=[new_impact])

    da = xr.concat([da, summed], dim="impacts")
    
    # --- Units
    units = da.coords["impacts"].attrs["units"].copy()
    units[("LCIA Aviation", "human health", "total: human health")] = 'DALY'

    # ------------------------------------------------------------------
    # 2. Convert to dataframe
    # ------------------------------------------------------------------

    df = da.to_dataframe().reset_index()

    if start_year:
        df = df[df["year"] >= start_year]
    if end_year:
        df = df[df["year"] <= end_year]

    df = (
        df.set_index(["impacts", "axis", "year"])
        .pivot_table(values="lca", index=["impacts", "axis"], columns="year")
    )

    df = df[~df.index.get_level_values("axis").str.contains("sum")]

    methods = df.index.get_level_values("impacts").unique()
    years = df.columns

    # ------------------------------------------------------------------
    # 3. Plot layout
    # ------------------------------------------------------------------

    n_methods = len(methods)
    n_cols = 3
    n_rows = math.ceil(n_methods / n_cols)

    fig, axes = plt.subplots(
        n_rows,
        n_cols,
        figsize=(12, n_rows * 4),
        constrained_layout=False,
    )

    axes = axes.flatten()

    # ------------------------------------------------------------------
    # 4. Plot each impact
    # ------------------------------------------------------------------

    for i, method in enumerate(methods):

        df_method = df.xs(method, level="impacts")
        df_method.index = df_method.index.str.replace("_other_", "Others")

        df_method = df_method.loc[~(df_method.eq(0).all(axis=1))]

        # enforce pollutant order
        present = [p for p in order if p in df_method.index]
        remaining = [p for p in df_method.index if p not in order]

        df_method = df_method.loc[present + remaining]

        colors = [palette_dict.get(key, ["gray"])[0] for key in df_method.index]

        #stacks = axes[i].stackplot(
        #    years,
        #    df_method,
        #    labels=df_method.index,
        #    alpha=0.8,
        #    colors=colors,
        #    linewidth=0.2,
        #)
        
        values = df_method.values

        positive = np.where(values > 0, values, 0)
        negative = np.where(values < 0, values, 0)

        # positive stack
        stacks_pos = axes[i].stackplot(
            years,
            positive,
            labels=df_method.index,
            alpha=0.8,
            colors=colors,
            linewidth=0.2,
        )

        # negative stack
        stacks_neg = axes[i].stackplot(
            years,
            negative,
            alpha=0.8,
            colors=colors,
            linewidth=0.2,
        )

        stacks = stacks_pos + stacks_neg

        # ---- Format title
        name = method[0] + " " + method[2]
        #name = name.replace("total", "")
        name = name.split("- ")[0]
        name = name.replace(":", "\n")
        name = "".join(
            [a if a.isupper() else b for a, b in zip(name, name.title())]
        )

        # ---- Format unit
        unit = units.get(method, '') #xarray_data.coords["impacts"].attrs["units"][method] 
        unit = (
            unit.replace("]", "")
            .replace("-Eq", "-eq")
            .replace("CO2", r"CO$_2$")
        )

        ax = axes[i]
        ax.set_title(name, fontsize=12)
        ax.set_xlabel("Year")
        ax.set_ylabel(unit)
        ax.grid(True)
        ax.set_axisbelow(True)
        ax.ticklabel_format(axis="y", scilimits=(0, 4))
        ax.set_facecolor("white")

        # ---- Apply hatches
        hatches = [palette_dict.get(key, ["", ""])[1] for key in df_method.index]

        for stack, hatch, values in zip(stacks, hatches, df_method.values):

            if np.any(values != 0):
                stack.set_edgecolor("0.1")

            if hatch:
                stack.set_hatch(hatch)

    # ------------------------------------------------------------------
    # 5. Global legend
    # ------------------------------------------------------------------

    all_handles = []
    all_labels = []

    for ax in axes:
        handles, labels = ax.get_legend_handles_labels()
        all_handles.extend(handles)
        all_labels.extend(labels)

    entries = collections.OrderedDict()

    for handle, label in zip(all_handles, all_labels):

        if "CO2" in label:
            label_name = label.replace("CO2", r"CO$_2$")
        elif "non_NOx" in label:
            label_name = label.replace(
                "non_NOx",
                r"non-NO$_x$ (for PM$_{2.5}$ & O$_3$)",
            )
        elif "NOx" in label:
            label_name = label.replace("NOx", r"NO$_x$")
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
        #title="Contribution",
        title_fontsize=12,
    )

    bbox = legend.get_window_extent(fig.canvas.get_renderer()).transformed(
        fig.transFigure.inverted()
    )

    fig.tight_layout(rect=(0, bbox.y1, 1, 1), h_pad=0.5, w_pad=0.5)

    plt.show()
    

def stacked_cascade_impacts(
    da, 
    year, 
    ax, 
    palette_dict, 
    lcia_method: str = 'LCIA Aviation',
    targets=[
        "climate change: human health",
        "pm25: human health",
        "o3: human health",
    ], 
):

    # --- Compute non-NOx contribution (fuel_burn_air_quality - NOx excl. LH2)
    da = prepare_non_nox(da)
    
    # --- Merge NOx contributions (all fuels incl. LH2)
    da = merge_nox_axes(da)

    da_year = da.sel(year=year)

    df = da_year.to_dataframe().reset_index()
    df = df[df["impacts"].apply(lambda x: lcia_method in x[0] and x[2] in targets)]

    df_pivot = df.pivot_table(
        values="lca",
        index="axis",
        columns="impacts",
        aggfunc="sum"
    ).fillna(0)

    # List impacts, and reorder by priority order
    impacts = list(df_pivot.columns)
    priority = ["climate change", "pm25", "particulate matter", "o3", "ozone", "photochemical oxidant"]
    ordered = []
    for p in priority:
        ordered.extend([x for x in impacts if p.lower() in x[2].lower()])
    ordered.extend([x for x in impacts if x not in ordered])
    impacts = ordered

    # sort pollutants by magnitude
    #pollutant_order = df_pivot.sum(axis=1).abs().sort_values(ascending=False).index
    df_pivot = df_pivot.loc[order]

    pollutants = df_pivot.index

    colors = [palette_dict.get(p, ("gray",""))[0] for p in pollutants]
    hatches = [palette_dict.get(p, ("",""))[1] for p in pollutants]

    cumulative = 0
    bar_width = 0.65

    for i, impact in enumerate(impacts):

        values = df_pivot[impact].values
        impact_total = values.sum()

        pos_bottom = cumulative
        neg_bottom = cumulative

        for pollutant, value, color, hatch in zip(pollutants, values, colors, hatches):

            if value >= 0:
                bar = ax.bar(i, value, bottom=pos_bottom,
                             width=bar_width, color=color, edgecolor="0.2")
                pos_bottom += value
            else:
                bar = ax.bar(i, value, bottom=neg_bottom,
                             width=bar_width, color=color, edgecolor="0.2")
                neg_bottom += value

            if hatch:
                bar[0].set_hatch(hatch)

        new_level = cumulative + impact_total

        # true visible bar limits
        top = max(pos_bottom, neg_bottom)
        bottom = min(pos_bottom, neg_bottom)

        # connector at top of bar
        if i < len(impacts) - 1:
            ax.plot(
                [i + bar_width/2, i + 1 - bar_width/2],
                [top, top],
                color="black",
                linewidth=1
            )

        # place label at bar extremity
        label_y = top + 1e5 #if impact_total >= 0 else bottom - 0.1
        exponent = int(np.floor(np.log10(abs(impact_total))))
        coeff = impact_total / 10**exponent

        ax.text(
            i,
            label_y,
            #f"{impact_total:.2e}",
            r"${:.1f}\times10^{{{}}}$".format(coeff, exponent),
            ha="center",
            va="bottom" if impact_total >= 0 else "top",
            fontsize=10.5
        )

        cumulative = max(pos_bottom, neg_bottom)# + impact_total #new_level

    labels = [
        imp[2]
        .replace(": human health","")
        .replace("pm25","PM$_{2.5}$")
        .replace("o3","O$_3$")
        .replace("climate change","climate\nchange")
        .replace('particulate matter formation', "PM$_{2.5}$")
        .replace('photochemical oxidant formation', "O$_{3}$")
        #.title()
        for imp in impacts
    ]
    
    ymin, ymax = ax.get_ylim()
    ax.set_ylim(ymin, ymax * 1.03)

    ax.set_xticks(range(len(impacts)))
    ax.set_xticklabels(labels)

    ax.axhline(0, color="black", linewidth=0.8)

    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    ax.set_facecolor("white")
    
    

def stacked_cascade_scenarios(
    scenarios, 
    ylim=None, 
    lcia_method: str = 'LCIA Aviation',
    targets=[
        "climate change: human health",
        "pm25: human health",
        "o3: human health",
    ], 
):
    
    n = len(scenarios)
    n_cols = 4
    n_rows = math.ceil(n / n_cols)

    fig, axes = plt.subplots(
        n_rows,
        n_cols,
        figsize=(10, n_rows * 6.5),
        sharey=True,
        facecolor="white"
    )

    axes = axes.flatten()

    for i, ((name, (da, year)), ax) in enumerate(zip(scenarios.items(), axes)):
        
        stacked_cascade_impacts(
            da,
            year=year,
            ax=ax,
            palette_dict=palette_dict,
            lcia_method=lcia_method,
            targets=targets
        )

        ax.set_title(name, fontsize=11)

        if i % n_cols == 0:
            ax.set_ylabel("Health Impacts (DALYs)", fontsize=12)

    # hide unused axes
    for j in range(i+1, len(axes)):
        axes[j].axis("off")

    # legend
    entries = collections.OrderedDict()

    for key, (color, hatch) in palette_dict.items():

        label = key

        if "CO2" in label:
            label = r"CO$_2$"
        elif key == "non_NOx":
            label = r"non-NO$_x$ (for PM$_{2.5}$ & O$_3$)"
        elif key == "NOx":
            label = r"NO$_x$"
        else:
            label = label.replace("_"," ").title()

        patch = plt.Rectangle(
            (0,0),1,1,
            facecolor=color,
            edgecolor="0.2",
            hatch=hatch
        )

        entries[label] = patch
        
    if ylim:
        axes[0].set_ylim(ylim)
    
    axes[0].yaxis.set_major_formatter(ticker.FuncFormatter(sci_notation))
    axes[0].tick_params(axis='y', labelsize=12)

    legend = fig.legend(
        entries.values(),
        entries.keys(),
        loc="lower center",
        bbox_to_anchor=(0.5, 0),
        ncol=4,
        fontsize=11,
        #title="Contribution",
        title_fontsize=12,
    )

    bbox = legend.get_window_extent(fig.canvas.get_renderer()).transformed(
        fig.transFigure.inverted()
    )

    fig.tight_layout(rect=(0, bbox.y1, 1, 1), h_pad=0.5, w_pad=0.5)

    plt.show()
    

def sci_notation(x, pos):
    if x == 0:
        return "0"
    exponent = int(np.floor(np.log10(abs(x))))
    coeff = x / 10**exponent
    return r"${:.0f}\times10^{{{}}}$".format(coeff, exponent)