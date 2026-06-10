"""
fleet_model push_visualisation
===========

Module for visualising the result of the push fleet model.
"""
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib as mpl
import matplotlib.pyplot as plt

colors_26 = ["#E41A1C",     "#377EB8",    "#4DAF4A",      "#984EA3",
    "#FF7F00",      "#FFFF33",      "#A65628",     "#00FFFF",
    "#FF00FF",     "#008080",     "#3F51B5",
    "#B2FF00",     "#0A2A4F",     "0.85",     "#FF6F61",
    "#808000",    "#87CEEB",      "#B22222",    "#CFA0E9",
    "#FFD700",    "#228B22",      "#003F5C",   "#D100D1",    "#000000",]

def visualise_5y_seats_deliveries_by_submarket(
    classification_yaml_path: str,
    aircraft_parameters_excel_path: str,
    fleet_excel_path: str,
    aircraft_parameters_sheet_name=0,
    fleet_sheet_name=0,
) -> pd.DataFrame:
    """
    Compute and visualise weighted aircraft production volumes by submarket over 2020-2024.

    The weighted volume for each aircraft type is:
        production_volume * average_seats

    Then values are aggregated by submarket for each year.

    Parameters
    ----------
    classification_yaml_path : str
        Path to the YAML file mapping aircraft types to submarkets.
    aircraft_parameters_excel_path : str
        Path to the Excel file containing at least:
        - 'Aircraft Type'
        - 'average_seats'
    fleet_excel_path : str
        Path to the Excel file containing aircraft production volumes:
        - aircraft types in index or first column
        - years as columns
    aircraft_parameters_sheet_name : int or str, default=0
        Sheet name/index for the aircraft parameters Excel file.
    production_sheet_name : int or str, default=0
        Sheet name/index for the production Excel file.

    Returns
    -------
    pd.DataFrame
        Aggregated weighted production volumes by submarket and year.
    """
    module_dir = Path(__file__).resolve().parent
    project_root = module_dir.parents[4]

    classification_yaml_path = Path(classification_yaml_path)
    if not classification_yaml_path.is_absolute():
        classification_yaml_path = (project_root / classification_yaml_path).resolve()

    aircraft_parameters_excel_path = Path(aircraft_parameters_excel_path)
    if not aircraft_parameters_excel_path.is_absolute():
        aircraft_parameters_excel_path = (project_root / aircraft_parameters_excel_path).resolve()

    fleet_excel_path = Path(fleet_excel_path)
    if not fleet_excel_path.is_absolute():
        fleet_excel_path = (project_root / fleet_excel_path).resolve()


    with classification_yaml_path.open("r", encoding="utf-8") as f:
        classification_data = yaml.safe_load(f) or {}

    mapping = {
        str(aircraft_type).strip(): str(submarket).strip()
        for item in classification_data.get("aircraft_types", [])
        if isinstance(item, dict)
        for aircraft_type, submarket in item.items()
    }

    params_df = pd.read_excel(aircraft_parameters_excel_path, sheet_name=aircraft_parameters_sheet_name)
    params_df = params_df.copy()
    params_df["Aircraft Type"] = params_df["Aircraft Type"].astype(str).str.strip()
    params_df["submarket"] = params_df["Aircraft Type"].map(mapping)
    params_df["average_seats"] = pd.to_numeric(params_df["average_seats"], errors="coerce")

    params_df = params_df[params_df["submarket"].notna() & params_df["average_seats"].notna()].copy()

    production_df = pd.read_excel(
        fleet_excel_path,
        sheet_name=fleet_sheet_name,
        index_col=0,
    )

    production_df = production_df.copy()
    production_df.index = production_df.index.astype(str).str.strip()
    production_df.columns = [str(col).strip() for col in production_df.columns]

    years = [2020, 2021, 2022, 2023, 2024]
    result_rows = []

    for year in years:
        year_col = str(year)

        merged = params_df[["Aircraft Type", "submarket", "average_seats"]].merge(
            production_df[[year_col]],
            left_on="Aircraft Type",
            right_index=True,
            how="inner",
        )

        merged[year_col] = pd.to_numeric(merged[year_col], errors="coerce")
        merged = merged[merged[year_col].notna()].copy()

        merged["weighted_seats_deliveries"] = merged[year_col] * merged["average_seats"]

        grouped = (
            merged.groupby("submarket", as_index=False)["weighted_seats_deliveries"]
            .sum()
            .assign(year=year)
        )

        result_rows.append(grouped)

    result_df = pd.concat(result_rows, ignore_index=True)

    pivot_df = result_df.pivot(index="submarket", columns="year", values="weighted_seats_deliveries").fillna(0.0)
    pivot_df = pivot_df[years]

    ax = pivot_df.T.plot(
        kind="bar",
        figsize=(12, 6),
        width=0.85,
    )
    ax.set_xlabel("Year")
    ax.set_ylabel("Seats production volumes")
    ax.legend(title="Submarket", bbox_to_anchor=(1.02, 1), loc="upper left")
    ax.grid(axis="y", alpha=0.3)
    plt.yscale('log')
    plt.tight_layout()
    plt.show()

    return result_df


def visu_deliveries_array(deliveries, obs_sizes, obs_names, period_duration, n_market, color_mix = colors_26):
    T, M = deliveries.shape
    deliveries = deliveries * obs_sizes[None,:]
    col_sums = deliveries.sum(axis=0)
    N_m = (col_sums>0).sum()

    # indices des plus gros volumes
    top_idx = np.argsort(-col_sums)[:min(n_market * 2-3,N_m)]
    # calcul de la date moyenne d'utilisation
    mean_date = []

    for m in range(M):
        if col_sums[m] > 0:
            t_vals = np.arange(T)
            mean_date.append((t_vals * deliveries[:, m]).sum() / col_sums[m])
        else:
            mean_date.append(-np.inf)

    # masque top
    is_top = np.zeros(M, dtype=bool)
    is_top[top_idx] = True

    # tri
    cols_sorted = sorted(
        range(M),
        key=lambda m: (
            not is_top[m],  # priorité au top
            -mean_date[m]  # date moyenne décroissante
        )
    )

    rank = {m: k for k, m in enumerate(cols_sorted)}

    # --- TRI SELON RANK ---
    ordered_indices = sorted(
        range(len(rank)),
        key=lambda i: rank[i]
    )

    deliveries = deliveries[:, ordered_indices]
    obs_names = [obs_names[i] for i in ordered_indices]
    n_bars = deliveries.shape[0]
    p_categories = deliveries.shape[1]
    x = np.arange(n_bars) * period_duration + 2024
    bottom = np.zeros(n_bars)
    top = np.zeros(n_bars)
    fig, ax = plt.subplots(figsize=(10, 5.5))
    plt.grid(axis='y', color='grey', linestyle='--')
    for i in range(min(p_categories, N_m)):
        top = top + deliveries[:, i]
        if i < n_market:
            ax.fill_between(x, bottom, top, label=obs_names[i],
                            color=color_mix[i], linewidth=0, alpha=1, zorder=2)
            bottom = top
        elif i < 2 * n_market - 3:
            ax.fill_between(x, bottom, top, label=obs_names[i],
                            color=color_mix[i - n_market], linewidth=0, edgecolor='0.2', alpha=1, hatch='..', zorder=2)
            bottom = top
    ax.fill_between(x, bottom, top, alpha=0.8, color='grey', linewidth=0, edgecolor='white', label='Others', hatch='//',
                    zorder=2)
    ax.legend(framealpha=1, bbox_to_anchor=(1.05, 1),
              loc='upper left', borderaxespad=0., ncol=2)
    plt.xlim(x.min(), x.max())
    plt.ylim(0, 1.05 * top.max())
    plt.xlabel('Years')
    plt.ylabel('Produced aircraft seats')
    plt.tight_layout()
    plt.show()
    return None

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
    period_duration : float
        Distance between two time steps on the x-axis.
    n_market : int
        Number of main categories to highlight.
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

    # ------------------------------------------------------------
    # 1) Compute retirements on the time axis
    # ------------------------------------------------------------
    # Optional monotonic correction from the end of the horizon:
    # we preserve all dimensions explicitly with ellipsis.
    vol_obs_p = np.maximum.accumulate(vol_obs[::-1, ...], axis=0)[::-1, ...]

    # Retirements between consecutive time steps
    retirement_seats_volumes = -np.diff(vol_obs_p, axis=0)
    retirements_seats_volumes_ini =  -np.diff(vol_obs, axis=0)
    retirements_seats_volumes_ini[vol_obs[:-1]==0] = 0

    # ------------------------------------------------------------
    # 2) Aggregate over the second axis
    # Result shape: (T-1, M)
    # ------------------------------------------------------------
    type_obs = retirement_seats_volumes.sum(axis=1)
    type_obs_ini = retirements_seats_volumes_ini.sum(axis=1)
    # If there is no positive retirement at all, stop early
    if np.all(type_obs == 0):
        print("No retirement volumes to plot.")
        return None

    # ------------------------------------------------------------
    # 3) Sort categories by total volume and mean date
    # ------------------------------------------------------------
    totals = vol_obs.sum(axis=(0,1))
    top_k = min(48, vol_obs.shape[2])
    top_indices = np.argsort(-totals)[:top_k]

    # vecteur temps
    t = np.arange(vol_obs.shape[0])
    # calcul de la date moyenne d'utilisation
    mean_date = {}
    for m in top_indices:
        if totals[m] > 0:
            mean_date[m] = (t * (vol_obs[:,:, m].sum(axis=1))).sum() / totals[m]
        else:
            mean_date[m] = -np.inf

    # tri décroissant
    sorted_top = sorted(
        top_indices,
        key=lambda m: -mean_date[m]
    )

    # ajouter les autres colonnes dans leur ordre
    others = [m for m in range(vol_obs.shape[2]) if m not in sorted_top]
    types_sorted = list(sorted_top) + others

    # ranking final
    rank2 = {m: k for k, m in enumerate(types_sorted)}

    # --- TRI SELON RANK ---
    ordered_indices = sorted(
        rank2.keys(),
        key=lambda i: rank2[i]
    )

    type_obs = type_obs[:, ordered_indices]
    type_obs_ini = type_obs_ini[:, ordered_indices]
    obs_names = [obs_names[i] for i in ordered_indices]

    # ------------------------------------------------------------
    # 4) Plot stacked areas
    # ------------------------------------------------------------
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
    ax.fill_between(x, 0, 0, color='grey', linewidth=0.5, edgecolor='black', alpha=0.2, label='Temporary \n storage')

    ax.legend(
        framealpha=1,
        bbox_to_anchor=(1.05, 1),
        loc="upper left",
        borderaxespad=0.0,
        ncol=2,
    )

    ax.set_xlim(x.min(), x.max())
    ax.set_ylim(min(0, 1.05 * top_ini.min()), 1.05 *top.max())
    ax.set_xlabel("Years")
    ax.set_ylabel("Retired aircraft seats")
    plt.tight_layout()
    plt.show()
    return None

def visu_fleet_array(vol_obs,
    obs_names,
    obs_name,
    color_mix=colors_26):

    totals = vol_obs.sum(axis=(0))
    top_k = min(48, vol_obs.shape[1])
    top_indices = np.argsort(-totals)[:top_k]

    # vecteur temps
    t = np.arange(vol_obs.shape[0])
    # calcul de la date moyenne d'utilisation
    mean_date = {}
    for m in top_indices:
        if totals[m] > 0:
            mean_date[m] = (t * vol_obs[:, m]).sum() / totals[m]
        else:
            mean_date[m] = -np.inf

    # tri décroissant
    sorted_top = sorted(
        top_indices,
        key=lambda m: -mean_date[m]
    )

    # ajouter les autres colonnes dans leur ordre
    others = [m for m in range(vol_obs.shape[1]) if m not in sorted_top]
    types_sorted = list(sorted_top) + others

    # ranking final
    rank2 = {m: k for k, m in enumerate(types_sorted)}

    # --- TRI SELON RANK ---
    ordered_indices = sorted(
        rank2.keys(),
        key=lambda i: rank2[i]
    )
    vol_obs = vol_obs[:, ordered_indices]
    obs_names = [obs_names[i] for i in ordered_indices]

    n_bars = vol_obs.shape[0]
    p_categories = vol_obs.shape[1]

    x = np.arange(n_bars)  + 2025
    bottom = np.zeros(n_bars)
    top = np.zeros(n_bars)
    fig, ax = plt.subplots(figsize=(10, 6))
    plt.grid(axis='y', color='grey', linestyle='--')

    for i in range(p_categories):
        top = top + vol_obs[:, i]
        if i < 24:
            ax.fill_between(x, bottom, top, label=obs_names[i],
                            color=color_mix[i], linewidth=0, alpha=0.9)
            bottom = top
        elif i < 48:
            ax.fill_between(x, bottom, top, label=obs_names[i],
                            color=color_mix[i - 24], linewidth=0, alpha=0.9, hatch='..', edgecolor='0.2')
            bottom = top
    mpl.rcParams['hatch.color'] = 'white'
    ax.fill_between(x, bottom, top, alpha=0.9, color='grey', linewidth=0, edgecolor='white', label='Others', hatch='//')
    ax.legend(framealpha=1, bbox_to_anchor=(1.05, 1),
              loc='upper left', borderaxespad=0., ncol=2)

    plt.xlim(x.min(), x.max())
    plt.ylim(0, 1.1 * top.max())
    plt.xlabel('Years')
    plt.ylabel('Quantity of ' + obs_name)
    plt.tight_layout()
    plt.show()
    return None

def visu_retirement_age(vol_obs,
                        obs_names,
                        color_mix=colors_26):
    totals = vol_obs.sum(axis=(0, 1))
    top_k = min(48, vol_obs.shape[2])
    top_indices = np.argsort(-totals)[:top_k]

    # vecteur temps
    t = np.arange(vol_obs.shape[0])
    # calcul de la date moyenne d'utilisation
    mean_date = {}
    for m in top_indices:
        if totals[m] > 0:
            mean_date[m] = (t * (vol_obs[:, :, m].sum(axis=1))).sum() / totals[m]
        else:
            mean_date[m] = -np.inf

    # tri décroissant
    sorted_top = sorted(
        top_indices,
        key=lambda m: -mean_date[m]
    )

    # ajouter les autres colonnes dans leur ordre
    others = [m for m in range(vol_obs.shape[2]) if m not in sorted_top]
    types_sorted = list(sorted_top) + others

    # ranking final
    rank2 = {m: k for k, m in enumerate(types_sorted)}

    # --- TRI SELON RANK ---
    ordered_indices = sorted(
        rank2.keys(),
        key=lambda i: rank2[i]
    )



    ages_y = np.arange(vol_obs.shape[1])
    ages_t = np.arange(vol_obs.shape[0])[:-1]
    ages_t_y = ages_t[:, None] - ages_y[None, :]+vol_obs.shape[1]-vol_obs.shape[0]

    vol_obs = vol_obs[:, :, ordered_indices]
    obs_names = [obs_names[i] for i in ordered_indices]
    retirements_seats_volumes_ini = -np.diff(vol_obs, axis=0)
    retirements_seats_volumes_ini[vol_obs[:-1] == 0] = 0

    n_years = (retirements_seats_volumes_ini*ages_t_y[:,:,None]).sum(axis=1)
    volumes = retirements_seats_volumes_ini.sum(axis = 1)

    x = t[:-1] + 2025
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.grid(axis='y', color='grey', linestyle='--')
    for ac in range(len(obs_names)):
        y = np.divide(
            n_years[:, ac],
            volumes[:, ac],
            out=np.full_like(n_years[:, ac], np.nan, dtype=float),
            where=volumes[:, ac] != 0
        )
        mask = np.isfinite(x) & np.isfinite(y) & (retirements_seats_volumes_ini[:,:,ac].sum(axis=1)>500)
        y[~mask]=np.nan
        if not np.any(mask):
            continue
        if ac < 24:
            ax.plot(x, y, '-', color=color_mix[ac], markersize=2, label=obs_names[ac], linewidth=1)
        else:
            ax.plot(x, y, '--', color=color_mix[ac - 24], markersize=2, label=obs_names[ac], linewidth=1)
    y_agg = np.divide(
        n_years.sum(axis=1),
        volumes.sum(axis=1),
        out=np.full_like(n_years.sum(axis=1), np.nan, dtype=float),
        where=volumes.sum(axis=1)!= 0
    )
    mask = np.isfinite(x) & np.isfinite(y_agg) & (retirements_seats_volumes_ini.sum(axis=(1,2)) > 500)
    y_agg[~mask]=np.nan
    ax.plot(x, y_agg, '*-', color='black', markersize=5, label='avg ret age', linewidth=2)

    operating_years = (vol_obs[:-1, :, :] * ages_t_y[:, :, None]).sum(axis=(1,2))
    operating_volumes = vol_obs[:-1, :, :].sum(axis=(1,2))
    ax.plot(x, operating_years/operating_volumes, '*-', color=(1,0,1), markersize=5, label='avg op age', linewidth=2)

    plt.xlim(xmin=2025, xmax=2025+vol_obs.shape[0])
    plt.ylim(0)
    plt.xlabel('Years')
    plt.ylabel('Average retirement age')
    plt.legend(ncol=2, title='Retirements volumes > 500 seats per year', bbox_to_anchor=(1.05, 1))
    plt.tight_layout()
    plt.show()
    return(None)