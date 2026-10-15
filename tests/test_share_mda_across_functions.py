"""``share_mda_across_functions`` on GEMSEO's Sellar problem: same optimum, fewer solves."""

import logging

from gemseo import create_scenario
from gemseo.algos.opt.scipy_local.settings.slsqp import SLSQP_Settings
from gemseo.problems.mdo.sellar.sellar_1 import Sellar1
from gemseo.problems.mdo.sellar.sellar_2 import Sellar2
from gemseo.problems.mdo.sellar.sellar_design_space import SellarDesignSpace
from gemseo.problems.mdo.sellar.sellar_system import SellarSystem

from aeromaps.core.gemseo import share_mda_across_functions


def _sellar(formulation="MDF"):
    scenario = create_scenario(
        [Sellar1(), Sellar2(), SellarSystem()],
        "obj",
        SellarDesignSpace(),
        formulation_name=formulation,
    )
    scenario.add_constraint("c_1", constraint_type="ineq")
    scenario.add_constraint("c_2", constraint_type="ineq")
    scenario.set_differentiation_method("finite_differences")
    return scenario


def _solve(scenario, share):
    """Run the scenario and count how many times its MDA really solved."""
    mda = scenario.formulation.mda
    solves = 0
    solve = mda.execute

    def counted(*args, **kwargs):
        nonlocal solves
        solves += 1
        return solve(*args, **kwargs)

    # Counted beneath the memo, so a memo hit is not a solve.
    mda.execute = counted
    if share:
        share_mda_across_functions(scenario)
    scenario.execute(SLSQP_Settings(max_iter=10))
    return scenario.optimization_result, solves


def test_same_optimum_with_fewer_mda_solves():
    plain, plain_solves = _solve(_sellar(), share=False)
    shared, shared_solves = _solve(_sellar(), share=True)

    assert shared.f_opt == plain.f_opt
    assert (shared.x_opt == plain.x_opt).all()
    # One objective and two constraints differentiated separately: each design point is
    # solved three times without the memo, once with it.
    assert shared_solves < plain_solves / 2


def test_reinstalling_clears_the_memo():
    scenario = _sellar()
    share_mda_across_functions(scenario)
    memo = scenario.formulation.mda._shared_solve_memo
    scenario.execute(SLSQP_Settings(max_iter=2))
    assert memo

    share_mda_across_functions(scenario)
    assert scenario.formulation.mda._shared_solve_memo is memo
    assert not memo


def test_non_mdf_formulation_is_left_alone(caplog):
    scenario = _sellar("IDF")
    with caplog.at_level(logging.WARNING):
        share_mda_across_functions(scenario)
    assert "needs an MDF formulation" in caplog.text


def test_parallel_differentiation_warns(caplog):
    scenario = _sellar()
    scenario.formulation.optimization_problem.parallel_differentiation = True
    with caplog.at_level(logging.WARNING):
        share_mda_across_functions(scenario)
    assert "parallel_differentiation" in caplog.text
