"""Reproduce, on a real scenario, the three MDA failures that PR #157 fixes.

The tests that ship with those fixes assert the *invariants* -- no discipline mutates
its input, a non-solution raises. They do not show the failures, because by then the
failures are gone: two of them are pinned on synthetic two-discipline loops, and the
third asserts something that now holds everywhere.

This script does the opposite. It puts each defect back at runtime, on a shipped
scenario, and prints what the solver reported before and after. Nothing here is
imported by the package or collected by pytest; it exists to be run and read.

    python aeromaps/notebooks/dev/mda_failure_modes.py            # all three
    python aeromaps/notebooks/dev/mda_failure_modes.py residual   # just one

The three cases:

1. ``residual``   -- a discipline mutating an MDA input pins the residual above any
                     usable tolerance, and nothing says so. (PR section 3.)
2. ``nan``        -- a solver excursion to a negative airfare turns the whole chain to
                     NaN, and the residual reports that as *convergence*. (Section 1b,
                     and the reason for the airfare bound in section 4.)
3. ``iterations`` -- a chain that simply runs out of iterations returns ordinary-looking
                     DataFrames. (Section 1a, and the reason for section 2.)

Each case runs twice: once with the defect reinstated, once as the code stands. The
second run is what the first should have looked like.
"""

import logging
import sys
import warnings
from pathlib import Path

import pandas as pd
from gemseo.mda.mda_chain import MDAChain

from aeromaps import create_process
from aeromaps.core.gemseo import (
    MDAConvergenceError,
    _couplings_with_spread_nans,
    check_mda_convergence,
)
from aeromaps.models.air_transport.air_traffic.rpk_market import RPKElasticity
from aeromaps.models.impacts.emissions.co2_emissions import CO2Emissions

# Cases 1 and 3 need a chain with a cost-feedback loop; this one converges in 109
# iterations and is what the PR's before/after numbers were measured on.
CONFIG = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "tested_configs"
    / "config_elasticity_demand.yaml"
)

# Case 2 needs ``RPKElasticity`` specifically -- the airfare <-> RPK power law -- which
# only the ``cagr_elasticity`` demand model instantiates. ``config_elasticity_demand``
# uses ``constant_elasticity`` (``PriceAndIncomeElasticity``), a different loop that
# never touches the airfare at all.
AIRFARE_CONFIG = (
    Path(__file__).resolve().parents[1]
    / "tutorials"
    / "08_use_variable_demand"
    / "data_elasticity"
    / "config_elasticity.yaml"
)

# GEMSEO logs one line per iteration per discipline; the point here is the summary.
logging.getLogger().setLevel(logging.ERROR)
# Models warn about scenario choices on every process construction; not the subject here.
warnings.simplefilter("ignore")


# --------------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------------


def _solver(process):
    """The one inner MDA of this scenario's chain, or None if no loop was found."""
    inner = list(getattr(process.mda_chain, "inner_mdas", []))
    return inner[0] if inner else None


def _verdict(process):
    """What the run reported: iterations, final residual, and what the check makes of it."""
    mda = _solver(process)
    if mda is None:
        return "no inner MDA (this chain has no coupling loop)"

    history = list(mda.residual_history)
    failures = check_mda_convergence(process.mda_chain, on_failure="ignore")
    verdict = "CONVERGED" if not failures else "FAILED"
    line = (
        f"{verdict:>9}  |  {len(history):>3} iterations  |  "
        f"final residual {history[-1]:.3e}  (tolerance {mda.settings.tolerance:.0e})"
    )
    if failures:
        line += "\n" + "\n".join("           " + f for f in failures[0].splitlines())
    return line


def _nan_couplings(process):
    """Count the coupling variables holding a NaN *after* a real value.

    That is the tell of a chain that died mid-solve: a NaN over the historical years is
    ordinary in AeroMAPS, and a coupling from a pathway the scenario does not use is
    legitimately NaN throughout. The same helper the convergence check uses, so the two
    numbers in this output cannot disagree.
    """
    mda = _solver(process)
    if mda is None:
        return 0, 0
    return (
        len(_couplings_with_spread_nans(mda)),
        len(mda.coupling_structure.strong_couplings),
    )


def _run(label, build=create_process, config=None, **kwargs):
    """Run one configuration and print its verdict; never let a raise stop the script."""
    print(f"\n  {label}")
    try:
        process = build(configuration_file=config or CONFIG, **kwargs)
        process.on_mda_failure = "ignore"  # the verdict is printed, not thrown
        process.compute()
    except MDAConvergenceError as error:  # pragma: no cover - defensive
        print(f"    raised MDAConvergenceError: {error}")
        return None
    print(f"    {_verdict(process)}")
    return process


# --------------------------------------------------------------------------------
# 1. A discipline mutating its input pins the residual
# --------------------------------------------------------------------------------


def case_residual():
    """PR section 3.

    GEMSEO snapshots the previous iterate with ``self.io.data.copy()`` -- a *shallow*
    copy, so the Series it holds are the very objects handed to ``compute()``.
    ``CO2Emissions`` used to call ``.fillna(0, inplace=True)`` on one of them. For an
    all-NaN emission factor (any scenario without hydrogen or electric aircraft, which
    is most of them) the output side of the residual converts to the ``-999999``
    sentinel while the input side has already been rewritten to ``0``: a constant
    difference of 999999 per element, every iteration, forever.
    """
    print("\n=== 1. Residual floor: a discipline mutating its MDA input =================")
    print(case_residual.__doc__.strip().split("\n\n", 1)[1])

    original_compute = CO2Emissions.compute
    observed = {}

    def mutating_compute(self, input_data):
        """The pre-#157 body: 'locally' fill the NaNs of a coupling input. In place."""
        for name, value in input_data.items():
            if name.endswith("_mean_co2_emission_factor") and isinstance(value, pd.Series):
                observed.setdefault(name, {"id": id(value), "nan_before": int(value.isna().sum())})
                value.fillna(0, inplace=True)
                observed[name]["nan_after"] = int(value.isna().sum())
        return original_compute(self, input_data)

    CO2Emissions.compute = mutating_compute
    try:
        _run("with the in-place fillna reinstated (i.e. main):")
    finally:
        CO2Emissions.compute = original_compute

    for name, seen in sorted(observed.items())[:3]:
        print(
            f"      {name}: id={seen['id']} "
            f"nan={seen['nan_before']} at the top of compute() -> "
            f"nan={seen.get('nan_after')} by the time the residual is taken"
        )
    print("      Same object both times: the snapshot the solver differences against.")

    _run("as the code stands:")


# --------------------------------------------------------------------------------
# 2. A NaN chain reported as converged
# --------------------------------------------------------------------------------


def case_nan():
    """PR sections 1b and 4.

    ``RPKElasticity`` raises the airfare ratio to a fractional exponent, and numpy
    returns NaN for a negative float64 base -- silently. A solver excursion to a
    negative airfare therefore turns the chain to NaN; the sentinel then differences
    against itself to exactly zero, and the residual reports convergence on a state
    that carries no values at all.

    The excursion is forced here by seeding the airfare coupling negative, with the
    bound widened so it cannot intervene. In the spike it took no forcing: GEMSEO's
    acceleration methods extrapolate the coupling vector by unconstrained least
    squares, and one of them produced -2.11 EUR/RPK on its own.
    """
    print("\n\n=== 2. Converged on NaN: an excursion the residual cannot see ============")
    print(case_nan.__doc__.strip().split("\n\n", 1)[1])

    original_initialize = RPKElasticity._initialize_df
    original_bounds = RPKElasticity.AIRFARE_BOUNDS_RELATIVE

    def negative_seed(self):
        original_initialize(self)
        self._coupling_defaults = {
            "airfare_per_rpk": pd.Series(
                -2.11,  # EUR/RPK, the value measured in the spike
                index=range(self.historic_start_year, self.end_year + 1),
            )
        }

    RPKElasticity._initialize_df = negative_seed
    RPKElasticity.AIRFARE_BOUNDS_RELATIVE = (-1e9, 1e9)  # the bound cannot fire
    try:
        process = _run(
            "seeded at -2.11 EUR/RPK, bound disabled (i.e. main):", config=AIRFARE_CONFIG
        )
        if process is not None:
            spread, total = _nan_couplings(process)
            print(f"      {spread} of {total} coupling variables hold a NaN after a real value.")
    finally:
        RPKElasticity.AIRFARE_BOUNDS_RELATIVE = original_bounds

    try:
        process = _run("same seed, bound restored:", config=AIRFARE_CONFIG)
        if process is not None:
            spread, total = _nan_couplings(process)
            print(f"      {spread} of {total} coupling variables hold a NaN after a real value.")
    finally:
        RPKElasticity._initialize_df = original_initialize


# --------------------------------------------------------------------------------
# 3. Out of iterations, silently
# --------------------------------------------------------------------------------


def case_iterations():
    """PR sections 1a and 2.

    ``_setup_unified_mda`` asked for ``tolerance=1e-5`` and, by omitting
    ``max_mda_iter``, took GEMSEO's default of 20 -- while ``AeroMAPSProcess`` uses
    1e-10 / 200, with a comment saying why. The looser chain stops early and returns a
    full set of ordinary-looking DataFrames. Reproduced here by rebuilding the chain
    with the loose settings.
    """
    print("\n\n=== 3. Out of iterations: a non-solution shaped exactly like a solution ===")
    print(case_iterations.__doc__.strip().split("\n\n", 1)[1])

    def loose(configuration_file, **kwargs):
        process = create_process(configuration_file=configuration_file, **kwargs)
        # Rebuilt rather than reassigned: pydantic re-runs MDAChain_Settings' cascade
        # validator on any assignment to an existing chain's settings, so tuning one in
        # place silently does nothing. See "Tuning an MDAChain" in aeromaps/core/gemseo.py.
        process.mda_chain = MDAChain(
            disciplines=process.disciplines,
            tolerance=1e-5,
            max_mda_iter=20,
            initialize_defaults=True,
            inner_mda_name="MDAGaussSeidel",
        )
        return process

    process = _run("tolerance 1e-5, max_mda_iter 20 (the old unified_mda):", build=loose)
    if process is not None:
        outputs = process.data["vector_outputs"]
        print(
            f"      ...and it returned {outputs.shape[1]} output columns, "
            f"rpk 2050 = {outputs['rpk'].loc[2050]:.6e}. Nothing marks it as a non-solution."
        )

    process = _run("tolerance 1e-10, max_mda_iter 200 (AeroMAPSProcess):")
    if process is not None:
        outputs = process.data["vector_outputs"]
        print(
            f"      ...and it returned {outputs.shape[1]} output columns, "
            f"rpk 2050 = {outputs['rpk'].loc[2050]:.6e}."
        )


CASES = {"residual": case_residual, "nan": case_nan, "iterations": case_iterations}


if __name__ == "__main__":
    requested = sys.argv[1:] or list(CASES)
    unknown = [name for name in requested if name not in CASES]
    if unknown:
        sys.exit(f"unknown case(s) {unknown}; choose from {list(CASES)}")
    for name in requested:
        CASES[name]()
    print()
