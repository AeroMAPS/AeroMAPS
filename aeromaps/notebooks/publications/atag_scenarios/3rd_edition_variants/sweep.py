"""Full lever sweep over the third-edition Waypoint 2050 grid.

The report defines its scenarios as combinations of five levers, and publishes
three of them (S0, S1, S2). This module runs the rest of the grid: every
combination of traffic growth, aircraft technology, operations and SAF
deployment. Market-based measures are not swept -- they are computed as the
residual needed to reach the target, so they follow from the other four rather
than varying independently.

    3 traffic x 4 technology x 3 operations x 4 SAF = 144 runs

Processes are built on the fly rather than from 144 committed configuration
files. Only traffic and SAF need to differ at configuration level (they select
data files, which are read at construction), so twelve scratch configurations
are generated into ``_generated/`` and reused; technology and operations are applied
afterwards as parameter overrides. Each run is computed, reduced to the series
and scalars worth keeping, and then discarded, so memory stays flat regardless
of grid size.

Lever definitions follow the report:

* traffic     low / central / high, via the shared digitised market files
* technology  T1 baseline existing aircraft, T2 conservative next-generation
              tube-and-wing, T3 new configurations, T4 towards non-drop-in
              energies. T0 (frozen fleet efficiency) is excluded: it is a
              notional counterfactual, not a scenario.
* operations  O1 / O2 / O3 at 0.00 / 0.10 / 0.20 %/yr, entered as the
              cumulative gain over 2020-2050 (0 / 3 / 6 %). Note that the
              sweep varies the gain alone: every cell inherits S1's load
              factor, which rises to 88.389 % by 2050. Table 2's operations
              axis instead varies gain and load factor together, as the
              reports bundle them, so a sweep O1 cell is not the same run as
              the O1 row of that table -- it carries a load-factor gain the
              table row does not. Reconciling the two would move the quoted
              grid range, so it is left as a known difference rather than
              changed silently.
* SAF         F0 no drop-in SAF at all, F1 stated policies (~150 Mt), F2 (~430 Mt),
              F3 (~280-380 Mt).

A note on SAF resolution. F2 and F3 are published as quantities *per pathway*,
so they map onto the eleven-carrier energy files of the full edition. F1
publishes only a total volume with no pathway breakdown, so it is modelled as a
single generic SAF carrier, reusing the light edition's S0 energy file rather
than inventing a pathway split. Consequently pathway-level outputs (biofuel
mix, per-pathway resource use) are not defined for the F1 arm, and comparisons
across the SAF axis must stay on totals. F0 is not published at all; it is a
counterfactual added to give the fuel axis a floor, so that F1-F3 can be read
as reductions from a stated reference rather than as absolute levels.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

from aeromaps import create_process
from aeromaps.utils import sweep as sweep_utils
from aeromaps.utils.scenarios import find_scenario, scenarios_root

HERE = Path(__file__).resolve().parent
ATAG = HERE.parent
GENERATED = HERE / "_generated"

# The scenario definitions these runs draw on ship with the package, while the
# generated configurations are throwaway files in a gitignored folder. Absolute
# paths therefore, rather than a relative prefix that would have to track the depth
# of two directory trees at once.
FULL_INPUTS = (find_scenario("atag_3rd_edition_full").path / "data_inputs").as_posix()
LIGHT_INPUTS = (find_scenario("atag_3rd_edition_light").path / "data_inputs").as_posix()
MARKETS = (scenarios_root() / "markets").as_posix()

# The third edition uses its own low/high files. The shared markets_low/high.yaml encode
# second-edition growth whose spread lives in a COVID trough that the observed-data
# baseline removes, which inverts the ordering; markets_{low,high}_3rd.yaml instead scale
# central growth after the prospection start to hit the published 2050 figures. Built by
# make_traffic_variants.py.
TRAFFIC_LEVELS = {
    "low": f"{MARKETS}/markets_low_3rd.yaml",
    "central": f"{MARKETS}/markets_central.yaml",
    "high": f"{MARKETS}/markets_high_3rd.yaml",
}

# Cumulative operations-and-infrastructure gain over 2020-2050, from the
# report's 0.00 / 0.10 / 0.20 %/yr scenarios.
OPERATIONS_LEVELS = {
    "O1": [0, 0],
    "O2": [0, 3],
    "O3": [0, 6],
}

SAF_LEVELS = {
    # No drop-in SAF at all: fossil kerosene plus the two alternative-aircraft
    # carriers, the same file the technology-only T0-T4 runs use. This isolates
    # the drop-in fuel lever from the technology one, since T4's battery-electric
    # and liquid-hydrogen fleet is still available under F0 and does not depend
    # on any of F1-F3 being present.
    "F0": {
        "energy_carriers_model_data_file": f"{FULL_INPUTS}/tech_energy.yaml",
        "resources_model_data_file": f"{FULL_INPUTS}/resources.yaml",
        "processes_model_data_file": f"{FULL_INPUTS}/processes.yaml",
    },
    # F1 reuses the light edition's single-carrier setup, which draws its
    # feedstock from the packaged default resources rather than an
    # edition-local file.
    "F1": {
        "energy_carriers_model_data_file": f"{LIGHT_INPUTS}/s0_energy.yaml",
        "resources_model_data_file": "default",
        "processes_model_data_file": "default",
    },
    "F2": {
        "energy_carriers_model_data_file": f"{FULL_INPUTS}/s1_energy.yaml",
        "resources_model_data_file": f"{FULL_INPUTS}/resources.yaml",
        "processes_model_data_file": f"{FULL_INPUTS}/processes.yaml",
    },
    "F3": {
        "energy_carriers_model_data_file": f"{FULL_INPUTS}/s2_energy.yaml",
        "resources_model_data_file": f"{FULL_INPUTS}/resources.yaml",
        "processes_model_data_file": f"{FULL_INPUTS}/processes.yaml",
    },
}

TECHNOLOGY_LEVELS = ("T1", "T2", "T3", "T4")

# The technology lever proper. The t*_inputs.json files also differ in load
# factor, operations and offsets, because they are isolated technology runs
# with everything else switched off; those keys are deliberately not copied
# here, since the sweep varies operations separately and keeps S1's demand,
# load factor and offset assumptions throughout.
TECHNOLOGY_KEYS = (
    "short_range_energy_per_ask_dropin_fuel_gain_reference_years",
    "short_range_energy_per_ask_dropin_fuel_gain_reference_years_values",
    "medium_range_energy_per_ask_dropin_fuel_gain_reference_years",
    "medium_range_energy_per_ask_dropin_fuel_gain_reference_years_values",
    "long_range_energy_per_ask_dropin_fuel_gain_reference_years",
    "long_range_energy_per_ask_dropin_fuel_gain_reference_years_values",
    "short_range_electric_final_market_share",
    "short_range_electric_introduction_year",
)

# The published scenarios, as coordinates in this grid. S1 and S2 are the
# third-edition headline scenarios; the sweep reproduces them exactly, which is
# what makes them usable as a correctness check.
PUBLISHED_CELLS = {
    "S0": ("central", "T2", "O2", "F1"),
    "S1": ("central", "T3", "O3", "F2"),
    "S2": ("central", "T4", "O3", "F3"),
}

# Line style per published scenario, so the three are told apart in a legend that
# is otherwise all black.
PUBLISHED_STYLES = {"S0": ":", "S1": "-", "S2": "--"}

# Annual series kept for every run. Anything else can be recomputed from the
# committed scenario outputs, so the sweep file stays small enough to commit.
SERIES_COLUMNS = {
    "climate": (
        "co2_emissions",
        "temperature_increase_from_aviation",
        "temperature_increase_from_contrails_from_aviation",
        "total_erf",
        "co2_erf",
    ),
    "vector": (
        "rpk",
        "load_factor",
        "energy_consumption",
        "carbon_offset",
        "cumulative_carbon_offset",
        "cumulative_co2_emissions",
        "co2_emissions_last_historical_year_technology_baseline3",
        "co2_emissions_last_historical_year_technology",
        "co2_emissions_including_aircraft_efficiency",
        "co2_emissions_including_load_factor",
        "co2_emissions_including_energy",
        # Needed to split the energy term into its SAF and alternative-aircraft
        # parts, the way atag_decomposition does for the headline scenarios.
        # Absent arms are skipped by the `column in vector` guard above: only the
        # T4 technology level flies anything that is not a drop-in.
        "energy_consumption_dropin_fuel",
        "energy_consumption_hydrogen",
        "energy_consumption_electric",
        "dropin_fuel_mean_co2_emission_factor",
        "co2_per_energy_mean",
    ),
}


def _standards():
    """Model bundles of the third-edition full scenarios, read from S1."""
    base = yaml.safe_load((ATAG / "3rd_edition_full/config_files/config_s1.yaml").read_text())
    return base["models"]["standards"]


def config_path(traffic, saf):
    """Path of the scratch configuration for one (traffic, SAF) pair.

    Written on first use and reused afterwards: the pair selects data files,
    which are read when the process is constructed, so it cannot be applied as
    a parameter override the way technology and operations can.
    """
    GENERATED.mkdir(exist_ok=True)
    path = GENERATED / f"config_{traffic}_{saf.lower()}.yaml"
    if not path.exists():
        config = {
            "data": {
                "inputs": {"json_inputs_file": f"{FULL_INPUTS}/s1_inputs.json"},
                "outputs": {"json_outputs_file": f"./{path.stem}_outputs.json"},
            },
            "models": {
                "climate": {"climate_model_data_file": "default"},
                "energy": dict(SAF_LEVELS[saf]),
                "standards": _standards(),
                "markets": {"markets_data_file": TRAFFIC_LEVELS[traffic]},
            },
        }
        path.write_text(yaml.safe_dump(config, sort_keys=False))
    return path


def technology_overrides(technology):
    """Parameter overrides carrying one technology variant."""
    inputs = json.loads(
        (ATAG / f"3rd_edition_full/data_inputs/{technology.lower()}_inputs.json").read_text()
    )
    missing = [key for key in TECHNOLOGY_KEYS if key not in inputs]
    if missing:
        raise KeyError(f"{technology}_inputs.json is missing {missing}")
    return {key: inputs[key] for key in TECHNOLOGY_KEYS}


def build_process(traffic, technology, operations, saf):
    """Build one grid cell, ready to compute."""
    process = create_process(configuration_file=str(config_path(traffic, saf)))
    for key, value in technology_overrides(technology).items():
        setattr(process.parameters, key, value)
    process.parameters.operations_gain_reference_years = [2020, 2050]
    process.parameters.operations_gain_reference_years_values = OPERATIONS_LEVELS[operations]
    return process


def extract(process, traffic, technology, operations, saf):
    """Reduce a computed process to the rows worth keeping.

    Returns a long frame of annual series. Scalars are derived from it later
    rather than stored twice.
    """
    years = process.data["years"]["full_years"]
    climate = process.data["climate_outputs"]
    vector = process.data["vector_outputs"]

    frames = []
    for column in SERIES_COLUMNS["climate"]:
        if column in climate:
            frames.append(
                pd.DataFrame(
                    {
                        "year": years,
                        "variable": column,
                        "value": climate.loc[years, column].to_numpy(),
                    }
                )
            )
    for column in SERIES_COLUMNS["vector"]:
        if column in vector:
            frames.append(
                pd.DataFrame(
                    {
                        "year": years,
                        "variable": column,
                        "value": vector.loc[years, column].to_numpy(),
                    }
                )
            )

    # Drop-in energy by origin, so the SAF share can be recomputed downstream.
    # Collected dynamically because the F1 arm carries a different carrier set
    # from the F2/F3 arms.
    for column in vector.columns:
        if column.startswith("dropin_fuel_") and column.endswith("_energy_consumption"):
            frames.append(
                pd.DataFrame(
                    {
                        "year": years,
                        "variable": column,
                        "value": vector.loc[years, column].to_numpy(),
                    }
                )
            )

    tidy = pd.concat(frames, ignore_index=True)
    tidy.insert(0, "traffic", traffic)
    tidy.insert(1, "technology", technology)
    tidy.insert(2, "operations", operations)
    tidy.insert(3, "saf", saf)
    return tidy


# The lever axes, in the order a cell tuple carries them.
AXES = {
    "traffic": TRAFFIC_LEVELS,
    "technology": TECHNOLOGY_LEVELS,
    "operations": OPERATIONS_LEVELS,
    "saf": SAF_LEVELS,
}

CELL_KEYS = list(AXES)


def grid():
    """The 144 cells, in a stable order."""
    return sweep_utils.grid(AXES)


def run_sweep(cells=None, progress=True):
    """Run the grid and return one tidy frame of annual series."""
    return sweep_utils.run_grid(
        cells if cells is not None else grid(),
        build=lambda cell: build_process(*cell),
        extract=lambda process, cell: extract(process, *cell),
        progress=progress,
        label=lambda cell: "%-7s %s %s %s" % cell,
    )


def summarise(tidy, year=2050):
    """One row per cell: the headline quantities in a given year."""
    return sweep_utils.summarise(tidy, CELL_KEYS, year)


RESULTS = HERE / "data_outputs" / "sweep_results.csv.gz"


def write_results(tidy, path=None):
    """Persist the sweep as a gzipped tidy CSV."""
    return sweep_utils.write_results(tidy, path or RESULTS)


def read_results(path=None):
    """Read a persisted sweep."""
    return sweep_utils.read_results(path or RESULTS)


# ---------------------------------------------------------------------------
# Whole-grid figure
# ---------------------------------------------------------------------------

# Panels: (column, title, y label, scale applied to the stored value).
# Stored units are Mt CO2, MJ and RPK, so energy becomes EJ by 1e-12 and carbon
# intensity becomes g/RPK by 1e12 (Mt -> g).
# Traffic leads, since it is the quantity the reports hold exogenous and the one
# the colouring separates: the three traffic levels fan out here and carry that
# fan into every panel below.
#
# CO2 and the carbon intensity are gross, that is, before any offsetting.
# ``co2_emissions`` and ``carbon_offset`` are separate series and the former is
# never net of the latter, which is checked in the notebook by the fact that
# ``co2_emissions`` equals ``co2_emissions_including_energy`` in every cell.
# Two columns over three rows, which fits a portrait page: the two extensive
# quantities first, then the two intensities, then the emissions they multiply
# out to. The sixth cell is left free and carries the legend.
PANELS = (
    ("rpk", "Air traffic", "trillion RPK / yr", 1e-12),
    ("energy_consumption", "Final energy", "EJ / yr", 1e-12),
    ("energy_per_rpk", "Energy intensity", "MJ / RPK", 1.0),
    ("co2_per_rpk", "Carbon intensity, before offsetting", "g CO$_2$ / RPK", 1.0),
    ("co2_emissions", "CO$_2$ emissions, before offsetting", "Mt CO$_2$ / yr", 1.0),
)

# Derived intensities. Stored as functions rather than as series, since a ratio
# committed alongside its own numerator invites the two to disagree.
DERIVED = {
    "energy_per_rpk": lambda frame: frame["energy_consumption"] / frame["rpk"],
    # Mt -> g so the intensity reads in grams per RPK.
    "co2_per_rpk": lambda frame: frame["co2_emissions"] * 1e12 / frame["rpk"],
}


def wide(tidy=None):
    """Grid results as one row per (cell, year), with the two intensities derived."""
    return sweep_utils.tidy_to_wide(read_results() if tidy is None else tidy, CELL_KEYS, DERIVED)


def plot_grid(tidy=None, color_by="traffic", first_year=2023, alpha=0.18, figsize=(11, 12)):
    """Every cell of the grid, one translucent line each, over five metrics.

    One line per scenario at low opacity, so the density of the bundle carries the
    message rather than any single trajectory -- the same reading as the envelope
    comparison plots, but showing the individual runs instead of a min/max band,
    which matters here because 144 cells do not form a single ordered family.

    ``color_by`` picks which lever separates the colours; the remaining three vary
    inside each colour. Choose it to match the question. Traffic is the default,
    because it is the only lever that separates all five panels, and because it is
    the one the reports hold exogenous, so the fan it opens is the range their own
    scenarios cannot express. SAF separates the two carbon panels but does nothing
    to the energy ones, since substituting the fuel changes what a joule emits
    rather than how many are burned; technology separates the energy panels but
    resolves only three bands out of four levels, T3 and T4 consuming identical
    energy and differing only in what carries it.

    ``first_year`` defaults to the last observed year rather than 2019, because the
    COVID collapse drives RPK down without a matching drop in energy: 2020 reads about
    2.3 MJ/RPK against a 1.4 trend, and that spike compresses both intensity panels
    into illegibility.

    The three published scenarios are drawn on top in black so the reported cases can
    be located inside the spread they belong to.
    """
    frame = wide(tidy)
    figure = sweep_utils.plot_grid(
        frame,
        cell_keys=CELL_KEYS,
        panels=PANELS,
        color_by=color_by,
        first_year=first_year,
        alpha=alpha,
        figsize=figsize,
        highlight=PUBLISHED_CELLS,
        highlight_styles=PUBLISHED_STYLES,
        suptitle="All %d lever combinations, coloured by %s"
        % (frame[frame["year"] >= first_year].groupby(CELL_KEYS).ngroups, color_by),
    )
    return figure, figure.axes
