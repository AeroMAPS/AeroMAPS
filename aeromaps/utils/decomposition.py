"""Decompose a scenario's CO2 trajectory into mitigation wedges.

AeroMAPS resolves a scenario into demand management, aircraft efficiency, fleet
operations and load factor, and a single "aircraft energy" term. Roadmaps such as
ATAG *Waypoint 2050* split the same ground differently, and this module draws the
boundaries their way, because a reproduction has to be comparable to the thing it
reproduces. Two differences matter:

- **aircraft technology can be split in two.** Fleet renewal, the roll-out of the
  latest existing generation into the fleet, is separated from next generation
  aircraft technology. That split needs counterfactual runs to anchor it: a
  frozen-technology trajectory and a renewal-only one. Pass them as ``anchors``.
- **alternative aircraft can count as technology, not as energy.** Battery-electric
  and hydrogen aircraft sit in ATAG's next generation technology pillar, while
  AeroMAPS folds them into the energy term alongside SAF. Here the energy term is
  split so that only its drop-in part is reported as fuel.

``anchors`` generalises the first point. It takes the trajectories that bound the
technology pillar from above, outermost first:

``()``
    No technology pillar. The chart starts at the scenario's own post-technology
    emissions, which is all a scenario without counterfactual runs can support.
``(frozen,)``
    One technology pillar, from the frozen baseline down to what the scenario
    achieves.
``(frozen, renewal_only)``
    Two pillars, fleet renewal then next generation technology. This is the ATAG
    convention and the default framing of the plots built on this module.

Both splits are only legitimate when the anchor runs share the scenario's traffic,
since otherwise the difference between them is demand rather than technology. The
caller owns that: in the third-edition ATAG reproduction it holds because the
report maps T1-T4 onto the central traffic forecast, verified at 2.2322e13 RPK in
every one of them.

The demand wedge AeroMAPS would draw is identically zero wherever traffic is
exogenous, so it is absent rather than drawn flat.
"""

import numpy as np

# ATAG's own palette, read off the report's chart, and its pillar names. Both are
# defaults: a caller drawing a different roadmap's decomposition overrides them
# rather than editing this module.
DEFAULT_COLORS = {
    "fleet_renewal": "#d6e4f0",
    "next_generation": "#4a6fb5",
    # Used in place of the renewal/next-generation pair when fewer than two
    # anchors are given and the technology pillar cannot be split.
    "technology": "#4a6fb5",
    "operations": "#f5a04c",
    "fuel": "#a8c545",
    "market_based": "#b3b3b3",
}
DEFAULT_LABELS = {
    "fleet_renewal": "Fleet renewal",
    "next_generation": "Next generation aircraft technology",
    "technology": "Aircraft technology",
    "operations": "Operations and infrastructure",
    "fuel": "Sustainable aviation fuel (SAF)",
    "market_based": "Market-based measures",
}

# The aircraft types AeroMAPS folds into the energy term. Anything that is not
# drop-in is an alternative aircraft and belongs in the technology pillar.
ALTERNATIVE = ("hydrogen", "electric")

# Read this before quoting a wedge as a lever's contribution.
ORDER_DEPENDENCE = """
A wedge chart does not measure what each lever contributed. It measures what
each lever contributed *given an order*, and the order is chosen by whoever
draws it. The levers overlap: SAF and a battery-electric fleet both decarbonise
the same joule, so whichever is peeled off first is credited with it and the
other is credited with what is left.

Measured on the third edition's S2 at 2050, where the energy term is
1475.1 MtCO2:

    ordering                        SAF          alternative aircraft
    SAF first                    1468.9 Mt                    6.3 Mt
    alternative aircraft first   1257.1 Mt                  218.1 Mt
    Shapley value                1363.0 Mt                  112.2 Mt

The fleet is identical in all three rows. Nothing physical distinguishes them;
only the order does, and it moves the alternative-aircraft pillar by a factor of
35. The same fleet change in T4, where no SAF competes for the credit, is worth
247.0 Mt.

The lever table shows the same effect across runs rather than across orderings:
a lever removes a fixed *proportion* of whatever remains when it is applied, so
its value in Mt is set by the levers ordered before it. Operations takes
11.6703 % of the post-technology baseline in the standalone O3 run and in both
S1 and S2, identical to six decimal places, which is 275.6 Mt in the first case
and 242.6 Mt in the other two.

This module takes the alternative leg first, because the figure stacks
alternative aircraft above SAF and an attribution that contradicts its own
drawing order is simply wrong. That makes the choice defensible, not canonical.
The total is determinate; the split is not, and a single quoted percentage is
meaningless without the ordering that produced it. A roadmap's own headline
lever percentages are produced by this construction and inherit the same
indeterminacy.
"""


def _series(view, name, missing_ok=False):
    """One vector output as a float array, whatever shape the view stores.

    A committed JSON read raw gives a list or a year-keyed dict; a ``ResultsView``
    rebuilds a DataFrame, so the same name gives a Series. All three are accepted
    because both callers exist in this repository.

    ``missing_ok`` returns zeros instead of raising. Use it only where absence
    genuinely means zero: a scenario deploying no hydrogen or battery-electric
    aircraft may never write those consumption columns at all, and reading that
    as "none flown" is right, whereas a missing emissions column is a broken run.
    """
    outputs = view.data["vector_outputs"]
    try:
        raw = outputs[name]
    except KeyError:
        if not missing_ok:
            raise
        reference = outputs["co2_emissions_including_energy"]
        return np.zeros(len(reference), dtype=float)
    if isinstance(raw, dict):
        raw = list(raw.values())
    return np.asarray(raw, dtype=float)


def _energy_split(view, start_index):
    """Split the energy term into its drop-in and alternative-aircraft parts.

    The energy term is the whole effect of the fleet-average carbon intensity
    moving away from its start-year value. Nesting the two causes separates
    them: hold the aircraft-type energy mix at its start-year shares and let
    only the drop-in emission factor move, and what you get is the part the fuel
    is responsible for. The remainder, from moving to the mix actually flown, is
    what the alternative aircraft did.

    Returns ``(fuel_fraction, alternative_fraction)``, each a share of the total
    intensity reduction, summing to one wherever that reduction is non-zero.

    **The result depends on the order, and the order is a choice.** See
    ORDER_DEPENDENCE at the top of this module before quoting any wedge as a
    lever's contribution.
    """
    dropin = _series(view, "energy_consumption_dropin_fuel")
    alternative = sum(
        _series(view, "energy_consumption_%s" % kind, missing_ok=True) for kind in ALTERNATIVE
    )
    total = dropin + alternative

    dropin_factor = _series(view, "dropin_fuel_mean_co2_emission_factor")
    mean_factor = _series(view, "co2_per_energy_mean")

    with np.errstate(invalid="ignore", divide="ignore"):
        start_factor = mean_factor[start_index]
        total_change = start_factor - mean_factor

        # The alternative leg is evaluated first, against the start-year
        # intensity, so that it is credited with displacing the fuel that was
        # actually being burned rather than whatever the mandate had already
        # replaced. Its own factor is recovered from the fleet average rather
        # than assumed:
        # mean = (dropin * factor_dropin + alternative * factor_alt) / total.
        alternative_share = np.divide(alternative, total, out=np.zeros_like(total), where=total > 0)
        factor_alt = np.divide(
            mean_factor * total - dropin_factor * dropin,
            alternative,
            out=np.full_like(total, start_factor),
            where=alternative > 0,
        )
        alternative_change = alternative_share * (start_factor - factor_alt)
        alternative_fraction = np.where(
            np.abs(total_change) > 1e-12, alternative_change / total_change, 0.0
        )

    alternative_fraction = np.clip(np.nan_to_num(alternative_fraction, nan=0.0), 0.0, 1.0)
    return 1.0 - alternative_fraction, alternative_fraction


def pillar_totals(view, anchors=(), year=2050, start_year=2024, first_year=2000):
    """What each pillar removes in ``year``, plus the gross residual.

    The wedge boundaries carry the technology pillar in two pieces, the efficiency
    gain and the alternative aircraft, because the figure stacks them as one
    contiguous band above the fuel. A table reports the pillar, so the two are
    added back together here.

    Returns ``(pillars, gross)``. The pillars and the gross residual sum to the
    outermost anchor, which is what makes the decomposition a partition: with the
    ATAG anchors that is the frozen-fleet baseline.
    """
    years, boundaries = mitigation_wedges(view, anchors, start_year, first_year)
    index = int(np.where(years == year)[0][0])
    wedges = [boundaries[k][index] - boundaries[k + 1][index] for k in range(len(boundaries) - 2)]
    gross = boundaries[-2][index]

    if len(anchors) >= 2:
        # fleet renewal, then efficiency and alternative aircraft merged, then the
        # rest as drawn.
        merged = [wedges[0], wedges[1] + wedges[2], *wedges[3:]]
    elif len(anchors) == 1:
        merged = [wedges[0] + wedges[1], *wedges[2:]]
    else:
        merged = list(wedges)
    return merged, gross


def mitigation_wedges(view, anchors=(), start_year=2024, first_year=2000):
    """The wedge boundaries, top to bottom, as year-indexed arrays.

    Parameters
    ----------
    view
        The scenario to decompose: a process, or a view over committed outputs.
    anchors
        Trajectories bounding the technology pillar from above, outermost first.
        See the module docstring: ``()``, ``(frozen,)`` or ``(frozen, renewal)``.
    start_year
        Year the energy split is measured against, normally the prospection start.
    first_year
        Year the stored series begin at, used to turn years into indices.

    Returns
    -------
    (years, boundaries)
        Consecutive pairs of ``boundaries`` are the wedges. ``boundaries[-2]`` is
        the gross trajectory and ``boundaries[-1]`` the net one after offsets, so
        the pair between them is what market-based measures are assumed to remove.
    """
    net = _series(view, "co2_emissions_including_energy")
    years = np.arange(first_year, first_year + len(net))
    start_index = int(start_year - first_year)

    scenario_technology = _series(view, "co2_emissions_including_aircraft_efficiency")
    after_operations = _series(view, "co2_emissions_including_load_factor")
    offset = _series(view, "carbon_offset")

    upper = [_series(anchor, "co2_emissions_including_aircraft_efficiency") for anchor in anchors]

    # An intermediate anchor is only a valid split point when the scenario is at
    # least as efficient as it, i.e. frozen >= renewal_only >= scenario. For the
    # frozen scenario itself, scenario_technology == frozen, which puts
    # renewal_only *below* both and would make one of the two wedges negative
    # (fleet renewal +473.8, next generation -473.8, in the ATAG third edition).
    # Clamping each intermediate anchor between its neighbours keeps every wedge
    # non-negative there and is a no-op wherever the ordering already holds.
    for position in range(1, len(upper)):
        low = scenario_technology if position == len(upper) - 1 else upper[position + 1]
        upper[position] = np.clip(
            upper[position],
            np.minimum(low, upper[position - 1]),
            np.maximum(low, upper[position - 1]),
        )

    _, alternative_fraction = _energy_split(view, start_index)
    energy_term = after_operations - net
    alternative_term = alternative_fraction * energy_term
    operations_term = scenario_technology - after_operations

    # Alternative aircraft are part of the technology pillar, so they are stacked
    # directly under the efficiency gain rather than below operations. Ordering a
    # nested decomposition is a choice, not a fact; taking it in the roadmap's
    # order is what keeps the pillar contiguous instead of splitting the band in
    # two.
    after_alternative = scenario_technology - alternative_term
    after_operations_reordered = after_alternative - operations_term

    return years, [
        *upper,
        scenario_technology,
        after_alternative,
        after_operations_reordered,
        net,
        net - offset,
    ]
