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

from gemseo.mda.mda_chain import MDAChain

# What AeroMAPSProcess uses, and what every measurement in RAPPORT.md was taken at.
# _setup_unified_mda ships tolerance=1e-5 with no max_mda_iter (GEMSEO default: 20).
DEFAULTS = {"tolerance": 1e-10, "max_mda_iter": 200, "log_convergence": False}


def tune(process, over_relaxation_factor=None, acceleration_method=None, **settings):
    """Apply settings to the chain the process already built, without rebuilding it."""
    mdas = [process.mda_chain, *process.mda_chain.inner_mdas]
    for key, value in {**DEFAULTS, **settings}.items():
        for mda in mdas:
            setattr(mda.settings, key, value)
    # Properties, not settings -- see the module docstring.
    for inner in process.mda_chain.inner_mdas:
        if over_relaxation_factor is not None:
            inner.over_relaxation_factor = over_relaxation_factor
        if acceleration_method is not None:
            inner.acceleration_method = acceleration_method
    return process.mda_chain


def rebuild(process, **settings):
    """Rebuild the unified chain over the same disciplines with different settings."""
    inner = {}
    for key in ("over_relaxation_factor", "acceleration_method"):
        if key in settings:
            inner[key] = settings.pop(key)
    kwargs = {
        "disciplines": process.disciplines,
        "initialize_defaults": True,
        "inner_mda_name": "MDAGaussSeidel",
        **DEFAULTS,
        **settings,
    }
    if inner:
        kwargs["inner_mda_settings"] = inner
    process.mda_chain = MDAChain(**kwargs)
    return process.mda_chain
