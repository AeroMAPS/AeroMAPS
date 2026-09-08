"""Convert energy-carrier emission factors between life-cycle and CORSIA scopes.

AeroMAPS reports well-to-wake (WtW) emissions by default: everything released
from growing or generating the fuel through to burning it. Industry roadmaps
following ICAO CORSIA headline tank-to-wake (TtW) instead, and the two are not
the same accounting of the same fleet. CORSIA states the method:

    The role of SAF in this analysis is based on the ICAO CORSIA methodology,
    which reflects the combustion-related emissions portion (3.16 gCO2/gfuel) of
    life cycle values ... within this methodology, a majority of the life cycle
    emissions reductions from SAF that occur in the well to tank (WtT) phase are
    accounted for as TtW reductions.

So a drop-in pathway's CORSIA factor is the fossil combustion baseline scaled by
that pathway's carbon-intensity ratio::

    corsia = FOSSIL_TTW x (lifecycle_pathway / FOSSIL_WTW)

Taking the ratio rather than a roadmap's rounded percentages avoids importing
their rounding: woody biomass at 2050 comes out at 5.9905 rather than
73.8 x 0.08 = 5.904.

Carriers that are not drop-in fuels are not combusted, so their CORSIA factor is
zero: the carbon behind a battery-electric or electrolysis-derived pathway is
well-to-tank by definition. Conversion processes are zeroed for the same reason,
which is what :func:`processes_to_corsia` is for.

``FOSSIL_TTW`` is 73.8 and not the 71.81 that 3.16 gCO2/g over 44 MJ/kg gives.
73.8 is the value the ATAG editions' own files carry, and it is kept so that a
reproduction stays comparable to what it reproduces; the discrepancy is the
data's, not this transform's.

Two routes, one transform
-------------------------
:func:`lifecycle_to_corsia` and :func:`corsia_to_lifecycle` rewrite a carriers
file, producing the twin YAML a parallel ``-TTW`` configuration reads.

:func:`apply_corsia_scope` and :func:`apply_lifecycle_scope` do the same thing to
a live process, between ``create_process`` and ``compute``, so one configuration
can be run in both scopes and no twin file is needed at all.

Both call the same conversion, so the two routes cannot drift apart. Which to
prefer is a workflow choice: committed twins are auditable and diffable, while
the in-place route removes a whole family of generated files.
"""

from aeromaps.models.base import AeroMapsCustomDataType
from aeromaps.utils.yaml import read_yaml_file, write_yaml_file

FOSSIL_WTW = 88.7  # gCO2/MJ, fossil kerosene, well-to-wake
FOSSIL_TTW = 73.8  # gCO2/MJ, combustion only
CORSIA_RATIO = FOSSIL_TTW / FOSSIL_WTW

EF_KEY = "mean_co2_emission_factor_without_resource"
DROPIN = "dropin_fuel"

# Converted factors are rounded to this many decimals by default. The rounding is
# cosmetic -- four decimals is far finer than the one to three the sources carry,
# and 5e-5 gCO2/MJ is nothing physically -- but it is not free to change: the
# committed CORSIA twins in this repository were written with it, so dropping it
# would shift every one of them in the last digits and move every scenario output
# computed from them. Pass ``decimals=None`` for the unrounded conversion.
DEFAULT_DECIMALS = 4


def _round(value, decimals):
    return value if decimals is None else round(value, decimals)


def _scaled(factor, ratio, decimals=DEFAULT_DECIMALS):
    """Scale an emission-factor entry, whatever shape the YAML gave it."""
    if isinstance(factor, AeroMapsCustomDataType):
        factor.values = [_round(value * ratio, decimals) for value in factor.values]
        return factor
    if isinstance(factor, dict):
        return {
            key: [_round(v * ratio, decimals) for v in value] if key == "values" else value
            for key, value in factor.items()
        }
    return _round(factor * ratio, decimals)


def _emission_factor(entry):
    """The environmental block's emission-factor entry, or None."""
    return entry.get("inputs", {}).get("environmental", {}).get(EF_KEY)


def _convert_carriers(carriers, ratio, invert=False, decimals=DEFAULT_DECIMALS):
    """Apply ``ratio`` to drop-in carriers and zero everything else.

    ``invert`` divides instead of multiplying. It cannot restore a zeroed
    non-drop-in factor, since that information is gone, so those are left alone
    on the way back: see :func:`corsia_to_lifecycle`.
    """
    scaled, zeroed = [], []
    for name, entry in carriers.items():
        if not isinstance(entry, dict):
            continue
        factor = _emission_factor(entry)
        if factor is None:
            continue
        if entry.get("aircraft_type") == DROPIN:
            entry["inputs"]["environmental"][EF_KEY] = _scaled(
                factor, (1.0 / ratio) if invert else ratio, decimals
            )
            scaled.append(name)
        elif not invert:
            entry["inputs"]["environmental"][EF_KEY] = _scaled(factor, 0.0, decimals)
            zeroed.append(name)
    return carriers, scaled, zeroed


def _load(source):
    """Accept either a path to a carriers file or an already-loaded dict."""
    if isinstance(source, dict):
        return source
    return read_yaml_file(str(source))


def _emit(carriers, output_file):
    if output_file is not None:
        write_yaml_file(carriers, str(output_file))
    return carriers


def lifecycle_to_corsia(energy_carriers, output_file=None, decimals=DEFAULT_DECIMALS):
    """Rewrite a carriers file from well-to-wake onto the CORSIA scope.

    Parameters
    ----------
    energy_carriers : str, Path or dict
        The source ``energy_carriers`` YAML, or an already-loaded mapping.
    output_file : str or Path, optional
        Where to write the twin. The mapping is always returned.

    Returns
    -------
    dict
        The converted carriers.
    """
    carriers, _, _ = _convert_carriers(_load(energy_carriers), CORSIA_RATIO, decimals=decimals)
    return _emit(carriers, output_file)


def corsia_to_lifecycle(energy_carriers, output_file=None, decimals=DEFAULT_DECIMALS):
    """Rewrite a CORSIA-scope carriers file back onto well-to-wake.

    Only drop-in pathways are restored. A non-drop-in carrier's life-cycle factor
    was set to zero on the way out and cannot be recovered from the result, so it
    is left untouched rather than silently invented; convert from the well-to-wake
    source instead when the true value is needed.
    """
    carriers, _, _ = _convert_carriers(
        _load(energy_carriers), CORSIA_RATIO, invert=True, decimals=decimals
    )
    return _emit(carriers, output_file)


def processes_to_corsia(processes, output_file=None, decimals=DEFAULT_DECIMALS):
    """Zero every conversion process's emission factor.

    A process such as liquefaction or electrolysis emits before the fuel reaches
    the tank, so under CORSIA it contributes nothing.
    """
    entries = _load(processes)
    for entry in entries.values():
        if not isinstance(entry, dict):
            continue
        factor = _emission_factor(entry)
        if factor is not None:
            entry["inputs"]["environmental"][EF_KEY] = _scaled(factor, 0.0, decimals)
    return _emit(entries, output_file)


def _apply_scope(process, ratio, invert, decimals=DEFAULT_DECIMALS):
    """Scale the emission-factor curves a built process already carries.

    Every carrier intensity curve is exposed on ``process.parameters`` as
    ``<name>_mean_co2_emission_factor_without_resource`` plus its ``_years`` and
    ``_values`` pair, so the conversion is a rewrite of the ``_values`` lists.
    Carriers are classified through ``process.pathways_manager``; anything
    carrying such a curve without being a known carrier is a conversion process,
    and is zeroed for the same reason :func:`processes_to_corsia` zeroes them.
    """
    parameters = process.parameters
    aircraft_types = {
        carrier.name: carrier.aircraft_type for carrier in process.pathways_manager.get_all()
    }

    suffix = f"_{EF_KEY}_values"
    for attribute in [name for name in vars(parameters) if name.endswith(suffix)]:
        owner = attribute[: -len(suffix)]
        values = getattr(parameters, attribute)
        if owner in aircraft_types:
            if aircraft_types[owner] == DROPIN:
                factor = (1.0 / ratio) if invert else ratio
            elif invert:
                continue  # zeroed on the way out, not recoverable: see corsia_to_lifecycle
            else:
                factor = 0.0
        elif invert:
            continue
        else:
            factor = 0.0  # a conversion process: well-to-tank by definition
        setattr(parameters, attribute, [_round(value * factor, decimals) for value in values])
    return process


def apply_corsia_scope(process, decimals=DEFAULT_DECIMALS):
    """Put a built process onto the CORSIA scope, in place, before ``compute()``.

    Returns the process, so it can be chained onto ``create_process``.
    """
    return _apply_scope(process, CORSIA_RATIO, invert=False, decimals=decimals)


def apply_lifecycle_scope(process, decimals=DEFAULT_DECIMALS):
    """Put a CORSIA-scope process back onto well-to-wake, in place.

    Subject to the same limitation as :func:`corsia_to_lifecycle`: only drop-in
    pathways are restored.
    """
    return _apply_scope(process, CORSIA_RATIO, invert=True, decimals=decimals)
