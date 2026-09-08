"""Transform the policy mandates declared in an ``energy_carriers`` YAML file.

A carrier's mandate says how much of it must be supplied, and AeroMAPS accepts two
spellings of that. A ``quantity`` mandate fixes a volume; a ``share`` mandate fixes
a percentage of drop-in energy. The distinction is not cosmetic once demand can
respond to price: a fixed volume tightens on its own as demand falls, and a fixed
share does not, so the two give materially different answers.

Three transforms live here, all of the same shape -- take a carriers mapping, alter
the mandate curves, hand it back:

:func:`quantity_to_share`
    Rewrite volume mandates as the equivalent percentage mandates. Needed before a
    scenario can be run with price-elastic demand at all, since a quantity mandate
    makes the blend share depend on total demand, which is itself a coupling
    variable, and the MDA fails on the resulting coupling shape mismatch.
:func:`zero_mandates`
    Remove named pathways from the blend, for a counterfactual that deploys none of
    them.
:func:`retime_mandates`
    Re-anchor curves onto the prospection start year, so that a mandate written
    from 2020 is not back-extended across years that are now observed.

Each accepts a path or an already-loaded mapping and returns the mapping, writing
it only if ``output_file`` is given, matching
:mod:`aeromaps.utils.energy_aggregation` and :mod:`aeromaps.utils.emission_scopes`.
"""

from aeromaps.models.base import AeroMapsCustomDataType
from aeromaps.utils.yaml import read_yaml_file, write_yaml_file

QUANTITY = "quantity"
SHARE = "share"
CURVE_KEYS = {QUANTITY: "mandate_quantity", SHARE: "mandate_share"}


def _load(source):
    return source if isinstance(source, dict) else read_yaml_file(str(source))


def _emit(carriers, output_file):
    if output_file is not None:
        write_yaml_file(carriers, str(output_file))
    return carriers


def _mandate(entry):
    """The mandate block of a carrier entry, or None when it declares none."""
    if not isinstance(entry, dict):
        return None
    return (entry.get("inputs") or {}).get("mandate")


def _curve(mandate):
    """``(key, curve)`` for whichever spelling this mandate uses."""
    for key in CURVE_KEYS.values():
        if key in mandate:
            return key, mandate[key]
    return None, None


def _interpolate(years, values, target):
    """Linear interpolation of a reference curve at ``target``, clamped at both ends."""
    if target <= years[0]:
        return values[0]
    if target >= years[-1]:
        return values[-1]
    for index in range(len(years) - 1):
        if years[index] <= target <= years[index + 1]:
            span = years[index + 1] - years[index]
            if span == 0:
                return values[index]
            weight = (target - years[index]) / span
            return values[index] + weight * (values[index + 1] - values[index])
    raise AssertionError("unreachable: target lies inside the curve")


def quantity_to_share(energy_carriers, shares, output_file=None, decimals=10):
    """Rewrite every quantity mandate as the equivalent share mandate.

    Parameters
    ----------
    energy_carriers : str, Path or dict
        The source carriers file, or an already-loaded mapping.
    shares : dict
        ``{carrier: {year: percentage}}``, the blend shares to adopt. Sampling
        these from a run of the same scenario with exogenous demand is what makes
        the converted file reproduce that run's fuel trajectory; inventing them
        would not.
    decimals : int, optional
        Rounding applied to the sampled shares.

    Raises
    ------
    KeyError
        If a carrier carrying a quantity mandate has no share to convert to.
        Silently skipping it would drop that pathway from the blend.
    """
    carriers = _load(energy_carriers)
    converted = []
    for name, entry in carriers.items():
        mandate = _mandate(entry)
        if not mandate or mandate.get("mandate_type") != QUANTITY:
            continue
        quantity = mandate.pop(CURVE_KEYS[QUANTITY])
        if name not in shares:
            raise KeyError(f"no share given for {name!r}, which carries a quantity mandate")
        anchors = [int(year) for year in quantity.years]
        missing = [year for year in anchors if year not in shares[name]]
        if missing:
            raise KeyError(f"no share for {name!r} at {missing}")
        mandate["mandate_type"] = SHARE
        mandate[CURVE_KEYS[SHARE]] = AeroMapsCustomDataType(
            {
                "years": anchors,
                "values": [round(shares[name][year], decimals) for year in anchors],
                "method": quantity.method,
            }
        )
        converted.append(name)
    return _emit(carriers, output_file)


def zero_mandates(energy_carriers, pathways, output_file=None):
    """Zero the mandate of each named pathway, removing it from the blend.

    Parameters
    ----------
    pathways : iterable of str
        Carrier names to zero.

    Raises
    ------
    KeyError
        If a named pathway is absent, or carries no mandate curve. Both would
        otherwise be silent no-ops, and a counterfactual that quietly failed to
        remove what it names is worse than one that does not run.
    """
    carriers = _load(energy_carriers)
    for name in pathways:
        if name not in carriers:
            raise KeyError(f"{name!r} is not declared in this carriers file")
        mandate = _mandate(carriers[name])
        key, curve = _curve(mandate) if mandate else (None, None)
        if curve is None:
            raise KeyError(f"{name!r} declares no mandate curve to zero")
        if isinstance(curve, AeroMapsCustomDataType):
            curve.values = [0] * len(curve.values)
        else:
            mandate[key] = 0
    return _emit(carriers, output_file)


def retime_mandates(energy_carriers, start_year, output_file=None):
    """Re-anchor every mandate curve onto ``start_year``.

    ``yaml_interpolator`` extends a curve backwards whenever its first reference
    year precedes the prospection start, so a mandate anchored at 2020 back-fills
    fuel across years that are now observed. Each curve is evaluated at
    ``start_year`` against its *original* anchors, anchors before it are dropped,
    and everything from it onwards is left alone, so the projected trajectory is
    preserved exactly while the historic period carries no mandate. Anchoring the
    start at zero instead would cut the following year's volume substantially.

    Idempotent: a curve already starting at or after ``start_year`` is untouched.

    Returns
    -------
    dict
        The carriers mapping. ``retimed`` names are available on the returned
        object only through inspection, so callers wanting a report should diff.
    """
    carriers = _load(energy_carriers)
    for entry in carriers.values():
        mandate = _mandate(entry)
        if not mandate:
            continue
        _, curve = _curve(mandate)
        if not isinstance(curve, AeroMapsCustomDataType) or not len(curve.years):
            continue
        years = [int(year) for year in curve.years]
        values = list(curve.values)
        if years[0] >= start_year:
            continue
        kept = [i for i, year in enumerate(years) if year >= start_year and year != start_year]
        first = (
            values[years.index(start_year)]
            if start_year in years
            else _interpolate(years, values, start_year)
        )
        curve.years = [start_year] + [years[i] for i in kept]
        curve.values = [first] + [values[i] for i in kept]
    return _emit(carriers, output_file)
