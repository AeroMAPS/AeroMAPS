"""
atag_decomposition
==================
Draw the annual CO2 trajectory decomposed the way ATAG *Waypoint 2050* does it,
rather than the way AeroMAPS does it by default.

AeroMAPS resolves a scenario into demand management, aircraft efficiency, fleet
operations and load factor, and a single "aircraft energy" term. ATAG splits the
same ground differently, and two of the differences matter:

- **aircraft technology is split in two.** Fleet renewal, the roll-out of the
  latest existing generation into the fleet, is separated from next generation
  aircraft technology. The report gives the anchors directly: T0 is the notional
  frozen-fleet efficiency trajectory, and T1 is where emissions would sit "with
  no further improvements in aircraft efficiency and no new technology beyond
  ongoing planned fleet renewal". So T0 -> T1 is fleet renewal, and T1 -> the
  scenario's own technology level is next generation technology.

- **alternative aircraft count as technology, not as energy.** Battery-electric
  and hydrogen aircraft sit in ATAG's next generation technology pillar, while
  AeroMAPS folds them into the energy term alongside SAF. Here the energy term
  is split, and only its drop-in part is reported as SAF.

Both splits are legitimate only because every T-variant and every scenario in
the third edition runs on the same traffic, which is the report's own note that
"each of the T1-T4 scenarios is mapped using the central traffic growth
forecast". Verified against the committed outputs: 2050 RPK is 2.2322e13 in all
of them. Were that not so, T0 and T1 could not be differenced against a
scenario.

The demand wedge AeroMAPS would draw is identically zero here, since traffic is
exogenous in all three editions, so it is absent rather than drawn flat.

Usage::

    from atag_decomposition import plot_atag_decomposition
    plot_atag_decomposition(s1_view, t0_view, t1_view, ax=ax)
"""

import numpy as np

# ATAG's own palette, read off the report's chart.
COLORS = {
    "fleet_renewal": "#d6e4f0",
    "next_generation": "#4a6fb5",
    "operations": "#f5a04c",
    "saf": "#a8c545",
    "market_based": "#b3b3b3",
}
LABELS = {
    "fleet_renewal": "Fleet renewal",
    "next_generation": "Next generation aircraft technology",
    "operations": "Operations and infrastructure",
    "saf": "Sustainable aviation fuel (SAF)",
    "market_based": "Market-based measures",
}

# The aircraft types AeroMAPS folds into the energy term. Anything that is not
# drop-in is an alternative aircraft and belongs in the technology pillar.
ALTERNATIVE = ("hydrogen", "electric")


def _series(view, name):
    """One vector output as a float array."""
    return np.asarray(view.data["vector_outputs"][name], dtype=float)


def _energy_split(view, start_index):
    """Split the energy term into its SAF and alternative-aircraft parts.

    The energy term is the whole effect of the fleet-average carbon intensity
    moving away from its start-year value. Nesting the two causes separates
    them: hold the aircraft-type energy mix at its start-year shares and let
    only the drop-in emission factor move, and what you get is the part SAF is
    responsible for. The remainder, from moving to the mix actually flown, is
    what the alternative aircraft did.

    Returns ``(saf_fraction, alternative_fraction)``, each a share of the total
    intensity reduction, summing to one wherever that reduction is non-zero.
    """
    dropin = _series(view, "energy_consumption_dropin_fuel")
    alternative = sum(_series(view, "energy_consumption_%s" % kind) for kind in ALTERNATIVE)
    total = dropin + alternative

    dropin_factor = _series(view, "dropin_fuel_mean_co2_emission_factor")
    mean_factor = _series(view, "co2_per_energy_mean")

    with np.errstate(invalid="ignore", divide="ignore"):
        start_share = dropin[start_index] / total[start_index]
        start_factor = mean_factor[start_index]

        # Only the drop-in factor moves; the mix stays where it started. The
        # non-drop-in leg keeps the intensity the start-year average implies for
        # it, so that saf_only reduces to start_factor in the start year.
        residual = max(1.0 - start_share, 1e-12)
        alternative_start_intensity = (
            start_factor - start_share * dropin_factor[start_index]
        ) / residual
        saf_only = start_share * dropin_factor + (1.0 - start_share) * alternative_start_intensity

        total_change = start_factor - mean_factor
        saf_change = start_factor - saf_only
        saf_fraction = np.where(np.abs(total_change) > 1e-12, saf_change / total_change, 1.0)

    saf_fraction = np.clip(np.nan_to_num(saf_fraction, nan=1.0), 0.0, 1.0)
    return saf_fraction, 1.0 - saf_fraction


def atag_wedges(view, t0_view, t1_view, start_year=2024, first_year=2000):
    """The ATAG wedge boundaries, top to bottom, as year-indexed arrays.

    Returns ``(years, boundaries)``. Consecutive pairs of ``boundaries`` are the
    wedges; ``boundaries[0]`` is the frozen-fleet baseline, ``boundaries[-2]``
    the gross trajectory and ``boundaries[-1]`` the net one after offsets.
    """
    net = _series(view, "co2_emissions_including_energy")
    years = np.arange(first_year, first_year + len(net))
    start_index = int(start_year - first_year)

    frozen = _series(t0_view, "co2_emissions_including_aircraft_efficiency")
    renewal_only = _series(t1_view, "co2_emissions_including_aircraft_efficiency")
    scenario_technology = _series(view, "co2_emissions_including_aircraft_efficiency")
    after_operations = _series(view, "co2_emissions_including_load_factor")
    offset = _series(view, "carbon_offset")

    _, alternative_fraction = _energy_split(view, start_index)
    energy_term = after_operations - net
    alternative_term = alternative_fraction * energy_term
    operations_term = scenario_technology - after_operations

    # Alternative aircraft are part of the technology pillar, so they are stacked
    # directly under the efficiency gain rather than below operations. Ordering a
    # nested decomposition is a choice, not a fact; taking it in ATAG's order is
    # what keeps the pillar contiguous instead of splitting the band in two.
    after_alternative = scenario_technology - alternative_term
    after_operations_reordered = after_alternative - operations_term

    return years, [
        frozen,
        renewal_only,
        scenario_technology,
        after_alternative,
        after_operations_reordered,
        net,
        net - offset,
    ]


def plot_atag_decomposition(
    view, t0_view, t1_view, ax, start_year=2024, first_year=2000, legend=True, title=None
):
    """Draw the ATAG-style decomposition for one scenario onto ``ax``."""
    years, boundaries = atag_wedges(view, t0_view, t1_view, start_year, first_year)

    # The next generation wedge is drawn in two pieces carrying one label: the
    # efficiency gain beyond fleet renewal, and the alternative aircraft.
    fills = [
        (0, 1, "fleet_renewal", True),
        (1, 2, "next_generation", True),
        (2, 3, "next_generation", False),
        (3, 4, "operations", True),
        (4, 5, "saf", True),
        (5, 6, "market_based", True),
    ]
    for upper, lower, key, labelled in fills:
        ax.fill_between(
            years,
            boundaries[upper],
            boundaries[lower],
            color=COLORS[key],
            label=LABELS[key] if labelled else None,
            linewidth=0,
        )

    historic = years < start_year
    prospective = years >= start_year - 1
    ax.plot(
        years[historic],
        boundaries[5][historic],
        color="black",
        linewidth=2.4,
        label="Historical combustion CO$_2$",
        zorder=5,
    )
    ax.plot(
        years[prospective],
        boundaries[6][prospective],
        color="#8e44ad",
        linestyle="--",
        linewidth=2,
        label="Net CO$_2$ emissions (projection)",
        zorder=5,
    )
    ax.plot(
        years[prospective],
        boundaries[0][prospective],
        color="black",
        linestyle=":",
        linewidth=1.4,
        label="Frozen-fleet baseline (T0)",
        zorder=5,
    )

    ax.set_xlim(years[0], years[-1])
    ax.set_xlabel("Year")
    ax.set_ylabel("Annual CO$_2$ emissions [MtCO$_2$]")
    ax.grid(alpha=0.3)
    if title:
        ax.set_title(title)
    if legend:
        ax.legend(loc="upper left", fontsize=7, framealpha=0.9)
    return ax
