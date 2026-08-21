"""MDA settings for the spike scenario, applied the way the project wants them applied.

The spike originally carried a ``regionalisation.mda`` config block. That block was
rejected in review of #157: MDA settings stay on the GEMSEO objects and are tuned from
the notebook, as ``AeroMAPSProcess`` does. This module is that pattern, in code.

Two routes, and they are not interchangeable:

* ``tune`` writes on the objects of an already-built chain. ``tolerance`` and
  ``max_mda_iter`` are re-read from ``settings`` at every iteration, so assigning to
  them works. ``over_relaxation_factor`` and ``acceleration_method`` are NOT: they are
  baked into the solver's ``RelaxationAcceleration`` at construction, and only the
  *properties* of the same name write through to it.
* ``rebuild`` builds a fresh ``MDAChain`` over the process' existing disciplines. Needed
  for anything structural, i.e. ``inner_mda_name``.
"""

from gemseo.algos.sequence_transformer.acceleration import AccelerationMethod
from gemseo.mda.mda_chain import MDAChain

# Tolerance and iteration cap: what AeroMAPSProcess uses, and what every measurement in
# RAPPORT.md was taken at.
#
# Acceleration: AeroMAPS ships none by default, deliberately -- it changes the iterates
# of every existing scenario. The spike turns it on because its own § 4 measured it as
# the only lever that works on the real chain: over-relaxation rescued nothing at 0.7 or
# 0.4, MDAJacobi failed outright, and Alternate2Delta moved the market's stiffness
# ceiling from "between 4 and 8" to "at least 16". A market discipline is exactly the
# stiff-coupling case it is for.
DEFAULTS = {
    "tolerance": 1e-10,
    "max_mda_iter": 200,
    "log_convergence": False,
    "acceleration_method": AccelerationMethod.ALTERNATE_2_DELTA,
}


def tune(process, over_relaxation_factor=None, acceleration_method=None, **settings):
    """Apply settings to the chain the process already built, without rebuilding it."""
    settings = {**DEFAULTS, **settings}
    if acceleration_method is None:
        acceleration_method = settings.pop("acceleration_method", None)
    else:
        settings.pop("acceleration_method", None)

    # Assigned on the chain, which cascades them to the inner MDAs -- the reverse does
    # not hold, see "Tuning an MDAChain" in aeromaps/core/gemseo.py.
    for key, value in settings.items():
        setattr(process.mda_chain.settings, key, value)

    # Properties, not settings -- see the module docstring.
    for inner in process.mda_chain.inner_mdas:
        if over_relaxation_factor is not None:
            inner.over_relaxation_factor = over_relaxation_factor
        if acceleration_method is not None:
            inner.acceleration_method = acceleration_method
    return process.mda_chain


# The knobs MDAChain does not forward: they only reach the solver that iterates
# through inner_mda_settings. Passed at the top level they are silently ignored.
_INNER_ONLY = ("over_relaxation_factor", "acceleration_method")


def rebuild(process, **settings):
    """Rebuild the unified chain over the same disciplines with different settings."""
    merged = {"inner_mda_name": "MDAGaussSeidel", **DEFAULTS, **settings}
    inner = {key: merged.pop(key) for key in _INNER_ONLY if key in merged}
    process.mda_chain = MDAChain(
        disciplines=process.disciplines,
        initialize_defaults=True,
        inner_mda_settings=inner,
        **merged,
    )
    return process.mda_chain
