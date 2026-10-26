"""A non-converged MDA must be an error, not a silent result.

Nothing downstream distinguishes an unconverged run from a converged one: the output
DataFrames look the same, and GEMSEO only logs a warning among thousands of lines. The
values are simply not a solution of the coupled system -- the coupling variables were
still moving when the solver gave up.
"""

from pathlib import Path

import logging

import pytest
import numpy as np
from gemseo.disciplines.analytic import AnalyticDiscipline
from gemseo.mda.mda_chain import MDAChain

from aeromaps import create_process
from aeromaps.core.gemseo import MDAConvergenceError, check_mda_convergence

CONFIG_DIR = Path(__file__).parent.parent / "tested_configs"


def _chain(gain, max_mda_iter=5):
    """A two-discipline loop with fixed-point gain ``gain**2``: diverges above 1."""
    disciplines = [
        AnalyticDiscipline({"x": f"1.0 + {gain} * y"}, name="Dx"),
        AnalyticDiscipline({"y": f"1.0 + {gain} * x"}, name="Dy"),
    ]
    return MDAChain(
        disciplines=disciplines,
        inner_mda_name="MDAGaussSeidel",
        tolerance=1e-10,
        max_mda_iter=max_mda_iter,
    )


def test_converged_mda_passes():
    chain = _chain(0.4, max_mda_iter=100)
    chain.execute()
    assert check_mda_convergence(chain) == []


def test_unconverged_mda_raises():
    chain = _chain(2.0)
    chain.execute()

    with pytest.raises(MDAConvergenceError) as excinfo:
        check_mda_convergence(chain)

    message = str(excinfo.value)
    assert "did not converge" in message
    # The message must say what to do about it, which depends on why it stopped.
    assert "iterations" in message


def test_the_message_separates_slow_from_stuck():
    """The two failures need opposite fixes, so the message must tell them apart."""
    slow = _chain(0.95, max_mda_iter=5)  # converging, just not within 5 iterations
    slow.execute()
    with pytest.raises(MDAConvergenceError, match="still decreasing"):
        check_mda_convergence(slow)

    stuck = _chain(2.0)  # diverging: more iterations make it worse
    stuck.execute()
    with pytest.raises(MDAConvergenceError, match="stopped decreasing"):
        check_mda_convergence(stuck)


def test_unconverged_mda_can_be_downgraded_to_a_warning(caplog):
    chain = _chain(2.0)
    chain.execute()

    with caplog.at_level(logging.WARNING):
        failures = check_mda_convergence(chain, on_failure="warn")

    assert len(failures) == 1
    assert "did not converge" in caplog.text

    assert check_mda_convergence(chain, on_failure="ignore") == failures


def test_context_is_reported():
    chain = _chain(2.0)
    chain.execute()

    with pytest.raises(MDAConvergenceError, match="region 'FR'"):
        check_mda_convergence(chain, context="region 'FR': ")


def test_converging_on_nan_is_not_convergence():
    """A residual at zero because every coupling went NaN is not a solution.

    NaN converts to the -999999 sentinel, so a NaN coupling differences against itself
    to exactly zero: the solver reports convergence on a state carrying no values. The
    tell is a NaN sitting *after* a real value -- historical-only or unused-pathway
    series are NaN from the start, which is legitimate.
    """
    chain = _chain(0.4, max_mda_iter=100)
    chain.execute()
    assert check_mda_convergence(chain) == []

    coupling = sorted(chain.inner_mdas[0].coupling_structure.strong_couplings)[0]
    chain.inner_mdas[0].io.data[coupling] = np.array([1.0, np.nan])

    with pytest.raises(MDAConvergenceError, match="converged on NaN"):
        check_mda_convergence(chain)


def test_leading_nans_are_legitimate():
    """Historical years, and pathways the scenario does not use, are NaN by design."""
    chain = _chain(0.4, max_mda_iter=100)
    chain.execute()
    couplings = sorted(chain.inner_mdas[0].coupling_structure.strong_couplings)

    chain.inner_mdas[0].io.data[couplings[0]] = np.array([np.nan, np.nan, 1.0])
    assert check_mda_convergence(chain) == []

    chain.inner_mdas[0].io.data[couplings[0]] = np.array([np.nan, np.nan])
    assert check_mda_convergence(chain) == []


def test_unknown_policy_is_rejected():
    chain = _chain(0.4)
    chain.execute()

    with pytest.raises(ValueError, match="on_failure"):
        check_mda_convergence(chain, on_failure="shrug")


def test_a_chain_without_coupling_has_nothing_to_check():
    chain = MDAChain(
        disciplines=[
            AnalyticDiscipline({"y": "2.0 * x"}, name="D1"),
            AnalyticDiscipline({"z": "3.0 * y"}, name="D2"),
        ]
    )
    chain.execute()

    assert chain.inner_mdas == []
    assert check_mda_convergence(chain) == []


def test_process_compute_raises_when_the_solver_stops_short():
    """End-to-end: the check is actually wired into AeroMAPSProcess.compute().

    ``config_elasticity_demand`` is one of the few tested configs with a real coupling
    loop (``airfare_per_rpk`` <-> ``rpk``); it needs ~110 Gauss-Seidel iterations, so
    capping it at 3 stops it well short of its tolerance.

    The cap is set on the *chain*, which cascades it to the inner MDAs. Setting it on
    ``inner_mdas[i].settings`` instead would not survive: see
    ``test_inner_mda_settings_do_not_survive_the_first_execute``.
    """
    process = create_process(configuration_file=CONFIG_DIR / "config_elasticity_demand.yaml")
    assert process.mda_chain.inner_mdas, "this config is supposed to have a coupling loop"

    process.mda_chain.settings.max_mda_iter = 3

    with pytest.raises(MDAConvergenceError):
        process.compute()

    # The outputs are harvested before the check, so a caught failure stays inspectable.
    assert not process.data["vector_outputs"].empty

    process.on_mda_failure = "warn"
    process.compute()


def test_inner_mda_settings_do_not_survive_the_first_execute():
    """Why the tuning handle is the chain, never the inner MDA.

    ``MDAChain_Settings`` cascades ``tolerance``, ``max_mda_iter`` and
    ``log_convergence`` to every inner MDA from a pydantic ``model_validator``, and
    pydantic re-runs it on *any* assignment to the chain's settings. ``MDAChain.execute``
    performs one such assignment -- ``initialize_defaults = False`` -- on its first run.
    So a value written directly on an inner MDA is silently reverted to the chain's the
    moment the chain executes.
    """
    chain = _chain(0.4, max_mda_iter=100)
    chain.inner_mdas[0].settings.max_mda_iter = 3
    assert chain.inner_mdas[0].settings.max_mda_iter == 3

    chain.settings.initialize_defaults = True
    chain.execute()

    assert chain.inner_mdas[0].settings.max_mda_iter == 100
