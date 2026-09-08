"""Turn a target on net emissions into the residual share AeroMAPS parameterises.

Roadmaps usually state offsetting as a destination -- net zero by some year --
rather than as the share of residual emissions that has to be bought each year.
AeroMAPS takes the share. Converting between them is one line of algebra, but it
is worth having in one place because the share is *scenario-specific*: with no
level offset and no manual offset after the handover,

    net = gross * (1 - share / 100)

so recovering the share divides by that scenario's own gross trajectory. Copying
one scenario's schedule onto another therefore does not reproduce its target, and
makes net emissions rise after the handover rather than fall. That is a mistake
this module exists to make hard.

Gross emissions do not depend on offsets, so this is a single pass over committed
outputs rather than an iteration. It does have to be redone whenever a scenario's
gross trajectory changes.
"""

import numpy as np


def residual_share_for_net_target(
    gross, offset, handover_year, net_zero_year, first_year=2000, decimals=4
):
    """The residual-offset share that glides net emissions linearly to zero.

    Up to and including ``handover_year`` the existing offsets are left alone.
    From the year after, net emissions fall on a straight line from their
    handover value to zero at ``net_zero_year``:

        net(t) = net(handover) * (net_zero - t) / (net_zero - handover)

    which is continuous at the handover by construction, monotone, and reaches
    exactly 100 % offsetting at the target year.

    Parameters
    ----------
    gross, offset : sequence of float
        The scenario's gross emissions and its already-modelled offsets, both
        annual series starting at ``first_year``. NaNs in ``offset`` are read as
        zero, since a year with no offset modelled has none.
    handover_year : int
        Last year the existing offsets cover.
    net_zero_year : int
        Year net emissions must reach zero.
    first_year : int, optional
        Year the series begin at.
    decimals : int, optional
        Rounding on the emitted shares.

    Returns
    -------
    (years, shares, net_at_handover)
        ``years`` runs from ``handover_year + 1`` to ``net_zero_year``.
    """
    gross = np.asarray(gross, dtype=float)
    offset = np.nan_to_num(np.asarray(offset, dtype=float))

    if net_zero_year <= handover_year:
        raise ValueError(f"net_zero_year {net_zero_year} must follow handover_year {handover_year}")

    index = handover_year - first_year
    net_at_handover = gross[index] - offset[index]

    years = list(range(handover_year + 1, net_zero_year + 1))
    span = net_zero_year - handover_year
    shares = [
        round(
            100.0
            * (1.0 - (net_at_handover * (net_zero_year - year) / span) / gross[year - first_year]),
            decimals,
        )
        for year in years
    ]
    return years, shares, net_at_handover
