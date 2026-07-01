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

import os

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
                k: (_resolve(base_dir, v) if k.endswith("_file") else v)
                for k, v in value.items()
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


def _aggregate_fuel_policy(region_configs, fuel_carrier, year_range):
    """
    Compute every region and aggregate the ``fuel_carrier`` policy into a global share and
    a global emission factor over ``year_range``.

    Returns ``(years, global_share_pct, global_ef, reference_region_id)`` where
    ``reference_region_id`` is the first region that defines ``fuel_carrier`` (used as the
    template for the technical/economic block of the aggregated carrier).
    """
    from aeromaps import create_process  # local import: avoids circular import at load time

    years = np.arange(year_range[0], year_range[1] + 1)
    total_dropin = np.zeros(len(years))
    total_saf = np.zeros(len(years))
    total_saf_ef = np.zeros(len(years))
    reference_region = None

    ef_var = f"{fuel_carrier}_mean_co2_emission_factor_without_resource"
    saf_var = f"{fuel_carrier}_energy_consumption"

    for region_id, region_config_path in region_configs.items():
        process = create_process(configuration_file=region_config_path)
        process.compute()
        df = process.data["vector_outputs"]
        idx = df.index

        def at_years(series):
            # Restrict/reindex the model series onto the year grid.
            return np.array([float(series.loc[y]) if y in idx else 0.0 for y in years])

        total_dropin += at_years(df["energy_consumption_dropin_fuel"])
        if saf_var in df.columns:
            saf = at_years(df[saf_var])
            ef = at_years(df[ef_var]) if ef_var in df.columns else np.zeros(len(years))
            total_saf += saf
            total_saf_ef += saf * ef
            if reference_region is None:
                reference_region = region_id

    if reference_region is None:
        raise ValueError(
            f"No region defines the fuel carrier '{fuel_carrier}'; cannot aggregate a "
            f"fuel policy."
        )

    global_share = 100.0 * np.divide(
        total_saf, total_dropin, out=np.zeros_like(total_saf), where=total_dropin > 0
    )
    global_ef = np.divide(
        total_saf_ef, total_saf, out=np.full_like(total_saf, np.nan), where=total_saf > 0
    )
    global_ef = pd.Series(global_ef).ffill().bfill().to_numpy()
    return years, global_share, global_ef, reference_region


def _custom_data_type(years, values):
    return AeroMapsCustomDataType(
        {
            "years": [int(y) for y in years],
            "values": [float(v) for v in values],
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
    year_range=(2020, 2050),
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
    year_range : tuple of int, optional
        Inclusive ``(start, end)`` yearly grid for the aggregated mandate/emission series.
    **create_process_kwargs
        Forwarded to :func:`aeromaps.create_process`.

    Returns
    -------
    AeroMAPSProcess
        A single-region global process driven by the aggregated fuel policy.
    """
    from aeromaps import create_process  # local import: avoids circular import at load time

    region_configs = _read_regionalisation(configuration_file)

    years, global_share, global_ef, auto_reference = _aggregate_fuel_policy(
        region_configs, fuel_carrier, year_range
    )
    if reference_region is None:
        reference_region = auto_reference
    elif reference_region not in region_configs:
        raise KeyError(
            f"reference_region '{reference_region}' not found. "
            f"Available: {list(region_configs)}"
        )

    # --- assemble the aggregated energy-carriers file ----------------------------------
    reference_config_path = region_configs[reference_region]
    reference_dir = os.path.dirname(reference_config_path)
    reference_energy = read_yaml_file(_region_energy_file(reference_config_path))

    aggregated_carrier = reference_energy[fuel_carrier]
    aggregated_carrier["inputs"]["mandate"] = {
        "mandate_type": "share",
        "mandate_share": _custom_data_type(years, global_share),
    }
    aggregated_carrier["inputs"].setdefault("environmental", {})
    aggregated_carrier["inputs"]["environmental"][
        "mean_co2_emission_factor_without_resource"
    ] = _custom_data_type(years, global_ef)

    aggregated_energy = {}
    if "fossil_kerosene" in reference_energy:
        aggregated_energy["fossil_kerosene"] = reference_energy["fossil_kerosene"]
    aggregated_energy[fuel_carrier] = aggregated_carrier

    out_dir = os.path.dirname(os.path.abspath(output_config))
    os.makedirs(out_dir, exist_ok=True)
    write_yaml_file(aggregated_energy, output_energy_file)

    # --- model chain -------------------------------------------------------------------
    reference_full_config = read_yaml_file(reference_config_path)
    if standards_override is None:
        models = reference_full_config.get("models", {})
    elif isinstance(standards_override, str):
        models = read_yaml_file(standards_override).get("models", {})
    else:
        models = dict(reference_full_config.get("models", {}))
        models["standards"] = list(standards_override)
    models = _resolve_model_paths(models, reference_dir)

    reference_models = _resolve_model_paths(
        reference_full_config.get("models", {}), reference_dir
    )
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

    collapsed = {
        "data": {
            "inputs": {"json_inputs_file": inputs_file},
            "outputs": {"json_outputs_file": os.path.abspath(output_json)},
        },
        "models": models,
    }
    write_yaml_file(collapsed, output_config)

    return create_process(configuration_file=output_config, **create_process_kwargs)
