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
    idx = np.clip(
        np.searchsorted(periods, years, side="right") - 1, 0, len(reference_periods) - 2
    )
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
