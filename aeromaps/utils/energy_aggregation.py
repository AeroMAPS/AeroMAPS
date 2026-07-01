"""
Energy-carrier aggregation helpers for AeroMAPS.

This module provides :func:`aggregate_carriers_to_generic`, which collapses several
energy carriers defined in an ``energy_carriers`` YAML file into a single "generic"
carrier. It is used to build the *light* editions of the ATAG Waypoint 2050 scenarios,
where the seven individual biomass SAF pathways (HEFA/ATJ/FT) are replaced by one
generic biofuel that:

- carries the **summed** quantity mandate across the merged pathways, and
- has a **quantity-weighted mean** CO2 emission factor (and mean cost / technical
  parameters).

The non-merged carriers (electrofuel, fossil kerosene, hydrogen, electric, ...) are
preserved untouched, so the resulting file is a drop-in replacement for the original.
"""

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMapsCustomDataType
from aeromaps.utils.yaml import read_yaml_file, write_yaml_file


def _series_to_yearly(custom_data_type, years):
    """
    Interpolate an :class:`AeroMapsCustomDataType` (linear) onto a yearly grid.

    Mirrors the model's ``interp1d(kind="linear")`` behaviour, clamping to the first
    and last reference values outside the reference range (``numpy.interp`` default).

    Parameters
    ----------
    custom_data_type : AeroMapsCustomDataType
        Source reference years/values.
    years : numpy.ndarray
        Target yearly grid.

    Returns
    -------
    numpy.ndarray
        Interpolated values, one per year in ``years``.
    """
    ref_years = np.asarray(custom_data_type.years, dtype=float)
    ref_values = np.asarray(custom_data_type.values, dtype=float)
    if ref_years.size == 0:
        # No reference years: constant series (matches YAMLInterpolator behaviour).
        return np.full(years.shape, ref_values[0] if ref_values.size else 0.0, dtype=float)
    return np.interp(years, ref_years, ref_values)


def _yearly_custom_data_type(years, values):
    """Build an :class:`AeroMapsCustomDataType` from a yearly grid and values."""
    return AeroMapsCustomDataType(
        {
            "years": [int(y) for y in years],
            "values": [float(v) for v in values],
            "method": "linear",
        }
    )


def _weighted_mean_series(values_per_carrier, quantity_per_carrier):
    """
    Quantity-weighted mean across carriers, per year, with nan-fill for zero-weight years.

    ``EF(y) = sum_i q_i(y) * v_i(y) / sum_i q_i(y)``. Years where the total quantity is
    zero (e.g. the very first year, before any pathway ramps up) are forward/back-filled
    from the nearest weighted value to avoid divide-by-zero.
    """
    stacked_values = np.vstack(values_per_carrier)
    stacked_quantity = np.vstack(quantity_per_carrier)
    numerator = np.sum(stacked_values * stacked_quantity, axis=0)
    total_quantity = np.sum(stacked_quantity, axis=0)
    weighted = np.divide(
        numerator,
        total_quantity,
        out=np.full_like(total_quantity, np.nan),
        where=total_quantity > 0,
    )
    filled = pd.Series(weighted).ffill().bfill().to_numpy()
    return filled


def aggregate_carriers_to_generic(
    energy_carriers_file,
    carriers_to_merge,
    generic_name="generic_biofuel",
    output_file=None,
    resource_name="generic_biomass",
    year_range=(2020, 2050),
    energy_origin="biomass",
):
    """
    Merge several energy carriers into a single generic carrier.

    Parameters
    ----------
    energy_carriers_file : str
        Path to the source ``energy_carriers`` YAML file.
    carriers_to_merge : list of str
        Carrier keys to collapse into one (e.g. the seven biomass SAF pathways). They
        must all use ``mandate_type: "quantity"``.
    generic_name : str, optional
        Key/name of the resulting generic carrier (default ``"generic_biofuel"``).
    output_file : str, optional
        If given, the aggregated YAML is written there (preserving
        ``!AeroMapsCustomDataType`` tags). The dict is always returned.
    resource_name : str, optional
        Name of the single generic feedstock resource the generic carrier consumes.
    year_range : tuple of int, optional
        Inclusive ``(start, end)`` yearly grid used for the merged series.
    energy_origin : str, optional
        ``energy_origin`` metadata for the generic carrier.

    Returns
    -------
    dict
        The full energy-carriers mapping with the merged carriers replaced by the
        single generic carrier (inserted at the position of the first merged carrier).
    """
    data = read_yaml_file(energy_carriers_file)

    missing = [c for c in carriers_to_merge if c not in data]
    if missing:
        raise KeyError(
            f"Carriers not found in '{energy_carriers_file}': {missing}. "
            f"Available: {list(data.keys())}"
        )

    years = np.arange(year_range[0], year_range[1] + 1)

    quantity_per_carrier = []
    ef_per_carrier = []
    mfsp_per_carrier = []
    total_quantity_weight = []  # scalar per carrier: total energy over all years
    rsc_per_carrier = []  # scalar resource_specific_consumption per carrier
    ksel_per_carrier = []  # scalar kerosene_selectivity per carrier
    emission_index = None

    for carrier in carriers_to_merge:
        inputs = data[carrier]["inputs"]
        mandate = inputs["mandate"]
        if mandate.get("mandate_type") != "quantity":
            raise ValueError(
                f"Carrier '{carrier}' has mandate_type "
                f"'{mandate.get('mandate_type')}', expected 'quantity'."
            )
        quantity = _series_to_yearly(mandate["mandate_quantity"], years)
        quantity_per_carrier.append(quantity)
        total_quantity_weight.append(float(np.sum(quantity)))

        environmental = inputs["environmental"]
        ef_per_carrier.append(
            _series_to_yearly(environmental["co2_emission_factor_without_resource"], years)
        )
        if emission_index is None:
            emission_index = environmental.get("emission_index")

        economics = inputs.get("economics") or {}
        if "mean_mfsp_without_resource" in economics:
            mfsp_per_carrier.append(
                _series_to_yearly(economics["mean_mfsp_without_resource"], years)
            )

        technical = inputs["technical"]
        rsc_map = technical.get("resource_specific_consumption", {})
        # A biomass pathway consumes a single feedstock; take its scalar value.
        rsc_per_carrier.append(float(next(iter(rsc_map.values()), 0.0)))
        ksel_per_carrier.append(float(technical.get("kerosene_selectivity", 1.0)))

    total_quantity = np.sum(np.vstack(quantity_per_carrier), axis=0)
    generic_ef = _weighted_mean_series(ef_per_carrier, quantity_per_carrier)

    weights = np.asarray(total_quantity_weight)
    weight_sum = weights.sum() if weights.sum() > 0 else 1.0
    generic_rsc = float(np.dot(weights, rsc_per_carrier) / weight_sum)
    generic_ksel = float(np.dot(weights, ksel_per_carrier) / weight_sum)

    generic_carrier = {
        "name": generic_name,
        "environmental_model": "top-down",
        "cost_model": "top-down",
        "aircraft_type": "dropin_fuel",
        "energy_origin": energy_origin,
        "default": False,
        "compute_all_years": True,
        "inputs": {
            "mandate": {
                "mandate_type": "quantity",
                "mandate_quantity": _yearly_custom_data_type(years, total_quantity),
            },
            "technical": {
                "resource_names": [resource_name],
                "resource_specific_consumption": {resource_name: generic_rsc},
                "kerosene_selectivity": generic_ksel,
                "lhv": 44,
                "plant_load_factor": 0.95,
                "plant_lifespan": 25,
            },
            "environmental": {
                "co2_emission_factor_without_resource": _yearly_custom_data_type(
                    years, generic_ef
                ),
                "emission_index": emission_index,
            },
            "economics": {},
        },
        "outputs": None,
    }

    if mfsp_per_carrier:
        generic_mfsp = _weighted_mean_series(mfsp_per_carrier, quantity_per_carrier)
        generic_carrier["inputs"]["economics"]["mean_mfsp_without_resource"] = (
            _yearly_custom_data_type(years, generic_mfsp)
        )

    # Rebuild the mapping in original order, replacing the merged block with the generic
    # carrier at the position of the first merged carrier.
    merge_set = set(carriers_to_merge)
    result = {}
    inserted = False
    for key, value in data.items():
        if key in merge_set:
            if not inserted:
                result[generic_name] = generic_carrier
                inserted = True
            continue
        result[key] = value

    if output_file is not None:
        write_yaml_file(result, output_file)

    return result
