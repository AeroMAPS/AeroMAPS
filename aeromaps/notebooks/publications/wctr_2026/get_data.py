from matplotlib.pyplot import figure
from matplotlib.pyplot import subplots
from numpy import interp
from numpy import linspace
from numpy import ones
from numpy import sqrt
from numpy import array
from numpy import isnan
from numpy import ndarray
from numpy import sum
from numpy import zeros
from pandas import read_csv
from scipy.interpolate import CubicSpline

scenario_to_model = {
    "SSP2-19": "REMIND-MAgPIE 1.5",
    "SSP2-26": "REMIND-MAgPIE 1.5",
    # "SSP2-34": "REMIND-MAgPIE 1.5",
    "SSP2-45": "REMIND-MAgPIE 1.5",
}


def lines_gen():
    """Linestyle generator."""
    yield "-"
    for i in range(1, 12):
        yield 0, (i, 1, 1, 1)


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
        fig, axes = subplots(1, 3, figsize=(9, 4), layout="constrained")
        for i, (key, unit_name_convert) in enumerate(var_units_name_convert.items()):
            lines = lines_gen()
            color = "royalblue"
            for scenario in scenario_to_model:
                line = next(lines)
                if scenario == list(scenario_to_model.keys())[-1]:
                    line = next(lines)
                axes[i].plot(
                    years,
                    [
                        value / var_units_name_convert[key][-1]
                        for value in ar6_data[key][scenario]
                    ],
                    label=scenario,
                    color=color,
                    linestyle=line,
                    linewidth=2,
                )
                axes[i].set_title(var_units_name_convert[key][1])
                axes[i].set_ylabel(var_units_name_convert[key][0])
                axes[i].set_xlabel("Year")
        axes[0].legend(loc="lower right")
        axes[0].set_ylim(bottom=0)
        axes[1].set_ylim(bottom=0)
        axes[2].set_ylim(bottom=0)

    return ar6_data, years
