"""The fuel-clearing kernel: a convex program that sets volumes and prices.

A **pure function**. Numpy arrays in, numpy arrays out, no AeroMAPS import, no state
of its own. ``FuelClearing.compute()`` calls :func:`clear_market` as it stands; there
is no second implementation to keep in step.

What it solves, over ``R`` regions, ``P`` pathways and ``T`` prospective years, in one
vectorised solve with perfect foresight:

.. code-block:: text

    min  sum_t d_t * [ sum_{r,p} ( c*q + c*gamma/(n+1) * q^(n+1) / K^n )
                       + sum_r B*x ]

    s.t. sum_p q[r,p,t]                    =  D[r,t]           -> energy_price
         sum_{p sust} q[r,p,t] + x[r,t]    >= m[r,t] * D[r,t]  -> compliance_price
         ramp-up, sustainable pathways only                    -> rampup_price
         q >= 0,  x >= 0

Three things about that program are load-bearing.

**One solve, not one per year.** The ramp-up ties year ``t`` to year ``t-1``, so
solving year by year would throw away the anticipation that makes a producer build
ahead of an obligation. Sustainable output above the mandate in early years is a
result, not a bug.

**Convex, so the duals are prices.** The multiplier on the energy balance *is* the
marginal cost of energy and the multiplier on the mandate *is* the compliance price.
They come out certified and independent of the starting point. That is the whole
reason for a dedicated solver rather than a sub-MDA: a fixed point found by iteration
can depend on where it started.

**The ramp-up is a sum, not a max.** The optimisation mode's ramp-up (paper Eq. 12)
is ``q_t <= max{(1+tau) q_{t-1}, q_{t-1} + dE dt}``. A ``max`` of two affine functions
on the *upper* side describes a union of two convex sets, which is not convex, so it
cannot go in here -- see ``fuel_clearing_step1/INVENTORY.md`` section 1.1. The
``"relative"`` form below is its convex outer relaxation: strictly more permissive,
by the smaller of the two branches.

Units and conventions, none of which the arrays carry themselves:

- energies in MJ, costs in currency per MJ, ``mandate_share`` a **fraction in [0, 1]**
  (not a percentage -- validated, because a factor of 100 here would be silent);
- ``capacity`` is ``inf`` for a pathway with no saturation;
- every output is finite. Never NaN, in any code path. A NaN pattern that moves with
  the solution breaks the Gauss-Seidel loop this feeds.
"""

from __future__ import annotations

import time
import warnings
from dataclasses import dataclass, field, replace

import numpy as np

# Anything other than this raises. `optimal_inaccurate` included: an inaccurate dual
# is a wrong price, and it would be indistinguishable from a right one downstream.
_ACCEPTED_STATUS = "optimal"

_RAMPUP_FORMS = ("relative", "share_increment")

# A mandate share this close to 1 is treated as covering all demand. Not a fudge: the
# dual split degenerates exactly at 1, and a share meant to be 100 % routinely arrives
# as 0.9999999999 after a share-sum normalisation upstream.
_FULL_MANDATE_TOLERANCE = 1.0e-9


class ClearingError(RuntimeError):
    """The market did not clear, or cleared to something that fails its own invariants.

    Raised rather than warned on purpose (decision 11): everything downstream of this
    kernel consumes volumes and prices without re-deriving them, so a silent bad
    solution is rescaled CO2 and fuel cost with nothing to catch it.
    """


def _require_cvxpy():
    """Import cvxpy lazily, with an install hint rather than a bare ImportError.

    cvxpy is a test-group dependency, not a core one: the fuel-market mode is opt-in
    and the default mode must not make every AeroMAPS install carry a convex solver.
    """
    try:
        import cvxpy as cp
    except ImportError as exc:  # pragma: no cover - exercised by absence, not by tests
        raise ImportError(
            "The fuel-clearing kernel needs cvxpy and Clarabel, which are not part of "
            "the default AeroMAPS install. Install them with "
            "`poetry install --with test`, or `pip install 'cvxpy>=1.5'`."
        ) from exc
    return cp


@dataclass(frozen=True)
class ClearingInputs:
    """Everything the program needs. Shapes are checked, not assumed.

    Attributes
    ----------
    demand
        ``(R, T)`` total energy demand of the aircraft type the market serves, MJ.
    cost
        ``(R, P, T)`` cost of production per unit energy, at zero saturation. This is
        ``{p}_mean_mfsp`` from the top-down cost model -- already a full cost, capex
        included, which is why capacity carries no cost of its own here.
    is_sustainable
        ``(P,)`` or ``(R, P)`` boolean. True where the pathway counts towards the
        mandate. The per-region form is **eligibility**, not chemistry: the same fuel
        may count towards one jurisdiction's obligation and not another's, which is how
        real mandates differ (feedstock rules, certification, origin). Normalised to
        ``(R, P)`` by :meth:`validate`.

        Eligibility governs the *mandate* only. The ramp-up follows "sustainable in at
        least one region", because a growth limit is an industrial capacity constraint
        and does not change because a jurisdiction declines to count the fuel.
    mandate_share
        ``(R, T)`` minimum sustainable fraction of demand, **in [0, 1]**.
    submandate_share
        ``(R, T)`` or None. A **second, narrower obligation** on a subset of the
        eligible pathways, as a fraction of demand -- ReFuelEU's synthetic-fuel
        sub-target is the motivating case. ``None`` disables it entirely, and the
        kernel then behaves exactly as before.
    is_submandated
        ``(P,)`` or ``(R, P)`` boolean, required when ``submandate_share`` is given.
        Must be a subset of ``is_sustainable``: a fuel that satisfies the narrow
        obligation but not the broad one is not a sub-mandate, it is a second
        unrelated policy, and expressing it this way would make the two duals
        uninterpretable.
    submandate_buyout_price
        ``(R, T)`` or None. Release price for the sub-mandate; defaults to
        ``buyout_price``. Separate because regulators price the two differently, and
        because a shared cap would silently tie the two shadow prices together.
    buyout_price
        ``(R, T)`` price of the release penalty, per unit of missing energy. Caps the
        compliance price. Always present: without it an unreachable mandate makes the
        program infeasible instead of expensive.
    capacity
        ``(R, P, T)`` saturation scale ``K``, MJ. ``inf`` disables saturation for that
        entry. Exogenous at step 1 (decision 4): the top-down cost is a full cost, so
        a capacity variable with no cost of its own would be built without limit.
    sat_gamma
        ``(R, P)`` saturation intensity ``gamma``. Zero disables saturation.
    sat_n
        Saturation stiffness ``n``, a scalar >= 0. Marginal cost is
        ``c * (1 + gamma * (q/K)**n)``; ``n -> inf`` recovers a hard cap, which is
        what the soft form exists to avoid (a hard cap gives a step-function dual,
        and a step-function price whipsaws the traffic loop).
    rampup_form
        ``"relative"`` or ``"share_increment"``.
    rampup_limit
        ``(R, P)`` ``g`` for the relative form, ``delta`` for the share increment.
    rampup_seed
        ``(R, P)`` additive allowance, relative form only. **Not optional in
        practice**: with ``q_init = 0`` and ``seed = 0`` the relative form pins a
        pathway at zero for all time, since ``0 * (1+g) = 0``.
    q_init
        ``(R, P)`` production in the last year before the market acts, MJ. The
        ramp-up's initial condition.
    discount_rate
        Scalar. ``d_t = (1 + discount_rate) ** -t``.
    pricing_weight
        ``w`` of decision 10. ``market_mfsp = (1-w)*average cost + w*marginal price``.
        ``w = 0`` reproduces the current mode's cost pass-through.
    demand_init
        ``(R,)`` demand in the year before the market acts, MJ. Required by
        ``"share_increment"`` only, which is undefined at ``t = 0`` without it.
        **Not in the brief's input table** -- see REPORT.md.
    residual_pathway
        Index of the pathway that absorbs the exact-closure residual, mirroring
        ``EnergyUseChoice``'s ``default``. Inferred when exactly one pathway is
        non-sustainable.
    solver_tolerance
        Passed to Clarabel for primal, dual and gap feasibility.
    closure_tolerance
        Largest relative closure correction accepted before raising. The correction
        absorbs solver noise; it must never absorb an error.
    compute_elasticity
        Re-solve at ``demand * (1 + elasticity_step)`` and report the response.
        Off by default: it doubles the solve.
    elasticity_step
        Relative demand bump used for that finite difference.
    """

    demand: np.ndarray
    cost: np.ndarray
    is_sustainable: np.ndarray
    mandate_share: np.ndarray
    buyout_price: np.ndarray
    capacity: np.ndarray
    sat_gamma: np.ndarray
    sat_n: float
    rampup_limit: np.ndarray
    q_init: np.ndarray
    discount_rate: float = 0.0
    pricing_weight: float = 0.0
    rampup_form: str = "relative"
    rampup_seed: np.ndarray | None = None
    demand_init: np.ndarray | None = None
    residual_pathway: int | None = None
    solver_tolerance: float = 1e-9
    closure_tolerance: float = 1e-6
    compute_elasticity: bool = False
    elasticity_step: float = 1e-3
    submandate_share: np.ndarray | None = None
    is_submandated: np.ndarray | None = None
    submandate_buyout_price: np.ndarray | None = None

    @property
    def shape(self) -> tuple[int, int, int]:
        """``(R, P, T)``."""
        regions, years = np.shape(self.demand)
        return regions, np.shape(self.cost)[1], years

    def validate(self) -> "ClearingInputs":
        """Check shapes, domains and the one ambiguity the closure step cannot resolve.

        Returns a copy with arrays coerced to float64 and the inferable fields filled
        in, so the solve never has to ask these questions again.
        """
        demand = np.asarray(self.demand, dtype=float)
        if demand.ndim != 2:
            raise ValueError(f"demand must be (R, T); got shape {demand.shape}")
        regions, years = demand.shape

        cost = np.asarray(self.cost, dtype=float)
        if cost.shape[0] != regions or cost.shape[2:] != (years,) or cost.ndim != 3:
            raise ValueError(f"cost must be (R, P, T) = ({regions}, P, {years}); got {cost.shape}")
        pathways = cost.shape[1]

        def _check(name: str, array, shape: tuple[int, ...], dtype=float):
            value = np.asarray(array, dtype=dtype)
            if value.shape != shape:
                raise ValueError(f"{name} must have shape {shape}; got {value.shape}")
            return value

        eligibility = np.asarray(self.is_sustainable, dtype=bool)
        if eligibility.shape == (pathways,):
            eligibility = np.broadcast_to(eligibility, (regions, pathways)).copy()
        is_sustainable = _check("is_sustainable", eligibility, (regions, pathways), bool)
        mandate_share = _check("mandate_share", self.mandate_share, (regions, years))
        buyout_price = _check("buyout_price", self.buyout_price, (regions, years))
        capacity = _check("capacity", self.capacity, (regions, pathways, years))
        sat_gamma = _check("sat_gamma", self.sat_gamma, (regions, pathways))
        rampup_limit = _check("rampup_limit", self.rampup_limit, (regions, pathways))
        q_init = _check("q_init", self.q_init, (regions, pathways))

        seed = self.rampup_seed
        rampup_seed = (
            np.zeros((regions, pathways))
            if seed is None
            else _check("rampup_seed", seed, (regions, pathways))
        )

        # A NaN anywhere in the inputs becomes a NaN price, which the coupling loop
        # then reports as converged (the spike's false-convergence failure). Caught
        # here, where the offending array still has a name.
        for name, array in (
            ("demand", demand),
            ("cost", cost),
            ("mandate_share", mandate_share),
            ("buyout_price", buyout_price),
            ("sat_gamma", sat_gamma),
            ("rampup_limit", rampup_limit),
            ("rampup_seed", rampup_seed),
            ("q_init", q_init),
        ):
            if not np.all(np.isfinite(array)):
                raise ValueError(
                    f"{name} contains NaN or inf. The kernel takes zeros, never NaN "
                    "(decision 9); an absent value must be an explicit 0.0."
                )
        # capacity is the one array allowed to be inf -- that is how saturation is
        # switched off -- but never NaN.
        if np.any(np.isnan(capacity)):
            raise ValueError("capacity contains NaN; use inf to disable saturation.")

        if np.any(demand < 0):
            raise ValueError("demand must be non-negative.")
        if np.any(mandate_share < 0) or np.any(mandate_share > 1):
            raise ValueError(
                "mandate_share must be a fraction in [0, 1], not a percentage. "
                f"Got range [{mandate_share.min():.4g}, {mandate_share.max():.4g}]."
            )
        if np.any(buyout_price < 0):
            raise ValueError("buyout_price must be non-negative.")
        if np.any(q_init < 0):
            raise ValueError("q_init must be non-negative.")
        if self.sat_n < 0:
            raise ValueError(f"sat_n must be >= 0; got {self.sat_n}.")
        if self.rampup_form not in _RAMPUP_FORMS:
            raise ValueError(
                f"rampup_form must be one of {_RAMPUP_FORMS}; got {self.rampup_form!r}"
            )
        if not is_sustainable.any():
            raise ValueError(
                "At least one pathway must be sustainable for a mandate to mean anything."
            )

        demand_init = self.demand_init
        if self.rampup_form == "share_increment":
            if demand_init is None:
                raise ValueError(
                    "rampup_form='share_increment' compares shares across years, so it "
                    "needs demand_init (R,) -- the demand of the year before the market "
                    "acts. It is undefined at t=0 without it."
                )
            demand_init = _check("demand_init", demand_init, (regions,))
            if np.any(demand_init <= 0):
                raise ValueError("demand_init must be strictly positive for a share to be defined.")
        elif demand_init is not None:
            demand_init = _check("demand_init", demand_init, (regions,))

        submandate_share = self.submandate_share
        is_submandated = self.is_submandated
        submandate_buyout = self.submandate_buyout_price
        if submandate_share is not None:
            submandate_share = _check("submandate_share", submandate_share, (regions, years))
            if np.any(submandate_share < 0) or np.any(submandate_share > 1):
                raise ValueError("submandate_share must be a fraction in [0, 1].")
            if is_submandated is None:
                raise ValueError(
                    "submandate_share was given without is_submandated: the kernel has no "
                    "way to know which pathways satisfy the narrower obligation."
                )
            narrow = np.asarray(is_submandated, dtype=bool)
            if narrow.shape == (pathways,):
                narrow = np.broadcast_to(narrow, (regions, pathways)).copy()
            is_submandated = _check("is_submandated", narrow, (regions, pathways), bool)
            if not is_submandated.any():
                raise ValueError(
                    "submandate_share is set but no pathway is sub-mandated, so the "
                    "obligation can only ever be met by paying the release price."
                )
            # A sub-mandate is a narrowing of the mandate. Allowing a pathway that
            # satisfies the narrow obligation but not the broad one would make the two
            # duals incomparable: the same unit of fuel would carry one price towards a
            # target it does meet and none towards a target it does not.
            rogue = is_submandated & ~is_sustainable
            if rogue.any():
                where = np.argwhere(rogue)[0]
                raise ValueError(
                    f"Pathway {where[1]} is sub-mandated in region {where[0]} but not "
                    "eligible for the main mandate. A sub-mandate must be a SUBSET of "
                    "the mandate; two unrelated obligations need two separate mandates."
                )
            if np.any(submandate_share > mandate_share + 1e-12):
                where = np.argwhere(submandate_share > mandate_share + 1e-12)[0]
                raise ValueError(
                    f"submandate_share exceeds mandate_share at region {where[0]}, year "
                    f"index {where[1]} ({submandate_share[tuple(where)]:.4g} > "
                    f"{mandate_share[tuple(where)]:.4g}). The narrower obligation cannot "
                    "be larger than the one it narrows."
                )
            submandate_buyout = (
                buyout_price
                if submandate_buyout is None
                else _check("submandate_buyout_price", submandate_buyout, (regions, years))
            )
        elif is_submandated is not None:
            raise ValueError(
                "is_submandated was given without submandate_share; there is no "
                "obligation for it to apply to."
            )

        residual = self.residual_pathway
        if residual is None:
            # A residual must be ineligible EVERYWHERE: it absorbs the balance, so a
            # pathway that counts towards some region's mandate cannot play that part.
            candidates = np.flatnonzero(~is_sustainable.any(axis=0))
            if candidates.size != 1:
                raise ValueError(
                    "residual_pathway could not be inferred: the exact-closure step needs "
                    "exactly one pathway to absorb the residual, and there "
                    f"{'are' if candidates.size else 'is'} {candidates.size} non-sustainable "
                    "pathway(s). Name it explicitly, as EnergyUseChoice's `default` does."
                )
            residual = int(candidates[0])
        elif not 0 <= residual < pathways:
            raise ValueError(f"residual_pathway {residual} out of range for {pathways} pathways.")

        return replace(
            self,
            demand=demand,
            cost=cost,
            is_sustainable=is_sustainable,
            submandate_share=submandate_share,
            is_submandated=is_submandated,
            submandate_buyout_price=submandate_buyout,
            mandate_share=mandate_share,
            buyout_price=buyout_price,
            capacity=capacity,
            sat_gamma=sat_gamma,
            rampup_limit=rampup_limit,
            rampup_seed=rampup_seed,
            q_init=q_init,
            demand_init=demand_init,
            residual_pathway=residual,
        )


@dataclass(frozen=True)
class ClearingOutputs:
    """What the program produced. Every array is finite.

    Attributes
    ----------
    volume
        ``(R, P, T)`` production = consumption, MJ. No trade at step 1.
    unmet
        ``(R, T)`` energy covered by the buy-out instead of by fuel, MJ.
    energy_price
        ``(R, T)`` multiplier on the energy balance, in current (undiscounted) money.
        The **marginal** cost of energy, not the average.
    compliance_price
        ``(R, T)`` multiplier on the mandate. Always <= ``buyout_price``, with
        equality exactly where the buy-out is used.
    rampup_price
        ``(R, P, T)`` multiplier on the ramp-up. Zero for non-sustainable pathways,
        which carry no ramp-up constraint.
    marginal_price
        ``(R, P, T)`` ``energy_price + compliance_price * is_sustainable``.
    market_mfsp
        ``(R, P, T)`` decision 10's blend of average cost and marginal price.
    average_cost
        ``(R, P, T)`` ``c * (1 + gamma/(n+1) * (q/K)**n)``, the average unit cost of
        the volume produced. The gap to ``marginal_price`` is the rent.
    rent
        ``(R, P, T)`` ``(marginal_price - average_cost) * volume``.
    diagnostics
        Status, timings, the closure correction actually applied, and the elasticity
        if it was asked for.
    """

    volume: np.ndarray
    unmet: np.ndarray
    energy_price: np.ndarray
    compliance_price: np.ndarray
    submandate_price: np.ndarray
    submandate_unmet: np.ndarray
    rampup_price: np.ndarray
    marginal_price: np.ndarray
    market_mfsp: np.ndarray
    average_cost: np.ndarray
    rent: np.ndarray
    diagnostics: dict = field(default_factory=dict)


def _saturation_weight(cost, capacity, gamma, sat_n):
    """The saturation cost as ``w * (q/K)**(n+1)``, in utilisation rather than energy.

        integral_0^q c * (1 + gamma * (s/K)**n) ds
            = c*q  +  c*gamma*K/(n+1) * (q/K)**(n+1)

    so ``w = c * gamma * K / (n+1)``, and ``w = 0`` wherever saturation is off.

    The algebraically equivalent form ``a * q**(n+1)`` with ``a = c*gamma/((n+1)*K**n)``
    is what this used to build, and it is numerically unusable. ``a`` carries ``K**-n``,
    so on the bench -- where the smallest scaled capacity is 6e-3 -- the coefficients
    span 4 orders of magnitude at ``n = 2`` and 35 at ``n = 16``, against a power
    variable of the reciprocal size. Clarabel refuses half the (gamma, n) grid that way,
    at every tolerance from 1e-9 to 1e-5. Written in ``q/K`` the argument is order 1
    wherever the term matters and ``w`` stays the size of a cost, which is the whole
    difference between a grid that runs and one that does not.

    Computed with ``np.where`` guards rather than relying on ``inf ** n``: at ``n = 0``
    that is ``1.0``, which would silently switch saturation back *on* for a pathway
    whose capacity says it has none.
    """
    active = np.isfinite(capacity) & (gamma[..., None] > 0) & (capacity > 0)
    safe_capacity = np.where(active, capacity, 1.0)
    weight = np.where(active, cost * gamma[..., None] * safe_capacity / (sat_n + 1.0), 0.0)
    inverse_capacity = np.where(active, 1.0 / safe_capacity, 0.0)
    return weight, inverse_capacity, active


def _average_cost(cost, volume, capacity, gamma, sat_n):
    """``c * (1 + gamma/(n+1) * (q/K)**n)`` -- total cost over volume, not marginal."""
    active = np.isfinite(capacity) & (gamma[..., None] > 0) & (capacity > 0)
    safe_capacity = np.where(active, capacity, 1.0)
    ratio = np.where(active, np.maximum(volume, 0.0) / safe_capacity, 0.0)
    return cost * (1.0 + np.where(active, gamma[..., None] / (sat_n + 1.0) * ratio**sat_n, 0.0))


def _solve_scaled(inputs: ClearingInputs, energy_scale: float, cost_scale: float):
    """Build and solve the program in scaled units. Returns raw scaled results.

    Scaling is not cosmetic. Energies are ~1e13 MJ and costs ~1e-2 per MJ, which puts
    about 15 orders of magnitude between the objective's terms and makes an interior
    point method's convergence test meaningless. Both are normalised to order 1 here
    and put back afterwards by the caller.

    The duals need only the *cost* factor on the way back: the scaled objective is
    ``J/(c0*E0)`` and the scaled balance is in ``D/E0``, so
    ``dJ/dD = c0 * d(J~)/d(D~)``.
    """
    cp = _require_cvxpy()

    regions, pathways, years = inputs.shape
    rows = regions * pathways

    demand = inputs.demand / energy_scale
    cost = inputs.cost / cost_scale
    capacity = inputs.capacity / energy_scale
    buyout = inputs.buyout_price / cost_scale
    q_init = inputs.q_init / energy_scale
    seed = inputs.rampup_seed / energy_scale

    discount = (1.0 + inputs.discount_rate) ** -np.arange(years, dtype=float)

    # (R, P, T) -> (R*P, T). Row r*P + p is region r, pathway p.
    def flatten(array):
        return array.reshape(rows, years)

    q = cp.Variable((rows, years), nonneg=True, name="volume")
    x = cp.Variable((regions, years), nonneg=True, name="unmet")

    # --- objective -----------------------------------------------------------
    linear = cp.sum(cp.multiply(flatten(cost) * discount[None, :], q))
    objective = linear + cp.sum(cp.multiply(buyout * discount[None, :], x))

    weight, inverse_capacity, active = _saturation_weight(
        cost, capacity, inputs.sat_gamma, inputs.sat_n
    )
    saturating = flatten(active)
    if saturating.any():
        # Only the saturating entries get a cone. The rest carry a zero weight and would
        # contribute nothing, but power() builds its cone tree per entry regardless, so
        # masking is what keeps the program the size of the problem rather than the size
        # of the array -- on the bench, a quarter of the entries.
        utilisation = cp.multiply(flatten(inverse_capacity)[saturating], q[saturating])
        # power() with exponent > 1 is convex on the non-negative orthant, and the
        # argument is a non-negative constant times a non-negative variable.
        objective = objective + (flatten(weight) * discount[None, :])[saturating] @ cp.power(
            utilisation, inputs.sat_n + 1.0
        )

    # --- constraints ---------------------------------------------------------
    # Selector matrices, so each family is ONE constraint whose dual comes back with
    # the (R, T) shape the outputs want, instead of R*T separate scalar constraints.
    region_of_row = np.repeat(np.arange(regions), pathways)
    balance_selector = np.zeros((regions, rows))
    balance_selector[region_of_row, np.arange(rows)] = 1.0

    mandate_selector = np.zeros((regions, rows))
    # Two different row sets. The MANDATE counts only what each region declares
    # eligible; the RAMP-UP applies wherever the pathway is eligible anywhere, since an
    # industrial growth limit is not a policy choice.
    sustainable_rows = inputs.is_sustainable.ravel()
    rampup_rows = np.tile(inputs.is_sustainable.any(axis=0), regions)
    mandate_selector[region_of_row, np.arange(rows)] = sustainable_rows.astype(float)

    energy_balance = balance_selector @ q == demand
    mandate = mandate_selector @ q + x >= cp.multiply(inputs.mandate_share, demand)
    constraints = [energy_balance, mandate]

    # The sub-mandate is the same shape of constraint on a narrower row set, with its
    # own slack and its own release price. Built only when asked for, so a scenario
    # without one solves the identical program it did before.
    submandate = None
    x_sub = None
    if inputs.submandate_share is not None:
        submandate_selector = np.zeros((regions, rows))
        submandate_selector[region_of_row, np.arange(rows)] = inputs.is_submandated.ravel().astype(
            float
        )
        x_sub = cp.Variable((regions, years), nonneg=True, name="unmet_submandate")
        submandate = submandate_selector @ q + x_sub >= cp.multiply(inputs.submandate_share, demand)
        constraints.append(submandate)
        objective = objective + cp.sum(
            cp.multiply((inputs.submandate_buyout_price / cost_scale) * discount[None, :], x_sub)
        )

    # --- ramp-up, sustainable pathways only ----------------------------------
    sustainable_index = np.flatnonzero(rampup_rows)
    rampup = None
    if sustainable_index.size:
        q_sustainable = q[sustainable_index, :]
        # (S, 1) columns, one per sustainable (region, pathway) row.
        initial = q_init.reshape(rows, 1)[sustainable_index]
        growth = inputs.rampup_limit.reshape(rows, 1)[sustainable_index]
        # Year t-1 of the decision variable, with the initial condition in front.
        # A single-year horizon has no lagged term at all, and an empty (S, 0) slice
        # is squeezed by hstack rather than concatenated -- so it is built separately.
        previous = initial if years == 1 else cp.hstack([initial, q_sustainable[:, :-1]])

        if inputs.rampup_form == "relative":
            allowance = seed.reshape(rows, 1)[sustainable_index]
            # A SUM, not a max. See the module docstring.
            rampup = q_sustainable <= allowance + cp.multiply(1.0 + growth, previous)
        else:
            # q_t / D_t <= q_{t-1} / D_{t-1} + delta, rearranged so it stays affine:
            #   q_t <= (D_t / D_{t-1}) * q_{t-1} + D_t * delta
            demand_rows = demand[region_of_row][sustainable_index, :]
            previous_demand = np.hstack(
                [
                    (inputs.demand_init / energy_scale)[region_of_row][sustainable_index, None],
                    demand_rows[:, :-1],
                ]
            )
            rampup = (
                q_sustainable
                <= cp.multiply(demand_rows / previous_demand, previous) + demand_rows * growth
            )
        constraints.append(rampup)

    problem = cp.Problem(cp.Minimize(objective), constraints)

    context = (
        f"Shapes R={regions}, P={pathways}, T={years}; "
        f"sat_n={inputs.sat_n}, rampup_form={inputs.rampup_form!r}, "
        f"max mandate share {inputs.mandate_share.max():.4g}, "
        f"max gamma {inputs.sat_gamma.max():.4g}, "
        f"solver_tolerance {inputs.solver_tolerance:.1e}."
    )

    started = time.perf_counter()
    try:
        problem.solve(
            solver=cp.CLARABEL,
            tol_gap_abs=inputs.solver_tolerance,
            tol_gap_rel=inputs.solver_tolerance,
            tol_feas=inputs.solver_tolerance,
        )
    except cp.error.SolverError as exc:
        # Clarabel can fail outright rather than return a status -- a stiff saturation
        # (large gamma and n together) is enough to do it. Callers sweeping parameters
        # must be able to catch that the same way they catch a refused status, so it
        # does not escape as a bare cvxpy exception.
        raise ClearingError(
            f"The fuel market did not clear: the solver failed ({exc}). {context}"
        ) from exc
    elapsed = time.perf_counter() - started

    if problem.status != _ACCEPTED_STATUS:
        raise ClearingError(
            f"The fuel market did not clear: solver status {problem.status!r} "
            f"(only {_ACCEPTED_STATUS!r} is accepted -- an inaccurate dual is a wrong "
            f"price). {context}"
        )

    return {
        "q": np.asarray(q.value).reshape(regions, pathways, years),
        "x": np.asarray(x.value),
        "energy_dual": np.asarray(energy_balance.dual_value),
        "mandate_dual": np.asarray(mandate.dual_value),
        "submandate_dual": None if submandate is None else np.asarray(submandate.dual_value),
        "x_sub": None if x_sub is None else np.asarray(x_sub.value),
        "rampup_dual": None if rampup is None else np.asarray(rampup.dual_value),
        "sustainable_index": sustainable_index,
        "discount": discount,
        "status": problem.status,
        "solve_seconds": elapsed,
        "objective": float(problem.value),
    }


def clear_market(inputs: ClearingInputs) -> ClearingOutputs:
    """Clear the fuel market over every region and year at once.

    Parameters
    ----------
    inputs
        See :class:`ClearingInputs`. Validated here, not assumed.

    Returns
    -------
    ClearingOutputs
        Volumes, the three price families, and diagnostics.

    Raises
    ------
    ClearingError
        If the solver returns anything but ``optimal``, or if closing the energy
        balance exactly would need a correction larger than ``closure_tolerance``.
    ValueError
        If the inputs are the wrong shape, out of domain, or carry a NaN.
    """
    inputs = inputs.validate()
    regions, pathways, years = inputs.shape

    # Order-1 scaling for the solver; undone below. Both factors are strictly
    # positive: a zero here would divide the whole program by zero.
    energy_scale = float(np.max(inputs.demand))
    if energy_scale <= 0:
        raise ValueError("demand is zero everywhere; there is no market to clear.")
    fossil = ~inputs.is_sustainable.any(axis=0)
    reference_cost = inputs.cost[:, fossil, :] if fossil.any() else inputs.cost
    cost_scale = float(np.mean(reference_cost))
    if not np.isfinite(cost_scale) or cost_scale <= 0:
        raise ValueError(f"Reference cost must be finite and positive; got {cost_scale}.")

    solved = _solve_scaled(inputs, energy_scale, cost_scale)

    volume = solved["q"] * energy_scale
    unmet = solved["x"] * energy_scale
    discount = solved["discount"]

    # Duals come back discounted (the objective carries d_t) and in scaled money.
    # Dividing by d_t puts them in the current money of their own year, which is what
    # every consumer of a price expects.
    to_current_price = cost_scale / discount[None, :]

    # The equality's dual is NEGATED, and only the equality's. cvxpy forms
    # L = f + lambda'(Sq - D) for `Sq == D`, so dL/dD = -lambda: the shadow price of
    # demand is minus the reported dual. The inequalities (mandate, ramp-up) are
    # reported as non-negative multipliers on the slack and need no flip. Fixed by the
    # analytic case in test_kernel.py, which is the only reliable way to settle this.
    energy_price = -solved["energy_dual"] * to_current_price
    compliance_price = solved["mandate_dual"] * to_current_price

    # Where the obligation is zero the mandate constraint reads `sum q_s + x >= 0`,
    # which the variable bounds already guarantee. It is redundant, so the KKT system
    # is degenerate there: the solver may hang the multiplier on the mandate instead of
    # on the non-negativity bounds, and report a compliance price for an obligation
    # that does not exist. Measured on the bench: up to 0.0112 per MJ in 2020-2023,
    # about the whole cost of kerosene, in years with no obligation at all. It is not
    # harmless -- it flows into `marginal_price` and so into `market_mfsp` at any
    # w > 0, and it makes the dual depend on how many regions were solved at once.
    #
    # Complying with nothing costs nothing. A dual solution with lambda_M = 0 always
    # exists when the obligation is zero, so this restores the meaningful KKT value
    # rather than overriding the solver.
    compliance_price = np.where(inputs.mandate_share > 0, compliance_price, 0.0)

    # Same construction, same degeneracy, same remedy: where the narrower obligation is
    # zero its constraint is implied by the variable bounds, so the multiplier is free
    # and lambda = 0 is the meaningful member of that set.
    if solved["submandate_dual"] is None:
        submandate_price = np.zeros((regions, years))
        submandate_unmet = np.zeros((regions, years))
    else:
        submandate_price = solved["submandate_dual"] * to_current_price
        submandate_price = np.where(inputs.submandate_share > 0, submandate_price, 0.0)
        submandate_unmet = solved["x_sub"] * energy_scale

    # The mirror image, at the other end. Where the obligation covers ALL demand, the
    # mandate `sum q_s + x >= D` and the balance `sum q = D` have the same active rows:
    # every excluded pathway is forced to zero by the obligation rather than by cost.
    # Only the SUM of the two duals is then determined -- the split slides freely along
    # it. Measured on the continuity bench at a 100 % mandate: the sum is smooth through
    # the corner (0.21527 -> 0.21600) while the energy price flips to -0.026 per MJ, and
    # two runs of the *same* problem split it differently (-0.02054, -0.02070).
    #
    # A 100 % sustainable 2050 is an ordinary AeroMAPS scenario, not a corner case, so
    # this cannot be left to the solver. The split is pinned at the limit approached
    # from below: while a conventional pathway is still available, the energy price is
    # its marginal cost -- which at zero volume is its base cost, saturation being a
    # function of q/K -- and everything above it is the cost of compliance. Where the
    # obligation excludes nothing (every pathway sustainable) the mandate is implied by
    # the balance instead, and lambda_M = 0 is the meaningful value, exactly as above.
    # The sum is preserved to the last bit either way, so `marginal_price`,
    # `market_mfsp` and `rent` are untouched by this.
    full_mandate = inputs.mandate_share >= 1.0 - _FULL_MANDATE_TOLERANCE
    if full_mandate.any():
        total = energy_price + compliance_price
        # Per region: the cheapest pathway that region's own obligation excludes.
        excluded = ~inputs.is_sustainable
        pinned = np.where(
            excluded.any(axis=1)[:, None],
            np.min(np.where(excluded[:, :, None], inputs.cost, np.inf), axis=1),
            total,
        )
        # lambda_M stays a multiplier: non-negative, and capped by the buy-out, which is
        # what releases the obligation in the first place.
        share = np.clip(total - pinned, 0.0, inputs.buyout_price)
        compliance_price = np.where(full_mandate, share, compliance_price)
        energy_price = np.where(full_mandate, total - share, energy_price)
        diagnostics_full_mandate = int(np.count_nonzero(full_mandate))
    else:
        diagnostics_full_mandate = 0

    rampup_price = np.zeros((regions * pathways, years))
    if solved["rampup_dual"] is not None:
        # to_current_price is (1, T), so it broadcasts over the sustainable rows.
        rampup_price[solved["sustainable_index"], :] = solved["rampup_dual"] * to_current_price
    rampup_price = rampup_price.reshape(regions, pathways, years)

    # --- exact closure of the energy balance ---------------------------------
    # The solver satisfies the balance to its own tolerance, not to the last MJ. The
    # residual pathway absorbs the remainder so that sum_p E_p == demand exactly --
    # the invariant nothing downstream re-derives or checks (INVENTORY.md 3.1).
    residual = inputs.residual_pathway
    others = np.sum(np.delete(volume, residual, axis=1), axis=1)
    closed = inputs.demand - others
    correction = closed - volume[:, residual, :]
    scale = np.where(inputs.demand > 0, inputs.demand, np.nan)
    relative_correction = np.abs(correction) / scale
    worst = (
        float(np.nanmax(relative_correction)) if np.any(np.isfinite(relative_correction)) else 0.0
    )
    if worst > inputs.closure_tolerance:
        where = np.unravel_index(np.nanargmax(relative_correction), relative_correction.shape)
        raise ClearingError(
            f"Closing the energy balance needs a relative correction of {worst:.3e} at "
            f"region {where[0]}, year index {where[1]}, above the tolerance of "
            f"{inputs.closure_tolerance:.1e}. The closure step absorbs solver noise; a "
            "correction this large is an error in the program, not rounding."
        )
    volume[:, residual, :] = np.maximum(closed, 0.0)

    # --- prices and rent -----------------------------------------------------
    # A sub-mandated unit satisfies the narrow obligation AND the broad one, so it
    # carries both multipliers. That is not double counting: they price two distinct
    # constraints, and a unit of e-fuel genuinely relaxes both.
    marginal_price = energy_price[:, None, :] + (
        compliance_price[:, None, :] * inputs.is_sustainable[:, :, None]
    )
    if inputs.is_submandated is not None:
        marginal_price = marginal_price + (
            submandate_price[:, None, :] * inputs.is_submandated[:, :, None]
        )
    average_cost = _average_cost(
        inputs.cost, volume, inputs.capacity, inputs.sat_gamma, inputs.sat_n
    )
    weight = inputs.pricing_weight
    market_mfsp = (1.0 - weight) * average_cost + weight * marginal_price
    rent = (marginal_price - average_cost) * volume

    outputs = [
        volume,
        unmet,
        energy_price,
        compliance_price,
        submandate_price,
        rampup_price,
        marginal_price,
        market_mfsp,
        average_cost,
        rent,
    ]
    for name, array in zip(
        (
            "volume",
            "unmet",
            "energy_price",
            "compliance_price",
            "submandate_price",
            "rampup_price",
            "marginal_price",
            "market_mfsp",
            "average_cost",
            "rent",
        ),
        outputs,
    ):
        if not np.all(np.isfinite(array)):
            raise ClearingError(
                f"Output {name!r} is not finite. The kernel emits zeros, never NaN "
                "(decision 9); this is a bug in the kernel, not in its inputs."
            )

    diagnostics = {
        "status": solved["status"],
        "solve_seconds": solved["solve_seconds"],
        "objective_scaled": solved["objective"],
        "energy_scale": energy_scale,
        "cost_scale": cost_scale,
        "max_relative_closure_correction": worst,
        "rampup_form": inputs.rampup_form,
        "sat_n": inputs.sat_n,
        "pricing_weight": weight,
        # How many (region, year) cells had their price split pinned rather than taken
        # from the solver. Zero in any scenario short of a full obligation.
        "full_mandate_cells": diagnostics_full_mandate,
    }

    if inputs.compute_elasticity:
        # The elasticity is a DIAGNOSTIC (section 3.4, off by default), computed by
        # re-solving at a bumped demand. That second solve is strictly harder than the
        # first -- it perturbs the active set of a program already sitting on a stiff
        # power cone -- and it can fail where the primary one succeeded. Letting it
        # raise would destroy a perfectly good solution to protect a measurement of it.
        # So the failure is recorded and warned about, not propagated.
        try:
            diagnostics["elasticity_at_operating_point"] = _elasticity(inputs, market_mfsp, volume)
        except ClearingError as exc:
            diagnostics["elasticity_error"] = str(exc)
            warnings.warn(
                "The market cleared, but the elasticity diagnostic's re-solve at "
                f"demand x (1 + {inputs.elasticity_step:g}) did not: {exc} "
                "The solution itself is unaffected; 'elasticity_at_operating_point' "
                "is absent from the diagnostics.",
                stacklevel=2,
            )

    return ClearingOutputs(
        volume=volume,
        unmet=unmet,
        energy_price=energy_price,
        compliance_price=compliance_price,
        submandate_price=submandate_price,
        submandate_unmet=submandate_unmet,
        rampup_price=rampup_price,
        marginal_price=marginal_price,
        market_mfsp=market_mfsp,
        average_cost=average_cost,
        rent=rent,
        diagnostics=diagnostics,
    )


def _delivered_price(market_mfsp, volume):
    """Volume-weighted mean market MFSP per region and year.

    Years with no volume take the unweighted mean rather than zero: a zero would
    invent a price where there is none, and a NaN would travel (the zero-traffic
    DOC-means fix made the same choice).
    """
    total = np.sum(volume, axis=1)
    weighted = np.sum(market_mfsp * volume, axis=1)
    return np.where(
        total > 0, weighted / np.where(total > 0, total, 1.0), np.mean(market_mfsp, axis=1)
    )


def _elasticity(inputs: ClearingInputs, market_mfsp, volume):
    """``d ln(mean delivered price) / d ln(demand)``, **at the operating point**.

    A local finite difference on a program whose active set can change, so it is a
    diagnostic of the current solution and not a property of the market. Named that
    way everywhere on purpose.
    """
    step = inputs.elasticity_step
    bumped = clear_market(
        replace(
            inputs,
            demand=inputs.demand * (1.0 + step),
            compute_elasticity=False,
        )
    )
    base_price = _delivered_price(market_mfsp, volume)
    bumped_price = _delivered_price(bumped.market_mfsp, bumped.volume)
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(base_price > 0, bumped_price / base_price, 1.0)
        elasticity = np.log(np.where(ratio > 0, ratio, 1.0)) / np.log1p(step)
    return np.where(np.isfinite(elasticity), elasticity, 0.0)
