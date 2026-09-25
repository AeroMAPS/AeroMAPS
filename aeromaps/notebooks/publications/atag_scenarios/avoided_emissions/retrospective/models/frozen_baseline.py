"""
frozen_baseline
===============
The ATAG *Waypoint 2050* page-16 avoided-emissions construction, exposed as
configuration rather than as one number.

The published figure draws a single red dashed line labelled "Frozen 1990
efficiency" and reports the area between it and observed emissions as 14.6 Gt
of CO2 "already saved". Reproducing that line requires four choices the report
does not state: which intensity factors are held at 1990, what accounting scope
the series is on, over which window the area is integrated, and what 1990
emission level anchors it. Each choice moves the answer, so this module takes
all four as arguments and returns the whole family.

On top of the reproduction it adds the counterfactual the construction omits.
Freezing 1990 efficiency while letting traffic follow its observed path assumes
the direct rebound is exactly zero: that flying twice as expensive per
passenger-kilometre would have been flown just as much. ``adaptation="demand"``
relaxes that single assumption and nothing else, so the gap between the two is
the rebound in isolation.

Three adaptation modes, ordered so that ``R2 < R1 < R0``:

``"none"`` (R0)
    The published construction verbatim. Zero rebound by assumption.
``"demand"`` (R1)
    Traffic responds to the counterfactual fare through a constant-elasticity
    demand curve. Fleet and technology stay frozen exactly as in R0, so R0 - R1
    is attributable to the baseline's endogeneity and to nothing else.
``"supply"`` (R2)
    R1 plus a bounded partial adjustment of load factor toward the best the 1990
    frontier allowed. No technological progress is permitted, so this stays
    inside the report's own "frozen 1990 technology" premise while dropping the
    implausible claim that airlines would not have reacted at all.

Nothing here runs the model. Every series is read from a committed file:
observed traffic from ``resources/historical_data/``, observed CO2 from Kloewer
spliced to the reproduction's own output, jet fuel price from the WCTR
publication data. See ``../data_inputs/SOURCES.md``.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd

# .../atag_scenarios/avoided_emissions/retrospective/models/
MODELS = Path(__file__).resolve().parent
RETROSPECTIVE = MODELS.parent
ATAG = RETROSPECTIVE.parent.parent
REPO = ATAG.parents[3]

RESOURCES = REPO / "aeromaps" / "resources"
TRAFFIC = RESOURCES / "historical_data" / "world_air_transport_traffic_1929_2024.csv"
KLOWER = RESOURCES / "climate_data" / "historical_data_from_klower.csv"
PUBLICATIONS = REPO / "aeromaps" / "notebooks" / "publications"
FUEL_PRICE = (
    REPO
    / "aeromaps"
    / "resources"
    / "scenarios"
    / "icao_ltag_coupled_wctr"
    / "data"
    / "eia_jet_fuel_prices.csv"
)

# --------------------------------------------------------------------------
# The four undeclared choices
# --------------------------------------------------------------------------

#: Well-to-wake to tank-to-wake. Not a fitted number: this single constant
#: reconciles the 2019 observed value, the 2050 frozen endpoint and the 2050
#: no-effort value in the published figure simultaneously, which is what
#: identifies the series as tank-to-wake in the first place.
SCOPE_WTW_TO_TTW = 0.8320

#: 1990 tank-to-wake emissions, in Mt, under the anchor read off the figure
#: rather than out of the data: the level that makes the frozen line hit its own
#: labelled 2050 endpoint of ~5,200 Mt. The data-derived anchor is Kloewer's
#: 1990 CO2 times the scope factor, computed in :func:`e_1990`. They disagree by
#: 3.5 % and neither is treated as the answer.
E_1990_ENDPOINT_ANCHOR = 441.0

#: The Kaya chain, outermost first. Each entry converts the activity metric
#: above it into the one below:
#:
#:     RPK --(/load factor)--> ASK --(/seats per aircraft)--> aircraft-km
#:         --(x energy per aircraft-km)--> energy --(x CO2 per energy)--> CO2
#:
#: Holding a factor at 1990 removes it from the counterfactual; leaving it free
#: lets the observed path of that factor move the counterfactual. Because the
#: chain is nested, the set of frozen factors determines exactly one observed
#: activity series to scale the frozen 1990 intensity by.
FACTORS = (
    "load_factor",
    "seats_per_aircraft",
    "energy_per_aircraft_km",
    "co2_per_energy",
)

#: Frozen-factor set to the observed driver it implies. The report's own text
#: places load factor inside its 25 % "operational efficiency" gain, which is
#: what makes the first row the reading it must have used.
#:
#: Note on naming: the step from ASK to aircraft-km is average seats per
#: aircraft (up-gauging), not stage length. Stage length is already inside
#: aircraft-km, since aircraft-km is departures times mean stage length.
_DRIVER_BY_FROZEN = {
    frozenset(FACTORS): "rpk",
    frozenset(FACTORS[1:]): "ask",
    frozenset(FACTORS[2:]): "total_aircraft_distance",
}

#: Readable names for the three nested freezes, used as grid labels.
METHODS = {
    "freeze-all": FACTORS,
    "fuel-side": FACTORS[1:],
    "fuel-side-and-gauge": FACTORS[2:],
}

#: The figure integrates its shaded area from 1990 to the last year of observed
#: data it draws, which is 2023. 2019 and 2024 are carried as sensitivities.
WINDOW = (1990, 2023)

#: The frozen line's own labelled endpoint.
HORIZON = 2050

#: What the report claims on the same page, for the consistency checks.
ATAG_AVOIDED_GT = 14.6
ATAG_FROZEN_2050_MT = 5200.0
ATAG_OBSERVED_2019_MT = 915.0
ATAG_NO_EFFORT_2050_MT = 2400.0
ATAG_TECHNOLOGY_GAIN = 0.29
ATAG_OPERATIONS_GAIN = 0.25
ATAG_COMBINED_GAIN = 0.54


# --------------------------------------------------------------------------
# Observed series
# --------------------------------------------------------------------------


def _read_semicolon(path, columns):
    """Read one of the repository's ``;``-delimited historical files.

    Blank cells stay NaN. They are years the source does not cover and are
    never interpolated.
    """
    rows = list(csv.DictReader(path.open(encoding="utf-8"), delimiter=";"))
    frame = pd.DataFrame(rows)
    frame["year"] = frame["year"].astype(int)
    frame = frame.set_index("year")[list(columns)]
    return frame.apply(pd.to_numeric, errors="coerce")


def load_traffic():
    """Observed world air transport activity, indexed by year.

    Reuses the series ``climate_analysis/utils.load_observed`` reads, restricted
    to the columns the Kaya chain needs.
    """
    return _read_semicolon(
        TRAFFIC,
        ("rpk", "ask", "total_aircraft_distance", "load_factor", "aircraft_departures"),
    )


def load_klower():
    """Kloewer's observed aviation CO2, and the repository's rescale of it.

    The file carries two CO2 columns. ``CO2 [Mt/yr]`` is Kloewer's own series,
    1940-2018. ``CO2_AeroMAPS [Mt/yr]`` is the same series put on the coverage
    basis AeroMAPS models, and it exists only for 2000-2018. Their ratio is
    near-constant over that overlap, which is what makes the rescale usable
    outside it.
    """
    frame = _read_semicolon(KLOWER, ("CO2 [Mt/yr]", "CO2_AeroMAPS [Mt/yr]"))
    return frame.rename(columns={"CO2 [Mt/yr]": "klower", "CO2_AeroMAPS [Mt/yr]": "aeromaps"})


def _klower_rescale(rescale_klower):
    """Mean and spread of the AeroMAPS-to-Kloewer ratio over their overlap."""
    ratio = (load_klower()["aeromaps"] / load_klower()["klower"]).dropna()
    return (float(ratio.mean()) if rescale_klower else 1.0), float(ratio.max() - ratio.min())


def scenario_series(name, scenario="s1-TTW", edition="3rd_edition_full"):
    """One vector output of a committed scenario, indexed by year.

    ``write_json`` drops the index, but every vector runs to 2050 by
    construction, so the years are recoverable from the length.

    Reads only; the inherited edition directories are never written to.
    """
    path = ATAG / edition / "data_outputs" / f"{scenario}.json"
    with path.open(encoding="utf-8") as handle:
        outputs = json.load(handle)["vector_outputs"]
    values = np.asarray(outputs[name], dtype=float)
    years = range(HORIZON - len(values) + 1, HORIZON + 1)
    return pd.Series(values, index=pd.Index(years, name="year"), name=name)


def scenario_co2(scenario="s1-TTW", edition="3rd_edition_full"):
    """Total CO2 from a committed scenario output, indexed by year.

    Passenger plus freight, which is the whole of the modelled total. The
    ``co2_emissions_including_energy`` wedge carries the same value but is NaN
    before the last historical year, so it cannot serve as the observed leg.
    """
    passenger = scenario_series("co2_emissions_passenger", scenario, edition)
    freight = scenario_series("co2_emissions_freight", scenario, edition)
    return (passenger + freight).rename(scenario)


def observed_co2(scope=SCOPE_WTW_TO_TTW, splice_year=2019, rescale_klower=False, scenario="s1-TTW"):
    """Observed tank-to-wake CO2 from 1990 onward, the figure's lower curve.

    No single source covers the window. Kloewer stops at 2018 and the
    reproduction starts at 2000, so the series is spliced, and *where* it is
    spliced changes the avoided area.

    Parameters
    ----------
    splice_year
        First year taken from the scenario output. The default of 2019 uses
        Kloewer wherever it exists, and it is the reading that reproduces the
        published 14.6 Gt. It is not seamless: over 2010-2018 the two sources
        differ by a near-constant 7 %, so the series steps up at the seam.
        ``2000`` splices at the first year the reproduction covers instead.
    rescale_klower
        Put Kloewer on the reproduction's coverage basis before splicing, using
        the ratio the source file itself supplies over 2000-2018. Removes the
        seam step at the cost of moving the 1990 anchor.

    Returns
    -------
    series, diagnostics
        The spliced series, and a dict recording the splice year, the rescale
        applied, and the discontinuity left at the seam.
    """
    factor, spread = _klower_rescale(rescale_klower)
    historical = load_klower()["klower"].dropna() * factor * scope
    modelled = scenario_co2(scenario)

    years = range(WINDOW[0], int(modelled.index.max()) + 1)
    values = [
        historical.get(year, np.nan) if year < splice_year else modelled.get(year, np.nan)
        for year in years
    ]
    series = pd.Series(values, index=pd.Index(years, name="year"), name="observed_co2")

    seam = splice_year - 1
    step = float("nan")
    if seam in historical.index and seam in modelled.index:
        step = float(modelled[seam] / historical[seam] - 1.0)

    return series, {
        "splice_year": splice_year,
        "klower_rescale": factor,
        "klower_rescale_spread": spread,
        "seam_discontinuity": step,
        "observed_scenario": scenario,
    }


def e_1990(anchor="klower", scope=SCOPE_WTW_TO_TTW, rescale_klower=False):
    """1990 tank-to-wake emissions under one of the two surviving anchors.

    ``"klower"`` reads it from data; ``"endpoint"`` reads it off the figure's own
    2050 label. They differ by 3.5 % and the difference is carried, not resolved.
    """
    if anchor == "endpoint":
        return E_1990_ENDPOINT_ANCHOR
    if anchor != "klower":
        raise ValueError(f"unknown anchor {anchor!r}; expected 'klower' or 'endpoint'")
    factor, _ = _klower_rescale(rescale_klower)
    return float(load_klower()["klower"].loc[WINDOW[0]] * factor * scope)


def jet_fuel_price():
    """Annual mean US Gulf Coast jet fuel spot price, $/gal, indexed by year.

    Monthly FRED ``MJFUELUSGULF``, averaged to calendar years. 1990 is partial
    (April onward), which is stated rather than patched: R1 compares
    counterfactual and observed fare within the same year, so the level of any
    one year cancels and only its within-year ratio matters.
    """
    frame = pd.read_csv(FUEL_PRICE, parse_dates=["observation_date"])
    frame["year"] = frame["observation_date"].dt.year
    return frame.groupby("year")["MJFUELUSGULF"].mean()


# --------------------------------------------------------------------------
# The counterfactual family
# --------------------------------------------------------------------------


def driver_for(frozen_factors):
    """Observed activity series implied by a set of factors held at 1990."""
    key = frozenset(frozen_factors)
    if key not in _DRIVER_BY_FROZEN:
        raise ValueError(
            f"{sorted(key)} is not a suffix of the Kaya chain {list(FACTORS)}; "
            "only nested freezes map onto a single observed activity series"
        )
    return _DRIVER_BY_FROZEN[key]


def frozen_baseline(
    frozen_factors=FACTORS,
    scope=SCOPE_WTW_TO_TTW,
    window=WINDOW,
    anchor="klower",
    horizon=HORIZON,
    adaptation="none",
    elasticity=None,
    pass_through=1.0,
    fuel_cost_share=0.20,
    lf_adjustment=0.0,
    splice_year=2019,
    rescale_klower=False,
    scenario="s1-TTW",
):
    """One cell of the method grid: the frozen counterfactual and its avoided area.

    Parameters
    ----------
    frozen_factors
        Which Kaya factors are held at 1990. Must be a nested suffix of
        :data:`FACTORS`; see :func:`driver_for`.
    scope, anchor
        The accounting scope factor and the 1990 anchor, both undeclared in the
        report and both material.
    window
        Inclusive ``(first, last)`` years the avoided area is integrated over.
    horizon
        Year the frozen line is extended to, for comparison with the figure's
        own ~5,200 Mt endpoint. Beyond the observed record the driver comes from
        the reproduction's own traffic.
    adaptation
        ``"none"`` (R0), ``"demand"`` (R1) or ``"supply"`` (R2).
    elasticity
        Price elasticity of demand, a negative number. Required for R1 and R2.
    pass_through
        Fraction of the counterfactual fuel-cost increase that reaches the fare.
        1.0 is full pass-through.
    fuel_cost_share
        Fuel's share of the fare in the reference year. Fuel was about a fifth
        of airline operating cost through the 1990s, so 0.20 is the default; it
        is the single most consequential judgement in R1 and is swept.
    lf_adjustment
        R2 only. Fraction of the observed load-factor gain that airlines are
        allowed to recover under frozen technology, in [0, 1].

    Returns
    -------
    dict
        ``years``, ``counterfactual``, ``observed``, ``avoided`` (per year, Mt),
        ``avoided_gt`` over the window, ``counterfactual_at_horizon``,
        ``demand_ratio`` (counterfactual over observed traffic) and the full
        configuration that produced them.
    """
    if adaptation not in ("none", "demand", "supply"):
        raise ValueError(f"unknown adaptation {adaptation!r}")
    if adaptation != "none" and elasticity is None:
        raise ValueError(f"adaptation={adaptation!r} needs an elasticity")
    if elasticity is not None and elasticity > 0:
        raise ValueError("elasticity is a negative number")
    if not 0.0 <= lf_adjustment <= 1.0:
        raise ValueError("lf_adjustment is a fraction in [0, 1]")

    driver_name = driver_for(frozen_factors)
    traffic = load_traffic()
    observed, splice = observed_co2(
        scope=scope, splice_year=splice_year, rescale_klower=rescale_klower, scenario=scenario
    )
    anchor_value = e_1990(anchor=anchor, scope=scope, rescale_klower=rescale_klower)

    first, last = window
    years = np.arange(first, last + 1)
    driver = traffic[driver_name].reindex(years).to_numpy(dtype=float)
    base = float(traffic[driver_name].loc[first])
    observed_window = observed.reindex(years).to_numpy(dtype=float)

    # R0: the published construction. Observed activity, 1990 intensity, and
    # the assertion that the two are independent.
    activity_ratio = driver / base
    recovery = 1.0

    if adaptation == "supply":
        # Airlines that cannot buy a better aircraft can still fill the one they
        # have. Recovering a share of the observed load-factor gain lowers the
        # counterfactual without conceding any technological progress, so R2
        # stays inside the report's own frozen-technology premise.
        #
        # This is applied before the demand response, not after, because a
        # cheaper seat is a smaller fare premium and so a milder suppression.
        # Computing the two independently would double-count the saving.
        lf = traffic["load_factor"].reindex(years).to_numpy(dtype=float)
        recovery = 1.0 + lf_adjustment * (lf / float(traffic["load_factor"].loc[first]) - 1.0)
        activity_ratio = activity_ratio / recovery

    demand_ratio = np.ones_like(activity_ratio)
    if adaptation in ("demand", "supply"):
        demand_ratio = _demand_response(
            intensity_ratio=(anchor_value * activity_ratio) / observed_window,
            elasticity=elasticity,
            pass_through=pass_through,
            fuel_cost_share=fuel_cost_share,
        )

    counterfactual = anchor_value * activity_ratio * demand_ratio
    avoided = counterfactual - observed_window

    return {
        "years": years,
        "counterfactual": counterfactual,
        "observed": observed_window,
        "avoided": avoided,
        "avoided_gt": float(np.nansum(avoided) / 1000.0),
        "counterfactual_at_horizon": _extend_to_horizon(
            anchor_value=anchor_value,
            driver_name=driver_name,
            base=base,
            horizon=horizon,
            scenario=scenario,
            # Both adaptations are held at their terminal observed value beyond
            # the record. Extrapolating either would be inventing a trend the
            # figure's own endpoint label is supposed to test.
            terminal_ratio=float(demand_ratio[-1])
            / float(recovery[-1] if np.ndim(recovery) else recovery),
        ),
        "demand_ratio": demand_ratio,
        "config": {
            "frozen_factors": tuple(frozen_factors),
            "driver": driver_name,
            "scope": scope,
            "window": tuple(window),
            "anchor": anchor,
            "e_1990": anchor_value,
            "horizon": horizon,
            "adaptation": adaptation,
            "elasticity": elasticity,
            "pass_through": pass_through,
            "fuel_cost_share": fuel_cost_share,
            "lf_adjustment": lf_adjustment,
            **splice,
        },
    }


def _demand_response(intensity_ratio, elasticity, pass_through, fuel_cost_share):
    """Traffic in the frozen world, relative to observed traffic.

    The mechanism, and only this mechanism: frozen 1990 intensity means more
    fuel per passenger-kilometre than was actually burned; at the fuel price of
    the day that is a proportionally higher fuel cost; the fuel share of the
    fare passes that through to the ticket; and a constant-elasticity demand
    curve converts the fare ratio into a traffic ratio.

    Both fares are evaluated in the same year, so the comparison is
    deflator-free and the absolute price level never enters. What does enter is
    the fuel *share* of the fare, which is why it is a declared argument rather
    than a constant buried here.
    """
    fare_ratio = 1.0 + pass_through * fuel_cost_share * (intensity_ratio - 1.0)
    return np.power(fare_ratio, elasticity)


def _extend_to_horizon(anchor_value, driver_name, base, horizon, scenario, terminal_ratio):
    """The frozen line at the horizon, using the reproduction's own traffic.

    The observed record stops in 2024; the figure's frozen line runs to 2050. It
    can only get there on a projected driver, and the reproduction's is the one
    this repository can defend. Only ``rpk`` and ``ask`` exist in a scenario
    output, so an aircraft-km driver has no horizon value and says so.
    """
    if driver_name not in ("rpk", "ask"):
        return float("nan")
    series = scenario_series(driver_name, scenario)
    if horizon not in series.index:
        return float("nan")
    return float(anchor_value * series.loc[horizon] / base * terminal_ratio)


# --------------------------------------------------------------------------
# Derived quantities the document reports
# --------------------------------------------------------------------------


def epsilon_star(target_gt=ATAG_AVOIDED_GT, lo=-3.0, hi=0.0, tolerance=1e-5, **kwargs):
    """Elasticity at which R1 reproduces the published avoided figure.

    Bisection on a monotone function: more elastic demand suppresses more
    counterfactual traffic and so avoids less. If the published number is only
    recoverable at an elasticity outside every estimate in the literature, the
    figure is indefensible under any plausible parameterisation, which is a
    stronger statement than any point estimate of the error.

    Returns NaN when even zero rebound does not reach the target, which is the
    honest answer rather than an extrapolated root.
    """
    kwargs.setdefault("adaptation", "demand")

    def gap(eps):
        return frozen_baseline(elasticity=eps, **kwargs)["avoided_gt"] - target_gt

    if gap(hi) < 0.0:
        return float("nan")
    if gap(lo) > 0.0:
        return float("nan")
    while hi - lo > tolerance:
        mid = 0.5 * (lo + hi)
        if gap(mid) < 0.0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def stated_gain_composition():
    """Test how the report composes its own two stated efficiency gains.

    Page 16 states ~29 % from aircraft technology and 25 % from operations since
    1990, then reports 54 % combined. Two efficiency factors compose
    multiplicatively, not additively, so the two readings differ and only one
    can be right.
    """
    tech, ops, combined = ATAG_TECHNOLOGY_GAIN, ATAG_OPERATIONS_GAIN, ATAG_COMBINED_GAIN
    multiplicative = 1.0 - (1.0 - tech) * (1.0 - ops)
    additive = tech + ops
    return {
        "stated_technology": tech,
        "stated_operations": ops,
        "stated_combined": combined,
        "multiplicative": multiplicative,
        "additive": additive,
        "reading": (
            "additive"
            if abs(additive - combined) < abs(multiplicative - combined)
            else "multiplicative"
        ),
        "overstatement": combined - multiplicative,
        "implied_frozen_ratio_stated": 1.0 / (1.0 - combined),
        "implied_frozen_ratio_multiplicative": 1.0 / (1.0 - multiplicative),
    }


# --------------------------------------------------------------------------
# The counterfactual under the WCTR demand model
# --------------------------------------------------------------------------

# The coupled runs carry the history the demand model is driven by: population and
# income per capita from 2000, and the model's own historical energy cost per RPK.
# The history is the same in every one of them, whatever the carbon price.
COUPLED_RUN = ATAG / "3rd_edition_full_coupled_demand" / "data_outputs" / "ssp2_19_share.json"


def wctr_model():
    """The calibrated demand model exactly as AeroMAPS carries it.

    Its parameters are read from the class, so the elasticity and the delay used
    here are the ones the coupled scenarios use, not copies of them.
    """
    from aeromaps.models.air_transport.air_traffic.price_elasticity_logistic_income import (
        RPKLogisticIncomePriceElasticity,
    )

    return RPKLogisticIncomePriceElasticity(name="wctr", passenger_market_ids=[])


def wctr_history():
    """Population, income per capita and energy cost per RPK, 2000 to 2023."""
    from aeromaps.utils.results_view import load_results

    run = load_results(COUPLED_RUN, name="history")
    inputs, outputs = run.data["vector_inputs"], run.data["vector_outputs"]
    population = np.asarray(inputs["population_init"], dtype=float)
    years = np.arange(2000, 2000 + len(population))
    return pd.DataFrame(
        {
            "population": population,
            "gdp_per_capita": np.asarray(inputs["gdp_per_capita_init"], dtype=float),
            "price": outputs["doc_net_energy_per_rpk_mean"].reindex(years).to_numpy(dtype=float),
        },
        index=years,
    )


def wctr_counterfactual(window=WINDOW, scope=SCOPE_WTW_TO_TTW, anchor="klower", scenario="s1-TTW"):
    """The frozen-1990 counterfactual, with traffic set by the WCTR demand model.

    The model gives traffic per capita as a logistic function of income, times
    ``(P / P_ref) ** elasticity``, with ``P`` the energy cost per RPK after a
    first-order delay, and total traffic as that times population. Income and
    population are the same in the frozen world and the observed one, so they
    cancel from the ratio of the two; what is left is the ratio of the two
    delayed energy costs per RPK raised to the elasticity. From 2000 the model is
    evaluated in full on the population and income parameters, and the ratio is
    asserted to equal the price-only one. Before 2000 those parameters do not
    exist, and the price-only ratio, which is the same expression, is used.

    Energy cost per RPK is fuel price times energy per RPK. Frozen 1990 efficiency
    means the 1990 energy per RPK, so at the same fuel price the frozen cost is
    the observed cost times the ratio of the two energy intensities. The observed
    cost is the model's own historical series from 2000, extended back to 1990 with
    the jet fuel price and observed energy per RPK.

    Returns the same fields as :func:`frozen_baseline`, plus the elasticity and
    delay used, the two energy costs and the modelled traffic.
    """
    from aeromaps.models.air_transport.air_traffic.price_delay import apply_price_delay
    from aeromaps.models.air_transport.air_traffic.price_elasticity_logistic_income import (
        generalised_logistic_function,
    )

    model = wctr_model()
    elasticity, delay = model.price_elast, model.price_delay

    reference = frozen_baseline(window=window, scope=scope, anchor=anchor, scenario=scenario)
    years = reference["years"]
    observed = reference["observed"]
    e_1990 = reference["config"]["e_1990"]

    traffic = load_traffic()
    rpk = traffic["rpk"].reindex(years).to_numpy(dtype=float)
    activity = rpk / float(traffic["rpk"].loc[years[0]])
    intensity_ratio = e_1990 * activity / observed

    # Observed energy cost per RPK: the model's series where it has one, the jet
    # fuel price times observed energy per RPK before that, scaled to join it.
    history = wctr_history()
    fuel = jet_fuel_price().reindex(years).ffill().to_numpy(dtype=float)
    proxy = pd.Series(fuel * observed / rpk, index=years)
    first = int(history.index[0])
    cost_observed = proxy * (float(history["price"].loc[first]) / float(proxy.loc[first]))
    overlap = [year for year in history.index if year in cost_observed.index]
    cost_observed.loc[overlap] = history["price"].loc[overlap].to_numpy()
    cost_frozen = cost_observed * intensity_ratio

    start, end = int(years[0]), int(years[-1])
    delayed_observed = apply_price_delay(cost_observed, delay, start, end)
    delayed_frozen = apply_price_delay(cost_frozen, delay, start, end)
    price_ratio = (delayed_frozen / delayed_observed).to_numpy()
    traffic_ratio = price_ratio**elasticity

    # The model evaluated in full where its drivers exist, as a check that income
    # and population do drop out of the ratio.
    years_full = [y for y in history.index if y in delayed_observed.index]
    trend = generalised_logistic_function(
        history["gdp_per_capita"].loc[years_full],
        model.left_asymptote,
        model.capacity,
        model.growth_rate,
        model.logistic_nu,
        model.asymptote_coeff,
        model.x_lag,
    )
    price_ref = model.price_ref * model.eur_usd_exchange_rate
    traffic_observed = (
        history["population"].loc[years_full]
        * trend
        * (delayed_observed.loc[years_full] / price_ref) ** elasticity
    )
    traffic_frozen = (
        history["population"].loc[years_full]
        * trend
        * (delayed_frozen.loc[years_full] / price_ref) ** elasticity
    )
    modelled_ratio = (traffic_frozen / traffic_observed).to_numpy()
    offset = years_full[0] - start
    assert np.allclose(modelled_ratio, traffic_ratio[offset : offset + len(years_full)], rtol=1e-9)

    counterfactual = e_1990 * activity * traffic_ratio
    avoided = counterfactual - observed
    return {
        "years": years,
        "counterfactual": counterfactual,
        "observed": observed,
        "avoided": avoided,
        "avoided_gt": float(np.nansum(avoided) / 1000.0),
        "demand_ratio": traffic_ratio,
        "price_ratio": price_ratio,
        "elasticity": float(elasticity),
        "delay_years": float(delay),
        "cost_observed": cost_observed.to_numpy(),
        "cost_frozen": cost_frozen.to_numpy(),
        "model_years": [int(y) for y in years_full],
        "model_traffic_observed": traffic_observed.to_numpy(),
        "config": {**reference["config"], "adaptation": "wctr", "elasticity": float(elasticity)},
    }
