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
