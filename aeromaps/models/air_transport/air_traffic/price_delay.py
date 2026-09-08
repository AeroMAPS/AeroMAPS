"""First-order delay on the price travellers respond to.

Demand does not respond to the spot price of energy. Tickets are bought ahead of
travel, fares adjust progressively to fuel markets, and capacity is committed over
several seasons, so the response is distributed over time. The observed price is
therefore replaced by an effective price that relaxes towards it with a response
time, and it is the effective price that enters the price multiplier.
"""

from math import exp


def apply_price_delay(price, tau, start_year, end_year):
    """Relax ``price`` towards itself with time constant ``tau``, in years.

    The recursion is ``p̃(t) = a·p̃(t-1) + (1-a)·p(t)`` with ``a = exp(-Δt/tau)``
    over an annual step, so the effective price is an exponentially weighted
    memory of past prices rather than the price at a single past instant.

    ``start_year`` must be the first year of the modelled series, not the first
    projected year, and the distinction is the whole point of this function
    living somewhere it can be documented. The recursion has to reach the
    projection carrying the memory the calibration gave it. Starting it at the
    prospection year instead leaves every historic year unfiltered and enters the
    projection from the raw price of a single year, which is not a transient
    error: the price index is anchored on this same series at a reference year
    that sits on that boundary, so a cold start there lands in the denominator of
    the index and shifts the whole projected demand level permanently. Measured
    on the coupled ATAG scenarios it was worth -2.6 % of 2050 traffic under
    SSP2-1.9 and +3.3 % under SSP2-4.5, in opposite directions.

    Because the memory is short, roughly ``tau`` years, the result does not depend
    on how far back the series happens to begin. Starting from 2000, 2010, 2015 or
    2019 gives the same effective price at 2024 to four decimals; only starting
    within about three years of it changes the answer.

    Parameters
    ----------
    price : pandas.Series
        Observed price, indexed by year.
    tau : float
        Response time in years. Zero or negative disables the delay and returns
        the observed price unchanged.
    start_year : int
        First year of the series, used as the initial condition.
    end_year : int
        Last year to filter.

    Returns
    -------
    pandas.Series
        The effective price, over the same index as ``price``.
    """
    delayed = price.copy()
    if not tau or tau <= 0.0:
        return delayed

    a = float(exp(-1.0 / tau))  # annual step, dt = 1 year
    previous = float(price.loc[start_year])
    delayed.loc[start_year] = previous
    for year in range(start_year + 1, end_year + 1):
        previous = a * previous + (1.0 - a) * float(price.loc[year])
        delayed.loc[year] = previous
    return delayed
