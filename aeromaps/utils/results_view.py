"""Read committed scenario outputs back into a plot-compatible object.

``process.write_json()`` stores a scenario's results as plain lists, dropping
the DataFrame indices and the ``years`` block that the plot classes read. This
module rebuilds both, so a committed ``data_outputs/*.json`` can be plotted with
the standard plot registry without re-running the model.

That matters for documents that must render from stored results: notebook
outputs are stripped on commit, so a figure either re-runs its scenario or
reads the committed JSON, and re-running is not always affordable.

The facade mirrors ``_GlobalOutputsView`` in
``aeromaps.core.multi_regional_process``: it exposes exactly what the plot base
classes read -- a ``data`` dict plus a ``pathways_manager`` attribute.

Examples
--------
>>> from aeromaps.utils.results_view import load_results
>>> s1 = load_results("3rd_edition_full/data_outputs/s1.json")
>>> s1.plot("air_transport_co2_emissions")

>>> from aeromaps import assemble_processes
>>> comparison = assemble_processes({"S1": s1, "S2": load_results(".../s2.json")})
>>> comparison.plot("temperature_decomposition_comparison")
"""

import json
from functools import lru_cache
from pathlib import Path

import pandas as pd

from aeromaps.plots.single_scenario import available_plots, available_plots_fleet

# Same location core.process resolves for its own defaults, computed locally so
# that reading a results file does not pull in the whole model stack.
DEFAULT_PARAMETERS_PATH = (
    Path(__file__).resolve().parent.parent / "resources" / "data" / "parameters.json"
)


@lru_cache(maxsize=1)
def _default_parameters():
    with open(DEFAULT_PARAMETERS_PATH, encoding="utf-8") as stream:
        return json.load(stream)


def _default_year(name, fallback):
    """Default value of a year parameter, falling back if it is not declared."""
    try:
        return _default_parameters().get(name, fallback)
    except OSError:  # pragma: no cover - defaults ship with the package
        return fallback


class ResultsView:
    """Single-scenario-process facade over a committed outputs JSON file.

    ``pathways_manager`` is None unless one is supplied: the JSON carries no
    pathway metadata, so plots that discover energy carriers dynamically
    (energy mix, fuel shares, drop-in supply breakdowns) cannot be served from
    a bare results file. Climate, emissions and traffic plots read only
    ``data`` and work unchanged.
    """

    def __init__(self, data, pathways_manager=None, name=None):
        self.data = data
        self.pathways_manager = pathways_manager
        self.name = name

    def __repr__(self):
        return f"ResultsView({self.name!r})" if self.name else "ResultsView(...)"

    def list_available_plots(self):
        """Names of the plots that can be drawn from this view."""
        return list(available_plots.keys())

    def compute(self):
        """No-op, so a view can stand in for a process in an assembly.

        The results were computed when the JSON was written; there is nothing
        left to solve. Present only so ``assemble_processes(...).compute_all()``
        does not fail on a mix of processes and views.
        """
        return self

    def plot(
        self, name, save=False, size_inches=None, remove_title=False, fig=None, ax=None, legend=True
    ):
        """Generate a predefined AeroMAPS plot from the stored results.

        Same contract as ``AeroMAPSProcess.plot``, minus the bottom-up fleet
        plots, which need model state the JSON does not carry.
        """
        if name in available_plots_fleet:
            raise NameError(
                f"Plot {name} requires the bottom-up fleet model and cannot be drawn "
                "from stored results. Run the process instead."
            )
        if name not in available_plots:
            raise NameError(
                f"Plot {name} is not available. List of available plots: "
                f"{list(available_plots.keys())}"
            )

        plot_object = available_plots[name](self, fig=fig, ax=ax, legend=legend)
        if save:
            if size_inches is not None:
                plot_object.fig.set_size_inches(size_inches)
            if remove_title:
                plot_object.fig.gca().set_title("")
            plot_object.fig.savefig(f"{name}.pdf", bbox_inches="tight")
        return plot_object


def _year_bounds_from_inputs(outputs_path):
    """Year settings declared by the scenario that produced ``outputs_path``.

    Scenarios are laid out as ``<edition>/data_outputs/<scenario>.json`` beside
    ``<edition>/data_inputs/<scenario>_inputs.json``, so the inputs file can be
    found by convention. This matters because the outputs JSON stores no year
    metadata at all: without it, a scenario that overrides a default (the second
    ATAG edition runs from 2020, not the default 2024) would be silently
    relabelled with the wrong historic/prospective split.

    Returns an empty dict when there is no sibling inputs file to read.
    """
    path = Path(outputs_path)
    candidate = path.parent.parent / "data_inputs" / f"{path.stem}_inputs.json"
    if not candidate.is_file():
        return {}
    try:
        with open(candidate, encoding="utf-8") as stream:
            declared = json.load(stream)
    except (OSError, ValueError):
        return {}
    keys = (
        "historic_start_year",
        "prospection_start_year",
        "end_year",
        "climate_historic_start_year",
    )
    return {key: declared[key] for key in keys if key in declared}


def load_results(
    json_file,
    historic_start_year=None,
    prospection_start_year=None,
    end_year=None,
    climate_historic_start_year=None,
    pathways_manager=None,
    name=None,
):
    """Load a committed outputs JSON into a plot-compatible view.

    Parameters
    ----------
    json_file
        Path to a ``data_outputs/*.json`` written by ``process.write_json()``.
    historic_start_year, prospection_start_year, end_year, climate_historic_start_year
        Year bounds used to rebuild the indices and the ``years`` block. The
        JSON stores none of them, so they default to the values in
        ``resources/data/parameters.json``. Pass them explicitly for any
        scenario that overrides a default -- notably ``prospection_start_year``,
        which cannot be inferred from the data and which silently mislabels the
        historic/prospective split if wrong.
    pathways_manager
        Optional manager for plots that discover energy carriers dynamically.
    name
        Optional label, used in the repr and by ``assemble_processes``.

    Returns
    -------
    ResultsView
    """
    path = Path(json_file)
    with open(path, encoding="utf-8") as stream:
        raw = json.load(stream)

    # Precedence: explicit argument, then whatever the producing scenario declared,
    # then the packaged default.
    declared = _year_bounds_from_inputs(path)

    def resolve(explicit, key, fallback):
        if explicit is not None:
            return explicit
        if key in declared:
            return int(declared[key])
        return _default_year(key, fallback)

    historic_start_year = resolve(historic_start_year, "historic_start_year", 2000)
    prospection_start_year = resolve(prospection_start_year, "prospection_start_year", 2024)
    end_year = resolve(end_year, "end_year", 2050)
    climate_historic_start_year = resolve(
        climate_historic_start_year, "climate_historic_start_year", 1940
    )

    full_years = list(range(historic_start_year, end_year + 1))
    climate_full_years = list(range(climate_historic_start_year, end_year + 1))

    vector_outputs = pd.DataFrame(raw["vector_outputs"])
    climate_outputs = pd.DataFrame(raw["climate_outputs"])

    _check_length(vector_outputs, full_years, "vector_outputs", path)
    _check_length(climate_outputs, climate_full_years, "climate_outputs", path)

    vector_outputs.index = full_years
    climate_outputs.index = climate_full_years

    data = {
        "years": {
            "full_years": full_years,
            "climate_full_years": climate_full_years,
            "historic_years": list(range(historic_start_year, prospection_start_year)),
            "climate_historic_years": list(
                range(climate_historic_start_year, prospection_start_year)
            ),
            "prospective_years": list(range(prospection_start_year - 1, end_year + 1)),
        },
        "float_inputs": raw.get("float_inputs", {}),
        "str_inputs": raw.get("str_inputs", {}),
        "vector_inputs": raw.get("vector_inputs", {}),
        "float_outputs": raw.get("float_outputs", {}),
        "vector_outputs": vector_outputs,
        "climate_outputs": climate_outputs,
    }

    return ResultsView(data, pathways_manager=pathways_manager, name=name or path.stem)


def _check_length(frame, years, label, path):
    """Fail loudly rather than silently misaligning a series with the wrong years."""
    if frame.empty:
        return
    if len(frame) != len(years):
        raise ValueError(
            f"{label} in '{path}' has {len(frame)} rows but the year bounds imply "
            f"{len(years)} ({years[0]}-{years[-1]}). Pass the year bounds this scenario "
            "was run with."
        )
