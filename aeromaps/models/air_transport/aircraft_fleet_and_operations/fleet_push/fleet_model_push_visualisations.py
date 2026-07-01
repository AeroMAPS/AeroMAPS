"""
fleet_model_push_visualisations
===============================

Matplotlib helpers for the delivery-driven ("push") fleet model.

These are deliberately kept outside the AeroMAPS ``SingleScenarioPlot`` registry:
the retirement / retirement-age charts read the engine's internal age-resolved 3D
arrays (``(periods, age, type)``) that the model does not expose as flat ``df``
columns. They are rendered by :meth:`PassengerAircraftEfficiencyFleetPush.plot`,
which caches those arrays during ``compute`` and calls these functions per segment
— the same pattern as the bottom-up :meth:`FleetModel.plot`.
"""

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

colors_26 = [
    "#E41A1C",
    "#377EB8",
    "#4DAF4A",
    "#984EA3",
    "#FF7F00",
    "#FFFF33",
    "#A65628",
    "#00FFFF",
    "#FF00FF",
    "#008080",
    "#3F51B5",
    "#B2FF00",
    "#0A2A4F",
    "0.85",
    "#FF6F61",
    "#808000",
    "#87CEEB",
    "#B22222",
    "#CFA0E9",
    "#FFD700",
    "#228B22",
    "#003F5C",
    "#D100D1",
    "#000000",
]


def visu_retirements_array(
    vol_obs,
    obs_names,
    color_mix=colors_26,
):
    """
    Visualise retired aircraft seats from a 3D volume array.

    Parameters
    ----------
    vol_obs : np.ndarray
        Array of shape (T, A, M), where:
        - T = time
        - A = aggregation axis, summed out before display
        - M = displayed categories
    obs_names : list[str]
        Names of the displayed categories (axis M).
    color_mix : list[str]
        Color palette.

    Returns
    -------
    None
    """
    vol_obs = np.asarray(vol_obs)

    if vol_obs.ndim != 3:
        raise ValueError(
            f"vol_obs must be 3D with shape (time, aggregation, displayed), got {vol_obs.shape}"
        )

    T, A, M = vol_obs.shape

    if len(obs_names) != M:
        raise ValueError(
            f"obs_names length ({len(obs_names)}) must match vol_obs third dimension ({M})."
        )

    # Optional monotonic correction from the end of the horizon.
    vol_obs_p = np.maximum.accumulate(vol_obs[::-1, ...], axis=0)[::-1, ...]

    # Retirements between consecutive time steps
    retirement_seats_volumes = -np.diff(vol_obs_p, axis=0)
    retirements_seats_volumes_ini = -np.diff(vol_obs, axis=0)
    retirements_seats_volumes_ini[vol_obs[:-1] == 0] = 0

    # Aggregate over the second axis. Result shape: (T-1, M)
    type_obs = retirement_seats_volumes.sum(axis=1)
    type_obs_ini = retirements_seats_volumes_ini.sum(axis=1)
    if np.all(type_obs == 0):
        print("No retirement volumes to plot.")
        return None

    # Sort categories by total volume and mean date
    totals = vol_obs.sum(axis=(0, 1))
    top_k = min(48, vol_obs.shape[2])
    top_indices = np.argsort(-totals)[:top_k]

    t = np.arange(vol_obs.shape[0])
    mean_date = {}
    for m in top_indices:
        if totals[m] > 0:
            mean_date[m] = (t * (vol_obs[:, :, m].sum(axis=1))).sum() / totals[m]
        else:
            mean_date[m] = -np.inf

    sorted_top = sorted(top_indices, key=lambda m: -mean_date[m])
    others = [m for m in range(vol_obs.shape[2]) if m not in sorted_top]
    types_sorted = list(sorted_top) + others
    rank2 = {m: k for k, m in enumerate(types_sorted)}
    ordered_indices = sorted(rank2.keys(), key=lambda i: rank2[i])

    type_obs = type_obs[:, ordered_indices]
    type_obs_ini = type_obs_ini[:, ordered_indices]
    obs_names = [obs_names[i] for i in ordered_indices]

    # Plot stacked areas
    n_bars = type_obs.shape[0]
    p_categories = type_obs.shape[1]

    x = np.arange(n_bars) + 2025
    bottom = np.zeros(n_bars)
    bottom_ini = np.zeros(n_bars)
    top = np.zeros(n_bars)
    top_ini = np.zeros(n_bars)

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.grid(axis="y", color="grey", linestyle="--")

    for i in range(p_categories):
        top = top + type_obs[:, i]
        top_ini = top_ini + type_obs_ini[:, i]

        if i < 24:
            ax.fill_between(
                x,
                bottom,
                top,
                label=obs_names[i],
                color=color_mix[i],
                linewidth=0,
                alpha=1.0,
                zorder=2,
            )
            ax.fill_between(
                x,
                bottom_ini,
                top_ini,
                color=color_mix[i],
                linewidth=0,
                alpha=0.2,
                zorder=1,
            )
            bottom = top
            bottom_ini = top_ini

        elif i < 48:
            ax.fill_between(
                x,
                bottom,
                top,
                label=obs_names[i],
                color=color_mix[i - 24],
                linewidth=0,
                edgecolor="0.2",
                alpha=1.0,
                hatch="..",
                zorder=2,
            )
            ax.fill_between(
                x,
                bottom_ini,
                top_ini,
                color=color_mix[i - 24],
                linewidth=0,
                edgecolor="0.2",
                alpha=0.2,
                hatch="..",
                zorder=1,
            )
            bottom = top
            bottom_ini = top_ini

    ax.fill_between(
        x,
        bottom,
        top,
        alpha=1,
        color="grey",
        linewidth=0,
        edgecolor="white",
        label="Others",
        hatch="//",
        zorder=2,
    )
    ax.fill_between(
        x,
        bottom_ini,
        top_ini,
        alpha=0.2,
        color="grey",
        linewidth=0,
        edgecolor="white",
        hatch="//",
        zorder=1,
    )
    ax.fill_between(
        x,
        0,
        0,
        color="grey",
        linewidth=0.5,
        edgecolor="black",
        alpha=0.2,
        label="Temporary \n storage",
    )

    ax.legend(
        framealpha=1,
        bbox_to_anchor=(1.05, 1),
        loc="upper left",
        borderaxespad=0.0,
        ncol=2,
    )

    ax.set_xlim(x.min(), x.max())
    ax.set_ylim(min(0, 1.05 * top_ini.min()), 1.05 * top.max())
    ax.set_xlabel("Years")
    ax.set_ylabel("Retired aircraft seats")
    plt.tight_layout()
    plt.show()
    return None


def visu_fleet_array(vol_obs, obs_names, obs_name, color_mix=colors_26):
    """Stacked-area evolution of a per-type 2D volume array (T, M)."""
    totals = vol_obs.sum(axis=0)
    top_k = min(48, vol_obs.shape[1])
    top_indices = np.argsort(-totals)[:top_k]

    t = np.arange(vol_obs.shape[0])
    mean_date = {}
    for m in top_indices:
        if totals[m] > 0:
            mean_date[m] = (t * vol_obs[:, m]).sum() / totals[m]
        else:
            mean_date[m] = -np.inf

    sorted_top = sorted(top_indices, key=lambda m: -mean_date[m])
    others = [m for m in range(vol_obs.shape[1]) if m not in sorted_top]
    types_sorted = list(sorted_top) + others
    rank2 = {m: k for k, m in enumerate(types_sorted)}
    ordered_indices = sorted(rank2.keys(), key=lambda i: rank2[i])
    vol_obs = vol_obs[:, ordered_indices]
    obs_names = [obs_names[i] for i in ordered_indices]

    n_bars = vol_obs.shape[0]
    p_categories = vol_obs.shape[1]

    x = np.arange(n_bars) + 2025
    bottom = np.zeros(n_bars)
    top = np.zeros(n_bars)
    fig, ax = plt.subplots(figsize=(10, 6))
    plt.grid(axis="y", color="grey", linestyle="--")

    for i in range(p_categories):
        top = top + vol_obs[:, i]
        if i < 24:
            ax.fill_between(
                x,
                bottom,
                top,
                label=obs_names[i],
                color=color_mix[i],
                linewidth=0,
                alpha=0.9,
            )
            bottom = top
        elif i < 48:
            ax.fill_between(
                x,
                bottom,
                top,
                label=obs_names[i],
                color=color_mix[i - 24],
                linewidth=0,
                alpha=0.9,
                hatch="..",
                edgecolor="0.2",
            )
            bottom = top
    mpl.rcParams["hatch.color"] = "white"
    ax.fill_between(
        x,
        bottom,
        top,
        alpha=0.9,
        color="grey",
        linewidth=0,
        edgecolor="white",
        label="Others",
        hatch="//",
    )
    ax.legend(
        framealpha=1,
        bbox_to_anchor=(1.05, 1),
        loc="upper left",
        borderaxespad=0.0,
        ncol=2,
    )

    plt.xlim(x.min(), x.max())
    plt.ylim(0, 1.1 * top.max())
    plt.xlabel("Years")
    plt.ylabel("Quantity of " + obs_name)
    plt.tight_layout()
    plt.show()
    return None


def visu_retirement_age(vol_obs, obs_names, color_mix=colors_26):
    """Average retirement age (and operating age) per type from a 3D array (T, A, M)."""
    totals = vol_obs.sum(axis=(0, 1))
    top_k = min(48, vol_obs.shape[2])
    top_indices = np.argsort(-totals)[:top_k]

    t = np.arange(vol_obs.shape[0])
    mean_date = {}
    for m in top_indices:
        if totals[m] > 0:
            mean_date[m] = (t * (vol_obs[:, :, m].sum(axis=1))).sum() / totals[m]
        else:
            mean_date[m] = -np.inf

    sorted_top = sorted(top_indices, key=lambda m: -mean_date[m])
    others = [m for m in range(vol_obs.shape[2]) if m not in sorted_top]
    types_sorted = list(sorted_top) + others
    rank2 = {m: k for k, m in enumerate(types_sorted)}
    ordered_indices = sorted(rank2.keys(), key=lambda i: rank2[i])

    ages_y = np.arange(vol_obs.shape[1])
    ages_t = np.arange(vol_obs.shape[0])[:-1]
    ages_t_y = ages_t[:, None] - ages_y[None, :] + vol_obs.shape[1] - vol_obs.shape[0]

    vol_obs = vol_obs[:, :, ordered_indices]
    obs_names = [obs_names[i] for i in ordered_indices]
    retirements_seats_volumes_ini = -np.diff(vol_obs, axis=0)
    retirements_seats_volumes_ini[vol_obs[:-1] == 0] = 0

    n_years = (retirements_seats_volumes_ini * ages_t_y[:, :, None]).sum(axis=1)
    volumes = retirements_seats_volumes_ini.sum(axis=1)

    x = t[:-1] + 2025
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.grid(axis="y", color="grey", linestyle="--")
    for ac in range(len(obs_names)):
        y = np.divide(
            n_years[:, ac],
            volumes[:, ac],
            out=np.full_like(n_years[:, ac], np.nan, dtype=float),
            where=volumes[:, ac] != 0,
        )
        mask = (
            np.isfinite(x)
            & np.isfinite(y)
            & (retirements_seats_volumes_ini[:, :, ac].sum(axis=1) > 500)
        )
        y[~mask] = np.nan
        if not np.any(mask):
            continue
        if ac < 24:
            ax.plot(x, y, "-", color=color_mix[ac], markersize=2, label=obs_names[ac], linewidth=1)
        else:
            ax.plot(
                x,
                y,
                "--",
                color=color_mix[ac - 24],
                markersize=2,
                label=obs_names[ac],
                linewidth=1,
            )
    y_agg = np.divide(
        n_years.sum(axis=1),
        volumes.sum(axis=1),
        out=np.full_like(n_years.sum(axis=1), np.nan, dtype=float),
        where=volumes.sum(axis=1) != 0,
    )
    mask = (
        np.isfinite(x) & np.isfinite(y_agg) & (retirements_seats_volumes_ini.sum(axis=(1, 2)) > 500)
    )
    y_agg[~mask] = np.nan
    ax.plot(x, y_agg, "*-", color="black", markersize=5, label="avg ret age", linewidth=2)

    operating_years = (vol_obs[:-1, :, :] * ages_t_y[:, :, None]).sum(axis=(1, 2))
    operating_volumes = vol_obs[:-1, :, :].sum(axis=(1, 2))
    ax.plot(
        x,
        operating_years / operating_volumes,
        "*-",
        color=(1, 0, 1),
        markersize=5,
        label="avg op age",
        linewidth=2,
    )

    plt.xlim(xmin=2025, xmax=2025 + vol_obs.shape[0])
    plt.ylim(0)
    plt.xlabel("Years")
    plt.ylabel("Average retirement age")
    plt.legend(ncol=2, title="Retirements volumes > 500 seats per year", bbox_to_anchor=(1.05, 1))
    plt.tight_layout()
    plt.show()
    return None


def visu_energy_intensity(energy_content, ask_content, years, market_name):
    """Per-segment drop-in energy intensity (MJ/ASK) over time from 3D arrays."""
    plt.grid(axis="y", color="grey", linestyle="--")
    plt.plot(years, energy_content.sum(axis=(1, 2)) / ask_content.sum(axis=(1, 2)))
    plt.title("Energy efficiency " + market_name)
    plt.ylim(ymin=0)
    plt.xlim(xmin=years[0], xmax=years[-1])
    plt.show()
    return None
