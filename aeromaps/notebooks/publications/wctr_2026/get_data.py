from matplotlib.pyplot import subplots
from numpy import isnan
from numpy import ndarray
from numpy import nanmin, nanmax, nanmedian, column_stack, asarray
from pandas import read_csv

from aeromaps.plots.multi_scenario_plot import DEFAULT_LINESTYLES, DEFAULT_COLORS

scenario_to_model = {
    "SSP2-19": "REMIND-MAgPIE 1.5",
    "SSP2-26": "REMIND-MAgPIE 1.5",
    "SSP2-34": "REMIND-MAgPIE 1.5",
    "SSP2-45": "REMIND-MAgPIE 1.5",
}

ENVELOPE_ALPHA = 0.25


def _draw_envelope(ax, x, series_by_label, color, linewidth=2, envelope_alpha=ENVELOPE_ALPHA):
    """
    Draw a group of series using the envelope style from MultiScenarioPlot.

    Linestyles are assigned by label INDEX so they are consistent across
    multiple subplots that share a legend.

    For a single series, falls back to a plain solid line.  For multiple series,
    draws a fill_between band (min/max), individual lines for all series
    except the last and the median one (using their index-based linestyle),
    and a median middle line (also index-based linestyle) with a legend label.
    """
    labels = list(series_by_label.keys())
    # Stable linestyle per label: index → DEFAULT_LINESTYLES[index]
    label_linestyle = {
        label: DEFAULT_LINESTYLES[i % len(DEFAULT_LINESTYLES)]
        for i, label in enumerate(labels)
    }

    if len(labels) == 1:
        display = labels[0].split(" (")[0] if " (" in labels[0] else labels[0]
        ax.plot(x, series_by_label[labels[0]], color=color,
                linestyle=label_linestyle[labels[0]],
                linewidth=linewidth, label=display)
        return

    arr = column_stack([asarray(series_by_label[l], dtype=float) for l in labels])
    y_min = nanmin(arr, axis=1)
    y_max = nanmax(arr, axis=1)
    y_mid = nanmedian(arr, axis=1)

    # Find which column is closest to the median
    diffs = [abs(arr[:, i] - y_mid).sum() for i in range(arr.shape[1])]
    mid_idx = int(min(range(len(diffs)), key=lambda i: diffs[i]))
    mid_label = labels[mid_idx]

    ax.fill_between(x, y_min, y_max, color=color, alpha=envelope_alpha, linewidth=0,
                    label=f"{labels[0]} to {labels[-1]} range")

    # Background lines: all except the last and the mid, each with its index linestyle
    for label in labels[:-1]:
        if label == mid_label:
            continue
        ax.plot(x, series_by_label[label], color=color,
                linestyle=label_linestyle[label],
                linewidth=linewidth, label=label)

    # Middle line: uses its own index linestyle, labelled with the median scenario name
    mid_display_label = mid_label.split(" (")[0] if " (" in mid_label else mid_label
    ax.plot(x, y_mid, color=color, linestyle=label_linestyle[mid_label],
            linewidth=linewidth, label=mid_display_label)


def get_scenario_color(scenario_name: str):
    """Get scenario color from SSP name."""
    name_split = scenario_name.split("SSP")
    ssp_idx = int(name_split[1][0])
    if ssp_idx == 1:
        return "darkgreen"
    if ssp_idx == 2:
        return "royalblue"
    if ssp_idx == 3:
        return "firebrick"
    if ssp_idx == 4:
        return "darkorange"
    return "darkviolet"


def get_ar6_input_data(start_year=2010, end_year=2100, plot_data=True):
    """Get relevant data from AR6 scenarios."""
    population_data = read_csv(
        "./ar6_scenarios/population.csv",
        index_col=1,
    )
    gdp_data = read_csv(
        "./ar6_scenarios/gdp.csv",
        index_col=1,
    )
    co2tax_data = read_csv(
        "./ar6_scenarios/carbon_tax.csv",
        index_col=1,
    )

    all_years = [
        int(year)
        for year in list(co2tax_data.keys())[5:]
        if start_year <= int(year) <= end_year
    ]
    var_units_name_convert = {
        "population": ("million hab.", "Population", 1e6),
        "gdp_per_capita": ("thousand US$2010/(hab. year)", "GDP per capita", 1e3),
        "carbon_tax": ("US$2010 / ton CO2", "Carbon Price", 1),
    }

    ar6_data = {
        "population": {},
        "gdp_per_capita": {},
        "carbon_tax": {},
    }
    years = []
    for scenario, model in scenario_to_model.items():
        for variable in ar6_data:
            ar6_data[variable][scenario] = []
        for year in all_years:
            array_or_pandas = population_data[str(year)][scenario][
                population_data["Model"][scenario] == model
            ]
            if isinstance(array_or_pandas, ndarray):
                pop = population_data[str(year)][scenario][
                    population_data["Model"][scenario] == model
                ]
                gdp = gdp_data[str(year)][scenario][
                    gdp_data["Model"][scenario] == model
                ]
                co2_tax = co2tax_data[str(year)][scenario][
                    co2tax_data["Model"][scenario] == model
                ]
            else:
                pop = population_data[str(year)][scenario][
                    population_data["Model"][scenario] == model
                ].to_numpy()
                gdp = gdp_data[str(year)][scenario][
                    gdp_data["Model"][scenario] == model
                ].to_numpy()
                co2_tax = co2tax_data[str(year)][scenario][
                    co2tax_data["Model"][scenario] == model
                ].to_numpy()

            if not any(
                isnan(data_array) or data_array.size == 0
                for data_array in [pop, gdp, co2_tax]
            ):
                if year not in years:
                    years.append(year)
                ar6_data["population"][scenario].append(
                    float(pop) * var_units_name_convert["population"][-1]
                )
                ar6_data["gdp_per_capita"][scenario].append(
                    float(gdp / pop) * var_units_name_convert["gdp_per_capita"][-1]
                )
                ar6_data["carbon_tax"][scenario].append(
                    float(co2_tax) * var_units_name_convert["carbon_tax"][-1]
                )

    if plot_data:
        # Group scenarios by SSP family for envelope plotting
        ssp_groups: dict[str, list[str]] = {}
        for scenario in scenario_to_model:
            ssp_key = "SSP" + scenario.split("SSP")[1][0]  # e.g. "SSP2"
            ssp_groups.setdefault(ssp_key, []).append(scenario)

        fig, axes = subplots(1, 3, figsize=(10, 4), layout="constrained")
        for i, (key, unit_name_convert) in enumerate(var_units_name_convert.items()):
            for ssp_key, group_scenarios in ssp_groups.items():
                color = get_scenario_color(ssp_key)
                series_by_label = {
                    scenario: [v / var_units_name_convert[key][-1] for v in ar6_data[key][scenario]]
                    for scenario in group_scenarios
                }
                _draw_envelope(axes[i], years, series_by_label, color=color, linewidth=2)
            axes[i].set_title(var_units_name_convert[key][1])
            axes[i].set_ylabel(var_units_name_convert[key][0])
            axes[i].set_xlabel("Year")
            axes[i].set_xlim(left=2010, right=2100)
        axes[0].legend(loc="lower right")
        axes[0].set_ylim(bottom=0)
        axes[1].set_ylim(bottom=0)
        axes[2].set_ylim(bottom=0, top=10000)

        # Inset zoom axes for GDP and carbon tax
        inset_configs = {
            1: {"xlim": (2019, 2031), "ylim": (14, 19)},
            2: {"xlim": (2019, 2031), "ylim": (0, 250)},
        }
        for ax_idx, cfg in inset_configs.items():
            ax_inset = axes[ax_idx].inset_axes([0.15, 0.45, 0.55, 0.5])
            key = list(var_units_name_convert.keys())[ax_idx]
            for ssp_key, group_scenarios in ssp_groups.items():
                color = get_scenario_color(ssp_key)
                series_by_label = {
                    scenario: [v / var_units_name_convert[key][-1] for v in ar6_data[key][scenario]]
                    for scenario in group_scenarios
                }
                _draw_envelope(ax_inset, years, series_by_label, color=color, linewidth=2)
            ax_inset.set_xlim(*cfg["xlim"])
            ax_inset.set_ylim(*cfg["ylim"])
            ax_inset.tick_params(labelsize=7)
            axes[ax_idx].indicate_inset_zoom(ax_inset, edgecolor="black")

        fig.savefig("scenario_data.pdf")

    return ar6_data, years


def get_ar6_rpk_data(start_year=2005, end_year=2100, plot_data=True):
    """Get RPK (Revenue Passenger Kilometres) data for all AR6 scenarios."""
    rpk_data = read_csv(
        "./ar6_scenarios/rpk.csv",
        index_col=1,
    )

    all_years = [
        int(year)
        for year in list(rpk_data.keys())[4:]
        if start_year <= int(year) <= end_year
    ]

    all_scenarios = rpk_data.index.unique().tolist()

    ar6_rpk = {}  # {scenario: {model: [rpk values]}}
    years_per_scenario = {}

    for scenario in all_scenarios:
        scenario_rows = rpk_data.loc[[scenario]]
        ar6_rpk[scenario] = {}
        for _, row in scenario_rows.iterrows():
            model = row["Model"]
            rpk_values = []
            valid_years = []
            for year in all_years:
                val = row[str(year)]
                try:
                    fval = float(val)
                    if not isnan(fval):
                        rpk_values.append(fval)
                        valid_years.append(year)
                except (ValueError, TypeError):
                    pass
            if rpk_values:
                ar6_rpk[scenario][model] = rpk_values
                years_per_scenario.setdefault(scenario, valid_years)

    if plot_data:
        fig, ax = subplots(figsize=(9, 5), layout="constrained")
        for scenario in all_scenarios:
            if scenario not in ar6_rpk or not ar6_rpk[scenario]:
                continue
            color = get_scenario_color(scenario)
            years_s = years_per_scenario[scenario]
            series_by_label = {
                f"{scenario} ({model})": values
                for model, values in ar6_rpk[scenario].items()
            }
            _draw_envelope(ax, years_s, series_by_label, color=color, linewidth=1.5)
        ax.set_title("Aviation RPK — AR6 Scenarios")
        ax.set_ylabel("bn pkm/yr")
        ax.set_xlabel("Year")
        ax.set_xlim(left=start_year, right=end_year)
        ax.set_ylim(bottom=0)

    return ar6_rpk, years_per_scenario
