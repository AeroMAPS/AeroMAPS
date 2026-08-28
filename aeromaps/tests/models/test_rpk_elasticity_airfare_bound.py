"""``RPKElasticity`` must stay defined on the airfares an MDA iterate can carry.

A converging fixed-point solver does not only evaluate models at plausible points.
GEMSEO's acceleration methods extrapolate the coupling vector by unconstrained least
squares, so this discipline can be handed an airfare no discipline ever produced -- a
negative one, for instance.

That matters because the multiplier raises the airfare ratio to ``price_elasticity``,
which is fractional. ``numpy`` returns ``nan`` for a negative float64 base, silently,
where plain Python would return a complex number. In the unified-MDA spike this single
operation turned a solver excursion into a chain-wide NaN that the residual then reported
as *convergence*.

**Where that is fixed is the point of this module.** The model does not defend itself.
It declares its physical domain in ``AIRFARE_BOUNDS_RELATIVE`` / ``_coupling_bounds``,
and the process hands that to ``MDAChain.set_bounds``; the solver projects its own
iterate, so wherever the bound applies, the value a discipline receives is the value the
residual is formed on.

The earlier version clipped the airfare at the top of ``compute``. These tests keep that
version around, as ``_clipping_compute``, to show what was wrong with it: a model that
silently substitutes its input computes something other than what the solver believes it
asked for, and the residual cannot tell.

The last two tests pin what the bound does *not* reach. Gauss-Seidel projects the
transformed iterate after the sweep, so a value the producer hands straight to the
consumer within one sweep is unprojected -- which is the case the real chain is in for
``airfare_per_rpk``. There the model returns NaN, and the run fails loudly through
``check_mda_convergence`` rather than quietly returning a saturated number.
"""

import numpy as np
import pandas as pd
import pytest
from gemseo.mda.mda_chain import MDAChain

from aeromaps.core.gemseo import (
    AeroMAPSCustomModelWrapper,
    apply_coupling_bounds,
    freeze_nan_masks_after_first_sweep,
)
from aeromaps.models.air_transport.air_traffic.rpk_market import RPKElasticity

HISTORIC_START, PROSPECTION_START, END = 2000, 2020, 2050
INITIAL_AIRFARE = RPKElasticity.REFERENCE_AIRFARE_PER_RPK
LOW_FACTOR, HIGH_FACTOR = RPKElasticity.AIRFARE_BOUNDS_RELATIVE
ELASTICITY = -0.9


class _Parameters:
    """Minimal stand-in for the process parameters object a model needs to build ``df``."""

    climate_historic_start_year = 1940
    historic_start_year = HISTORIC_START
    prospection_start_year = PROSPECTION_START
    end_year = END


def _series(value):
    return pd.Series(float(value), index=range(HISTORIC_START, END + 1))


def _build():
    return RPKElasticity(
        name="rpk_elasticity",
        passenger_market_ids=["short_range"],
        parameters=_Parameters(),
    )


def _inputs(airfare, initial_airfare=INITIAL_AIRFARE):
    return {
        "rpk_no_elasticity": _series(1.0e12),
        "airfare_per_rpk": airfare,
        "price_elasticity": ELASTICITY,
        "initial_airfare_per_rpk": initial_airfare,
        "rpk_short_range_no_elasticity": _series(1.0e12),
        "short_range_covid_end_year": float(PROSPECTION_START - 1),
    }


def _compute(airfare, initial_airfare=INITIAL_AIRFARE):
    return _build().compute(_inputs(airfare, initial_airfare))


# --------------------------------------------------------------------------------
# The hole, and that the model is honest about it
# --------------------------------------------------------------------------------


def test_a_negative_airfare_still_gives_nan_and_that_is_correct():
    """The model does not defend itself, on purpose.

    ``(negative) ** fractional`` is NaN and this model says so. Keeping the iterate
    physical is the solver's job -- see the bound tests below. A model that quietly
    substituted a different airfare would be computing something the solver never asked
    for, and the residual would be formed on a value the physics never used.
    """
    output = _compute(_series(-2.11))  # the value measured in the spike
    projected = output["elasticity_factor"].loc[PROSPECTION_START:END]
    assert np.isnan(projected.to_numpy()).all()


def test_an_ordinary_airfare_is_used_exactly_as_handed_in():
    output = _compute(_series(INITIAL_AIRFARE * 1.4))
    projected = output["elasticity_factor"].loc[PROSPECTION_START:END]
    assert projected.to_numpy() == pytest.approx(1.4**ELASTICITY)


def test_an_airfare_outside_the_declared_band_is_not_altered_by_the_model():
    """The band is the solver's business; the model applies no saturation of its own."""
    ratio = HIGH_FACTOR * 4
    output = _compute(_series(INITIAL_AIRFARE * ratio))
    projected = output["elasticity_factor"].loc[PROSPECTION_START:END]
    assert projected.to_numpy() == pytest.approx(ratio**ELASTICITY)


def test_a_nan_airfare_stays_nan():
    """A missing value is not a value to invent."""
    airfare = _series(INITIAL_AIRFARE)
    airfare.loc[2041:END] = np.nan
    output = _compute(airfare)
    assert output["elasticity_factor"].loc[2041:END].isna().all()
    assert output["elasticity_factor"].loc[PROSPECTION_START:2040].notna().all()


# --------------------------------------------------------------------------------
# The domain the model declares
# --------------------------------------------------------------------------------


def test_the_model_declares_its_domain_rather_than_enforcing_it():
    model = _build()
    model._initialize_df()

    low, high = model._coupling_bounds["airfare_per_rpk"]
    assert low == pytest.approx(INITIAL_AIRFARE * LOW_FACTOR)
    assert high == pytest.approx(INITIAL_AIRFARE * HIGH_FACTOR)
    assert not hasattr(model, "_warn_if_bounded"), "the model must not police its own input"


def test_the_band_is_wide_enough_to_be_inactive_at_a_solution():
    """A bound active at convergence would move the answer, which it must not."""
    low, high = INITIAL_AIRFARE * LOW_FACTOR, INITIAL_AIRFARE * HIGH_FACTOR
    # The widest range any shipped scenario hands this model, measured across
    # tutorial 08 and the three WCTR elasticity configs.
    assert low < 0.081
    assert high > 0.139


def test_the_declaration_reaches_the_solver():
    """``apply_coupling_bounds`` must actually collect what the model declared."""
    model = _build()
    model._initialize_df()
    discipline = AeroMAPSCustomModelWrapper(model)

    class _Chain:
        def __init__(self):
            self.received = None

        def set_bounds(self, bounds):
            self.received = bounds

    chain = _Chain()
    handed = apply_coupling_bounds(chain, [discipline])

    assert "airfare_per_rpk" in handed
    assert chain.received is not None
    low, high = chain.received["airfare_per_rpk"]
    assert float(low[0]) == pytest.approx(INITIAL_AIRFARE * LOW_FACTOR)
    assert float(high[0]) == pytest.approx(INITIAL_AIRFARE * HIGH_FACTOR)


def test_a_namespace_is_applied_to_the_bounded_name():
    """Each region bounds its own coupling: EU_DOM:airfare is not EU_INT:airfare."""
    model = _build()
    model._initialize_df()
    discipline = AeroMAPSCustomModelWrapper(model)

    class _Chain:
        def set_bounds(self, bounds):
            pass

    handed = apply_coupling_bounds(_Chain(), [discipline], namespace="EU_DOM:")
    assert list(handed) == ["EU_DOM:airfare_per_rpk"]


# --------------------------------------------------------------------------------
# Why clipping inside compute() was the wrong place
# --------------------------------------------------------------------------------


def _clipping_compute(model, input_data):
    """The pre-change body: substitute the airfare, then compute. Nothing else changed."""
    low, high = (
        f * float(input_data["initial_airfare_per_rpk"]) for f in (LOW_FACTOR, HIGH_FACTOR)
    )
    clipped = dict(input_data)
    clipped["airfare_per_rpk"] = input_data["airfare_per_rpk"].clip(low, high)
    return model.compute(clipped)


def test_clipping_made_the_model_answer_a_question_it_was_not_asked():
    """The defect, stated as a measurement.

    The solver's iterate says the airfare is x. With the clip, the physics ran on
    clip(x) while the residual was formed on x. Where the two differ, ``r(x) = 0`` no
    longer means this model is at equilibrium at x -- the fixed point found belongs to a
    different function, and nothing in the residual can reveal the substitution.
    """
    asked = _series(INITIAL_AIRFARE * HIGH_FACTOR * 4)  # what the solver believes it set
    clipped_answer = _clipping_compute(_build(), _inputs(asked))
    honest_answer = _compute(asked)

    clipped_factor = clipped_answer["elasticity_factor"].loc[END]
    honest_factor = honest_answer["elasticity_factor"].loc[END]

    # The old code returned a *plausible* number for an airfare nobody asked about.
    assert clipped_factor == pytest.approx(HIGH_FACTOR**ELASTICITY)
    assert honest_factor == pytest.approx((HIGH_FACTOR * 4) ** ELASTICITY)
    assert clipped_factor != pytest.approx(honest_factor)


def test_the_substitution_left_no_trace_in_any_output():
    """Why it was dangerous rather than merely wrong: nothing downstream could see it.

    ``airfare_per_rpk`` is an input, so a clip applied to it appears in no output
    variable. The only evidence was a warning -- in a notebook that emits thousands.
    """
    inside = _series(INITIAL_AIRFARE * HIGH_FACTOR * 0.999)
    outside = _series(INITIAL_AIRFARE * HIGH_FACTOR * 4)

    clipped_outside = _clipping_compute(_build(), _inputs(outside))
    clipped_inside = _clipping_compute(_build(), _inputs(inside))

    assert set(clipped_outside) == set(clipped_inside)
    assert not any("bound" in name or "clip" in name for name in clipped_outside)


def test_bounding_the_iterate_keeps_residual_and_physics_in_agreement():
    """The property ``set_bounds`` has and the clip did not.

    After projection the iterate itself is inside the band, so the value the discipline
    receives *is* the value the residual is formed on. There is no second, hidden
    airfare.
    """
    low, high = INITIAL_AIRFARE * LOW_FACTOR, INITIAL_AIRFARE * HIGH_FACTOR
    projected = _series(INITIAL_AIRFARE * HIGH_FACTOR * 4).clip(low, high)

    # What the solver would hand in after projecting, and what the model then computes,
    # are the same number -- unlike the clip, where the model saw one and the solver
    # recorded another.
    output = _compute(projected)
    assert output["elasticity_factor"].loc[END] == pytest.approx(HIGH_FACTOR**ELASTICITY)
    assert projected.loc[END] == pytest.approx(high)


# --------------------------------------------------------------------------------
# End to end: the bound closes the hole in a real solve
# --------------------------------------------------------------------------------


LOW, HIGH = INITIAL_AIRFARE * LOW_FACTOR, INITIAL_AIRFARE * HIGH_FACTOR


class _Fare(RPKElasticity):
    """Writes the airfare from the traffic, with an oscillating (negative) gain."""

    def __init__(self, **kwargs):
        super().__init__(name="fare", passenger_market_ids=["short_range"], **kwargs)
        self.input_names = {"rpk": pd.Series([0.0])}
        self.output_names = {"airfare_per_rpk": pd.Series([0.0])}
        self._coupling_bounds = {"airfare_per_rpk": (LOW, HIGH)}

    def _initialize_df(self):
        super(RPKElasticity, self)._initialize_df()
        self._coupling_bounds = {"airfare_per_rpk": (LOW, HIGH)}

    # Loop gain -2.5: the pair oscillates and diverges, so the iterate leaves any band.
    def compute(self, input_data):
        return {"airfare_per_rpk": INITIAL_AIRFARE - 5.0 * (input_data["rpk"] - 0.1)}


class _Demand(RPKElasticity):
    """Writes the traffic from the airfare, closing the loop."""

    def __init__(self, **kwargs):
        super().__init__(name="demand", passenger_market_ids=["short_range"], **kwargs)
        self.input_names = {"airfare_per_rpk": pd.Series([0.0])}
        self.output_names = {"rpk": pd.Series([0.0])}
        self._coupling_bounds = {}

    def _initialize_df(self):
        super(RPKElasticity, self)._initialize_df()
        self._coupling_bounds = {}

    def compute(self, input_data):
        return {"rpk": 0.1 + 0.5 * (input_data["airfare_per_rpk"] - INITIAL_AIRFARE)}


def _loop(bounded, consumer_first):
    """Run the two-discipline loop, recording every airfare the consumer receives.

    ``consumer_first`` decides whether the consumer reads the *projected* iterate from
    the previous iteration or the producer's brand-new output from this sweep. That
    single choice decides whether ``set_bounds`` reaches the model at all -- see the two
    tests below.
    """
    fare = _Fare(parameters=_Parameters())
    demand = _Demand(parameters=_Parameters())
    received = []

    original = demand.compute

    def recording(input_data):
        airfare = input_data["airfare_per_rpk"]
        values = airfare.to_numpy(dtype=float)
        received.append(values[np.isfinite(values)].copy())
        return original(input_data)

    demand.compute = recording

    wrapped = [AeroMAPSCustomModelWrapper(demand), AeroMAPSCustomModelWrapper(fare)]
    if not consumer_first:
        wrapped.reverse()

    for discipline in wrapped:
        for name, seed in (
            ("rpk", _series(0.1)),
            ("airfare_per_rpk", _series(INITIAL_AIRFARE * 1.2)),
        ):
            if name in discipline.io.input_grammar.names:
                discipline.default_input_data.setdefault(name, seed)

    chain = MDAChain(
        disciplines=wrapped,
        inner_mda_name="MDAGaussSeidel",
        tolerance=1e-12,
        max_mda_iter=40,
    )
    freeze_nan_masks_after_first_sweep(chain)
    if bounded:
        apply_coupling_bounds(chain, wrapped)
    # A large over-relaxation makes the transformed iterate overshoot -- the same
    # machinery whose least-squares extrapolation handed the spike -2.11 EUR/RPK.
    chain.inner_mdas[0].over_relaxation_factor = 1.95
    chain.execute()

    return np.concatenate(received) if received else np.array([])


def test_the_bound_reaches_the_model_when_it_reads_the_carried_iterate():
    """When the consumer runs first, it reads last iteration's projected value.

    That value has been through ``SequenceTransformer._project``, so the bound is real
    at the point of use.
    """
    unbounded = _loop(bounded=False, consumer_first=True)
    bounded = _loop(bounded=True, consumer_first=True)

    assert unbounded.min() < LOW - 1e-9 or unbounded.max() > HIGH + 1e-9, (
        "the unbounded loop stayed in band; this no longer reproduces anything"
    )
    assert bounded.min() >= LOW - 1e-9
    assert bounded.max() <= HIGH + 1e-9


def test_the_bound_does_not_reach_the_model_when_the_producer_runs_first():
    """And this is the case the real chain is in, which is worth knowing.

    ``MDAGaussSeidel._iterate_once`` runs the whole sweep and projects the transformed
    iterate *afterwards*. A value the producer computes and hands straight to the next
    discipline in the same sweep never passes through the projection.

    Measured on ``08_use_variable_demand``: a band of (0.099, 0.101), far tighter than
    the airfares the scenario produces, changed nothing at all -- ``RPKElasticity``
    received exactly the same [0.08925, 0.11199] with and without it, and the solve was
    bit-identical. So ``set_bounds`` guards the iterate the solver carries between
    iterations, not every value a discipline sees.
    """
    unbounded = _loop(bounded=False, consumer_first=False)
    bounded = _loop(bounded=True, consumer_first=False)

    assert np.array_equal(unbounded, bounded), (
        "the bound changed what the model received; the sweep order assumption is stale"
    )
