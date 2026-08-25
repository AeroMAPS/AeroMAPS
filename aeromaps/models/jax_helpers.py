"""
JAX helper functions for AeroMAPS models.

These helpers mirror the pandas-based utilities of ``aeromaps.models.base``
(``aeromaps_interpolation_function``, ``aeromaps_leveling_function``) with pure
``jax.numpy`` implementations, so that model ``jax_compute`` methods are
traceable by JAX (jit + autodiff) when wrapped in a
:class:`~aeromaps.core.jax_wrapper.AeroMAPSJAXModelWrapper`.

Conventions
-----------
* All year-indexed quantities are represented as flat arrays over the model's
  full year index ``range(historic_start_year, end_year + 1)``.
* Years for which the pandas implementation leaves the DataFrame cell unset
  are filled with NaN, matching the NaN produced by partially-assigned
  DataFrame columns.
* Reference years/periods are treated as *static* (Python ints known at trace
  time) while reference *values* may be traced (they can be design variables).
"""

import jax
import jax.numpy as jnp
import numpy as np

jax.config.update("jax_enable_x64", True)


def years_index(model) -> np.ndarray:
    """Return the model's full year index as a static numpy array."""
    return np.arange(model.historic_start_year, model.end_year + 1)


def jax_interpolation_function(
    model,
    reference_years,
    reference_years_values,
    positive_constraint: bool = False,
):
    """JAX equivalent of ``aeromaps_interpolation_function`` (linear method only).

    Returns a full-length array (over the model years index) with NaN before the
    interpolation start year, mirroring the partially-assigned DataFrame column
    of the pandas implementation.

    ``reference_years`` must be static (list/array of Python numbers), while
    ``reference_years_values`` may be a traced JAX array.
    """
    years = years_index(model)
    values = jnp.asarray(reference_years_values, dtype=jnp.float64)

    if len(reference_years) == 0:
        start = model.prospection_start_year
        out = jnp.full(years.shape, values[0])
    else:
        ref_years = np.asarray(reference_years, dtype=np.float64)
        # Same convention as the pandas helper: interpolation starts at the
        # first reference year when it differs from prospection_start_year.
        start = (
            int(ref_years[0])
            if int(ref_years[0]) != model.prospection_start_year
            else model.prospection_start_year
        )
        # jnp.interp keeps edge values constant outside the reference range,
        # matching the "last value used as a constant" behaviour.
        out = jnp.interp(jnp.asarray(years, dtype=jnp.float64), ref_years, values)

    if positive_constraint:
        out = jnp.maximum(out, 0.0)

    return jnp.where(years >= start, out, jnp.nan)


def jax_leveling_function(model, reference_periods, reference_periods_values):
    """JAX equivalent of ``aeromaps_leveling_function``.

    Step function: value ``v_i`` on ``[p_i, p_{i+1})``, with the last value
    extended up to ``end_year`` and NaN before ``p_0`` (or the value repeated
    from ``prospection_start_year`` when no periods are given).

    ``reference_periods`` must be static, ``reference_periods_values`` may be
    a traced JAX array.
    """
    years = years_index(model)
    values = jnp.asarray(reference_periods_values, dtype=jnp.float64)

    if len(reference_periods) == 0:
        out = jnp.full(years.shape, values[0])
        return jnp.where(years >= model.prospection_start_year, out, jnp.nan)

    periods = np.asarray(reference_periods, dtype=np.float64)
    idx = np.clip(np.searchsorted(periods, years, side="right") - 1, 0, len(reference_periods) - 2)
    out = values[idx]
    return jnp.where(years >= periods[0], out, jnp.nan)


def hist_mask(model) -> np.ndarray:
    """Static boolean mask of historic years (before prospection_start_year)."""
    years = years_index(model)
    return years < model.prospection_start_year


def prosp_mask(model) -> np.ndarray:
    """Static boolean mask of prospective years (>= prospection_start_year)."""
    return ~hist_mask(model)


def year_pos(model, year) -> int:
    """Static position of ``year`` in the model's full year index."""
    return int(year) - model.historic_start_year


def climate_years_index(model) -> np.ndarray:
    """Return the model's climate year index as a static numpy array."""
    return np.arange(model.climate_historic_start_year, model.end_year + 1)


def climate_year_pos(model, year) -> int:
    """Static position of ``year`` in the model's climate year index.

    Climate-indexed series start at ``climate_historic_start_year``, earlier
    than the model index, so they need their own offset.
    """
    return int(year) - model.climate_historic_start_year


def jax_scalar_root(residual, x0, n_iter: int = 60):
    """Differentiable scalar root find, JAX counterpart of ``scipy.optimize.fsolve``.

    Newton iterations (fixed count, so the loop is traceable) wrapped in
    :func:`jax.lax.custom_root`: the forward pass is the Newton solve and the
    derivative comes from the implicit function theorem on ``residual``, which
    is both exact and independent of the iteration count.
    """
    # GEMSEO may hand over size-1 arrays rather than scalars, and jax.grad needs
    # a scalar-valued function.
    original_residual = residual

    def residual(x):
        return jnp.reshape(original_residual(x), ())

    grad_residual = jax.grad(residual)

    def solve(fun, x_init):
        def step(_, x):
            step_size = fun(x) / grad_residual(x)
            # Guard against a vanishing derivative stalling or blowing up the step.
            return x - jnp.where(jnp.isfinite(step_size), step_size, 0.0)

        return jax.lax.fori_loop(0, n_iter, step, x_init)

    def tangent_solve(g, y):
        return y / jax.grad(g)(0.0)

    return jax.lax.custom_root(residual, jnp.asarray(x0, dtype=jnp.float64), solve, tangent_solve)


def jax_interp_backfill(model, reference_years, reference_years_values, hist_value=None):
    """Interpolation with historic years backfilled.

    Mirrors the common pandas pattern: interpolate over the prospective window,
    then set historic years to ``hist_value`` (or, by default, to the value at
    ``prospection_start_year``).
    """
    out = jax_interpolation_function(model, reference_years, reference_years_values)
    hist = hist_mask(model)
    if hist_value is None:
        hist_value = out[year_pos(model, model.prospection_start_year)]
    return jnp.where(hist, hist_value, out)


def jax_first_order_lag(model, values, tau):
    """First-order lag applied over the prospective years.

    Mirrors the pandas recursion ``y[k] = a * y[k-1] + (1 - a) * x[k]`` with
    ``a = exp(-1 / tau)`` (annual step), seeded at ``prospection_start_year`` and
    leaving the historic years untouched. ``tau <= 0`` disables the lag.
    """
    values = jnp.asarray(values)
    if not tau or tau <= 0.0:
        return values

    a = float(np.exp(-1.0 / tau))
    start = year_pos(model, model.prospection_start_year)
    seed = values[start]

    def step(previous, value):
        current = a * previous + (1.0 - a) * value
        return current, current

    _, tail = jax.lax.scan(step, seed, values[start + 1 :])
    return jnp.concatenate([values[:start], jnp.array([seed]), tail])


def jax_scalar_value(value):
    """Return ``value`` as a 0-d array when it holds a single number, else ``None``.

    GEMSEO passes scalar variables as plain floats when executing but as size-1
    arrays when linearizing, so models reading a per-year input have to accept
    both spellings of "one value for every year".
    """
    value = jnp.asarray(value)
    if value.ndim == 0:
        return value
    if value.size == 1:
        return value.reshape(())
    return None


def jax_vintage_windows(n_years: int, duration: int):
    """Index grids of the ``duration``-year window opened by each vintage year.

    Returns ``(positions, clamped, age)`` where ``positions[y, j] = y + j`` are
    the absolute positions of vintage ``y``'s window, ``clamped`` caps them at
    the last modelled year (the pandas loops reuse the last year's value beyond
    the horizon) and ``age`` is ``j``, the number of years since commissioning.
    """
    age = jnp.arange(duration)
    positions = jnp.arange(n_years)[:, None] + age[None, :]
    return positions, jnp.minimum(positions, n_years - 1), age


def jax_extended_carbon_price(carbon_price, positions, clamped):
    """Carbon price over vintage windows, extrapolated past the last model year.

    Beyond ``end_year`` the pandas models keep the growth rate of the last
    modelled year, which is what the ``future_scc_growth`` branch expresses.
    """
    carbon_price = jnp.asarray(carbon_price)
    last = carbon_price.shape[0] - 1
    future_growth = carbon_price[last] / carbon_price[last - 1]
    return jnp.where(
        positions <= last,
        carbon_price[clamped],
        carbon_price[last] * future_growth ** (positions - last),
    )


def jax_discounted_abatement_vals(
    n_years: int,
    discount_rate,
    duration: int,
    extra_cost_non_fuel,
    extra_cost_fuel,
    cac_reference_mfsp,
    cac_reference_co2_emission_factor,
    emissions_reduction,
    exogenous_carbon_price_trajectory,
    zero_guard: bool = False,
):
    """Specific / generic specific abatement cost of every vintage year at once.

    Vectorised form of the ``_get_discounted_vals`` loops shared by the
    operations and fleet abatement-cost models: each vintage year discounts its
    costs and avoided emissions over a ``duration``-year window, reusing the last
    modelled year's values beyond ``end_year`` and extrapolating the carbon price
    at the last modelled growth rate.

    ``zero_guard`` mirrors the NaN the operations model returns on a null
    cumulated abatement; the fleet models divide unguarded.
    """
    positions, clamped, age = jax_vintage_windows(n_years, int(duration))
    discount = (1.0 + discount_rate) ** (-age)

    extra_cost_non_fuel = jnp.asarray(extra_cost_non_fuel)
    extra_cost_fuel = jnp.asarray(extra_cost_fuel)
    cac_reference_mfsp = jnp.asarray(cac_reference_mfsp)
    cac_reference_co2_emission_factor = jnp.asarray(cac_reference_co2_emission_factor)
    emissions_reduction = jnp.asarray(emissions_reduction)
    exogenous_carbon_price_trajectory = jnp.asarray(exogenous_carbon_price_trajectory)

    mfsp_ratio = cac_reference_mfsp[clamped] / cac_reference_mfsp[:, None]
    discounted_cumul_cost = jnp.sum(
        (extra_cost_non_fuel[:, None] + extra_cost_fuel[:, None] * mfsp_ratio) * discount[None, :],
        axis=1,
    )

    emission_ratio = (
        emissions_reduction[:, None]
        * cac_reference_co2_emission_factor[clamped]
        / cac_reference_co2_emission_factor[:, None]
    )
    cumul_em = jnp.sum(emission_ratio, axis=1)

    carbon_price = jax_extended_carbon_price(exogenous_carbon_price_trajectory, positions, clamped)
    generic_discounted_cumul_em = jnp.sum(
        emission_ratio
        * carbon_price
        / exogenous_carbon_price_trajectory[:, None]
        * discount[None, :],
        axis=1,
    )

    if not zero_guard:
        return (
            discounted_cumul_cost / cumul_em,
            discounted_cumul_cost / generic_discounted_cumul_em,
        )
    return (
        jnp.where(cumul_em == 0, jnp.nan, discounted_cumul_cost / cumul_em),
        jnp.where(
            generic_discounted_cumul_em == 0,
            jnp.nan,
            discounted_cumul_cost / generic_discounted_cumul_em,
        ),
    )


def jax_nan_add(a, b):
    """NaN-aware addition mirroring ``Series.add(..., fill_value=0)``.

    NaN + NaN stays NaN, otherwise NaN counts as zero.
    """
    a = jnp.asarray(a)
    b = jnp.asarray(b)
    return jnp.where(
        jnp.isnan(a) & jnp.isnan(b),
        jnp.nan,
        jnp.nan_to_num(a) + jnp.nan_to_num(b),
    )


def jax_pct_change(x):
    """JAX equivalent of ``pd.Series.pct_change() * 100`` (NaN at position 0)."""
    rate = x[1:] / x[:-1] - 1.0
    return jnp.concatenate([jnp.array([jnp.nan]), rate]) * 100.0


def covid_recovery_trajectory(
    model,
    history,
    covid_start_year,
    covid_end_year,
    covid_drop,
    covid_end_ratio,
    annual_growth_rate,
):
    """Common RPK/RTK trajectory: historic data, COVID dip, compounded recovery.

    Mirrors the pandas pattern used by ``RPKMarket`` / ``RTKMarket`` /
    ``RPKReferenceMarket`` / ``RTKReferenceMarket``:

    * historic years keep ``history``;
    * years in ``[max(covid_start, prospection_start), covid_end]`` interpolate
      linearly from the value at ``covid_start - 1``;
    * later years compound with ``annual_growth_rate`` (in %/year).

    ``covid_start_year`` and ``covid_end_year`` must be static.
    """
    years = years_index(model)
    ps = model.prospection_start_year
    cs, ce = int(covid_start_year), int(covid_end_year)

    yr = jnp.asarray(years, dtype=jnp.float64)
    f0 = 1.0 - covid_drop / 100.0
    f1 = covid_end_ratio / 100.0
    covid_factor = f0 + (f1 - f0) * (yr - cs) / (ce - cs)

    anchor = history[year_pos(model, cs - 1)]
    covid_mask = (years >= max(cs, ps)) & (years <= ce)
    traj = jnp.where(covid_mask, anchor * covid_factor, history)

    start = max(ce + 1, ps)
    start_pos = year_pos(model, start)
    base = traj[start_pos - 1]
    positions = jnp.arange(len(years))
    factors = jnp.where(positions >= start_pos, 1.0 + annual_growth_rate / 100.0, 1.0)
    compounded = base * jnp.cumprod(factors)
    return jnp.where(positions >= start_pos, compounded, traj)


def compound_from(base_value, growth_factors, start_pos: int, years_len: int, history):
    """Compounded trajectory: ``x[k] = x[k-1] * growth_factors[k]`` from ``start_pos``.

    Parameters
    ----------
    base_value
        Value at ``start_pos - 1`` (the anchor).
    growth_factors
        Full-length array of multiplicative factors (only positions >=
        ``start_pos`` are used).
    start_pos
        Static position at which compounding starts.
    years_len
        Static length of the year index.
    history
        Full-length array holding the values before ``start_pos`` (kept as is).

    Returns
    -------
    Full-length array with ``history`` before ``start_pos`` and the compounded
    trajectory from ``start_pos`` on.
    """
    positions = jnp.arange(years_len)
    factors = jnp.where(positions >= start_pos, growth_factors, 1.0)
    cum = jnp.cumprod(factors)
    # cum[k] = prod(factors[start..k]) for k >= start (earlier factors are 1)
    compounded = base_value * cum
    return jnp.where(positions >= start_pos, compounded, history)
