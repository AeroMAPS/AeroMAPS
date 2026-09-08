"""
Energy-carrier aggregation helpers for AeroMAPS.

This module provides :func:`aggregate_carriers_to_generic`, which collapses several
energy carriers defined in an ``energy_carriers`` YAML file into a single "generic"
carrier. It is used to build the *light* editions of the ATAG Waypoint 2050 scenarios,
where the seven individual biomass SAF pathways (HEFA/ATJ/FT) are replaced by one
generic biofuel that:

- carries the **summed** quantity mandate across the merged pathways, and
- has a **quantity-weighted mean** CO2 emission factor, cost and feedstock intensity.

The non-merged carriers (electrofuel, fossil kerosene, hydrogen, electric, ...) are
preserved untouched, so the resulting file is a drop-in replacement for the original.

Aggregation rules, and why each is what it is
---------------------------------------------
``mean_co2_emission_factor_without_resource`` and ``mean_mfsp_without_resource`` are
purely additive terms per MJ of carrier (see ``top_down/environmental.py`` and
``top_down/cost.py``), so a quantity-weighted mean over the merged carriers conserves
the total. Weights are paired with their values so a carrier missing one of them cannot
silently shift the others.

``resource_specific_consumption`` is likewise per MJ of carrier, so the same weighting
conserves the integrated feedstock draw. Every resource is carried: when the merged
carriers each declare exactly one feedstock they are pooled onto ``resource_name``,
and otherwise the union is preserved rather than silently truncated to the first.

``kerosene_selectivity`` is the exception. The model **divides** by it
(``environmental.py:208``), so the aggregate that conserves mobilised feedstock is
harmonic in the selectivity, weighted by each carrier's feedstock draw::

    1 / sel = sum_i (q_i * rsc_i / sel_i) / sum_i (q_i * rsc_i)

An arithmetic mean under-estimates the feedstock mobilised, and the merged pathways
span 0.15 to 1.0, so the difference is not a rounding matter.

Parameters that cannot be meaningfully averaged -- ``lhv``, the model types, the
emission index -- are read from the merged carriers and must agree; a mismatch raises
rather than silently adopting one carrier's value.
"""

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMapsCustomDataType
from aeromaps.utils.yaml import read_yaml_file, write_yaml_file


def _series_to_yearly(value, years, fill_before=None):
    """Interpolate a value onto a yearly grid.

    Accepts an :class:`AeroMapsCustomDataType` or a plain scalar (a constant series).

    ``fill_before`` controls what happens before the first reference year. The default
    (``None``) clamps to the first reference value, matching ``numpy.interp``. Passing
    ``0.0`` instead leaves those years empty, which is what the model does for a
    *quantity* mandate: ``YAMLInterpolator`` starts the series at the first reference
    year (``yaml_interpolator.py:136-145``) and ``EnergyUseChoice`` fills the missing
    years with zero. Clamping there would invent a mandate in years the source file
    never declared one.
    """
    if not isinstance(value, AeroMapsCustomDataType):
        return np.full(years.shape, float(value), dtype=float)

    ref_years = np.asarray(value.years, dtype=float)
    ref_values = np.asarray(value.values, dtype=float)
    if ref_years.size == 0:
        # No reference years: constant series (matches YAMLInterpolator behaviour).
        return np.full(years.shape, ref_values[0] if ref_values.size else 0.0, dtype=float)

    interpolated = np.interp(years, ref_years, ref_values)
    if fill_before is not None:
        interpolated = np.where(years < ref_years[0], float(fill_before), interpolated)
    return interpolated


def _yearly_custom_data_type(years, values):
    """Build an :class:`AeroMapsCustomDataType` from a yearly grid and values."""
    array = np.asarray(values, dtype=float)
    if not np.all(np.isfinite(array)):
        # A NaN here serialises as `.nan` and only fails much later, inside the
        # interpolator, with an error that says nothing about where it came from.
        raise ValueError(
            "Refusing to write a non-finite value into an energy file. This usually "
            "means the merged carriers have zero quantity across the whole year range, "
            "so the quantity-weighted mean is undefined."
        )
    return AeroMapsCustomDataType(
        {
            "years": [int(y) for y in years],
            "values": [float(v) for v in array],
            "method": "linear",
        }
    )


def _weighted_mean_series(pairs):
    """Quantity-weighted mean per year over ``(values, quantity)`` pairs.

    ``v(y) = sum_i q_i(y) * v_i(y) / sum_i q_i(y)``. Values and weights travel together
    so a carrier that omits the quantity being averaged cannot desynchronise the two
    lists. Years with no weight at all (before any pathway ramps up) are filled from the
    nearest weighted value, since an intensity is undefined where nothing is produced.
    """
    if not pairs:
        return None
    stacked_values = np.vstack([values for values, _ in pairs])
    stacked_quantity = np.vstack([quantity for _, quantity in pairs])
    total_quantity = np.sum(stacked_quantity, axis=0)
    weighted = np.divide(
        np.sum(stacked_values * stacked_quantity, axis=0),
        total_quantity,
        out=np.full_like(total_quantity, np.nan),
        where=total_quantity > 0,
    )
    return pd.Series(weighted).ffill().bfill().to_numpy()


def _require_agreement(field, values_by_carrier):
    """Return the single shared value, or raise naming the carriers that disagree."""
    distinct = {}
    for carrier, value in values_by_carrier.items():
        distinct.setdefault(repr(value), []).append(carrier)
    if len(distinct) > 1:
        detail = "; ".join(
            f"{value} <- {', '.join(carriers)}" for value, carriers in distinct.items()
        )
        raise ValueError(
            f"Cannot merge carriers that disagree on '{field}': {detail}. "
            f"This value is not meaningfully averaged, so it must match across the "
            f"merged carriers."
        )
    return next(iter(values_by_carrier.values()))


def _as_scalar_or_series(years, values):
    """Emit a scalar when the series is constant, else a yearly custom data type."""
    array = np.asarray(values, dtype=float)
    if np.allclose(array, array[0], rtol=0, atol=1e-12):
        return float(array[0])
    return _yearly_custom_data_type(years, array)


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
        Name of the pooled feedstock resource, used only when every merged carrier
        declares exactly one resource. When any carrier declares several, the union of
        the original resources is preserved instead and this argument is ignored.
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

    quantity_per_carrier = {}
    ef_pairs = []
    economics_pairs = {}  # key -> list of (values, quantity)
    economics_scalars = {}  # key -> {carrier: value}
    resources_per_carrier = {}  # carrier -> {resource: yearly rsc}
    selectivity_per_carrier = {}
    technical_shared = {}  # field -> {carrier: value}
    carrier_shared = {}  # field -> {carrier: value}
    emission_index_per_carrier = {}

    for carrier in carriers_to_merge:
        block = data[carrier]
        inputs = block["inputs"]

        mandate = inputs["mandate"]
        if mandate.get("mandate_type") != "quantity":
            raise ValueError(
                f"Carrier '{carrier}' has mandate_type "
                f"'{mandate.get('mandate_type')}', expected 'quantity'."
            )
        # fill_before=0: a quantity mandate does not exist before its first anchor.
        quantity = _series_to_yearly(mandate["mandate_quantity"], years, fill_before=0.0)
        quantity_per_carrier[carrier] = quantity

        environmental = inputs["environmental"]
        # The model reads `mean_co2_emission_factor_without_resource`
        # (environmental.py:186) via .get(..., null_series), so a key written without the
        # `mean_` prefix does not raise -- it silently yields a zero emission factor.
        if "mean_co2_emission_factor_without_resource" not in environmental:
            raise KeyError(
                f"Carrier '{carrier}' declares no "
                f"'mean_co2_emission_factor_without_resource'. Found: "
                f"{sorted(environmental)}. A key written without the 'mean_' prefix is "
                f"ignored by the model and yields a silently zero emission factor."
            )
        # Clamp (fill_before=None), unlike the mandate above. An emission factor is a
        # property of the fuel, not a quantity: it does not become zero before its first
        # reference year. The model clamps these curves too -- see _INTENSITY_SUFFIXES in
        # models/yaml_interpolator.py -- so anything else here would make the light
        # edition stop reproducing the full one at the head of the curve.
        ef_pairs.append(
            (
                _series_to_yearly(
                    environmental["mean_co2_emission_factor_without_resource"],
                    years,
                ),
                quantity,
            )
        )
        emission_index_per_carrier[carrier] = environmental.get("emission_index")

        # Every economics entry is carried, not just MFSP: dropping unit taxes or
        # subsidies would silently change the net cost the model computes.
        for key, value in (inputs.get("economics") or {}).items():
            if isinstance(value, AeroMapsCustomDataType):
                # Clamped, like the emission factor above: costs, taxes and subsidies are
                # per-MJ intensities, not quantities.
                economics_pairs.setdefault(key, []).append(
                    (_series_to_yearly(value, years), quantity)
                )
            else:
                economics_scalars.setdefault(key, {})[carrier] = value

        technical = inputs["technical"]
        resources_per_carrier[carrier] = {
            resource: _series_to_yearly(consumption, years)
            for resource, consumption in (
                technical.get("resource_specific_consumption") or {}
            ).items()
        }
        selectivity_per_carrier[carrier] = float(technical.get("kerosene_selectivity", 1.0))
        for field in ("lhv", "plant_load_factor", "plant_lifespan"):
            if field in technical:
                technical_shared.setdefault(field, {})[carrier] = technical[field]

        for field in ("environmental_model", "cost_model", "aircraft_type"):
            if field in block:
                carrier_shared.setdefault(field, {})[carrier] = block[field]

    quantities = [quantity_per_carrier[c] for c in carriers_to_merge]
    total_quantity = np.sum(np.vstack(quantities), axis=0)
    generic_ef = _weighted_mean_series(ef_pairs)

    # --- resources -------------------------------------------------------------
    # Pool onto one merged feedstock only when that is faithful, i.e. every carrier
    # declares exactly one. Otherwise keep the union: collapsing several resources of
    # different kinds (electricity and CO2, say) onto one number is meaningless.
    single_resource_each = all(
        len(resources) == 1 for resources in resources_per_carrier.values()
    )
    if single_resource_each and resource_name:
        pooled = [
            (next(iter(resources_per_carrier[c].values())), quantity_per_carrier[c])
            for c in carriers_to_merge
        ]
        generic_resources = {resource_name: _weighted_mean_series(pooled)}
    else:
        union = sorted({r for res in resources_per_carrier.values() for r in res})
        generic_resources = {}
        for resource in union:
            pairs = [
                (
                    resources_per_carrier[c].get(resource, np.zeros_like(years, dtype=float)),
                    quantity_per_carrier[c],
                )
                for c in carriers_to_merge
            ]
            generic_resources[resource] = _weighted_mean_series(pairs)

    # --- kerosene selectivity (harmonic, weighted by feedstock draw) -----------
    feedstock_draw = {
        c: quantity_per_carrier[c] * sum(resources_per_carrier[c].values())
        if resources_per_carrier[c]
        else np.zeros_like(years, dtype=float)
        for c in carriers_to_merge
    }
    draw_total = np.sum(np.vstack([feedstock_draw[c] for c in carriers_to_merge]), axis=0)
    mobilised = np.sum(
        np.vstack(
            [feedstock_draw[c] / selectivity_per_carrier[c] for c in carriers_to_merge]
        ),
        axis=0,
    )
    with np.errstate(divide="ignore", invalid="ignore"):
        selectivity = np.divide(
            draw_total, mobilised, out=np.full_like(draw_total, np.nan), where=mobilised > 0
        )
    selectivity = pd.Series(selectivity).ffill().bfill().to_numpy()
    if not np.all(np.isfinite(selectivity)):
        # No carrier draws any feedstock anywhere: selectivity is meaningless, and the
        # model's own default is 1.0.
        selectivity = np.ones_like(years, dtype=float)

    generic_technical = {
        "resource_names": list(generic_resources),
        "resource_specific_consumption": {
            resource: _as_scalar_or_series(years, values)
            for resource, values in generic_resources.items()
        },
        "kerosene_selectivity": _as_scalar_or_series(years, selectivity),
    }
    for field, values in technical_shared.items():
        generic_technical[field] = _require_agreement(field, values)

    generic_carrier = {
        "name": generic_name,
        "environmental_model": _require_agreement(
            "environmental_model", carrier_shared.get("environmental_model", {})
        )
        if "environmental_model" in carrier_shared
        else "top-down",
        "cost_model": _require_agreement("cost_model", carrier_shared.get("cost_model", {}))
        if "cost_model" in carrier_shared
        else "top-down",
        "aircraft_type": _require_agreement(
            "aircraft_type", carrier_shared.get("aircraft_type", {})
        )
        if "aircraft_type" in carrier_shared
        else "dropin_fuel",
        "energy_origin": energy_origin,
        "default": False,
        "compute_all_years": True,
        "inputs": {
            "mandate": {
                "mandate_type": "quantity",
                "mandate_quantity": _yearly_custom_data_type(years, total_quantity),
            },
            "technical": generic_technical,
            "environmental": {
                "mean_co2_emission_factor_without_resource": _yearly_custom_data_type(
                    years, generic_ef
                ),
                "emission_index": _require_agreement(
                    "emission_index", emission_index_per_carrier
                ),
            },
            "economics": {},
        },
        "outputs": None,
    }

    economics = generic_carrier["inputs"]["economics"]
    for key, pairs in economics_pairs.items():
        economics[key] = _yearly_custom_data_type(years, _weighted_mean_series(pairs))
    for key, values in economics_scalars.items():
        economics[key] = _require_agreement(key, values)

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
