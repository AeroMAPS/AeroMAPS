"""Tests 3.3.a-3.3.j of the step-1 fuel-clearing brief.

The kernel is a pure function, so every test here builds numpy arrays and calls it
directly. Nothing runs an MDA; the one test that compares against the real chain reads
the committed fixture instead (``fuel_clearing_step1/export_reference.py`` regenerates
it).

The analytic case (3.3.a) is the load-bearing one: it is what fixes the dual sign
conventions and the rescaling, neither of which can be settled from documentation.
"""

from __future__ import annotations

import json
import time
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from aeromaps.models.impacts.generic_energy_model.fuel_clearing.kernel import (
    ClearingError,
    ClearingInputs,
    clear_market,
)

FIXTURE_DIR = Path(__file__).parents[1] / "fixtures" / "fuel_clearing"

# Analytic case constants, shared by 3.3.a and the scale test.
COST_KEROSENE = 0.012
COST_SUSTAINABLE = 0.024
DEMAND = 1.0e13
MANDATE = 0.20
CAPACITY = 5.0e12
GAMMA = 2.0
SAT_N = 4.0


def _single_year_case(scale: float = 1.0, **overrides) -> ClearingInputs:
    """One region, one year, two pathways: saturating sustainable + flat kerosene.

    ``scale`` multiplies every *extensive* (energy-dimensioned) quantity, which is what
    test 3.3.i needs: scaling demand alone while holding capacity fixed would change
    the saturation ratio and so legitimately change prices.
    """
    defaults = dict(
        demand=np.array([[DEMAND * scale]]),
        cost=np.array([[[COST_SUSTAINABLE], [COST_KEROSENE]]]),
        is_sustainable=np.array([True, False]),
        mandate_share=np.array([[MANDATE]]),
        buyout_price=np.array([[1.0e3]]),  # far above any marginal cost: must not bind
        capacity=np.array([[[CAPACITY * scale], [np.inf]]]),
        sat_gamma=np.array([[GAMMA, 0.0]]),
        sat_n=SAT_N,
        rampup_limit=np.array([[10.0, 0.0]]),
        rampup_seed=np.array([[DEMAND * scale, 0.0]]),
        q_init=np.array([[0.0, 0.0]]),
        discount_rate=0.0,
        pricing_weight=0.0,
    )
    defaults.update(overrides)
    return ClearingInputs(**defaults)


def _multi_year_case(years: int = 12, **overrides) -> ClearingInputs:
    """One region, a rising mandate, saturation on -- the shape the bench has."""
    demand = np.full((1, years), DEMAND)
    mandate = np.linspace(0.0, 0.5, years)[None, :]
    defaults = dict(
        demand=demand,
        cost=np.broadcast_to(
            np.array([[[COST_SUSTAINABLE], [COST_KEROSENE]]]), (1, 2, years)
        ).copy(),
        is_sustainable=np.array([True, False]),
        mandate_share=mandate,
        buyout_price=np.full((1, years), 0.5),
        capacity=np.broadcast_to(np.array([[[CAPACITY], [np.inf]]]), (1, 2, years)).copy(),
        sat_gamma=np.array([[GAMMA, 0.0]]),
        sat_n=SAT_N,
        rampup_limit=np.array([[0.30, 0.0]]),
        rampup_seed=np.array([[DEMAND * 1e-3, 0.0]]),
        q_init=np.array([[0.0, 0.0]]),
        discount_rate=0.04,
        pricing_weight=0.0,
    )
    defaults.update(overrides)
    return ClearingInputs(**defaults)


def _energy_atol(demand) -> float:
    """The noise floor for a volume comparison, in MJ.

    Clarabel runs at ``solver_tolerance`` (1e-9 by default) on a problem scaled so the
    largest demand is 1, so volumes come back with an absolute error of order
    ``1e-9 * max(demand)`` -- about 1e4 MJ on this bench. Comparing volumes against a
    fixed absolute figure like 1 MJ tests the solver's last bit, not the kernel. Two
    orders of headroom on top.
    """
    return float(np.max(demand)) * 1e-7


def _assert_all_finite(outputs):
    """3.3.h, asserted everywhere rather than in one place."""
    for name in (
        "volume",
        "unmet",
        "energy_price",
        "compliance_price",
        "rampup_price",
        "marginal_price",
        "market_mfsp",
        "average_cost",
        "rent",
    ):
        array = getattr(outputs, name)
        assert np.all(np.isfinite(array)), f"{name} is not finite"


# --- 3.3.a analytic case ----------------------------------------------------------


def test_analytic_case_fixes_signs_and_scaling():
    """One region, one year, saturation known in closed form.

    At the optimum the mandate binds and the buy-out does not, so
    ``q_s = m*D`` and ``q_k = (1-m)*D``. The KKT conditions then give both prices
    exactly:

        energy_price     = c_k                              (kerosene sets the margin)
        compliance_price = c_s*(1 + gamma*(q_s/K)**n) - c_k  (what the mandate costs)

    This is the test that catches a flipped dual sign or a rescaling applied to the
    wrong factor -- both of which produce plausible-looking numbers.
    """
    outputs = clear_market(_single_year_case())

    assert outputs.volume[0, 0, 0] == pytest.approx(MANDATE * DEMAND, rel=1e-6)
    assert outputs.volume[0, 1, 0] == pytest.approx((1 - MANDATE) * DEMAND, rel=1e-6)
    # Relative to demand: an absolute MJ tolerance on a ~1e13 quantity is meaningless.
    assert outputs.unmet[0, 0] / DEMAND < 1e-9

    expected_compliance = (
        COST_SUSTAINABLE * (1 + GAMMA * (MANDATE * DEMAND / CAPACITY) ** SAT_N) - COST_KEROSENE
    )
    # The energy price is the one the equality-dual sign convention gets wrong.
    assert outputs.energy_price[0, 0] == pytest.approx(COST_KEROSENE, rel=1e-6)
    assert outputs.energy_price[0, 0] > 0
    # The compliance dual sits on the curved cone and is the least accurate of the
    # three; 1e-4 relative at the default solver tolerance of 1e-9 (measured 2.2e-5).
    assert outputs.compliance_price[0, 0] == pytest.approx(expected_compliance, rel=1e-4)

    # marginal_price = energy + compliance on the sustainable pathway, energy alone on
    # the other. Nothing else.
    assert outputs.marginal_price[0, 0, 0] == pytest.approx(
        outputs.energy_price[0, 0] + outputs.compliance_price[0, 0], rel=1e-12
    )
    assert outputs.marginal_price[0, 1, 0] == pytest.approx(outputs.energy_price[0, 0], rel=1e-12)
    _assert_all_finite(outputs)


def test_average_cost_is_below_marginal_where_saturation_is_active():
    """The whole point of the soft saturation: an inframarginal rent that is not zero.

    ``average = c*(1 + gamma/(n+1)*(q/K)**n)`` against
    ``marginal = c*(1 + gamma*(q/K)**n)``, so the gap is the rent and it is positive
    exactly where the pathway saturates.
    """
    outputs = clear_market(_single_year_case())
    assert outputs.average_cost[0, 0, 0] < outputs.marginal_price[0, 0, 0]
    assert outputs.rent[0, 0, 0] > 0
    # Kerosene is unsaturated, so its average cost is just its cost, and it earns
    # nothing above it. Judged against its own revenue: rent is an absolute money
    # amount on ~1e13 MJ, so even a 1e-11 error in the dual shows up as hundreds.
    assert outputs.average_cost[0, 1, 0] == pytest.approx(COST_KEROSENE, rel=1e-12)
    revenue = outputs.average_cost[0, 1, 0] * outputs.volume[0, 1, 0]
    assert abs(outputs.rent[0, 1, 0]) / revenue < 1e-6


# --- 3.3.b energy balance ---------------------------------------------------------


def test_energy_balance_is_exact_after_closure():
    """Exact to the MJ, and the correction that made it so stays below tolerance."""
    inputs = _multi_year_case()
    outputs = clear_market(inputs)

    total = outputs.volume.sum(axis=1)
    np.testing.assert_allclose(total, inputs.demand, rtol=0, atol=0)
    assert outputs.diagnostics["max_relative_closure_correction"] < inputs.closure_tolerance
    _assert_all_finite(outputs)


def test_closure_refuses_to_absorb_a_real_imbalance():
    """The closure step exists to absorb solver noise, never an error.

    Driving `closure_tolerance` below the solver's own accuracy makes the correction
    look like an error, and the kernel must then raise rather than silently rewrite
    the residual pathway.
    """
    inputs = _multi_year_case(closure_tolerance=1e-18, solver_tolerance=1e-7)
    with pytest.raises(ClearingError, match="Closing the energy balance"):
        clear_market(inputs)


# --- 3.3.c reproduction against the real chain ------------------------------------


def _reference():
    parquet = FIXTURE_DIR / "reference.parquet"
    if not parquet.exists():  # pragma: no cover - fixture is committed
        pytest.skip("reference fixture missing; run fuel_clearing_step1/export_reference.py")
    table = pd.read_parquet(parquet)
    metadata = json.loads((FIXTURE_DIR / "metadata.json").read_text())
    return table, metadata


def test_reproduces_the_current_mode_given_the_same_shares_as_mandate():
    """3.3.c -- the consistency test between the two modes.

    Mandate set to the reference's realised shares, capacity effectively infinite,
    ramp-up loose and buy-out far above any cost. Under those settings the market has
    exactly one degree of freedom left and it should land on the reference allocation.

    It does so only because kerosene is cheaper than the sustainable pathway in every
    year of this fixture (checked below): where the sustainable fuel is cheaper, the
    market would rightly exceed the mandate and the two modes would differ. That is
    the documented, expected divergence of the brief.
    """
    table, metadata = _reference()
    regions = metadata["regions"]
    sustainable, residual = "hefa_fog", "fossil_kerosene"
    first = metadata["years"]["prospection_start"]
    last = metadata["years"]["end"]

    prospective = table[(table["year"] >= first) & (table["year"] <= last)]
    years = sorted(prospective["year"].unique())

    def stack(column):
        return np.array(
            [
                prospective[prospective["region"] == region].sort_values("year")[column].to_numpy()
                for region in regions
            ]
        )

    demand = stack("energy_demand")
    cost_sustainable = stack(f"{sustainable}_mean_mfsp")
    cost_residual = stack(f"{residual}_mean_mfsp")
    reference_share = stack(f"{sustainable}_share_dropin_fuel") / 100.0

    # The premise of the test. If this ever fails, the divergence below is expected
    # and the assertion on volumes is the wrong one to make.
    assert np.all(cost_residual < cost_sustainable), (
        "Kerosene is not cheaper than the sustainable pathway in every year; the "
        "market would legitimately exceed the mandate and this test's premise breaks."
    )

    shape = (len(regions), 2, len(years))
    inputs = ClearingInputs(
        demand=demand,
        cost=np.stack([cost_sustainable, cost_residual], axis=1),
        is_sustainable=np.array([True, False]),
        mandate_share=reference_share,
        buyout_price=np.full(demand.shape, 1.0e3),
        capacity=np.full(shape, np.inf),  # saturation off
        sat_gamma=np.zeros((len(regions), 2)),
        sat_n=4.0,
        rampup_limit=np.full((len(regions), 2), 1.0e3),  # loose
        rampup_seed=np.tile(demand.max(axis=1)[:, None], (1, 2)),  # loose, and non-zero
        q_init=np.zeros((len(regions), 2)),
        discount_rate=0.04,
        pricing_weight=0.0,
    )
    outputs = clear_market(inputs)
    _assert_all_finite(outputs)

    expected_sustainable = reference_share * demand
    atol = _energy_atol(demand)
    np.testing.assert_allclose(outputs.volume[:, 0, :], expected_sustainable, rtol=1e-6, atol=atol)
    np.testing.assert_allclose(
        outputs.volume[:, 1, :], demand - expected_sustainable, rtol=1e-6, atol=atol
    )
    assert np.allclose(outputs.unmet, 0.0, atol=atol)

    # At w = 0 and with saturation off, market_mfsp is the production cost -- which is
    # exactly what the current mode passes through. This is the bridge between modes.
    np.testing.assert_allclose(outputs.market_mfsp[:, 0, :], cost_sustainable, rtol=1e-10)
    np.testing.assert_allclose(outputs.market_mfsp[:, 1, :], cost_residual, rtol=1e-10)


# --- 3.3.d the buy-out ------------------------------------------------------------


def test_unreachable_mandate_pays_the_buyout_at_its_price():
    """A tight ramp-up against a mandate that outruns it: feasible, and priced at B.

    Without the buy-out this program would simply be infeasible, which is why it is
    always present (decision 7). Where it is used, the compliance price must sit
    exactly at the buy-out price -- that is what caps the dual.
    """
    buyout = 0.35
    inputs = _multi_year_case(
        rampup_limit=np.array([[0.05, 0.0]]),  # 5 %/year against a mandate reaching 50 %
        rampup_seed=np.array([[DEMAND * 1e-4, 0.0]]),
        buyout_price=np.full((1, 12), buyout),
    )
    outputs = clear_market(inputs)
    _assert_all_finite(outputs)

    used = outputs.unmet[0] > _energy_atol(inputs.demand)
    assert used.any(), "the mandate was supposed to outrun the ramp-up"
    np.testing.assert_allclose(outputs.compliance_price[0, used], buyout, rtol=1e-4)
    # And never above it, anywhere: the buy-out is a cap on the dual, not a fee.
    assert np.all(outputs.compliance_price <= buyout * (1 + 1e-6))


# --- 3.3.e ramp-up ----------------------------------------------------------------


def test_realised_growth_respects_the_ramp_up_limit():
    growth_limit = 0.30
    seed = DEMAND * 1e-3
    inputs = _multi_year_case(
        rampup_limit=np.array([[growth_limit, 0.0]]),
        rampup_seed=np.array([[seed, 0.0]]),
    )
    outputs = clear_market(inputs)
    volume = outputs.volume[0, 0, :]

    previous = np.concatenate([inputs.q_init[0, :1], volume[:-1]])
    allowed = seed + (1 + growth_limit) * previous
    assert np.all(volume <= allowed + _energy_atol(inputs.demand))


def test_relative_form_locks_a_pathway_at_zero_without_a_seed():
    """The zero-lock, documented rather than worked around.

    ``q_t <= seed + (1+g) q_{t-1}`` with ``q_init = 0`` and ``seed = 0`` gives
    ``q_t <= 0`` for every t, because ``0 * (1+g) = 0``. A pathway that starts from
    nothing never starts at all, however high the mandate or the buy-out.

    This is not hypothetical on the step-1 bench: its sustainable pathway has
    ``q_init = 0`` (metadata.json records the coercion), so ``rampup_seed`` is
    mandatory there.
    """
    inputs = _multi_year_case(
        rampup_seed=np.array([[0.0, 0.0]]),
        q_init=np.array([[0.0, 0.0]]),
    )
    outputs = clear_market(inputs)

    assert np.allclose(outputs.volume[0, 0, :], 0.0, atol=_energy_atol(inputs.demand))
    # The whole obligation is therefore bought out, at the buy-out price.
    mandated = inputs.mandate_share[0] * inputs.demand[0]
    np.testing.assert_allclose(
        outputs.unmet[0], mandated, rtol=1e-6, atol=_energy_atol(inputs.demand)
    )


def test_share_increment_form_is_accepted_and_binds():
    """The second ramp-up form, which needs demand_init to be defined at t = 0."""
    years = 12
    inputs = _multi_year_case(
        years=years,
        rampup_form="share_increment",
        rampup_limit=np.array([[0.02, 0.0]]),  # +2 points of share per year
        demand_init=np.array([DEMAND]),
    )
    outputs = clear_market(inputs)
    _assert_all_finite(outputs)

    share = outputs.volume[0, 0, :] / inputs.demand[0]
    previous_share = np.concatenate([[0.0], share[:-1]])
    assert np.all(share <= previous_share + 0.02 + 1e-9)


def test_share_increment_without_demand_init_is_refused():
    with pytest.raises(ValueError, match="demand_init"):
        clear_market(_multi_year_case(rampup_form="share_increment"))


# --- 3.3.f price continuity -------------------------------------------------------


def _sweep_compliance_price(points, sat_n, top=1.9):
    """Compliance price in the final year against a multiplier on the mandate.

    The ramp-up is loose on purpose. With the tight one this module uses elsewhere it
    binds before the mandate does, the volume stops responding, the buy-out covers the
    whole gap and the price sits flat on the buy-out for the entire sweep -- measured.
    A flat curve passes any continuity bound while testing nothing, so the regime has
    to be the one where the mandate is what sets the volume.

    ``top`` stops at a 95 % mandate. At 100 % kerosene is driven out of the mix
    entirely and the energy balance changes character, which is a real regime change
    and moves the price by a real step (measured: 7.2x the sweep step at n = 2). That
    is a property of the market, not a defect, and it is not what this test is about.
    """
    base = np.linspace(0.0, 0.5, 12)[None, :]
    factors = np.linspace(0.5, top, points)
    prices = [
        clear_market(
            _multi_year_case(
                mandate_share=np.clip(base * factor, 0.0, 1.0),
                sat_n=sat_n,
                rampup_limit=np.array([[2.0, 0.0]]),
                rampup_seed=np.array([[DEMAND * 0.1, 0.0]]),
                buyout_price=np.full((1, 12), 0.3),
            )
        ).compliance_price[0, -1]
        for factor in factors
    ]
    return np.array(prices)


@pytest.mark.parametrize("sat_n", [2.0, 8.0, 16.0])
def test_compliance_price_is_continuous_in_the_mandate(sat_n):
    """3.3.f -- the dual must not step as the mandate is swept.

    Testing this against a fixed bound needs a magic constant, and a stiff-but-smooth
    curve fails it for the wrong reason. The honest test is refinement: **halving the
    sweep step halves the largest jump between neighbours** if the curve is continuous,
    and leaves it unchanged if there is a genuine discontinuity.

    A hard capacity cap -- what decision 5 rejected -- would show a ratio near 1.
    """
    coarse = _sweep_compliance_price(100, sat_n)
    fine = _sweep_compliance_price(200, sat_n)

    # Guard against passing trivially on a flat curve.
    assert fine.ptp() > 0.01, f"the swept price barely moved ({fine.ptp():.4g}); nothing is tested"

    coarse_jump = np.abs(np.diff(coarse)).max()
    fine_jump = np.abs(np.diff(fine)).max()
    ratio = fine_jump / coarse_jump
    assert ratio < 0.75, (
        f"halving the sweep step took the largest jump from {coarse_jump:.4g} to "
        f"{fine_jump:.4g} (ratio {ratio:.3f}); a continuous price gives about 0.5, a "
        "genuine step stays near 1."
    )


# --- 3.3.g determinism ------------------------------------------------------------


def test_identical_calls_give_bit_identical_outputs_even_when_interleaved():
    inputs = _multi_year_case()
    first = clear_market(inputs)
    # A different problem in between: if anything leaked into module state or the
    # solver were warm-started, this is what would expose it.
    clear_market(_single_year_case())
    second = clear_market(inputs)

    for name in ("volume", "unmet", "energy_price", "compliance_price", "market_mfsp"):
        np.testing.assert_array_equal(
            getattr(first, name), getattr(second, name), err_msg=f"{name} is not reproducible"
        )


# --- 3.3.i scale invariance -------------------------------------------------------


def test_scaling_every_energy_scales_volumes_and_leaves_prices_alone():
    """Demand x1000 -> volumes x1000, prices unchanged.

    Capacity, the ramp-up seed and q_init scale with it: they are energies too, and
    holding capacity fixed while demand grew would change the saturation ratio, which
    *should* change prices.
    """
    base = clear_market(_single_year_case(scale=1.0))
    scaled = clear_market(_single_year_case(scale=1000.0))

    np.testing.assert_allclose(scaled.volume, base.volume * 1000.0, rtol=1e-6)
    np.testing.assert_allclose(scaled.energy_price, base.energy_price, rtol=1e-6)
    np.testing.assert_allclose(scaled.compliance_price, base.compliance_price, rtol=1e-4)
    np.testing.assert_allclose(scaled.market_mfsp, base.market_mfsp, rtol=1e-6)


# --- input hygiene (decision 9) ---------------------------------------------------


def test_a_nan_input_is_refused_by_name():
    inputs = _multi_year_case()
    cost = inputs.cost.copy()
    cost[0, 0, 3] = np.nan
    with pytest.raises(ValueError, match="cost contains NaN"):
        clear_market(_multi_year_case(cost=cost))


def test_a_percentage_mandate_is_refused():
    """The single easiest way to be wrong by a factor of 100, caught at the door."""
    with pytest.raises(ValueError, match="fraction in .0, 1."):
        clear_market(_multi_year_case(mandate_share=np.full((1, 12), 20.0)))


def test_ambiguous_residual_pathway_is_refused():
    """Two non-sustainable pathways and no `residual_pathway`: the closure has no home."""
    years = 12
    with pytest.raises(ValueError, match="residual_pathway could not be inferred"):
        clear_market(
            _multi_year_case(
                cost=np.broadcast_to(
                    np.array([[[COST_SUSTAINABLE], [COST_KEROSENE], [COST_KEROSENE]]]),
                    (1, 3, years),
                ).copy(),
                is_sustainable=np.array([True, False, False]),
                capacity=np.full((1, 3, years), np.inf),
                sat_gamma=np.zeros((1, 3)),
                rampup_limit=np.array([[0.3, 0.0, 0.0]]),
                rampup_seed=np.array([[DEMAND * 1e-3, 0.0, 0.0]]),
                q_init=np.zeros((1, 3)),
            )
        )


# --- 3.4 elasticity ---------------------------------------------------------------


def test_elasticity_is_reported_only_when_asked_for():
    plain = clear_market(_multi_year_case())
    assert "elasticity_at_operating_point" not in plain.diagnostics

    with_elasticity = clear_market(_multi_year_case(compute_elasticity=True))
    elasticity = with_elasticity.diagnostics["elasticity_at_operating_point"]
    assert elasticity.shape == plain.energy_price.shape
    assert np.all(np.isfinite(elasticity))


# --- 3.3.j timings ----------------------------------------------------------------


@pytest.mark.parametrize(
    "regions, pathways, years",
    [(2, 2, 31), (9, 10, 35)],
    ids=["bench_2x2x31", "synthetic_9x10x35"],
)
def test_solve_time_is_reported(regions, pathways, years, capsys):
    """Reports the solve time for the report's section 3.3.j. The bound is a guard
    against an accidental blow-up, not a performance target."""
    rng = np.random.default_rng(0)
    is_sustainable = np.array([i != pathways - 1 for i in range(pathways)])
    demand = np.full((regions, years), DEMAND)
    inputs = ClearingInputs(
        demand=demand,
        cost=COST_SUSTAINABLE * (1 + 0.1 * rng.random((regions, pathways, years))),
        is_sustainable=is_sustainable,
        mandate_share=np.tile(np.linspace(0.0, 0.5, years), (regions, 1)),
        buyout_price=np.full((regions, years), 0.5),
        capacity=np.full((regions, pathways, years), CAPACITY),
        sat_gamma=np.full((regions, pathways), GAMMA),
        sat_n=4.0,
        rampup_limit=np.full((regions, pathways), 0.3),
        rampup_seed=np.full((regions, pathways), DEMAND * 1e-3),
        q_init=np.zeros((regions, pathways)),
        discount_rate=0.04,
    )
    started = time.perf_counter()
    outputs = clear_market(inputs)
    wall = time.perf_counter() - started
    _assert_all_finite(outputs)

    with capsys.disabled():
        print(
            f"\n  {regions}x{pathways}x{years}: "
            f"solve {outputs.diagnostics['solve_seconds']:.3f}s, wall {wall:.3f}s"
        )
    assert wall < 60.0


def test_no_compliance_price_where_there_is_no_obligation():
    """A zero obligation must cost zero to comply with.

    Where ``mandate_share`` is 0 the constraint is ``sum q_s + x >= 0``, which the
    variable bounds already give -- redundant, so the dual is degenerate and the solver
    may report a price for an obligation that does not exist. Measured on the real
    bench before the fix: 0.0112 per MJ in a year with no obligation, roughly the whole
    cost of kerosene, which then flowed into ``market_mfsp`` at any w > 0.
    """
    years = 12
    mandate = np.linspace(0.0, 0.5, years)
    mandate[:4] = 0.0  # a genuine no-obligation window, as ReFuelEU has before 2025
    outputs = clear_market(_multi_year_case(mandate_share=mandate[None, :]))

    assert np.all(outputs.compliance_price[0, :4] == 0.0)
    # And the marginal price of the sustainable pathway falls back to the energy price
    # alone there, instead of carrying a phantom premium.
    np.testing.assert_allclose(
        outputs.marginal_price[0, 0, :4], outputs.energy_price[0, :4], rtol=1e-12
    )
    # The obligation still prices where it exists.
    assert outputs.compliance_price[0, 4:].max() > 0


def test_price_split_is_pinned_under_a_full_obligation():
    """At a 100 % mandate only the SUM of the two duals is determined.

    The obligation then forces every conventional pathway to zero, so the mandate and
    the energy balance have the same active rows and the split slides freely along the
    sum. Left to the solver it produced a NEGATIVE energy price (-0.026 per MJ on the
    continuity bench) and split the same problem two different ways on two runs. A
    100 % sustainable 2050 is an ordinary scenario, so the split is pinned at the limit
    from below instead: the energy price is the cheapest conventional marginal cost,
    the rest is compliance.
    """
    years = 12
    mandate = np.full(years, 1.0)
    outputs = clear_market(_multi_year_case(mandate_share=mandate[None, :]))

    assert outputs.diagnostics["full_mandate_cells"] == years
    # Pinned at the conventional pathway's cost, which is what a buyer would pay for
    # energy if the obligation let them.
    np.testing.assert_allclose(outputs.energy_price[0], COST_KEROSENE, rtol=1e-9)
    assert np.all(outputs.compliance_price[0] >= 0.0)
    # The premium is real: an all-sustainable mandate costs more than kerosene.
    assert outputs.compliance_price[0, -1] > 0.0

    # The sum is what the solver actually determined, and pinning must not have moved
    # it -- everything downstream reads the sum, not the split.
    np.testing.assert_allclose(
        outputs.marginal_price[0, 0],
        outputs.energy_price[0] + outputs.compliance_price[0],
        rtol=1e-12,
    )
    # Approached from below, the split is continuous rather than jumping at the corner.
    just_under = clear_market(_multi_year_case(mandate_share=np.full((1, years), 0.999)))
    np.testing.assert_allclose(
        outputs.energy_price[0, -1], just_under.energy_price[0, -1], rtol=1e-6
    )


# --- complementary slackness, the property behind every degeneracy found so far ------


def _slackness_residuals(inputs, outputs):
    """``lambda * slack`` for each inequality family, in price units over the cost scale.

    Complementary slackness says a multiplier may be non-zero only where its constraint
    is tight. Every dual defect found in this kernel violated it: a compliance price
    where the obligation was zero, a price split where two constraints coincided, a
    multiplier on a constraint that could not bind.

    The normalisation matters. Judging "slack wherever lambda exceeds a threshold"
    reports the slack of any year whose dual carries solver noise, and dividing by
    ``max(lambda)`` blows up precisely in the slack case the check exists for. The
    product, against the cost scale, is stable in both limits.
    """
    scale = float(np.max(inputs.demand))
    cost_scale = float(np.max(inputs.cost))
    sustainable = inputs.is_sustainable

    previous = np.concatenate([inputs.q_init[:, :, None], outputs.volume[:, :, :-1]], axis=2)
    allowance = inputs.rampup_seed[..., None] + (1.0 + inputs.rampup_limit[..., None]) * previous
    rampup_slack = np.maximum((allowance - outputs.volume) / scale, 0.0)[:, sustainable, :]
    rampup = float(np.max(outputs.rampup_price[:, sustainable, :] * rampup_slack) / cost_scale)

    supplied = outputs.volume[:, sustainable, :].sum(axis=1) + outputs.unmet
    mandate_slack = np.maximum((supplied - inputs.mandate_share * inputs.demand) / scale, 0.0)
    mandate = float(np.max(outputs.compliance_price * mandate_slack) / cost_scale)

    return rampup, mandate


@pytest.mark.parametrize(
    "label,overrides",
    [
        ("baseline", {}),
        ("ramp-up so loose it cannot bind", {"rampup_limit": np.array([[1.0e3, 0.0]])}),
        ("seed so large the ramp-up is slack", {"rampup_seed": np.array([[DEMAND, 0.0]])}),
        ("saturation off", {"sat_gamma": np.array([[0.0, 0.0]])}),
        ("tight ramp-up", {"rampup_limit": np.array([[0.10, 0.0]])}),
        ("cheap buy-out", {"buyout_price": np.full((1, 12), 0.02)}),
        ("stiff saturation", {"sat_n": 16.0}),
    ],
)
def test_complementary_slackness_holds_in_every_regime(label, overrides):
    """No price on a constraint that is not tight, whatever the regime.

    Parametrised rather than written once because the degeneracies this guards against
    appeared at the *edges* -- a zero obligation, a full one, a constraint that cannot
    bind -- and a single mid-range case sees none of them.
    """
    inputs = _multi_year_case(**overrides)
    outputs = clear_market(inputs)
    rampup, mandate = _slackness_residuals(inputs, outputs)

    # Clarabel runs at 1e-9 on a scaled problem, so a residual of order 1e-8 is the
    # solver's own accuracy rather than a modelling defect. The phantom compliance
    # price this replaces scored 0.46 on the same measure.
    assert rampup < 1e-6, f"{label}: ramp-up price on a slack constraint ({rampup:.2e})"
    assert mandate < 1e-6, f"{label}: compliance price on a slack mandate ({mandate:.2e})"


def test_capacity_is_inert_when_saturation_is_off():
    """With ``gamma = 0`` the capacity enters no term, so it must change nothing.

    Worth pinning because the capacity is the only input that reaches the objective
    through two guards (``isfinite`` and ``gamma > 0``); a change to either could let a
    capacity silently start mattering in scenarios that declared no saturation.
    """
    base = None
    for capacity in (5.0e12, 1.0e12, 1.0e11, np.inf):
        outputs = clear_market(
            _multi_year_case(
                sat_gamma=np.array([[0.0, 0.0]]),
                capacity=np.broadcast_to(np.array([[[capacity], [np.inf]]]), (1, 2, 12)).copy(),
            )
        )
        signature = np.concatenate(
            [outputs.volume.ravel(), outputs.market_mfsp.ravel(), outputs.compliance_price.ravel()]
        )
        if base is None:
            base = signature
        else:
            np.testing.assert_allclose(signature, base, rtol=0, atol=0)


# --- sub-mandates: a second, narrower obligation -----------------------------------


def _submandate_case(years: int = 12, level: float = 0.15, **overrides):
    """Three pathways: kerosene, a general sustainable one, and a sub-mandated one."""
    demand = np.full((1, years), DEMAND)
    defaults = dict(
        demand=demand,
        cost=np.broadcast_to(
            np.array([[[COST_SUSTAINABLE], [COST_KEROSENE], [COST_SUSTAINABLE * 2]]]),
            (1, 3, years),
        ).copy(),
        is_sustainable=np.array([True, False, True]),
        is_submandated=np.array([False, False, True]),
        mandate_share=np.linspace(0.0, 0.5, years)[None, :],
        submandate_share=np.minimum(np.linspace(0.0, level, years), np.linspace(0.0, 0.5, years))[
            None, :
        ],
        buyout_price=np.full((1, years), 0.5),
        submandate_buyout_price=np.full((1, years), 0.9),
        capacity=np.broadcast_to(
            np.array([[[CAPACITY], [np.inf], [CAPACITY]]]), (1, 3, years)
        ).copy(),
        sat_gamma=np.array([[GAMMA, 0.0, GAMMA]]),
        sat_n=SAT_N,
        rampup_limit=np.array([[0.30, 0.0, 0.60]]),
        rampup_seed=np.array([[DEMAND * 1e-3, 0.0, DEMAND * 2e-2]]),
        q_init=np.array([[0.0, 0.0, 0.0]]),
        discount_rate=0.04,
        pricing_weight=0.0,
        residual_pathway=1,
    )
    defaults.update(overrides)
    return ClearingInputs(**defaults)


def test_submandate_binds_and_is_priced():
    """The narrower obligation is met, and carries its own shadow price."""
    inputs = _submandate_case()
    outputs = clear_market(inputs)

    # The obligation holds every year -- counting the release, which is how an
    # obligation with a buy-out is satisfied when the ramp-up cannot deliver it.
    supplied = outputs.volume[0, 2] + outputs.submandate_unmet[0]
    assert np.all(supplied / inputs.demand[0] - inputs.submandate_share[0] > -1e-7)
    # On this case it is met by BUILDING, not by paying: the ramp-up is loose enough.
    assert outputs.submandate_unmet[0].max() / DEMAND < 1e-6
    # And it costs something where it forces the issue.
    assert outputs.submandate_price[0].max() > 0
    # A sub-mandated pathway carries BOTH multipliers: it relaxes both constraints.
    np.testing.assert_allclose(
        outputs.marginal_price[0, 2],
        outputs.energy_price[0] + outputs.compliance_price[0] + outputs.submandate_price[0],
        rtol=1e-10,
    )
    # The generally-eligible pathway carries only the broad one.
    np.testing.assert_allclose(
        outputs.marginal_price[0, 0],
        outputs.energy_price[0] + outputs.compliance_price[0],
        rtol=1e-10,
    )
    _assert_all_finite(outputs)


def test_absent_submandate_changes_nothing():
    """A scenario without one must solve the program it solved before.

    The sub-mandate adds a constraint, a slack variable and an objective term; this is
    what guarantees they are absent rather than present-and-zero, which would perturb
    the solver path and quietly move every dual.
    """
    plain = clear_market(_multi_year_case())
    assert plain.submandate_price.shape == plain.compliance_price.shape
    assert np.all(plain.submandate_price == 0.0)
    assert np.all(plain.submandate_unmet == 0.0)
    np.testing.assert_allclose(
        plain.marginal_price[0, 0],
        plain.energy_price[0] + plain.compliance_price[0],
        rtol=1e-12,
    )


def test_no_submandate_price_where_there_is_no_subobligation():
    """Same degeneracy as the main mandate, at the same place: a zero obligation."""
    years = 12
    level = np.zeros(years)
    level[6:] = 0.10
    outputs = clear_market(
        _submandate_case(submandate_share=np.minimum(level, np.linspace(0, 0.5, years))[None, :])
    )
    assert np.all(outputs.submandate_price[0, :6] == 0.0)
    assert outputs.submandate_price[0, 6:].max() > 0


def test_submandate_must_be_a_subset_of_the_mandate():
    """A pathway sub-mandated but not eligible makes the two duals incomparable."""
    with pytest.raises(ValueError, match="SUBSET"):
        clear_market(
            _submandate_case(
                is_sustainable=np.array([True, False, False]),
                is_submandated=np.array([False, False, True]),
            )
        )


def test_submandate_cannot_exceed_the_mandate():
    years = 12
    with pytest.raises(ValueError, match="cannot be larger"):
        clear_market(
            _submandate_case(
                mandate_share=np.full((1, years), 0.10),
                submandate_share=np.full((1, years), 0.20),
            )
        )


def test_submandate_inputs_must_come_as_a_pair():
    years = 12
    # A share without the row set: the kernel cannot know what satisfies it.
    with pytest.raises(ValueError, match="is_submandated"):
        clear_market(_submandate_case(is_submandated=None))
    # A row set without a share: an obligation that does not exist.
    with pytest.raises(ValueError, match="no obligation"):
        clear_market(
            _submandate_case(submandate_share=None, is_submandated=np.array([False, False, True]))
        )
    # Neither is not an error -- it is simply a scenario without a sub-mandate.
    outputs = clear_market(_submandate_case(submandate_share=None, is_submandated=None))
    assert np.all(outputs.submandate_price == 0.0)
    assert years == 12


def test_submandate_satisfies_complementary_slackness():
    inputs = _submandate_case()
    outputs = clear_market(inputs)
    scale = float(np.max(inputs.demand))
    cost_scale = float(np.max(inputs.cost))
    supplied = outputs.volume[:, inputs.is_submandated[0], :].sum(axis=1) + outputs.submandate_unmet
    slack = np.maximum((supplied - inputs.submandate_share * inputs.demand) / scale, 0.0)
    residual = float(np.max(outputs.submandate_price * slack) / cost_scale)
    assert residual < 1e-6, f"sub-mandate price on a slack constraint ({residual:.2e})"


# --- the kink: where the price is not a function of cost at all ---------------------
#
# These are the tests behind REPORT.md section 8.6. The failure they describe is the one
# that kept `pricing_weight > 0` from converging, and it is not a solver problem: the
# value function genuinely has a kink, so the multiplier there is an interval rather
# than a number, and no amount of accelerating a fixed-point iteration fixes a quantity
# that has no single value to iterate towards.


def _kinked_case(**overrides):
    """A market whose obligation is met EXACTLY at the ramp-up limit.

    Two pathways, two years. Year 1 carries a 50 % obligation, and the ramp-up allows
    the sustainable pathway exactly 50 % of demand in that year -- no more, no less. The
    two constraints therefore meet at a point, and the compliance price is undetermined
    between them:

    * relax the ramp-up and nothing is saved, because the obligation is already met, so
      the right derivative of the cost is 0;
    * tighten it and the shortfall must be bought out, so the left derivative is
      ``buyout - (c_sust - c_kero)``.

    Any ``lambda_M`` in ``[c_sust - c_kero, buyout]`` satisfies the KKT conditions. The
    program is perfectly well posed; it is the PRICE that is set-valued.
    """
    demand = np.full((1, 2), DEMAND)
    defaults = dict(
        demand=demand,
        cost=np.broadcast_to(np.array([[[COST_SUSTAINABLE], [COST_KEROSENE]]]), (1, 2, 2)).copy(),
        is_sustainable=np.array([True, False]),
        mandate_share=np.array([[0.0, 0.5]]),
        buyout_price=np.full((1, 2), 0.30),
        capacity=np.broadcast_to(np.array([[[np.inf], [np.inf]]]), (1, 2, 2)).copy(),
        sat_gamma=np.array([[0.0, 0.0]]),
        sat_n=SAT_N,
        rampup_form="relative",
        # Year 0 allows the seed; year 1 allows seed + (1+g) * year 0. With g = 0 and
        # seed = 0.25 D that is exactly 0.5 D in year 1: the obligation, to the MJ.
        rampup_limit=np.array([[0.0, 0.0]]),
        rampup_seed=np.array([[0.25 * DEMAND, 0.0]]),
        q_init=np.array([[0.0, DEMAND]]),
        discount_rate=0.0,
        pricing_weight=1.0,
    )
    defaults.update(overrides)
    return ClearingInputs(**defaults)


def test_the_compliance_price_is_an_interval_where_the_two_limits_meet():
    """The kink is real: the volume is pinned, and lambda_M sits strictly inside a range.

    This does not assert a value -- there is no right one. It asserts that the solution
    is on the corner (so the degeneracy is genuinely reached) and that the multiplier the
    solver returns is an arbitrary member of a WIDE interval, which is what makes it
    unusable as the input to a coupling loop.
    """
    inputs = _kinked_case()
    outputs = clear_market(inputs)

    obligation = inputs.mandate_share[0, 1] * DEMAND
    assert outputs.volume[0, 0, 1] == pytest.approx(
        obligation, rel=1e-6
    ), "the case is only degenerate if the ramp-up and the obligation meet exactly"
    assert outputs.unmet[0, 1] == pytest.approx(0.0, abs=1e-3 * DEMAND)

    floor = COST_SUSTAINABLE - COST_KEROSENE
    ceiling = float(inputs.buyout_price[0, 1])
    assert floor <= outputs.compliance_price[0, 1] <= ceiling + 1e-9
    # The interval is 25x the substitution cost. Any point in it is KKT-optimal, so the
    # delivered price at w = 1 is undetermined to within 0.5 * (ceiling - floor) per MJ.
    assert (ceiling - floor) / floor > 20


def test_the_demand_slope_picks_one_point_of_that_interval():
    """Give the balance a slope and the price becomes a number -- the demand's number.

    Stationarity in the demand adjustment reads

        lambda_E + m * lambda_M  =  p0 - a / beta,

    the inverse demand at the quantity served. The check is that identity, to solver
    tolerance, at three anchors chosen to bracket the interval. It is the whole
    mechanism: quantity from supply, price from demand.
    """
    inputs = _kinked_case()
    rigid = clear_market(inputs)
    share = inputs.mandate_share
    slope = (
        0.5 * inputs.demand / np.maximum(rigid.energy_price + share * rigid.compliance_price, 1e-12)
    )

    seen = []
    for factor in (0.8, 1.0, 1.4):
        anchor = (rigid.energy_price + share * rigid.compliance_price) * factor
        outputs = clear_market(replace(inputs, anchor_price=anchor, demand_slope=slope))
        delivered = outputs.energy_price + share * outputs.compliance_price
        implied = anchor - outputs.demand_adjustment / slope
        assert delivered == pytest.approx(
            implied, abs=1e-9
        ), "the delivered marginal price must sit on the demand line it was given"
        seen.append(float(delivered[0, 1]))

    # A different anchor gives a different price: the selection is doing something, and
    # it moves the right way -- a market willing to pay more clears higher.
    assert seen[0] < seen[1] < seen[2]


def test_the_demand_slope_is_inert_at_its_own_fixed_point():
    """Anchored at the price the market itself returns, nothing changes.

    This is why the device is exact rather than a relaxation. A coupling loop using it
    converges to a solution of the UNREGULARISED program or it does not converge at all;
    there is no fixed point at which the slope is still bending the answer.
    """
    inputs = _kinked_case()
    rigid = clear_market(inputs)
    delivered = rigid.energy_price + inputs.mandate_share * rigid.compliance_price
    slope = 0.5 * inputs.demand / np.maximum(delivered, 1e-12)

    outputs = clear_market(replace(inputs, anchor_price=delivered, demand_slope=slope))
    scale = float(np.max(inputs.demand))
    assert np.max(np.abs(outputs.demand_adjustment)) / scale < 1e-7
    assert np.max(np.abs(outputs.volume - rigid.volume)) / scale < 1e-7
    assert outputs.energy_price == pytest.approx(rigid.energy_price, abs=1e-7)


def test_a_rigid_balance_leaves_the_demand_adjustment_at_exactly_zero():
    """Every scenario without a slope must be bit-identical to what it was before."""
    outputs = clear_market(_multi_year_case())
    assert np.all(outputs.demand_adjustment == 0.0)
    assert "max_relative_demand_adjustment" not in outputs.diagnostics


def test_the_demand_curve_needs_both_a_point_and_a_slope():
    inputs = _kinked_case()
    with pytest.raises(ValueError, match="go together"):
        clear_market(replace(inputs, demand_slope=np.full((1, 2), 1.0e15)))
    with pytest.raises(ValueError, match="go together"):
        clear_market(replace(inputs, anchor_price=np.full((1, 2), 0.02)))
    with pytest.raises(ValueError, match="dD/dp"):
        clear_market(
            replace(
                inputs,
                anchor_price=np.full((1, 2), 0.02),
                demand_slope=np.full((1, 2), -1.0),
            )
        )


# --- the proximal anchor, and what it can and cannot do -----------------------------


def test_the_proximal_anchor_is_inert_at_the_solution():
    """Anchoring on the answer returns the answer, at any weight."""
    base = _multi_year_case()
    plain = clear_market(base)
    scale = float(np.max(base.demand))
    for rho in (0.01, 1.0, 10.0):
        outputs = clear_market(replace(base, proximal_anchor=plain.volume, proximal_weight=rho))
        assert np.max(np.abs(outputs.volume - plain.volume)) / scale < 1e-7
        assert outputs.energy_price == pytest.approx(plain.energy_price, abs=1e-7)
        assert outputs.compliance_price == pytest.approx(plain.compliance_price, abs=1e-6)


def test_the_proximal_anchor_cannot_resolve_a_pinned_primal():
    """The negative result, kept because it is what sent the fix to the demand side.

    Where the volume is fixed by a constraint, a penalty on the volume has nothing to
    act on: every candidate dual shares the same primal. Moving the anchor by +/- 50 %
    moves the compliance price across 0.6 % of the interval it is free in -- which is
    why `convergence.py` shows the proximal weight alone still failing to converge, and
    why the fix had to come from the demand side instead.
    """
    inputs = _kinked_case()
    rigid = clear_market(inputs)
    interval = float(inputs.buyout_price[0, 1]) - (COST_SUSTAINABLE - COST_KEROSENE)

    spread = []
    for factor in (0.5, 1.0, 1.5):
        anchor = rigid.volume * factor
        outputs = clear_market(replace(inputs, proximal_anchor=anchor, proximal_weight=1.0))
        assert outputs.volume[0, 0, 1] == pytest.approx(rigid.volume[0, 0, 1], rel=1e-6)
        spread.append(float(outputs.compliance_price[0, 1]))

    assert (max(spread) - min(spread)) / interval < 1e-2


def test_the_proximal_anchor_must_be_a_volume():
    base = _multi_year_case()
    with pytest.raises(ValueError, match="non-negative"):
        clear_market(replace(base, proximal_anchor=-np.ones((1, 2, 12)), proximal_weight=1.0))
    with pytest.raises(ValueError, match="proximal_weight"):
        clear_market(replace(base, proximal_weight=-1.0))


# --- the active set, reported so the coupling loop can be watched -------------------


def test_the_active_signature_is_a_function_of_which_constraints_are_tight():
    """Same active set, same signature; a changed one, a changed signature.

    The signature is what turns "the duals are piecewise" from an inference about a
    residual into an observation (fuel_clearing_step1/convergence.py). It has to be
    stable under a change that does not move the active set, and it has to move under
    one that does -- otherwise it measures noise, or nothing.
    """
    base = _multi_year_case()
    first = clear_market(base)
    again = clear_market(base)
    assert first.diagnostics["active_signature"] == again.diagnostics["active_signature"]

    # Doubling demand leaves every share the same, so the same constraints are tight.
    scaled = clear_market(
        replace(
            base,
            demand=base.demand * 2.0,
            capacity=base.capacity * 2.0,
            rampup_seed=base.rampup_seed * 2.0,
        )
    )
    assert scaled.diagnostics["active_signature"] == first.diagnostics["active_signature"]

    # Removing the obligation cannot leave the same constraints tight: the sustainable
    # pathway drops to zero in every year, so more entries sit on their lower bound.
    # (Its mandate row counts as tight in MORE cells, not fewer -- `sum q_s + x >= 0` is
    # satisfied with equality at q_s = 0. That is the redundant-constraint degeneracy
    # `clear_market` already pins the dual to zero for, visible here from the primal.)
    relaxed = clear_market(replace(base, mandate_share=np.zeros_like(base.mandate_share)))
    assert relaxed.diagnostics["active_signature"] != first.diagnostics["active_signature"]
    assert (
        relaxed.diagnostics["active_counts"]["at_zero"]
        > first.diagnostics["active_counts"]["at_zero"]
    )


# --- scoring the answer against the objective, not against the solver ---------------
#
# The brief's last open item, and the one whose absence cost the most. The saturation
# term was once written in a form that made Clarabel return a point 0.13 % dearer than
# the optimum -- a 3.4 % error in the delivered price -- while reporting `optimal`. All
# 22 tests in the suite at the time passed on it, because every one of them checked a
# property of the returned point and none checked that it was the CHEAPEST point.
#
# A solver status is the solver's opinion of its own work. These helpers form a second
# opinion: recompute the objective in numpy, then go looking for a feasible neighbour
# that beats it.


def _objective(inputs: ClearingInputs, volume, unmet, submandate_unmet=None) -> float:
    """The programme's objective at an arbitrary point, recomputed independently.

    Takes **validated** inputs: `is_sustainable` normalised to ``(R, P)``, the residual
    pathway resolved, the sub-mandate buy-out defaulted. Callers pass
    ``inputs.validate()``, as the kernel does before it builds anything.

    Deliberately written out from the formulation rather than imported from the kernel:
    a second opinion computed by the code under test is not a second opinion. If this
    and the kernel ever disagree about what is being minimised, that disagreement is
    the thing worth finding.
    """
    years = inputs.demand.shape[1]
    discount = (1.0 + inputs.discount_rate) ** -np.arange(years, dtype=float)

    saturating = (
        np.isfinite(inputs.capacity) & (inputs.sat_gamma[..., None] > 0) & (inputs.capacity > 0)
    )
    capacity = np.where(saturating, inputs.capacity, 1.0)
    utilisation = np.where(saturating, np.maximum(volume, 0.0) / capacity, 0.0)
    squeeze = np.where(
        saturating,
        inputs.cost * inputs.sat_gamma[..., None] * capacity / (inputs.sat_n + 1.0),
        0.0,
    ) * utilisation ** (inputs.sat_n + 1.0)

    total = float(np.sum((inputs.cost * volume + squeeze) * discount[None, None, :]))
    total += float(np.sum(inputs.buyout_price * unmet * discount[None, :]))
    if inputs.submandate_share is not None and submandate_unmet is not None:
        total += float(
            np.sum(inputs.submandate_buyout_price * submandate_unmet * discount[None, :])
        )
    return total


def _violation(inputs: ClearingInputs, volume, unmet, submandate_unmet=None) -> float:
    """Largest constraint violation, relative to demand. Zero means feasible.

    Validated inputs, as :func:`_objective`.

    Only the rigid balance is handled; an elastic one moves the right-hand side of both
    the balance and the obligation, and a neighbour search over a moving feasible set
    would be measuring the wrong thing.
    """
    scale = float(np.max(inputs.demand))
    served = inputs.demand
    worst = max(0.0, -float(np.min(volume)) / scale, -float(np.min(unmet)) / scale)
    worst = max(worst, float(np.max(np.abs(volume.sum(axis=1) - served))) / scale)

    supplied = np.where(inputs.is_sustainable[:, :, None], volume, 0.0).sum(axis=1) + unmet
    worst = max(
        worst, float(np.max(np.maximum(inputs.mandate_share * served - supplied, 0.0))) / scale
    )

    if inputs.submandate_share is not None and submandate_unmet is not None:
        narrow = (
            np.where(inputs.is_submandated[:, :, None], volume, 0.0).sum(axis=1) + submandate_unmet
        )
        worst = max(
            worst,
            float(np.max(np.maximum(inputs.submandate_share * served - narrow, 0.0))) / scale,
        )

    # The growth limit applies to rows sustainable in at least one region, as the kernel
    # builds it -- not to rows eligible in this one.
    rows = inputs.is_sustainable.any(axis=0)
    if inputs.rampup_form == "relative" and rows.any():
        previous = np.concatenate([inputs.q_init[:, :, None], volume[:, :, :-1]], axis=2)
        allowed = (
            inputs.rampup_seed[:, :, None] + (1.0 + inputs.rampup_limit[:, :, None]) * previous
        )
        worst = max(worst, float(np.max(np.maximum(volume - allowed, 0.0)[:, rows, :])) / scale)
    return worst


def _cheapest_neighbour(inputs: ClearingInputs, outputs, steps=(3e-2, 3e-3, 3e-4)):
    """Search feasible neighbours of the returned point for a cheaper one.

    Two move families, chosen because they are the two margins the programme trades on:

    * **swap one pathway for another** within a (region, year), which preserves the
      energy balance exactly. This is the direction the suboptimal solve got wrong;
    * **build versus buy out**, in *both* directions: give up a unit of eligible fuel,
      backfill the balance with the residual pathway and pay the release price on the
      shortfall -- or the reverse, build the unit and stop paying. Both are needed. With
      only the first, a solve that over-used the buy-out would pass the search, since
      nothing would propose building instead.

    Returns ``(best_relative_improvement, description)``. A correct solve returns
    something at or below solver noise.
    """
    inputs = inputs.validate()
    scale = float(np.max(inputs.demand))
    base = _objective(inputs, outputs.volume, outputs.unmet, outputs.submandate_unmet)
    regions, pathways, years = inputs.shape
    residual = inputs.residual_pathway
    best, where = 0.0, "none"

    def consider(volume, unmet, label):
        nonlocal best, where
        if _violation(inputs, volume, unmet, outputs.submandate_unmet) > 1e-9:
            return
        value = _objective(inputs, volume, unmet, outputs.submandate_unmet)
        gain = (base - value) / abs(base)
        if gain > best:
            best, where = gain, label

    for step in steps:
        delta = step * scale
        for r in range(regions):
            for t in range(years):
                for source in range(pathways):
                    if outputs.volume[r, source, t] < delta:
                        continue
                    for target in range(pathways):
                        if target == source:
                            continue
                        trial = outputs.volume.copy()
                        trial[r, source, t] -= delta
                        trial[r, target, t] += delta
                        consider(
                            trial, outputs.unmet, f"swap p{source}->p{target} r{r} t{t} @{step:g}"
                        )

                    if inputs.is_sustainable[r, source] and source != residual:
                        trial = outputs.volume.copy()
                        trial[r, source, t] -= delta
                        trial[r, residual, t] += delta
                        relief = outputs.unmet.copy()
                        relief[r, t] += delta
                        consider(trial, relief, f"buy out instead of p{source} r{r} t{t} @{step:g}")

                # ... and the same margin from the other side: stop paying, build.
                if outputs.unmet[r, t] >= delta:
                    for target in range(pathways):
                        if not inputs.is_sustainable[r, target] or target == residual:
                            continue
                        if outputs.volume[r, residual, t] < delta:
                            continue
                        trial = outputs.volume.copy()
                        trial[r, target, t] += delta
                        trial[r, residual, t] -= delta
                        relief = outputs.unmet.copy()
                        relief[r, t] -= delta
                        consider(
                            trial,
                            relief,
                            f"build p{target} instead of buying out r{r} t{t} @{step:g}",
                        )
    return best, where


@pytest.mark.parametrize(
    "label, inputs",
    [
        ("single year, saturating", _single_year_case()),
        ("multi year, rising mandate", _multi_year_case()),
        ("multi year, tight ramp-up", _multi_year_case(rampup_limit=np.array([[0.15, 0.0]]))),
        ("at the kink", _kinked_case()),
    ],
)
def test_the_returned_point_beats_every_feasible_neighbour(label, inputs):
    """No feasible neighbour is cheaper. The check the suite was missing.

    This is what `optimal` does not tell you: the solver's status is its opinion of its
    own work, and the historical failure was a point it called `optimal` that was 0.13 %
    dearer than the optimum.

    **What this is and is not verified to do.** It has teeth --
    ``test_the_neighbour_search_can_actually_detect_a_worse_point`` degrades the answer
    and the search finds its way back. It does not produce false alarms -- across the
    four cases here, a 64-cell scan of (gamma, n, capacity) and the 30-cell bench grid,
    the best neighbour is a loss in every direction.

    It has **not** been shown to catch that specific historical solve. Restoring the
    pre-rewrite saturation term reproduces the other half of that defect -- it refuses
    to solve 13 of 64 scanned settings and 22 of 30 bench cells -- but wherever it does
    solve it returns the same objective to 1e-7, so there is no longer a suboptimal
    point there to catch. The reconstruction is behavioural, not the original code, and
    that is the honest limit of what this test is known to guard.
    """
    outputs = clear_market(inputs)
    gain, where = _cheapest_neighbour(inputs, outputs)
    assert gain < 1e-7, (
        f"{label}: a feasible neighbour is {gain:.3e} cheaper than the returned point "
        f"({where}). The solver reported {outputs.diagnostics['status']!r}."
    )


def test_the_neighbour_search_can_actually_detect_a_worse_point():
    """The guard on the guard: a test that never fails is not a test.

    A deliberately degraded point -- eligible fuel swapped for kerosene down to the
    obligation, which stays feasible -- must be caught. Without this, a bug in
    `_violation` that rejected every neighbour would make the test above vacuous and
    it would pass forever.
    """
    inputs = _multi_year_case().validate()
    outputs = clear_market(inputs)

    # Spoil it by paying the release price where building was cheaper: give up 1 % of
    # demand from the eligible pathway in the FINAL year, backfill with kerosene, and
    # buy out the shortfall. Feasible by construction -- lowering output can only relax
    # a growth limit, the obligation is still met because the buy-out counts towards it,
    # and the final year has no successor whose ramp-up could be tightened. Dearer by a
    # lot: the release price is 0.5 against a substitution cost of about 0.012.
    scale = float(np.max(inputs.demand))
    delta = 0.01 * scale
    last = inputs.demand.shape[1] - 1
    assert outputs.volume[0, 0, last] > delta

    spoiled = outputs.volume.copy()
    spoiled[0, 0, last] -= delta
    spoiled[0, 1, last] += delta
    bought = outputs.unmet.copy()
    bought[0, last] += delta
    assert _violation(inputs, spoiled, bought) < 1e-9, "the spoiled point must be feasible"
    assert _objective(inputs, spoiled, bought) > _objective(inputs, outputs.volume, outputs.unmet)

    degraded = replace(outputs, volume=spoiled, unmet=bought)
    gain, where = _cheapest_neighbour(inputs, degraded)
    assert gain > 1e-4, f"the search failed to find the way back from a spoiled point ({where})"


def test_the_independent_objective_agrees_with_the_solver():
    """The numpy objective must be the same function Clarabel minimised.

    Compared against the solver's own value, undone from the scaling the kernel applies.
    A silent disagreement here would make every assertion above meaningless -- they
    would be scoring a different programme.
    """
    inputs = _multi_year_case()
    inputs = inputs.validate()
    outputs = clear_market(inputs)
    scaled = outputs.diagnostics["objective_scaled"]
    reported = scaled * outputs.diagnostics["energy_scale"] * outputs.diagnostics["cost_scale"]
    independent = _objective(inputs, outputs.volume, outputs.unmet, outputs.submandate_unmet)
    assert independent == pytest.approx(reported, rel=1e-6)
