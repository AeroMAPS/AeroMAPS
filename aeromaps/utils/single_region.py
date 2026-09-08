"""
Build a single global AeroMAPS process from a multi-regional configuration, aggregating
the per-region fuel policies into one global fuel policy.

A multi-regional configuration (one containing a ``regionalisation`` section, e.g. the
``_a_r_m`` publication's ``regionalisation_all_regions.yaml``) runs one
:class:`AeroMAPSProcess` per region, each with its own SAF policy (some regions have a
share mandate, some a quantity mandate, some no SAF at all). To run a single *global*
process that reflects those heterogeneous policies, we cannot just copy one region's
mandate: we compute every region, sum the drop-in fuel and SAF energy across regions, and
derive a single global fuel policy:

- **global SAF share(year)** = total SAF energy / total drop-in fuel energy across regions;
- **global SAF emission factor(year)** = SAF-energy-weighted mean of the regional factors.

That aggregated fuel policy is then run globally (no ``regionalisation`` key, so
:func:`aeromaps.create_process` builds a standard single-region process), optionally with a
different demand and model chain. This is how the ATAG "3rd edition light" S0 is built: the
``_a_r_m`` regional SAF policies aggregated into one global share, run on the 3rd-edition
central-traffic demand, T2 efficiency and top-down model chain.
"""

import copy
import io
import json
import os
import warnings

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMapsCustomDataType
from aeromaps.utils.yaml import read_yaml_file, write_yaml_file


def _resolve(base_dir, path):
    """Resolve ``path`` (possibly relative to ``base_dir``) to absolute, leaving the
    sentinel ``"default"`` and absolute paths untouched."""
    if path is None or path == "default" or os.path.isabs(path):
        return path
    return os.path.normpath(os.path.join(base_dir, path))


def _relativize(base_dir, path):
    """Inverse of ``_resolve``: rewrite an absolute path as relative to ``base_dir``,
    forward-slashed to match the convention every hand-written config in the repo uses.

    Internally every path is resolved to absolute so that region configs living under
    different directory trees can be combined against a common frame -- but writing that
    absolute form into the generated config bakes in the machine it was built on. Without
    this, the config resolves on the machine that generated it and nowhere else.
    """
    if path is None or path == "default" or not os.path.isabs(path):
        return path
    return os.path.relpath(path, base_dir).replace(os.sep, "/")


def _relativize_model_paths(models, base_dir):
    """Copy of a ``models`` block with all ``*_file`` paths relativized to ``base_dir``."""
    relativized = {}
    for group, value in models.items():
        if isinstance(value, dict):
            relativized[group] = {
                k: (_relativize(base_dir, v) if k.endswith("_file") else v)
                for k, v in value.items()
            }
        else:
            relativized[group] = value
    return relativized


def _read_regionalisation(configuration_file):
    """Parse the ``regionalisation`` section (mirrors
    ``MultiRegionalProcess._read_regionalisation_config``): return ``region_id -> abs
    config path``."""
    config = read_yaml_file(configuration_file)
    regionalisation = config.get("regionalisation")
    if regionalisation is None:
        raise ValueError(
            f"'{configuration_file}' has no 'regionalisation' section; it is not a "
            f"multi-regional configuration."
        )
    regions = regionalisation.get("regions", {})
    if not regions:
        raise ValueError("Regionalisation config must specify at least one region.")
    base_dir = os.path.dirname(os.path.abspath(configuration_file))
    return {
        rid: _resolve(base_dir, rd.get("config_file"))
        for rid, rd in regions.items()
        if rd.get("config_file") is not None
    }


def _resolve_model_paths(models, base_dir):
    """Copy of a ``models`` block with all ``*_file`` paths resolved to absolute."""
    resolved = {}
    for group, value in models.items():
        if isinstance(value, dict):
            resolved[group] = {
                k: (_resolve(base_dir, v) if k.endswith("_file") else v) for k, v in value.items()
            }
        else:
            resolved[group] = value
    return resolved


def _region_energy_file(region_config_path):
    """Absolute path to a region config's energy-carriers file."""
    region_dir = os.path.dirname(region_config_path)
    region_config = read_yaml_file(region_config_path)
    energy = region_config.get("models", {}).get("energy", {})
    return _resolve(region_dir, energy.get("energy_carriers_model_data_file"))


def _rebaselined_region_configs(region_configs, baseline, work_dir):
    """Write a copy of each region config whose inputs carry ``baseline``.

    A region's historic window is consumed when its process is built: the ``*_init``
    vectors are turned into Series indexed by
    ``[historic_start_year, prospection_start_year)`` before any model runs, so the
    baseline cannot be pushed in after ``create_process`` returns. It has to reach the
    inputs file the region loads.

    The regions of a multi-regional publication typically pin no baseline of their own
    and inherit whatever the packaged ``parameters.json`` carries, which means a caller
    that wants them on a different one has no way to say so without editing the
    publication. That is what this does instead: it copies each region's inputs file with
    ``baseline`` merged in, and a config pointing at the copy, leaving the publication
    untouched. Every other path in the copied config is resolved to absolute so it still
    finds its data from the new location.
    """
    os.makedirs(work_dir, exist_ok=True)
    rebaselined = {}
    for region_id, region_config_path in region_configs.items():
        region_dir = os.path.dirname(region_config_path)
        config = copy.deepcopy(read_yaml_file(region_config_path))

        data = config.setdefault("data", {})
        inputs = data.setdefault("inputs", {})
        inputs_path = _resolve(region_dir, inputs.get("json_inputs_file"))
        with io.open(inputs_path, encoding="utf-8") as handle:
            region_inputs = json.load(handle)
        region_inputs.update(baseline)

        new_inputs_path = os.path.join(work_dir, f"{region_id}_inputs.json")
        with io.open(new_inputs_path, "w", encoding="utf-8") as handle:
            json.dump(region_inputs, handle, indent=4)

        for key, value in list(inputs.items()):
            if key.endswith("_file"):
                inputs[key] = _resolve(region_dir, value)
        inputs["json_inputs_file"] = new_inputs_path
        for key, value in list(data.get("outputs", {}).items()):
            if key.endswith("_file"):
                data["outputs"][key] = _resolve(region_dir, value)
        if "models" in config:
            config["models"] = _resolve_model_paths(config["models"], region_dir)

        new_config_path = os.path.join(work_dir, f"{region_id}_config.yaml")
        write_yaml_file(config, new_config_path)
        rebaselined[region_id] = new_config_path
    return rebaselined


def _aggregate_fuel_policy(region_configs, fuel_carrier, year_range):
    """
    Compute every region and aggregate the ``fuel_carrier`` policy into a global share and
    a global emission factor over ``year_range``.

    Returns ``(years, global_share_pct, global_ef, reference_region_id)`` where
    ``reference_region_id`` is the first region that defines ``fuel_carrier`` (used as the
    template for the technical/economic block of the aggregated carrier).
    """
    from aeromaps import create_process  # local import: avoids circular import at load time

    ef_var = f"{fuel_carrier}_mean_co2_emission_factor_without_resource"
    saf_var = f"{fuel_carrier}_energy_consumption"

    # Compute every region first, so the year grid can be derived from what the regions
    # actually declare rather than assumed. Only the output frame and the horizon are
    # kept; the processes themselves are discarded as we go.
    region_frames = {}
    region_horizons = {}
    for region_id, region_config_path in region_configs.items():
        process = create_process(configuration_file=region_config_path)
        process.compute()
        region_frames[region_id] = process.data["vector_outputs"]
        region_horizons[region_id] = (
            int(process.parameters.prospection_start_year),
            int(process.parameters.end_year),
        )

    if year_range is None:
        # Derive from each region's own prospection window, NOT from the output frame's
        # index: the frame also carries the historic period (typically from 2000), and the
        # series being built here is a forward-looking mandate. Anchoring it in the
        # historic years would hand the interpolator a first reference year decades before
        # any policy exists.
        #
        # Intersect rather than union, because `at_years` substitutes 0.0 for years a
        # region does not cover -- spanning beyond the common window would silently
        # zero-fill the very quantities being aggregated.
        starts = [h[0] for h in region_horizons.values()]
        ends = [h[1] for h in region_horizons.values()]
        first, last = max(starts), min(ends)
        if first > last:
            raise ValueError(
                f"Regions {sorted(region_horizons)} share no common prospection window "
                f"(latest start {first}, earliest end {last}); pass an explicit year_range."
            )
        if len(set(starts)) > 1 or len(set(ends)) > 1:
            warnings.warn(
                f"Regions do not share a prospection window (starts {sorted(set(starts))}, "
                f"ends {sorted(set(ends))}). Aggregating over their intersection "
                f"{first}-{last}."
            )
        years = np.arange(first, last + 1)
    else:
        years = np.arange(year_range[0], year_range[1] + 1)

    total_dropin = np.zeros(len(years))
    total_saf = np.zeros(len(years))
    total_saf_ef = np.zeros(len(years))
    reference_region = None

    for region_id, df in region_frames.items():
        idx = df.index

        def at_years(series, idx=idx):
            # Restrict/reindex the model series onto the year grid.
            return np.array([float(series.loc[y]) if y in idx else 0.0 for y in years])

        total_dropin += at_years(df["energy_consumption_dropin_fuel"])
        if saf_var not in df.columns:
            continue

        saf = at_years(df[saf_var])
        if ef_var not in df.columns:
            # Substituting zeros here would count this region's energy in the
            # denominator while contributing nothing to the numerator, quietly
            # dragging the global emission factor toward zero in proportion to the
            # region's SAF volume. Given how easily the key can be misspelled --
            # without the `mean_` prefix the model ignores it -- that is a realistic
            # way to end up with a global factor that is wrong and looks plausible.
            raise KeyError(
                f"Region '{region_id}' deploys '{fuel_carrier}' but publishes no "
                f"'{ef_var}'. Refusing to treat its fuel as zero-carbon. Check that "
                f"the carrier declares 'mean_co2_emission_factor_without_resource' "
                f"(the model ignores the key written without the 'mean_' prefix)."
            )
        ef = at_years(df[ef_var])
        total_saf += saf
        total_saf_ef += saf * ef
        # Pick the reference on actual deployment, not merely on the column existing:
        # a region that declares the carrier and never uses it carries no information
        # about the technical block being copied from it.
        if reference_region is None and saf.sum() > 0:
            reference_region = region_id

    if reference_region is None:
        raise ValueError(
            f"No region deploys the fuel carrier '{fuel_carrier}' anywhere in "
            f"{years[0]}-{years[-1]}; cannot aggregate a fuel policy. Either no region "
            f"declares it, or every region that does leaves it at zero over this range."
        )

    global_share = 100.0 * np.divide(
        total_saf, total_dropin, out=np.zeros_like(total_saf), where=total_dropin > 0
    )
    global_ef = np.divide(
        total_saf_ef, total_saf, out=np.full_like(total_saf, np.nan), where=total_saf > 0
    )
    # ffill/bfill can only propagate from a year that has a value; if the carrier is
    # deployed nowhere the whole array is NaN and this is a no-op, which is why the
    # guard above tests deployment rather than declaration.
    global_ef = pd.Series(global_ef).ffill().bfill().to_numpy()
    return years, global_share, global_ef, reference_region


def _custom_data_type(years, values):
    array = np.asarray(values, dtype=float)
    if not np.all(np.isfinite(array)):
        # float(nan) is a perfectly valid float, so an unguarded conversion serialises
        # as `.nan` and only fails later inside the interpolator, with an error that
        # says nothing about where the value came from.
        raise ValueError(
            "Refusing to write a non-finite value into the aggregated energy file. "
            "This means the aggregation produced an undefined series -- typically a "
            "quantity-weighted mean with no weight anywhere in the year range."
        )
    return AeroMapsCustomDataType(
        {
            "years": [int(y) for y in years],
            "values": [float(v) for v in array],
            "method": "linear",
        }
    )


def aggregate_regions_to_single_process(
    configuration_file,
    output_config,
    output_energy_file,
    demand_override=None,
    standards_override=None,
    fuel_carrier="generic_saf",
    reference_region=None,
    output_json=None,
    year_range=None,
    region_baseline=None,
    **create_process_kwargs,
):
    """
    Aggregate a multi-regional configuration's fuel policies into a single global process.

    Every region is computed; the ``fuel_carrier`` policy is aggregated into a global share
    mandate and an energy-weighted global emission factor (see module docstring). The
    aggregated fuel policy is written to ``output_energy_file`` and driven globally.

    Parameters
    ----------
    configuration_file : str
        Path to a configuration file containing a ``regionalisation`` section.
    output_config : str
        Path where the assembled single-region config is written.
    output_energy_file : str
        Path where the aggregated energy-carriers file (fossil kerosene + aggregated SAF)
        is written.
    demand_override : str, optional
        Path to a global ``inputs.json`` to use as demand. If omitted, the reference
        region's own inputs are used.
    standards_override : list of str or str, optional
        Replacement model chain: a list of model-group names, or a path to a config YAML
        whose ``models`` block is copied. The energy carriers always come from
        ``output_energy_file``.
    fuel_carrier : str, optional
        Name of the SAF carrier to aggregate across regions (default ``"generic_saf"``).
    reference_region : str, optional
        Region whose fossil-kerosene block and SAF technical/emission-index block are used
        as the template for the aggregated carrier. Defaults to the first region that
        defines ``fuel_carrier``.
    output_json : str, optional
        Path for the process JSON outputs. Defaults to ``<output_config_dir>/outputs.json``.
    region_baseline : dict, optional
        Parameters to merge into every region's inputs before it is computed, for
        callers whose scenario sits on a different historic baseline than the regions
        do. Typically ``prospection_start_year``, ``historic_start_year`` and the
        ``*_init`` vectors. The regions of a multi-regional publication usually pin no
        baseline of their own and inherit the packaged defaults, so without this the
        only way to move them is to edit the publication. The copies are written under
        ``<output_config_dir>/_rebaselined`` and the publication is left untouched.
    year_range : tuple of int, optional
        Inclusive ``(start, end)`` yearly grid for the aggregated mandate/emission series.
        Defaults to ``None``, meaning the grid is derived from the regions themselves --
        the intersection of their prospection windows, which follows each region's own
        ``prospection_start_year``/``end_year`` instead of assuming a fixed window. Pass an
        explicit tuple only to deliberately restrict the range.
    **create_process_kwargs
        Forwarded to :func:`aeromaps.create_process`.

    Returns
    -------
    AeroMAPSProcess
        A single-region global process driven by the aggregated fuel policy.
    """
    from aeromaps import create_process  # local import: avoids circular import at load time

    region_configs = _read_regionalisation(configuration_file)

    if region_baseline:
        region_configs = _rebaselined_region_configs(
            region_configs,
            region_baseline,
            os.path.join(os.path.dirname(os.path.abspath(output_config)), "_rebaselined"),
        )

    years, global_share, global_ef, auto_reference = _aggregate_fuel_policy(
        region_configs, fuel_carrier, year_range
    )
    if reference_region is None:
        reference_region = auto_reference
    elif reference_region not in region_configs:
        raise KeyError(
            f"reference_region '{reference_region}' not found. Available: {list(region_configs)}"
        )

    # --- assemble the aggregated energy-carriers file ----------------------------------
    reference_config_path = region_configs[reference_region]
    reference_dir = os.path.dirname(reference_config_path)
    reference_energy = read_yaml_file(_region_energy_file(reference_config_path))

    if fuel_carrier not in reference_energy:
        # A caller-pinned reference is otherwise only checked for existing as a region,
        # not for actually declaring the carrier whose technical block is taken from it.
        raise KeyError(
            f"reference_region '{reference_region}' does not declare '{fuel_carrier}', "
            f"so it cannot supply the technical block for the aggregated carrier. "
            f"Declares: {sorted(reference_energy)}"
        )

    # Everything except the mandate and the emission factor -- the technical block
    # (feedstock, specific consumption, selectivity, LHV), the emission index and the
    # economics -- is taken from this one region rather than aggregated. That is only
    # sound while the regions agree on it, so say so plainly here; a mismatch across
    # regions would charge every region this one's feedstock and selectivity.
    aggregated_carrier = copy.deepcopy(reference_energy[fuel_carrier])
    aggregated_carrier["inputs"]["mandate"] = {
        "mandate_type": "share",
        "mandate_share": _custom_data_type(years, global_share),
    }
    aggregated_carrier["inputs"].setdefault("environmental", {})
    aggregated_carrier["inputs"]["environmental"]["mean_co2_emission_factor_without_resource"] = (
        _custom_data_type(years, global_ef)
    )

    aggregated_energy = {}
    if "fossil_kerosene" in reference_energy:
        aggregated_energy["fossil_kerosene"] = reference_energy["fossil_kerosene"]
    aggregated_energy[fuel_carrier] = aggregated_carrier

    out_dir = os.path.dirname(os.path.abspath(output_config))
    os.makedirs(out_dir, exist_ok=True)
    write_yaml_file(aggregated_energy, output_energy_file)

    # --- model chain -------------------------------------------------------------------
    reference_full_config = read_yaml_file(reference_config_path)
    # Relative model-data paths must resolve against the file they were written in:
    # an override config's paths are relative to that config, not to the region's.
    if standards_override is None:
        models = reference_full_config.get("models", {})
        models_base_dir = reference_dir
    elif isinstance(standards_override, str):
        models = read_yaml_file(standards_override).get("models", {})
        models_base_dir = os.path.dirname(os.path.abspath(standards_override))
    else:
        models = dict(reference_full_config.get("models", {}))
        models["standards"] = list(standards_override)
        models_base_dir = reference_dir
    models = _resolve_model_paths(models, models_base_dir)

    reference_models = _resolve_model_paths(reference_full_config.get("models", {}), reference_dir)
    models.setdefault("energy", {})
    models["energy"]["energy_carriers_model_data_file"] = os.path.abspath(output_energy_file)
    for key in ("resources_model_data_file", "processes_model_data_file"):
        if key not in models["energy"]:
            models["energy"][key] = reference_models.get("energy", {}).get(key, "default")

    # --- demand ------------------------------------------------------------------------
    if demand_override is not None:
        inputs_file = os.path.abspath(demand_override)
    else:
        inputs_file = _resolve(
            reference_dir,
            reference_full_config.get("data", {}).get("inputs", {}).get("json_inputs_file"),
        )

    if output_json is None:
        output_json = os.path.join(out_dir, "outputs.json")

    # Every path above is absolute -- needed internally to combine region configs living
    # under different directory trees against a common frame. Relativize to out_dir before
    # writing, or the generated config only resolves on the machine that built it.
    collapsed = {
        "data": {
            "inputs": {"json_inputs_file": _relativize(out_dir, inputs_file)},
            "outputs": {"json_outputs_file": _relativize(out_dir, os.path.abspath(output_json))},
        },
        "models": _relativize_model_paths(models, out_dir),
    }
    write_yaml_file(collapsed, output_config)

    return create_process(configuration_file=output_config, **create_process_kwargs)
