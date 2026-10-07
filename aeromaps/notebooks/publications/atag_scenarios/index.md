---
title: "Reviewing the Flight Plan: quantitative analysis and extensions of ATAG Waypoint 2050 scenarios"
authors:
  - name: Ian Costa-Alves
  - name: Antoine Salgas
  - name: Thomas Planès
  - name: Scott Delbecq
exports:
  - format: typst
    output: exports/waypoint2050-reproduction.pdf
kernelspec:
  name: python3
  display_name: Python 3
---

## Abstract

Several actors have drafted diverging visions for the future climate impact of air transport, among
them the Air Transport Action Group (ATAG) Waypoint 2050 stands as the industry vision of the
transition of the sector up until 2050. This paper aims to review and compare Waypoint 2050
scenarios across the three editions of the report, while quantifying emissions reductions achieved
from each of the mitigation levers presented. The methodology behind reproduction is described,
scenarios are simulated using the AeroMAPS open-source framework, and extensions of the Waypoint
scope are presented: coupling traffic growth to rising energy costs, and incorporating contrails
avoidance. The validation of scenarios was carried out on the aircraft technology variants alone,
with errors between 0.6 and 2.3 %. Besides technology, scenario variants are also explored
regarding traffic growth, operational improvements, and deployment of low-carbon fuels, yielding 144
possible combinations that span between 208 and 2359 Mt of well-to-wake residual CO₂ emissions in
2050. The three reference scenarios are reproduced with both well-to-wake and tank-to-wake
accounting scopes and lead to residual CO₂ emissions of about 1550 (1290, tank-to-wake), 420 (350),
and 360 (260) Mt. Exploring the demand-price coupling, which the reports explicitly refrain from
incorporating, reduces 2050 traffic by 2 to 22 % depending on the carbon price. Extending the
impact analysis into temperature impacts highlights the warming uncertainty, which is about four
times wider than the entire spread between the published scenarios. While the ATAG reports address
the modelling methods used for the quantification of aviation emissions, in a context where
policies are made based on such scenarios, the limited transparency hinders harmonization and
comparison with similar works. On this front, the authors advocate for the use of open-source and
open-data, which are greatly beneficial for making assumptions explicit and finding a common ground
for high-level decision making.

This document is the executable companion of the manuscript: its text follows the manuscript, and
every figure is drawn by the code cell above it from committed scenario outputs (see
[Reproducibility](#reproducibility)).

## Introduction

Historically the aviation sector witnessed significant environmental efficiency gains: in 2019 the
fuel burn per Revenue Passenger-Kilometer (RPK) reached 44 % (less than half) of its 1990 value
{cite:p}`bergero_pathways_2023`. These gains, driven by aircraft and propulsion technology, along
with operational efficiency, are significant when compared to other transportation modes
{cite:p}`eu-transport-efficiency`, where aviation shows the highest gains. Despite such efforts, the
CO₂ emissions of the sector increased 89 % (almost doubled) in the same period, as air traffic
demand significantly outpaced fuel burn reductions: from 1990 to 2019 RPK increased by 338 %.
However, CO₂ is only half of the story. From 1940 to 2018 only 34 % of aviation cumulative forcing
(expressed as net effective radiative forcing, ERF) came from CO₂ alone, the remaining 66 %
originating from non-CO₂ effects, although their associated uncertainty is roughly 8 times larger
than that of CO₂ {cite:p}`lee_contribution_2021`. Furthermore, while mitigation levers that tackle
CO₂ may also reduce non-CO₂ to some extent, this is still subject to ongoing research.

Achieving the Paris Agreement targets requires deep, rapid, and sustained emissions reductions
across all economic sectors. Aviation is considered a hard-to-abate sector whose mitigation relies
on a few levers with opposing effects on the cost of flying {cite:p}`delbecq_sustainable_2023`:
Sustainable Aviation Fuels (SAF), carbon pricing and Market-based measures (MBM) raise this cost,
while operational and vehicle efficiency are expected to lower the impact of increased fuel prices
to airlines and travelers. Besides its decarbonization policy, specific measures to tackle non-CO₂
have been formulated in the EU for monitoring these effects and including them in environmental
reporting {cite:p}`eu_nonco2_mrv`, and a revision of the EU Emissions Trading System (ETS) has been
proposed to allow airlines to claim carbon allowances from contrail avoidance strategies
{cite:p}`euets_contrails_2026`.

Among the numerous industrial {cite:p}`gifas,atag2026_waypoint,iata,airbus,boeing`, institutional
{cite:p}`icao,iea,icct,zheng_aviation_2025`, and academic
{cite:p}`sgouridis,terrenoire,grewe,klower,gossling,dray_cost_2022,franz,brazzola,bergero_pathways_2023,sacchi,costaalvesNOADS`
scenarios that have been made for aviation, the Air Transport Action Group (ATAG) Waypoint 2050
stands as the industry vision of the transition of the sector up until 2050. While the three
different editions of the report {cite:p}`atag2020_waypoint,atag2021_waypoint,atag2026_waypoint`
are rich in detail and figures for the next 25 years, the underlying methods and assumptions are
not always explicit nor reproducible. In the context where national and international policies are
derived from such scenarios, we argue for more openness regarding models, data, background
assumptions, limitations, and uncertainties. Furthermore, as highlighted by many academic works,
these industry and institutional scenarios do not account for the full climate impacts of aviation
{cite:p}`grewe,klower,brazzola,sacchi,zheng_aviation_2025`, nor for the feedback of policy-induced
cost increases on traffic demand {cite:p}`dray_cost_2022,gossling_covid-19_2021,costaalves_wctr`.

This work asks whether the ATAG third-edition scenarios can be reproduced transparently, lever by
lever, in the AeroMAPS {cite:p}`planes_aeromaps_2023` open-source framework. Furthermore, extra
capabilities of the framework are employed to demonstrate two points missing from all ATAG reports:
analysis of demand-side impacts of transition costs, and quantification of temperature impacts of
scenarios with different strategies for contrail avoidance.

### ATAG Waypoint Reports throughout editions

The first edition of the ATAG Waypoint 2050 report {cite:p}`atag2020_waypoint` was launched in
September 2020 during the COVID-19 crisis, when aviation experienced its greatest drop in traffic
levels seen in recent history. The report frames the pandemic as an opportunity for a "green
recovery" as the social function of air travel was put in question. By then, the official target
was to halve 2005 emission levels by 2050, and the sector's position as a hard-to-abate sector is
emphasized, mentioning that net zero could be achieved by 2060-2065. Four prospective scenarios are
presented:

- **S0: baseline/continuation of current trends**  
  Central range for traffic forecasts, conservative operational and technology improvements with a
  new generation of aircraft to enter into service by 2030-2035, SAF production is based on
  expected commitments made by then, carbon offsets are used as the principal lever to align
  emissions to emission reduction goals;
- **S1: pushing technology and operations**  
  Ambitious operational and technological improvements with conventional and hybrid-electric
  aircraft to enter into service by 2035-2040, progressive deployment of SAF is supposed to align
  scenario to industry goal by 2050, and offsets are used as a transition mechanism until 2050;
- **S2: aggressive sustainable fuel deployment**  
  Ambitious operational and technological improvements with conventional and disruptive aircraft
  configurations (blended wing body), but only using conventional propulsion based on jet-fuel, SAF
  deployment is accelerated and is supposed to align scenario to goals by 2035, offsets are used as
  a transition mechanism until 2035;
- **S3: aspirational and aggressive technology perspective**  
  Very ambitious technology improvements with larger deployment of unconventional aircraft (liquid
  hydrogen and hybrid-electric), SAF deployment is slower and partially aligns emissions to goals
  by 2050, offsets are used as a transition mechanism until 2050.

By 2021, member airlines of the International Air Transport Association (IATA) increased their
climatic ambition by adopting net-zero emissions by 2050 as a target {cite:p}`iata2021_netzero`, and
a new edition was published in the same year {cite:p}`atag2021_waypoint`. The second edition reuses
the same scenario definitions as the first one, but when quantifying the role of each mitigation
lever, it lowers expected emissions reductions for operations and technology, and significantly
increases the expected reductions from deploying SAF. The need for carbon offsets is also revised
upwards, as no scenario reaches the new goal of net zero without resorting to them.

Finally, the third edition was launched in 2026, as traffic levels are reaching all-time records
after the recovery from the pandemic crisis, and assumes a position more focused on practical
implementation of policies and the necessary regulatory framework to turn vision into reality. This
edition removes the S3 scenario, to reflect delayed expectations for aircraft with unconventional
propulsion systems, and switches the ordering and naming of scenarios: the **S1: focus on SAF
deployment** is inspired by the S2 of previous versions, and **S2: technology-centric market** is
similar to the previous S1. Regarding the extent of each of the mitigation levers, both operations
and technology display similar expectations compared to their analogous scenario in the previous
version, SAF deployment is revised to reflect delays due to policy coordination failures and
investment bottlenecks, but is still seen as the main lever for emissions reductions and delays are
compensated by assuming a stronger ramp-up of production volumes. The role of offsets is also
revised upwards and with more detailed modelling to reflect current policies: regionally-resolved
offsets are estimated based on the implementation of the Carbon Offsetting and Reduction Scheme for
International Aviation (CORSIA) until 2035, and an extra policy is assumed to be put in place after
that to allow for reaching net-zero by 2050.

The S0 charts of the three editions show the contribution of each of the modelled mitigation levers
to the baseline scenario. Overall, with every new edition the expected emissions reductions
attributable to fleet renewal, next generation aircraft technology, and operational efficiency are
revised downwards, while those attributable to SAF are revised upwards. The second edition increased
expected baseline emissions, while increasing ambition regarding emissions reductions, for which the
role of SAF increased (both in low and high SAF cases). The third edition also increased the role of
SAF in the low case, but revised the high case back to expectations of the first edition.

### Methodological critique of ATAG Waypoint scenarios

> "Omitting key variables simply because data are lacking is effectively equivalent to assigning
> them a value of zero, arguably the only value that is certain to be incorrect"
> {cite:p}`sterman2000`.

Besides the over-reliance of the Waypoint scenarios on SAF, two methodological critiques are also
made regarding the analysis carried out by ATAG:

- **Exogenous demand:** air traffic demand follows central industry forecasts unaffected by
  transition costs, even though energy carriers are several times costlier than kerosene has been in
  recent history and future carbon prices are expected to rise steeply to align with scenarios
  compatible with the Paris Agreement. The emissions reductions attributed to each lever are
  therefore estimated supposing traffic volumes are the same regardless of how strong SAF and carbon
  pricing policies are. "Accurate assessment of demand impacts across multiple market types, in
  multiple currencies and very different dynamics was not a task undertaken for the Waypoint 2050
  global analysis. Scenarios in this analysis, therefore, do not include feedback effects on global
  aviation traffic from potential costs of decarbonization" {cite:p}`atag2026_waypoint`;
- **Climate impacts:** besides CO₂ emissions, non-CO₂ effects carry the majority of aviation's
  historical forcing and are dominated by contrail cirrus, for which operational strategies exist
  and are not expected to be costly relative to decarbonization. The report's conclusion that "the
  current priority for industry and government climate action should continue to be CO₂ emissions
  reduction (where there is high scientific certainty)" {cite:p}`atag2026_waypoint` is not in line
  with the scientific literature that states that, despite their high associated uncertainties,
  contrail avoidance is shown to allow for significant reductions in climate impact, all while being
  cheaper and easier to scale relative to SAF {cite:p}`zheng_aviation_2025`.

```{code-cell} python
:tags: [hide-input]

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from aeromaps import assemble_processes
from aeromaps.plots.climate_mechanisms import MECHANISM_COLORS, MECHANISM_GROUPS, group_temperature
from aeromaps.utils.results_view import load_results
from aeromaps.utils.scenarios import find_scenario
from aeromaps.utils.yaml import read_yaml_file
from aeromaps.models.impacts.generic_energy_model.common.energy_carriers_manager import (
    build_pathways_manager,
)

HERE = Path.cwd()

FIGURES = []


def save_fig(fig=None, name=None):
    """Number every figure in document order and write it to exports/ for the PDF build.

    Execution order equals document order in a MyST build, so the numbering the
    reader sees and the numbering on disk are the same. exports/ is gitignored,
    so none of these enter a commit.

    A `name` additionally writes exports/<name>.pdf. The manuscript references
    those rather than the ordinals, so adding or dropping a figure here does not
    silently repoint every \includegraphics in the LaTeX.
    """
    fig = plt.gcf() if fig is None else fig
    FIGURES.append(fig)
    out = HERE / "exports"
    out.mkdir(exist_ok=True)
    fig.savefig(out / f"fig_{len(FIGURES)}.pdf", bbox_inches="tight")
    if name:
        fig.savefig(out / f"{name}.pdf", bbox_inches="tight")
    # Deliberately returns nothing: a cell whose last statement is a bare
    # save_fig call would echo the figure and render it a second time.


def results(edition, scenario, label, produced_by):
    """Load a committed scenario, or explain what to run if it is not there yet."""
    path = HERE / edition / "data_outputs" / f"{scenario}.json"
    if not path.exists():
        print(f"PENDING: {path.relative_to(HERE)} has not been generated yet.\n"
              f"         Run {produced_by} to produce it.")
        return None
    return load_results(path, name=label)


S0 = results("3rd_edition_light", "s0", "S0 reference", "3rd_edition_light/s0.ipynb")
S1 = results("3rd_edition_full", "s1", "S1 SAF-focused", "3rd_edition_full/s1.ipynb")
S2 = results("3rd_edition_full", "s2", "S2 technology-centric", "3rd_edition_full/s2.ipynb")

scenarios = {view.name: view for view in (S0, S1, S2) if view is not None}
comparison = assemble_processes(scenarios) if scenarios else None

# The same three scenarios in the reports' own tank-to-wake scope, and the two
# technology anchors the ATAG lever split needs: T0 is the frozen fleet, T1 is
# fleet renewal with nothing beyond it.
S0_TTW = results("3rd_edition_light", "s0-TTW", "S0 reference", "3rd_edition_light/s0.ipynb")
S1_TTW = results("3rd_edition_full", "s1-TTW", "S1 SAF-focused", "3rd_edition_full/s1.ipynb")
S2_TTW = results("3rd_edition_full", "s2-TTW", "S2 technology-centric", "3rd_edition_full/s2.ipynb")
T0 = results("3rd_edition_full", "t0", "T0", "3rd_edition_full/validation.ipynb")
T1 = results("3rd_edition_full", "t1", "T1", "3rd_edition_full/validation.ipynb")
T0_TTW = results("3rd_edition_full", "t0-TTW", "T0", "3rd_edition_full/validation.ipynb")
T1_TTW = results("3rd_edition_full", "t1-TTW", "T1", "3rd_edition_full/validation.ipynb")

print(f"loaded {len(scenarios)} scenarios: {', '.join(scenarios)}")
```

## Materials and Methods

Prospective analysis requires a mathematical model capable of describing: how the current reality
was reached from a past state, as well as which future realities may be reached from the current
state. Furthermore, in the case where disruptions in past trends are foreseen, possible evolution
paths of associated drivers must be quantified as well as their system-level impacts. In doing so,
if impacts are great enough to invalidate assumptions established by the mathematical model, a new
model proposition has to be made, and the cycle is repeated.

This means that both the analysis and the models used for it are continuously improved. However,
most prospective groups treat it as a sequential problem (see the N2 diagram below, continuous
lines): first a reference air traffic forecast is used based on annual growth rates of RPK, then
operational improvements in seat occupancy allow reducing Available Seat Kilometers (ASK) supply for
a given RPK demand; further improvements in operations allow reducing fuel burn by improving flight
trajectories and network, renewal of aircraft models within the fleet can also allow for further
reductions in fuel per ASK supply and are also subject to deployment on future aircraft concepts.
Besides the efficiency levers that intend to decouple demand from fuel/energy consumption, the
incorporation of SAF intends to reduce the carbon content per unit of fuel consumed by using
alternative production pathways for kerosene-like molecules, then residual unabated emissions are
addressed by MBMs by financing out-of-sector offsets or negative emissions technologies.

```{figure} diagrams/n2_sequential.svg
:name: fig-n2-sequential

**Sequential chain and coupled analysis loop.** N2 diagram of a scenario. Disciplines sit on the
diagonal in the order they run. Outputs leave along a row and feed the blocks below its column. The
chain employed by the reports lies along the diagonal (solid blue line). This work adds a background
scenario, with population, gross domestic product (GDP) and carbon price, and the cost-to-demand
feedback below the diagonal (dashed magenta line), which the Multidisciplinary Design Optimization
(MDO) framework iterates to a fixed point. The diagram is drawn from `diagrams/n2_sequential.tex`.
```

Scenario variants are developed for each lever: high/central/low traffic (H/C/L),
frozen/baseline/conservative/new configurations/non-drop in aircraft technology (T0-T4),
low/mid/high operational improvements (O1-O3), stated policies/aggressive deployment/technology-centric
SAF deployment (F1-F3). The three published scenarios correspond to points on that grid: S0 combines
central traffic, conservative aircraft technology and operational improvements, and stated policies
for SAF production (C·T2·O2·F1); S1 increases ambition regarding aircraft, operations, and SAF
(C·T3·O3·F2); and S2 increases ambition, relative to S1, regarding aircraft technology and decreases
ambition regarding SAF (C·T4·O3·F3). MBMs are not swept independently, since they are computed as
the residual required to reach the stated target and therefore do not represent an extra degree of
freedom. The full factorial scenario exploration, sweeping all possible combinations of levers, is
also not carried out in the ATAG analysis, but can be drawn after a full reproduction of these
assumptions.

One advantage of reproducing each lever separately is the possibility of combining different levels
of ambition for each lever. For example, the radar chart below places the three published scenarios
on the entire grid of scenario combinations and the sweep after it shows the outcomes of each of the
144 different scenarios from all possible combinations of traffic, technology, operations and fuel,
including a no-SAF level F0. Residual emissions in 2050 range from 208 to 2359 Mt. The published
scenarios sit in neither corner of this range. Three scenarios cannot show which combinations are
plausible, or which lever drives the spread.

```{code-cell} python
:tags: [hide-input]

import itertools

# The lever grid on one chart: a spoke per lever, each ordered outward from the
# least to the most mitigation, so that a larger polygon is a more ambitious
# scenario. Traffic therefore runs from high to low, and SAF by its 2050 volume,
# which puts F3 (about 280 to 380 Mt) before F2 (about 430 Mt). The 144 swept
# combinations are drawn faintly behind the three published scenarios.
RADAR_LEVERS = [
    ("Traffic", ["High", "Central", "Low"]),
    ("Aircraft technology", ["T1", "T2", "T3", "T4"]),
    ("Operations", ["O1", "O2", "O3"]),
    ("SAF", ["F0", "F1", "F3", "F2"]),
]
RADAR_SCENARIOS = {
    "S0": (["Central", "T2", "O2", "F1"], "#2a78d6", "-", "o"),
    "S1": (["Central", "T3", "O3", "F2"], "#eb6834", "--", "s"),
    "S2": (["Central", "T4", "O3", "F3"], "#1baf7a", ":", "D"),
}


def radar_radius(lever, level):
    levels = dict(RADAR_LEVERS)[lever]
    return (levels.index(level) + 1) / len(levels)


# Drawn on plain axes rather than polar ones, so each level label can sit beside
# its spoke, offset at right angles to it, instead of on top of the markers.
radar_angles = np.linspace(0, 2 * np.pi, len(RADAR_LEVERS), endpoint=False)


def radar_xy(angle, radius):
    return radius * np.sin(angle), radius * np.cos(angle)


def radar_polygon(radii):
    xs, ys = zip(*[radar_xy(angle, radius) for angle, radius in zip(radar_angles, radii)])
    return list(xs) + [xs[0]], list(ys) + [ys[0]]


fig, ax = plt.subplots(figsize=(6.2, 6.4), layout="constrained")
ax.set_aspect("equal")
ax.axis("off")
ax.set_xlim(-1.45, 1.75)
ax.set_ylim(-1.3, 1.3)

for angle, (name, levels) in zip(radar_angles, RADAR_LEVERS):
    ax.plot(*zip(radar_xy(angle, 0), radar_xy(angle, 1.0)), color="0.75", linewidth=0.8,
            zorder=0)
    # Names on the side spokes are anchored at their inner edge, so a long one
    # grows away from the chart instead of over its last level.
    horizontal = "left" if np.sin(angle) > 0.5 else "right" if np.sin(angle) < -0.5 else "center"
    ax.text(*radar_xy(angle, 1.1 if horizontal != "center" else 1.17), name, fontsize=10,
            ha=horizontal, va="center")
    # Unit vector at right angles to the spoke, for the level labels.
    side = np.array([np.cos(angle), -np.sin(angle)]) * 0.08
    for level in levels:
        x, y = radar_xy(angle, radar_radius(name, level))
        ax.plot(x, y, marker="o", markersize=3, color="0.6", zorder=1)
        ax.text(x + side[0], y + side[1], level, fontsize=7.5, color="0.3",
                ha="center", va="center", zorder=5,
                bbox=dict(boxstyle="round,pad=0.12", facecolor="white", edgecolor="none",
                          alpha=0.85))

# The swept grid, faint.
for combination in itertools.product(*[levels for _, levels in RADAR_LEVERS]):
    radii = [radar_radius(name, level) for (name, _), level in zip(RADAR_LEVERS, combination)]
    ax.plot(*radar_polygon(radii), color="0.55", linewidth=0.5, alpha=0.08, zorder=1)

# The three published scenarios, each with its own colour, line style and marker,
# so they stay apart where S1 and S2 share a level.
for label, (levels, colour, style, marker) in RADAR_SCENARIOS.items():
    radii = [radar_radius(name, level) for (name, _), level in zip(RADAR_LEVERS, levels)]
    xs, ys = radar_polygon(radii)
    ax.plot(xs, ys, color=colour, linestyle=style, linewidth=2, marker=marker, markersize=6,
            label=f"{label} ({'-'.join(levels)})", zorder=3)
    ax.fill(xs, ys, color=colour, alpha=0.06, zorder=2)
ax.plot([], [], color="0.55", linewidth=0.8, alpha=0.5, label="The 144 swept combinations")
fig.legend(loc="outside lower center", ncol=2, fontsize=8.5, frameon=False)
save_fig(fig, name="lever_radar")
```

*Grid of scenario variants. Each spoke is a lever, ordered from least to most ambitious mitigation,
the published scenarios are in colour and the 144 swept combinations in grey.*

```{code-cell} python
:tags: [hide-input]

import sys

sys.path.insert(0, str(HERE / "3rd_edition_variants"))
try:
    import sweep

    tidy = sweep.read_results()
    summary = sweep.summarise(tidy, year=2050)
    residual = summary.set_index(["traffic", "technology", "operations", "saf"])["co2_emissions"]
    print(f"2050 residual CO2 across the 144-cell grid [Mt]")
    print(f"  min    {residual.min():8.0f}   ({residual.idxmin()})")
    print(f"  median {residual.median():8.0f}")
    print(f"  max    {residual.max():8.0f}   ({residual.idxmax()})")
    for name, cell in sweep.PUBLISHED_CELLS.items():
        print(f"  {name}     {residual.loc[cell]:8.0f}   ({cell})")
    # Coloured by traffic, which is the only lever separating all five panels and
    # the one the reports hold exogenous, so the fan it opens is the range their
    # own scenarios cannot express.
    sweep.plot_grid(tidy, color_by="traffic")
    save_fig(name="lever_sweep")
except FileNotFoundError:
    print("PENDING: the sweep results have not been generated yet.\n"
          "         Run 3rd_edition_variants/sweep.ipynb to produce them.")
```

*Outcomes of scenario variants. Emissions of all 144 combinations, coloured by traffic, with the
published scenarios in black; the histograms give the 2050 values.*

Finally, the AeroMAPS framework is also employed to demonstrate how to break out of the sequential
approach by removing one key assumption kept by all three editions: that traffic growth will not be
affected by rising transition costs, which creates a demand-price coupling that cannot be solved
with purely sequential approaches. The N2 diagram above shows this chain, with the demand-price
coupling marked in dashed lines.

### AeroMAPS

Employing open-source tools to simulate policy scenarios can be highly beneficial for making
modelling assumptions explicit, improving the reproducibility of policy objectives, and supporting a
common ground for high-level decision-making. In this context, the present work uses AeroMAPS
{cite:p}`planes_aeromaps_2023`, an open-source sectoral integrated assessment framework for air
transport designed to represent prospective aviation scenarios and their environmental impacts
across multiple disciplinary fields.

AeroMAPS is organised as a graph of disciplinary modules that are solved together based on the
GEMSEO library {cite:p}`gemseo`: modules explicitly define their inputs and outputs through variable
names, allowing the solver to automatically handle model integration, execution sequence, numerical
couplings and feedback loops (necessary features for the demand-price coupling showcased later). The
framework was developed to be relatively easy to use and widely distributable among academic,
institutional, and industrial stakeholders, while enabling sectoral environmental sustainability
assessments and the evaluation of transition strategies. Its modular architecture also facilitates
the integration of models from different disciplinary fields and allows for dynamic model assembly,
which means simulation can be tailored to analysis of different scopes regarding:

- **Geographic coverage:** a scenario can be simulated either with a single global or regional
  (continent, country) level depending on the analysis geographic scope, or with multiple
  simultaneous regions solved together, where each has a tailored traffic, fleet and fuel policy,
  which are then aggregated together. Both are used here: the third-edition S1 and S2 scenarios are
  global, while the S0 reference is an aggregation of a twenty-region run with country-level SAF
  mandates based on current policies {cite:p}`salgas_pledges_2026`;
- **Market segmentation:** the split of global traffic into segmented markets is also left open,
  each with its own traffic driver, energy intensity and, where the demand-price coupling is active,
  its own price elasticity. The reproduction uses four: short, medium and long range passenger
  traffic in RPK, and freight in Revenue Tonne Kilometers (RTK);
- **Fleet renewal:** within each market, fleet-wise reductions in fuel-burn can be either modelled
  based on market-aggregated efficiency gains figures (top-down) or by splitting supply among
  different aircraft categories/subcategories/models each with its own energy consumption, market
  penetration, and subject to fleet renewal rates (bottom-up);
- **Energy production pathways:** each carrier is resolved into named production pathways carrying
  their own cost, emission factor and upstream resource demand, so that the fleet-average costs and
  carbon intensity follow the mix of several different production pathways. For instance, the S0
  scenario (which does not specify which types of SAF are expected to be deployed) aggregates the
  biomass pathways into a single generic carrier, the SAF-focused S1 scenario deploys seven biomass
  pathways, alongside electrofuel, and fossil kerosene, while technology-focused S2 scenario also
  adds liquid hydrogen and battery charging to the carriers set;
- **Emission scopes:** the standard accounting method in the ATAG reports is tank-to-wake (TtW)
  following the CORSIA methodology, which includes only emissions from combustion, however AeroMAPS
  default is to report them in well-to-wake (WtW) scope, which includes emissions that happen
  upstream in the fuel production lifecycle. Every scenario considered here is run in both scopes,
  as a pair of otherwise identical configurations;
- **Cost analysis:** fuel production costs, aircraft direct operating costs (DOC), carbon prices and
  marginal abatement costs are available, at a top-down resolution taking an aggregate cost per unit
  energy, or at a bottom-up one built from plant capital expenditure, operating costs and
  construction lead times. The top-down formulation is used throughout this reproduction, since it
  corresponds to the resolution published by the reports.

For more details on the software architecture, simulation workflow, and some model components
readers are referred to {cite:t}`planes_aeromaps_2023`. New developments have been carried out since
then to keep up with and advance the state-of-the-art regarding modeling: energy economics
{cite:p}`salgas_cost_2023,salgas_marginal_2024`, fleet renewal {cite:p}`viry_empirical_2024`,
temperature impacts {cite:p}`arriolabengoa_lightweight_2024`, prospective life-cycle assessment
{cite:p}`pollet_comprehensive_2024`, cost minimization of fuel mandates
{cite:p}`salgas_techno-economic_2025`, timing of entry-into-service of maturing propulsion systems
with energy constraints {cite:p}`costaalvesNOADS`, long-term behavioral impacts of policies on
traffic demand {cite:p}`costaalves_wctr`, and the impact of country-level SAF policies
{cite:p}`salgas_pledges_2026`, whose regional breakdown of emissions under current policies is the
basis of the S0 reference.

### Validation

Reproducing a scenario whose assumptions are partially published requires being explicit regarding
the origin of input values. Four classes are distinguished, in decreasing order of confidence:
values read directly from the text (operational assumptions), values digitized from published
figures (traffic, load factor, SAF production per pathway), values calibrated so that outcomes
reproduce their digitized trajectories (annual efficiency improvements from fleet renewal and next
generation aircraft technology), and values filled based on extra assumptions where the reports
disclose nothing that would constrain them (kerosene cost, carbon prices, electricity emission
factor).

The calibration of efficiency improvements was carried out based on the aircraft technology lever.
Even though the ATAG reports detail which technologies are expected to decrease the consumption of
future models, their expected energy consumption, market shares, and renewal rates are not explicit,
which motivated the choice for a top-down fleet model instead of the bottom-up one. All markets are
considered to have the same annual efficiency gains, whose values are chosen in order to reproduce
the emissions trajectory of technology-only scenarios:

- **T0 - Frozen fleet efficiency:** illustrative scenario with no further renewal of old aircraft
  models;
- **T1 - Baseline:** old aircraft are replaced by existing aircraft, but no new models are deployed;
- **T2 - Conservative:** new generation of tube-and-wing aircraft with conventional propulsion;
- **T3 - New configurations:** new propulsion systems (open-fan) up to 300 seat categories, radical
  aircraft configurations (blended wing-body, high aspect-ratio wings) in the 211-300 seat category;
- **T4 - Towards non-drop in energies:** batteries and liquid-hydrogen aircraft below 100 seat,
  hybrid propulsion systems in remaining seat categories.

These scenarios allow reproducing efficiency gains and emission reductions achieved by aircraft
technology alone, without the addition of any other mitigation levers. The figure below compares
values obtained after the calibration of annual efficiency gains against the report's digitized
curves in the TtW scope used by the report. The WtW emissions are also exported, as the appendix
figure of the manuscript.

```{code-cell} python
:tags: [hide-input]

tech_wtw = {}
tech_ttw = {}
for i in range(5):
    wtw = HERE / "3rd_edition_full" / "data_outputs" / f"t{i}.json"
    ttw = HERE / "3rd_edition_full" / "data_outputs" / f"t{i}-TTW.json"
    if wtw.exists():
        tech_wtw[f"T{i}"] = load_results(wtw, name=f"T{i}")
    if ttw.exists():
        tech_ttw[f"T{i}"] = load_results(ttw, name=f"T{i}")

# The report's own published curves, digitised from its charts. They are
# tank-to-wake, so they belong on that panel and nowhere else.
import yaml  # noqa: E402

with open(HERE / "report_data" / "atag_3rd_edition_figures.yaml") as handle:
    report = yaml.safe_load(handle)

if tech_wtw and tech_ttw:
    # As with the decomposition, one figure per scope: the tank-to-wake one
    # carries the comparison against the report's own curves and belongs with the
    # text, and the well-to-wake twin goes to the appendix on the same scale.
    fig_ttw, ax_ttw = plt.subplots(figsize=(6.4, 4.2), layout="constrained")
    assemble_processes(tech_ttw).plot("co2_emissions_comparison", fig=fig_ttw, ax=ax_ttw)
    fig_wtw, ax_wtw = plt.subplots(figsize=(6.4, 4.2), layout="constrained")
    assemble_processes(tech_wtw).plot("co2_emissions_comparison", fig=fig_wtw, ax=ax_wtw)

    for index, (name, curve) in enumerate(sorted(report["technology_scenarios"].items())):
        ax_ttw.plot(curve["years"], curve["values"], ":", color=f"C{index}", linewidth=1.6,
                    label=f"{name} - report")
    ax_ttw.legend(fontsize=7, ncol=2)

    ax_ttw.set_title("Tank-to-wake, against the report")
    ax_wtw.set_title("Well-to-wake")
    y_max = max(ax_wtw.get_ylim()[1], ax_ttw.get_ylim()[1])
    ax_ttw.set_ylim(0, y_max)
    ax_wtw.set_ylim(0, y_max)
    save_fig(fig_ttw, name="technology_scopes")
    save_fig(fig_wtw, name="technology_scopes_wtw")

    at_2050 = {name: np.interp(2050, curve["years"], curve["values"])
               for name, curve in report["technology_scenarios"].items()}
    print("2050 CO2 [Mt], reproduced tank-to-wake against the report's own curves:")
    for name in sorted(at_2050):
        ours = tech_ttw[name].data["vector_outputs"]["co2_emissions_including_energy"].loc[2050]
        print(f"  {name}  reproduced {ours:8.1f}   report {at_2050[name]:8.1f}"
              f"   {100 * (ours / at_2050[name] - 1):+6.2f} %")
else:
    print("PENDING: technology comparison outputs not generated yet. Run "
          "3rd_edition_full/validation.ipynb.")
```

*Aircraft technology variants without other levers. TtW CO₂ emissions of the five technology
scenarios after calibration (solid) against the report's curves (dotted). T0: Frozen fleet
efficiency, T1: Baseline, T2: Conservative, T3: New configurations, T4: Towards non-drop in
energies.*

The resolution at which SAF is published differs across the scenarios: the S1 and S2 fuel levels
are displayed per-pathway resulting in eleven energy carrier types overall, whereas the S0 level
publishes a total volume with no pathway breakdown and is therefore modelled as a single generic
carrier which includes both stated policies and goals for SAF. The present work, instead, derives
the S0 baseline scenario from stated policies alone, based on a multi-regional aggregation of
country-level SAF policies {cite:p}`salgas_pledges_2026`, and yields lower volumes than the ATAG
analysis.

Finally, another assumption that makes these scenarios stray further away from a pure reproduction
of ATAG is regarding MBMs. Up until 2035, the third edition estimates offsets regionally based on
CORSIA, whose ambition is only to reach a stabilization of emissions instead of decreasing residuals
until reaching net-zero in 2050. From 2035 onwards, the ATAG reports assume extra policies that
offset increasing shares of residual emissions such that net-zero is reached by 2050. This work also
reproduces regionally-resolved offsets based on CORSIA up to 2035; from 2035 onwards there is no
certainty that offsetting policies will strive for stabilizing emissions or net-zero emissions.
Therefore, the S0 baseline reproduced here assumes a continuation of the current policy until 2050,
which differs from the report's S0 assumption that offsetting will target net-zero by 2050. For the
S1 and S2 scenarios, on the other hand, from 2035 until 2050 scenarios are assumed to reduce
net-emissions in a linear pace until net-zero. While the report may vary this pace depending on each
scenario, this work chooses to harmonize results by comparing residual emissions, as there is little
visibility on the future policies targeting net-emissions beyond 2035.

| Scenario | 2030 [Mt] | 2040 [Mt] | 2050 [Mt] | 2024–2050 [Gt] |
|---|---|---|---|---|
| T0 | −16.4 (−1.3 %) | −35.9 (−2.1 %) | −52.0 (−2.2 %) | −0.87 (−2.0 %) |
| T1 | +26.5 (+2.1 %) | +29.4 (+1.7 %) | +18.1 (+0.8 %) | +0.73 (+1.7 %) |
| T2 | +26.5 (+2.1 %) | +24.0 (+1.4 %) | +11.4 (+0.5 %) | +0.65 (+1.5 %) |
| T3 | +26.5 (+2.1 %) | +25.5 (+1.5 %) | +26.1 (+1.1 %) | +0.74 (+1.7 %) |
| T4 | +26.5 (+2.1 %) | +22.5 (+1.3 %) | −35.3 (−1.5 %) | +0.45 (+1.0 %) |
| S0 | +45.7 (+3.6 %) | +63.5 (+3.6 %) | +146.6 (+6.2 %) | +2.26 (+5.1 %) |
| S1 | +17.9 (+1.4 %) | +64.2 (+3.7 %) | −45.3 (−1.9 %) | +0.87 (+2.0 %) |
| S2 | +10.7 (+0.8 %) | +89.2 (+5.1 %) | −101.1 (−4.3 %) | +0.82 (+1.9 %) |

*Validation against the report's curves. Error of the reproduced annual CO₂ emissions against the
third edition, TtW, in Mt (Gt for the cumulative column), with in brackets the error as a share of
the frozen-fleet (T0) emissions of the same year. Positive values mean the reproduction is higher.
T0 to T4 are compared with hand-digitised curves, S0 to S2 with curves traced from the report
charts. T0 is the frozen fleet and T1 the fleet renewed with existing aircraft, and neither includes
operations, fuels or MBMs. Both sides are gross emissions, before offsets. The report adds a hatched
band above S0 and S2, to represent an optimistic case of SAF deployment, which is covered by offsets
otherwise. Counting it as SAF moves the 2050 error from +147 to −37 Mt for S0, and from −101 to
−354 Mt for S2. The cumulative column starts in 2024, where the report curves begin.*

:::{include} report_data/lever_validation.md
:::

*Validation of each lever. Error of the abatement of each lever against the report's charts, TtW, in
Mt (Gt for the cumulative column), with in brackets the error as a share of the frozen-fleet (T0)
emissions of the same year. Positive values mean the reproduction attributes more abatement to the
lever. The report bands are traced from the report at 600 dpi and match its printed 2050 shares
within 1.0 point. Bands thinner than one pixel, about 5 Mt, cannot be read and are marked with a
dash. SAF is compared with and without the hatched band. Two rows differ by construction: S0 fuel
comes from stated country policies, and MBMs follow the offset path harmonised in the Methods.*

### Coupling air traffic and fuel prices

Transportation research links many economic, demographic, and geographic factors as drivers to
passenger and freight demand {cite:p}`european_conference_of_ministers_of_transport_managing_2003`.
In the context of climate mitigation scenarios, a specific focus is drawn to quantifying the impact
of variables that are affected by climate policies and climate damages, such as population,
per-capita income, and prices. These global analyses are the subject of the Working Group 3 (WG3) of
the Intergovernmental Panel on Climate Change (IPCC), and the quantitative data obtained from
scenarios analysed in their 6th Assessment Report (AR6) are openly available {cite:p}`ar6_database`.

In order to couple the costs of future policies to demand, a model of aggregate RPK demand has been
formulated and calibrated on historical data {cite:p}`costaalves_wctr`. The model uses: S-curves to
estimate trend per-capita demand from GDP per capita accounting for the stabilization of demand
growth as emergent aviation markets mature, long-run price sensitivity accounting for fluctuations
of fuel prices and the historical decrease in energy intensity, and delays between perceived airline
costs and transmission of airfares onto travelers. One limitation of this approach is that the price
elasticity is calibrated on the energy cost per RPK, not on the full airfare: the calibrated
elasticity of -0.345 would yield an airfare-equivalent price elasticity of -1.456 supposing 23.7 %
of the airfare is composed of fuel.

:::{include} literature/tables/demand_price.md
:::

As shown in the N2 diagram, two additions are made relative to the standard AeroMAPS simulation:
first a background is chosen based on a Shared Socioeconomic Pathways (SSP) scenario from the AR6
scenario database {cite:p}`ar6_database` impacting the future GDP, population, and carbon price
trajectories; and a bidirectional coupling is made between airline costs and air traffic, where
costs are estimated based on supply volumes (ASK) and demand volume (RPK) is estimated based on
supply cost. Another limitation of this approach is the fact that the connection to the background
system is considered as a soft-link, because the background is static and not updated to react to
changes in the air transport system, therefore the economic impacts of aviation-specific policies
are supposed to be minor relative to the wider impacts of background climate damages and the cost of
climate mitigation policies.

The incorporation of SAF in ATAG is reported in terms of total production volumes, while AeroMAPS
allows for both volume-based and mandate-based incorporation based on blending shares. As total
traffic varies within each iteration of the fixed-point problem, the volume-based incorporation
leaves fossil kerosene as the variable to be adjusted to traffic. This however is not consistent
with the form in which most SAF policies are adopted, which are mostly based on mandates (ReFuelEU,
UK and Brazilian schemes), therefore the ATAG quantities are converted into mandates before the
iterations begin. Also, instead of the kerosene price assumed by the reports, the coupled runs hold
from 2026 onwards a price taken from the distribution of the last 20 years of the weekly U.S. Gulf
Coast kerosene-type jet fuel spot price {cite:p}`eia_jetfuelprice`: the lower quartile under
SSP2-4.5, the mean under SSP2-2.6 and the upper quartile under SSP2-1.9, so that the pathway with the
strongest mitigation also faces the most expensive fossil fuel. In August 2026 dollars, the real
mean is 3.03 \$/gal, the lower quartile 2.22 and the upper quartile 3.95. Furthermore, the carbon
price assumed by the background scenario is supposed to start in 2027 in all pathways and to be
added to airline costs based on fuel WtW emissions. The table above compares this approach with
other studies of the same question, extending the comparison of {cite:t}`costaalves_wctr` to add
more roadmaps depending on their approach.

### Climate response and contrail avoidance

Broadening the scope from decarbonization into climate mitigation requires including non-CO₂
effects like contrails and nitrogen oxides (NOx) emissions. Furthermore, it requires a unified impact
metric in order to compare the short-lived and highly uncertain non-CO₂ warming with that of CO₂,
which is long-lived and less uncertain. The issue, however, is that there is no consensus on how to
compare them, and this choice may inherently emphasize some climate effects over others
{cite:p}`megill_alternative_2024`.

This work bypasses the need for such CO₂-equivalence metrics by using climate emulators based on the
Finite amplitude Impulse Response (FaIR) model {cite:p}`millar_fair_2017,leach_fair2_2021`, which
are able to compare mitigation strategies in terms of temperature impacts, and are lightweight
enough to allow for propagating climate-system uncertainties
{cite:p}`arriolabengoa_lightweight_2024`. Emissions are disaggregated per gas species acting as a
climate forcer. These enter as sources in a set of gas pools (stocks that accumulate a share of
emissions and deplete through sinks with a characteristic lifetime), and atmospheric concentrations
increase when sources outweigh sinks across all pools. Changes in concentrations lead to ERF
imbalances, which warm a climate system discretized into thermal boxes and change the global mean
temperature. Finally, the timescales of the sinks adjust to the state of the climate system at each
instant (concentration, temperature, and total volume stocked in sinks).

Even though contrails have a net warming impact on the climate, they are not considered as
greenhouse gases and therefore cannot have an associated atmospheric concentration. Therefore, the
estimation of their radiative forcing (RF) is based on the total flight distance
{cite:p}`lee_contribution_2021` and also on the overall particle number of the engine exhaust
{cite:p}`burkhardt_mitigating_2018`. Indeed, blending SAF with fossil kerosene can lead to a
reduction in soot emissions due to their lower aromatic content {cite:p}`voigt_cleaner_2021`,
resulting in a reduction in overall contrail impact aside from the lower carbon content. One
limitation of this aggregated approach is the inability to separate effects of different individual
flights, which is not suited for simulating SAF targeting strategies
{cite:p}`teoh_targeted_2022` where SAF is concentrated in few flights instead of spread over many
flights for minimizing climate impact with a limited supply.

Furthermore, the contrails generated by hydrogen aircraft are not accounted for due to the much
higher associated uncertainties relative to kerosene-based fuels, which already struggle with
uncertainties themselves. This is due to the poorly understood climate effects of propulsion systems
that are still being prototyped. Hydrogen propulsion can be achieved by fuel cells combined with
electric motors, which only emit water vapour to the atmosphere, or by combustion with gas turbine
engines, which emit water vapour and NOx. Initial simulations of hydrogen gas turbine fleets lead to
a wider geographical contrail coverage, but the absence of soot leads to reduced optical thickness,
resulting in overall 42 % radiative forcing reduction compared to kerosene
{cite:p}`strom_first_2002,contrail_h2`. However, these results lack empirical validation and do not
include mixed fleets, where kerosene soot in the air interacts with vapour-rich exhausts. Hydrogen
engines may be also different from their kerosene counterparts as they operate in lower temperatures
and leaner mixtures (less fuel to air ratio), requiring redesign of the combustion chamber for lower
NOx emissions {cite:p}`mourouzidis_2024`. The first in-flight measurements of fuel-cell exhausts are
still relatively recent and the measurement methodologies are also subject to limitations
{cite:p}`braun_fuel_2026`.

Besides the climate impact mitigation that alternative fuels provide, research has provided evidence
that operational strategies for contrail avoidance by modification of flight trajectories allow
mitigating a significant share of contrail warming with minimal penalties on fuel burn
{cite:p}`teoh2020`. Initial scenario-based assessments comparing mitigation levers in terms of their
temperature impact found that contrail avoidance alone can deliver more substantial near-term
reductions relative to decarbonization policy alone {cite:p}`zheng_aviation_2025`, and deployment at
scale is seen as simpler than investment-heavy levers such as aircraft technology and SAF. There are,
however, issues with this approach, as it does not incorporate uncertainties in the climate analysis.
In practice, contrail formation depends on the weather across the entire flight trajectory, whose
forecast is still highly uncertain for local humidity, which is needed to estimate
ice-supersaturated regions. Large diversions to avoid such regions can come at the expense of extra
fuel, trading a short-lived for a long-lived warming. For instance, despite the high impact of
contrails on current warming, {cite:t}`johansson_social_2025` estimate their long-run social costs to
be approximately 0.15 that of aviation's CO₂, but this value can vary from about 0.02 to 2 as
uncertainties are even larger than climate-system uncertainty to account for varying social discount
rates and background scenario emission profiles. Therefore, as argued by
{cite:t}`lynch_demonstrating_2020`, the present work treats non-CO₂ mitigation as parallel to that of
CO₂, so that short-term impact reductions due to contrail avoidance are not traded with delayed
decarbonization and higher long-term temperatures in consequence.

:::{include} literature/tables/climate_assumptions.md
:::

Contrail forcing in AeroMAPS scales with the distance flown, which allows for modelling contrail
avoidance as a reduction of this forcing at the expense of extra fuel burn. Contrail avoidance
strategies are accounted for by using logistic diffusion among the fleet, such that year of
introduction, share of avoided warming, and time to diffusion follow that of {cite:t}`teoh2020`. The
forcing per kilometre is set from the 2018 contrail RF of {cite:t}`lee_contribution_2021` and
converted into ERF with the efficacy of {cite:t}`wang_fuel_2026`. Fuel composition acts through soot,
where contrail forcing scales with the square root of the particle number emission index, calibrated
to match the warming reduction found by {cite:t}`wang_fuel_2026`. Avoidance strategies are applied to
S1 with SAF set as blending shares, as in the demand-price coupling, so that the extra fuel burnt
carries the same SAF share as the rest.

Uncertainties are explored with a low, a central and a high warming case (table above). The
uncertainty of CO₂ warming is added through the transient climate response to cumulative emissions
(TCRE), where the central run is scaled by the ratio of 1.0 and 2.3 K per 1000 PgC to the best
estimate of 1.65 {cite:p}`ipcc_ar6_wg1`.

## Results

The figure below splits the TtW emissions of the three scenarios by lever, using the same
categorization pillars of the reports. Fleet renewal and new aircraft technology are separated with
the T0 and T1 curves of the report. The WtW version is exported alongside it, as the appendix figure
of the manuscript.

```{code-cell} python
:tags: [hide-input]

# One figure per accounting scope, a row per scenario. The paper reports
# tank-to-wake throughout, as the reports do, so that is the figure the text
# carries and the well-to-wake twin goes to the appendix. Both are drawn before
# either is written, so that they share one vertical scale and the pair can still
# be read as the scope comparison it was.
TRIPLETS = [
    ("S0", S0_TTW, S0), ("S1", S1_TTW, S1), ("S2", S2_TTW, S2),
]
available = [(name, ttw, wtw) for name, ttw, wtw in TRIPLETS if ttw is not None and wtw is not None]

if available:
    scopes = [
        ("tank-to-wake", "atag_decomposition", 1, (T0_TTW, T1_TTW)),
        ("well-to-wake", "atag_decomposition_wtw", 2, (T0, T1)),
    ]
    # The wedges only exist from the last observed year, the energy split being
    # measured against it, so the history the helper would draw is empty before
    # 2023. It is taken here from the scenario's own passenger and freight
    # emissions instead, which are observed data in every scope and meet the
    # gross trajectory exactly at the handover.
    HISTORY_END = 2023
    # Observed data, in both figures that carry it: grey, solid, with a small dot
    # on each observed year, so it reads as data rather than as a scenario.
    HISTORY_STYLE = dict(color="grey", linestyle="-", linewidth=1.6, marker=".",
                         markersize=4)

    def draw_history(ax, view, scope):
        outputs = view.data["vector_outputs"]
        history = (outputs["co2_emissions_passenger"] + outputs["co2_emissions_freight"])
        history = history.loc[:HISTORY_END]
        label = "Historical combustion CO$_2$" if scope == "tank-to-wake" else "Historical CO$_2$"
        for line in ax.get_lines():
            if line.get_label().startswith("Historical"):
                line.set_data(history.index.to_numpy(), history.to_numpy(dtype=float))
                line.set_label(label)
                line.set(**HISTORY_STYLE)
                return
        ax.plot(history.index, history.to_numpy(dtype=float), label=label, zorder=5,
                **HISTORY_STYLE)

    drawn = []
    for scope, export_name, position, anchors in scopes:
        # One row, a panel per scenario, so the three read left to right against
        # one vertical axis the way the reports lay theirs out.
        fig, axes = plt.subplots(1, len(available), figsize=(13.0, 4.9), sharey=True,
                                 sharex=True, layout="constrained")
        axes = np.atleast_1d(axes)
        for entry, ax in zip(available, axes):
            name = entry[0]
            view = entry[position]
            view.plot("mitigation_wedges", fig=fig, ax=ax, anchors=anchors,
                      legend=False, title=f"{name} - {scope}")
            draw_history(ax, view, scope)
            legend = ax.get_legend()
            if legend is not None:
                legend.remove()
        for ax in axes[1:]:
            ax.set_ylabel("")
        # One legend for the row, beneath it: the bands are the same in all three
        # panels, and inside any of them it would cover the history it names.
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="outside lower center", ncol=5, fontsize=8,
                   frameon=False)
        drawn.append((fig, axes, export_name))

    # One scale across both figures, taken from the drawn data and applied before
    # anything is written, so no curve is clipped and the exported PDFs agree with
    # the page. Reading the limits back only works because the helper leaves
    # autoscaling alone.
    top = max(ax.get_ylim()[1] for _, axes, _ in drawn for ax in axes)
    for fig, axes, export_name in drawn:
        for ax in axes:
            ax.set_ylim(0, top)
        save_fig(fig, name=export_name)
```

*TtW emission reductions by lever. One panel per scenario, with historical emissions in grey. Fleet
renewal and new technology are split with the T0 and T1 curves of the report, and alternative
aircraft count as technology.*

The reproduced S0 is close to the reports in gross emissions, 147 Mt (6 %) above them in 2050 (see
the two validation tables), even though only adopted SAF policies are accounted for. The main
difference is in offsets: with CORSIA alone, S0 does not reach net-zero. This reflects the fact that,
while the sector's ambition has increased to reach net-zero by 2050, local policies still lag behind
this ambition and lead to implementation gaps in policy adoption {cite:p}`salgas_pledges_2026`, even
without accounting for the gap between adopted policies and their outcomes.

In S1 and S2 scenarios, with more ambitious decarbonization, SAF removes several times more CO₂ than
technology and operations together. Fleet renewal, efficiency and operations are the same in both
scenarios, which differ almost only in fuels and alternative aircraft. S2 replaces SAF worth 156 Mt
with 218 Mt of battery-electric flights, which leaves 62 Mt between their residual emissions. In the
[appendix](#appendix-additional-figures), the SAF pathway figure and the fuel cost and emissions
figure, respectively, split SAF into its production pathways and make explicit the report
assumptions on fuel price and emission factor.

The standard AeroMAPS categorization is based on the components of the Kaya identity
{cite:p}`planes_aeromaps_2023` and differs from that of the reports, for instance aircraft with
alternative energy carriers and aircraft efficiency gains are both considered as belonging to the
aircraft technology wedge in ATAG, while in the AeroMAPS standard alternative energy carriers are
grouped along with SAF as belonging to the reduction of the carbon intensity of energy. As the
estimation of emission reductions attributed to each lever is made based on relative gains, the
ordering of which levers are accounted first changes the values of the analysis: the first levers to
be incorporated are attributed higher absolute gains than levers incorporated later even if their
relative reduction is the same, due to the fact that previous levers reduce absolute emissions made
for the accounting. This issue is further addressed in the [Discussion](#discussion) as a limitation
of narratives based on the avoided emissions fallacy.

### Overview of scenario outcomes

The overview figure below summarizes the outcomes compared in the following sections, where results
are given as central [low, high] values. Cumulative CO₂ between 2024 and 2050 reaches 39.4, 27.6 and
27.7 Gt for S0, S1 and S2, within the 21.2 to 46.7 Gt spanned by the lever combinations. Energy
expenses over the same period amount to 9.1 [8.1, 10.3] and 9.2 [8.2, 10.3] trillion EUR for S1 and
S2, against 6.8 [5.1, 8.8] for S0, the brackets spanning the lower and upper quartiles of the
kerosene price. These scenarios carry no carbon price, as in the reports, whereas the coupled runs
pay the carbon price of their background scenario: S1 then reaches 11.8 [9.8, 17.6] trillion EUR, or
12.1 [7.9, 23.2] without SAF, the brackets spanning SSP2-4.5 and SSP2-1.9. Under SSP2-2.6, the
coupled S1 spends 9.3 trillion EUR on energy, as much as the uncoupled one, and 2.5 on carbon, so the
gap between the two groups is essentially the carbon price. The central warming in 2050 of the three
scenarios differs by 20 mK, less than the uncertainty on each of them, and contrail avoidance reduces
the warming of S1 by 5 to 14 mK.

```{code-cell} python
:tags: [hide-input]

# The three outcomes the paper compares, one panel each, read from committed outputs.
# Cumulative CO2 and energy expenses run over the prospective window, 2024 to 2050;
# warming is the 2050 value. Error bars are the range of an uncertain input: the carbon
# price of the three SSP2 pathways for the coupled runs, and the low- and high-warming
# bands, CO2 uncertainty included, for temperature.
from aeromaps.utils.results_view import load_results as _load

OVERVIEW_FIRST, OVERVIEW_LAST = 2024, 2050
_TCRE_BEST, _TCRE_LIKELY = 1.65, (1.0, 2.3)
_CO2_SCALE = {"low": _TCRE_LIKELY[0] / _TCRE_BEST, "central": 1.0, "high": _TCRE_LIKELY[1] / _TCRE_BEST}
_T_TOTAL = "temperature_increase_from_aviation"
_T_CO2 = "temperature_increase_from_co2_from_aviation"
_COUPLED = HERE / "3rd_edition_full_coupled_demand" / "data_outputs"
_SSPS = {"SSP2-4.5": "ssp2_45", "SSP2-2.6": "ssp2_26", "SSP2-1.9": "ssp2_19"}


def _vectors(path):
    return _load(path).data["vector_outputs"]


def _cumulative_expenses(vectors):
    # Energy expenses including the carbon tax, in trillion EUR.
    series = vectors["non_discounted_net_energy_expenses"]
    return series.loc[OVERVIEW_FIRST:OVERVIEW_LAST].sum() / 1e6


def _cumulative_co2(vectors):
    # Before offsets; the sweep stores the same series as co2_emissions.
    return vectors["co2_emissions_including_energy"].loc[OVERVIEW_FIRST:OVERVIEW_LAST].sum() / 1e3


published = {name: view.data["vector_outputs"] for name, view in scenarios.items()}
SHORT = {name: name.split()[0] for name in published}

# Panel 1: cumulative CO2, published scenarios and the two ends of the lever sweep.
import sweep as _sweep  # noqa: E402  (on sys.path from the lever-grid cell)

_tidy = _sweep.read_results()
_co2 = _tidy[_tidy["variable"] == "co2_emissions"]
_co2 = _co2[(_co2["year"] >= OVERVIEW_FIRST) & (_co2["year"] <= OVERVIEW_LAST)]
_cells = _co2.groupby(["traffic", "technology", "operations", "saf"])["value"].sum() / 1e3
_lowest, _highest = _cells.idxmin(), _cells.idxmax()
_TRAFFIC = {"low": "L", "central": "C", "high": "H"}


def _cell_label(cell):
    traffic, technology, operations, saf = cell
    return f"{_TRAFFIC[traffic]}$\\cdot${technology}$\\cdot${operations}$\\cdot${saf}"


co2_bars = [(SHORT[n], _cumulative_co2(v)) for n, v in published.items()]
co2_bars += [
    (f"Lowest\n{_cell_label(_lowest)}", _cells[_lowest]),
    (f"Highest\n{_cell_label(_highest)}", _cells[_highest]),
]

# Panel 2: cumulative energy expenses. The uncoupled scenarios are taken at the 20-year
# mean kerosene price, spanning its lower to upper quartile; the coupled runs span the
# three pathways, each with its own carbon and kerosene price.
_kerosene = pd.read_csv(HERE / "3rd_edition_full_coupled_demand" / "data_outputs"
                        / "kerosene_variants.csv.gz")


def _kerosene_expenses(scenario, case):
    rows = _kerosene[(_kerosene["scenario"] == scenario) & (_kerosene["kerosene"] == case)]
    series = rows.set_index("year")["non_discounted_net_energy_expenses"]
    return series.loc[OVERVIEW_FIRST:OVERVIEW_LAST].sum() / 1e6


cost_bars = [
    (SHORT[n], _kerosene_expenses(SHORT[n], "mean"),
     (_kerosene_expenses(SHORT[n], "lower quartile"), _kerosene_expenses(SHORT[n], "upper quartile")))
    for n in published
]
for label, suffix in (("S1\ncoupled", "_share"), ("S1 coupled\nno SAF", "_nosaf")):
    values = {
        ssp: _cumulative_expenses(_vectors(_COUPLED / f"{key}{suffix}.json"))
        for ssp, key in _SSPS.items()
    }
    cost_bars.append((label, values["SSP2-2.6"], (min(values.values()), max(values.values()))))

# Panel 3: 2050 warming, with the low- and high-warming bands and the CO2 uncertainty.
_bands = pd.read_csv(HERE / "climate_analysis" / "baseline_uncertainty_results.csv.gz")
_variants = pd.read_csv(HERE / "climate_analysis" / "contrail_variants_results.csv.gz")


def _scenario_warming(name, key):
    row = _bands[(_bands["scenario"] == name) & (_bands["band_key"] == key) & (_bands["year"] == 2050)]
    co2 = scenarios[name].data["climate_outputs"][_T_CO2].loc[2050]
    return 1000 * (float(row[_T_TOTAL].iloc[0]) + (_CO2_SCALE[key] - 1.0) * co2)


def _variant_warming(family, level):
    row = _variants[(_variants["family"] == family) & (_variants["level"] == level) & (_variants["year"] == 2050)]
    key = level.lower()
    return 1000 * (float(row[_T_TOTAL].iloc[0]) + (_CO2_SCALE[key] - 1.0) * float(row[_T_CO2].iloc[0]))


warming_bars = [
    (SHORT[n], _scenario_warming(n, "central"), (_scenario_warming(n, "low"), _scenario_warming(n, "high")))
    for n in published
]
_FAMILY_SHORT = {
    "Low-risk diversion": "S1 +\nlow-risk\ndiversion",
    "Small-scale diversion": "S1 +\nsmall-scale\ndiversion",
    "Long-term combustor technology": "S1 +\ncombustor\ntechnology",
}
for family, label in _FAMILY_SHORT.items():
    warming_bars.append(
        (label, _variant_warming(family, "Central"),
         (_variant_warming(family, "Low"), _variant_warming(family, "High")))
    )

PUBLISHED_COLOUR, VARIANT_COLOUR = "#4C72B0", "#9AA7B8"
fig, axes = plt.subplots(1, 3, figsize=(15.6, 4.6), layout="constrained")


def _bars(ax, bars, n_published, ylabel, title, fmt):
    labels = [b[0] for b in bars]
    values = [b[1] for b in bars]
    colours = [PUBLISHED_COLOUR if i < n_published else VARIANT_COLOUR for i in range(len(bars))]
    x = np.arange(len(bars))
    ax.bar(x, values, color=colours, width=0.62)
    for i, bar in enumerate(bars):
        spread = bar[2] if len(bar) > 2 else None
        if spread is not None:
            ax.errorbar(i, bar[1], yerr=[[bar[1] - spread[0]], [spread[1] - bar[1]]],
                        color="black", capsize=4, linewidth=1.2)
        # The value sits at the foot of its bar, below where any error bar reaches.
        ax.text(i, 0.04 * max(values), fmt.format(bar[1]), ha="center", va="bottom",
                fontsize=8, color="white", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=10)
    ax.grid(alpha=0.3, axis="y")
    ax.set_ylim(0, max((b[2][1] if len(b) > 2 and b[2] else b[1]) for b in bars) * 1.15)


_bars(axes[0], co2_bars, 3, "Cumulative CO$_2$, 2024-2050 [Gt]", "Cumulative CO$_2$ emissions", "{:.1f}")
_bars(axes[1], cost_bars, 3, "Cumulative energy expenses, 2024-2050 [trillion EUR]",
      "Energy expenses, carbon tax included", "{:.1f}")
# The reports' scenarios carry no carbon price, the coupled runs carry the AR6 one:
# said on the panel, since it is most of the gap between the two groups.
_top = 1.15 * axes[1].get_ylim()[1]
axes[1].set_ylim(0, _top)
for _centre, _text in ((1.0, "ATAG scenarios\nno carbon price"),
                       (3.5, "Coupled S1\nAR6 carbon price")):
    axes[1].text(_centre, 0.93 * _top, _text, ha="center", va="top", fontsize=8,
                 color="0.25")
axes[1].axvline(2.5, color="0.6", linewidth=0.8, linestyle="--")
_bars(axes[2], warming_bars, 3, "Warming in 2050 [mK]", "Temperature impact in 2050", "{:.0f}")
save_fig(fig, name="overview")

print(pd.DataFrame({"CO2 [Gt]": dict((b[0].replace("\n", " "), b[1]) for b in co2_bars)}).round(2))
print(pd.DataFrame({"expenses [T EUR]": {b[0].replace("\n", " "): b[1] for b in cost_bars},
                    "range": {b[0].replace("\n", " "): b[2] for b in cost_bars}}))
print(pd.DataFrame({"warming [mK]": {b[0].replace("\n", " "): b[1] for b in warming_bars},
                    "range": {b[0].replace("\n", " "): b[2] for b in warming_bars}}))
```

*Overview of scenario outcomes. Cumulative CO₂ emissions (WtW, before offsets) and cumulative energy
expenses including the carbon price, both from 2024 to 2050, and warming in 2050. The reproduced S0,
S1 and S2 carry no carbon price, as in the reports, while the coupled S1, with and without SAF,
carries the carbon price of each background scenario. Grey bars are the lowest and highest lever
combinations, the coupled runs, and the contrail avoidance measures applied to S1. Error bars span
the lower and upper quartiles of the kerosene price for S0, S1 and S2, SSP2-4.5 and SSP2-1.9 around
SSP2-2.6 for the coupled runs, each with its own kerosene price, and the low and high warming cases
of the non-CO₂ assumptions table for temperature.*

### Demand-side impacts of transition costs

The figure below shows the scenario outcomes when incorporating the demand-price coupling that was
left out of ATAG Waypoint reports. They are compared with a no-SAF case, in which all drop-in
mandates are removed. The three carbon prices come from the REMIND-MAgPIE SSP2 pathways
{cite:p}`ipcc_ar6_wg3,ar6_database`: SSP2-4.5 (+2.7 °C), SSP2-2.6 (+2.0 °C) and SSP2-1.9
(+1.5 °C). With the mandate, demand falls by 2.0, 7.3 and 22.3 % by 2050, more as carbon gets more
expensive and further increases the energy costs within DOC. This range includes the −16 and −14 %
quoted by the reports, which fall between SSP2-2.6 and SSP2-1.9. Without SAF, demand changes by
+14.0, −13.7 and −42.4 %: under the weakest carbon price and the cheapest kerosene, removing the
mandate makes flying cheaper and traffic grows further than the central traffic forecast. Unlike the
reports' scenarios, these runs pay a carbon price on the WtW emissions of their fuel.

```{code-cell} python
:tags: [hide-input]

import pandas as pd

COUPLED = HERE / "3rd_edition_full_coupled_demand" / "data_outputs"
PATHWAYS = ["ssp2_19", "ssp2_26", "ssp2_45"]
READINGS = {"fixed volume": "", "fixed share": "_share", "no SAF": "_nosaf"}

# End-of-century warming each pathway is consistent with {cite:p}`ipcc_ar6_wg3`, defined once
# here so every legend and caption that names a pathway can carry it rather than the reader
# having to hold SSP2-1.9 versus SSP2-4.5 in mind unaided.
SSP_WARMING = {"SSP2-1.9": "+1.5°C", "SSP2-2.6": "+2.0°C", "SSP2-4.5": "+2.7°C"}
# Weakest to strongest carbon price, used to order every figure column and legend
# that separates the three pathways, so the reader always moves the same direction.
SSP_ORDER = ["SSP2-4.5", "SSP2-2.6", "SSP2-1.9"]


def with_warming(name):
    return f"{name} ({SSP_WARMING[name]})" if name in SSP_WARMING else name


coupled = {}
for reading, suffix in READINGS.items():
    for pathway in PATHWAYS:
        path = COUPLED / f"{pathway}{suffix}.json"
        if path.exists():
            # SSP2-1.9 rather than SSP2-19: the label reaches the figure legends
            # directly once the comparison plots draw the members by name.
            name = pathway.upper().replace("SSP2_", "SSP2-")
            label = f"{name[:-1]}.{name[-1]} ({reading})"
            coupled[label] = load_results(path, name=label)

if not coupled:
    print("PENDING: coupled-demand results not generated yet. Run "
          "3rd_edition_full_coupled_demand/ssp_comparison.ipynb and ssp_comparison_share.ipynb.")
else:
    rows = []
    for label, view in coupled.items():
        vector, climate = view.data["vector_outputs"], view.data["climate_outputs"]
        with_feedback = vector.loc[2050, "rpk"]
        exogenous = vector.loc[2050, "rpk_no_elasticity"]
        dropin = vector.loc[2050, "energy_consumption_dropin_fuel"]
        fossil = vector.loc[2050, "dropin_fuel_fossil_energy_consumption"]
        rows.append({
            "scenario": label,
            "2050 RPK [T]": with_feedback / 1e12,
            "exogenous [T]": exogenous / 1e12,
            "response [%]": 100 * (with_feedback / exogenous - 1),
            "SAF share [%]": 100 * (1 - fossil / dropin),
            "2050 CO2 [Mt]": climate.loc[2050, "co2_emissions"],
        })
    display(pd.DataFrame(rows).set_index("scenario").round(1))
```

```{code-cell} python
:tags: [hide-input]

# The fixed-share reading, and its fuel-only counterfactual. A share mandate is
# how ReFuelEU Aviation, the UK and Brazilian schemes are actually written, so it
# is the SAF reading drawn here; the fixed-volume reading survives only in the
# crossover comparison above. No SAF pairs against it with every drop-in mandate
# zeroed, so the distance between the two bands below is what the SAF mandate's
# own cost does to traffic, isolated from the exogenous forecast entirely.
share_only = {
    label.split(" (")[0]: view for label, view in coupled.items() if "(fixed share)" in label
}
nosaf_only = {
    label.split(" (")[0]: view for label, view in coupled.items() if "(no SAF)" in label
}

# Every panel is drawn by the framework's own comparison plots in envelope mode:
# a band spanning the three pathways, with each pathway drawn inside it and named
# in the legend. The top row is the background the scenarios are given and the
# bottom row is what follows from it, so drawing both the same way is what lets
# the two be read against each other. Population is identical across the three
# and GDP per capita nearly so, since SSP2 is a single socioeconomic pathway, so
# their bands collapse; that collapse is the point of the row, since it leaves
# the carbon price as the only driver that separates the pathways below.
PANEL_ROWS = [
    [
        ("population_comparison", "Population", "Population [billion]"),
        ("gdp_per_capita_comparison", "GDP per capita", "GDP per capita [USD]"),
        ("carbon_price_comparison", "Carbon price", "Carbon price [USD/tCO2]"),
    ],
    [
        ("rpk_comparison", "Traffic", "Revenue passenger-kilometres [trillion]"),
        ("doc_net_energy_per_rpk_comparison", "Energy DOC per RPK", "Energy DOC per RPK [EUR/RPK]"),
        ("co2_emissions_comparison", "Residual CO2", "Annual CO2 [MtCO2]"),
    ],
]

# The uncoupled reference: S1, the published scenario the coupled runs are built
# on, with the reports' central traffic forecast held exogenous. It is drawn in
# black on the three bottom panels, traffic, cost and emissions, so the coupled
# bands read as departures from it. It carries the report-era kerosene price
# rather than the 2026 one, which is part of why the cost panel separates it
# from the bands.
REFERENCE_PATH = "3rd_edition_full/data_outputs/s1.json"
REFERENCE_LABEL = "S1, central traffic (uncoupled)"
REFERENCE_SERIES = {
    "rpk_comparison": ("vector_outputs", "rpk", 1e-12),
    "doc_net_energy_per_rpk_comparison": ("vector_outputs", "doc_net_energy_per_rpk_mean", 1.0),
    "co2_emissions_comparison": ("climate_outputs", "co2_emissions", 1.0),
}
# Every run shares the observed years, so the history is drawn once, in grey
# with a small dot on each observed year,
# and each coupled curve and the reference start where the projection does.
LAST_HISTORICAL_YEAR = 2024

# Two named groups sharing one comparison, SAF in dark green and no SAF in dark
# red, so the colour itself carries the counterfactual rather than requiring the
# legend to be read first. Keys are suffixed per family since both dicts share
# the same pathway names.
demand_families = {}
demand_families.update(
    {f"{with_warming(label)}, SAF": view for label, view in share_only.items()}
)
demand_families.update(
    {f"{with_warming(label)}, no SAF": view for label, view in nosaf_only.items()}
)
DEMAND_GROUP_COLORS = {"SAF (fixed share)": "darkgreen", "No SAF": "darkred"}
# The no-SAF family is the counterfactual, not the result, so it recedes: a
# fainter fill and a thinner line put it behind the mandate it is there to be
# read against, without changing what either band says.
DEMAND_GROUP_ALPHA = {"SAF (fixed share)": 0.25, "No SAF": 0.10}
DEMAND_GROUP_LINEWIDTH = {"SAF (fixed share)": 2.6, "No SAF": 1.6}

if share_only and nosaf_only:
    fig, all_axes = plt.subplots(2, 3, figsize=(15.6, 8.4), layout="constrained")
    comparison = assemble_processes(demand_families)
    groups = {
        "SAF (fixed share)": [
            f"{with_warming(label)}, SAF" for label in SSP_ORDER if label in share_only
        ],
        "No SAF": [
            f"{with_warming(label)}, no SAF" for label in SSP_ORDER if label in nosaf_only
        ],
    }

    for axes, panels in zip(all_axes, PANEL_ROWS):
        for ax, (plot_name, title, ylabel) in zip(axes, panels):
            comparison.plot(
                plot_name,
                fig=fig,
                ax=ax,
                scenario_groups=groups,
                colors=DEMAND_GROUP_COLORS,
                group_envelope_alpha=DEMAND_GROUP_ALPHA,
                group_envelope_linewidth=DEMAND_GROUP_LINEWIDTH,
                group_display="envelope",
                group_envelope_show_members=True,
                legend=False,
                # The cost plots default to the projection alone. Here the
                # historic part is populated, and it is what the elasticity was
                # calibrated against, so it belongs on the page.
                years_source="years",
            )
            ax.set_title(title)
            ax.set_ylabel(ylabel)
            ax.set_xlabel("Year")
            # 2010 rather than 2000: the AR6 background pathways only begin
            # there, so the earlier decade is blank in the top row and carries
            # nothing in the bottom one.
            ax.set_xlim(2010, 2050)

    # The top row is the background the runs are given, identical with and without
    # SAF, so the two families are not told apart there: each carbon-price pathway
    # is drawn once, in grey, and its line style alone names it. The families are
    # named on the bottom row, where they differ.
    for ax in all_axes[0]:
        for collection in list(ax.collections):
            collection.remove()
        for line in list(ax.get_lines()):
            label = line.get_label()
            if label.endswith(", no SAF"):
                line.remove()
                continue
            line.set_color("grey")
            line.set_linewidth(1.8)
            if label.endswith(", SAF"):
                line.set_label(label[: -len(", SAF")])
        # One grey envelope between the pathways, as the bottom row has per family.
        members = [line for line in ax.get_lines() if not line.get_label().startswith("_")]
        if members:
            x = np.asarray(members[0].get_xdata(), dtype=float)
            ys = np.array([np.interp(x, np.asarray(m.get_xdata(), dtype=float),
                                     np.asarray(m.get_ydata(), dtype=float)) for m in members])
            ax.fill_between(x, ys.min(axis=0), ys.max(axis=0), color="grey", alpha=0.2,
                            linewidth=0, zorder=1)

    # The history, once per panel. Every coupled curve carries the same observed
    # years, so they are cut at the last of them and the shared part is redrawn
    # as a single grey line, taken from the first curve before it is cut.
    # The envelopes need no cut: their members coincide there, so they have no
    # width to show.
    history_handle = None
    for ax in all_axes.ravel():
        history = None
        for line in ax.get_lines():
            x = np.asarray(line.get_xdata(), dtype=float)
            y = np.asarray(line.get_ydata(), dtype=float)
            if x.size == 0 or x.min() >= LAST_HISTORICAL_YEAR:
                continue
            if history is None:
                observed = x <= LAST_HISTORICAL_YEAR
                history = (x[observed], y[observed])
            projected = x >= LAST_HISTORICAL_YEAR
            line.set_data(x[projected], y[projected])
        if history is not None:
            history_handle, = ax.plot(*history, color="grey", linestyle="-", linewidth=1.6,
                                      marker=".", markersize=4, label="Historical",
                                      zorder=6)

    # S1 uncoupled, in black, on the three panels that carry a result. The traffic
    # panel also names the two families, since the top row no longer does.
    from matplotlib.patches import Patch

    family_handles = [
        Patch(facecolor=colour, edgecolor=colour, alpha=0.4, label=family)
        for family, colour in DEMAND_GROUP_COLORS.items()
    ]
    reference = load_results(HERE / REFERENCE_PATH, name=REFERENCE_LABEL)
    # Its cost is drawn at the same kerosene price uncertainty as the coupled runs,
    # the 20-year lower quartile to upper quartile, as a shade. Traffic is exogenous
    # and emissions do not depend on the price, so those two stay a single line.
    kerosene = pd.read_csv(HERE / "3rd_edition_full_coupled_demand" / "data_outputs"
                           / "kerosene_variants.csv.gz")
    kerosene_s1 = kerosene[kerosene["scenario"] == "S1"]
    for ax, (plot_name, _, _) in zip(all_axes[1], PANEL_ROWS[1]):
        block, key, scale = REFERENCE_SERIES[plot_name]
        if plot_name == "doc_net_energy_per_rpk_comparison":
            by_case = {
                case: rows.set_index("year")[key] * scale
                for case, rows in kerosene_s1.groupby("kerosene")
            }
            low, high = by_case["lower quartile"], by_case["upper quartile"]
            mean = by_case["mean"].loc[LAST_HISTORICAL_YEAR:]
            low, high = low.loc[LAST_HISTORICAL_YEAR:], high.loc[LAST_HISTORICAL_YEAR:]
            ax.fill_between(low.index, low, high, color="black", alpha=0.3, linewidth=0,
                            zorder=5)
            line, = ax.plot(mean.index, mean, color="black", linewidth=1.6,
                            label=REFERENCE_LABEL, zorder=6)
            # The three kerosene prices behind the shade and the coupled pathways, put on
            # this panel's own unit: the energy cost per RPK of an all-fossil fleet at S1's
            # energy intensity, without carbon price. The same product reproduces the
            # model's cost per RPK exactly before the carbon price starts.
            s1_vectors = reference.data["vector_outputs"]
            intensity = (s1_vectors["energy_consumption_passenger"]
                         / s1_vectors["rpk"]).loc[2026:2050]
            for case, short in (("lower quartile", "Q1"), ("mean", "mean"), ("upper quartile", "Q3")):
                price = kerosene[(kerosene["scenario"] == "S1") & (kerosene["kerosene"] == case)]
                price = price.set_index("year")["fossil_kerosene_mean_mfsp"].loc[2026:2050]
                fossil = price * intensity
                kerosene_line, = ax.plot(fossil.index, fossil, color="0.3", linestyle=":",
                                         linewidth=1.2, zorder=7,
                                         label="Kerosene only, no carbon price")
                ax.text(2049.6, fossil.iloc[-1], short, ha="right", va="bottom", fontsize=7,
                        color="0.3", zorder=8)
        else:
            series = np.asarray(reference.data[block][key], dtype=float) * scale
            first = 1940 if block == "climate_outputs" else 2000
            years = np.arange(first, first + len(series))
            projected = years >= LAST_HISTORICAL_YEAR
            line, = ax.plot(years[projected], series[projected], color="black", linewidth=1.6,
                            label=REFERENCE_LABEL, zorder=5)
        extra = family_handles if plot_name == "rpk_comparison" else []
        if plot_name == "doc_net_energy_per_rpk_comparison":
            extra = [kerosene_line]
        ax.legend(handles=extra + [line, history_handle], fontsize=8, loc="upper left")

    # The pathway legend, on the first panel, in grey with the history.
    handles, labels = all_axes[0][0].get_legend_handles_labels()
    all_axes[0][0].legend(handles, labels, fontsize=8)
    save_fig(fig, name="coupled_demand_share")
```

*Background scenario inputs and scenario outcomes including demand-price coupling. Fixed-share S1
SAF mandate (green) and no-SAF case (red) under three carbon and kerosene prices. Dotted lines give
the energy cost per RPK of a fleet flying only on fossil kerosene at S1's energy intensity, at the
lower quartile (Q1), mean and upper quartile (Q3) prices, without carbon price. History is in grey.
The solid black line shows S1 without coupling, at the mean kerosene price and without carbon price,
with a shade between the lower and upper quartiles of kerosene price.*

The next figure shows how the energy costs are broken down into the costs of each fuel as well as
the carbon price. Under the weak carbon price of SSP2-4.5 SAF is more expensive in 2050, yet under
carbon pricing trajectories compatible with the Paris Agreement SAF becomes cheaper from 2029 under
SSP2-1.9 and from 2040 under SSP2-2.6. The demand-side impacts of transition costs lead to changes in
traffic volumes of between 2 and 22 %, an effect which is as large as the technology and operations
levers together. The fuel cost and emissions figure drawn first is the one of the manuscript's
appendix; the breakdown needs the pathway definitions it rebuilds.

```{code-cell} python
:tags: [hide-input]

# What a megajoule of each production pathway costs to make and what emitting it
# releases. This is a property of the fuel, not of a scenario, so a single
# reference view suffices; the mandate only changes how much of each pathway is
# burned, not what that pathway costs or emits per unit energy.
#
# Drawn by the framework's own pathway-aware plots rather than by hand. Those
# resolve their carriers through a pathways_manager, which a view loaded from
# committed JSON does not carry, so one is rebuilt here from the same YAML the
# scenarios were run against. The metadata the plots need is declared in that
# file, so it does not require re-running the model.
COUPLED_INPUTS = find_scenario("atag_3rd_edition_coupled_demand").path / "data_inputs"
pathways_manager = build_pathways_manager(
    read_yaml_file(str(COUPLED_INPUTS / "s1_energy_share.yaml")),
    read_yaml_file(str(COUPLED_INPUTS / "processes.yaml")),
)
for view in share_only.values():
    view.pathways_manager = pathways_manager
for view in nosaf_only.values():
    view.pathways_manager = pathways_manager

if share_only:
    fig, price_axes = plt.subplots(1, 2, figsize=(10.4, 4.2), layout="constrained")
    reference = sorted(share_only)[0]
    # mean_mfsp rather than net_mfsp: the production cost alone, with the carbon
    # tax left to the DOC breakdown below where it is stacked separately.
    # 2025 rather than 2020: the mandates start there, so the earlier years are a
    # flat run-in that costs horizontal space without carrying information.
    share_only[reference].plot(
        "energy_mfsp", fig=fig, ax=price_axes[0], mfsp_type="mean_mfsp", legend=False
    )
    share_only[reference].plot("emission_factor_per_fuel", fig=fig, ax=price_axes[1], legend=False)
    for ax in price_axes:
        ax.set_xlim(2025, 2050)
        # The framework draws the years a pathway is not deployed as grey dotted
        # lines; they carry no information here, so they go.
        for line in list(ax.lines):
            if line.get_linestyle() == ":" and line.get_color() == "grey":
                line.remove()

    # One pathway the eleven-carrier file above does not carry, drawn here because
    # the paper uses it: the generic SAF the light edition's S0 runs on, which is an
    # aggregate of country-level policies rather than a production route. It takes
    # a colour of its own, outside the palette the panels use for the production
    # pathways, so that it is not mistaken for one of them. Black rather than a
    # purple: the palette already carries one for woody biomass.
    EXTRA_COLOUR = "#000000"
    reference_view = share_only[reference]
    kerosene_mfsp = np.asarray(
        reference_view.data["vector_outputs"]["fossil_kerosene_mean_mfsp"], dtype=float
    )
    kerosene_factor = np.asarray(
        reference_view.data["vector_outputs"]["fossil_kerosene_mean_co2_emission_factor"],
        dtype=float,
    )
    extra_years = np.arange(2000, 2000 + len(kerosene_mfsp))

    extras = []
    if S0 is not None:
        # The light edition's generic carrier aggregates country-level mandates
        # and their emission factors; it carries no production cost of its own,
        # so it appears on the intensity panel alone rather than as a zero.
        s0_outputs = S0.data["vector_outputs"]
        extras.append((
            "Generic SAF (S0)",
            "-",
            None,
            np.asarray(s0_outputs["generic_saf_mean_co2_emission_factor"], dtype=float),
        ))

    for label, style, mfsp, factor in extras:
        if mfsp is not None:
            price_axes[0].plot(extra_years[: len(mfsp)], mfsp, color=EXTRA_COLOUR, linestyle=style,
                               linewidth=2.0, label=label, zorder=6)
        price_axes[1].plot(extra_years[: len(factor)], factor, color=EXTRA_COLOUR, linestyle=style,
                           linewidth=2.0, label=label, zorder=6)

    # Both panels resolve the same pathways, so one legend serves them; placing it
    # outside to the right stops it covering the curves it names.
    handles, labels = price_axes[1].get_legend_handles_labels()
    kept = [(h, lb) for h, lb in zip(handles, labels) if lb != "Not used"]
    handles, labels = [h for h, _ in kept], [lb for _, lb in kept]
    price_axes[1].legend(handles, labels, loc="center left", bbox_to_anchor=(1.02, 0.5),
                         frameon=False, fontsize=8)
    save_fig(fig, name="fuel_price_intensity")
```

*Fuel cost and emissions. Cost (left) and WtW emissions (right) per megajoule, by pathway. The black
line is the generic SAF of S0, for which emissions, but no cost, are disclosed.*

```{code-cell} python
:tags: [hide-input]

# No-SAF on top, S1's SAF blend below, one column per pathway ordered weakest to
# strongest carbon price. Both rows are the same plot on different views, so the
# only thing that changes down a column is which mandate applied, and the only
# thing that changes across a row is the carbon price.
# Seven biomass routes and an electrofuel are more detail than the cost argument
# needs: what moves the cost per RPK is how much fossil kerosene is replaced, and
# by which family of fuel. Drop-in pathways are grouped by where their energy
# comes from; anything that is not a drop-in fuel would keep a band of its own.
DOC_GROUP_LABELS = {"fossil": "Fossil kerosene", "biomass": "Bio-SAF", "electricity": "e-SAF"}
DOC_GROUP_COLORS = {"Fossil kerosene": "#8c8c8c", "Bio-SAF": "#1baf7a", "e-SAF": "#2a78d6"}
DOC_GROUPS = {
    p.name: DOC_GROUP_LABELS[p.energy_origin]
    for p in pathways_manager.get_all()
    if p.aircraft_type == "dropin_fuel" and p.energy_origin in DOC_GROUP_LABELS
}

if share_only and nosaf_only:
    ssp_columns = [pathway for pathway in SSP_ORDER if pathway in share_only and pathway in nosaf_only]
    # sharey=True, not "row": scaling the two rows independently would make the
    # SAF and no-SAF panels look more alike than they are, and the distance
    # between them is the whole point of the figure.
    fig, axes = plt.subplots(2, len(ssp_columns), figsize=(15.6, 8.4),
                             sharey=True, layout="constrained")
    # Only the leftmost panel of each row keeps its legends, drawn as the plot
    # class draws them: the carriers, and the hatched cost components. Each row
    # needs its own pair, since the no-SAF row burns fossil kerosene alone and a
    # shared legend would name pathways half the figure never draws. The other
    # columns would only repeat them over the stacks they describe.
    for col, pathway in enumerate(ssp_columns):
        nosaf_only[pathway].plot("doc_net_energy_per_rpk_breakdown", fig=fig, ax=axes[0, col],
                                 legend=col == 0, groups=DOC_GROUPS,
                                 group_colors=DOC_GROUP_COLORS)
        share_only[pathway].plot("doc_net_energy_per_rpk_breakdown", fig=fig, ax=axes[1, col],
                                 legend=col == 0, groups=DOC_GROUPS,
                                 group_colors=DOC_GROUP_COLORS)
        axes[0, col].set_title(f"{with_warming(pathway)} -- no SAF")
        axes[1, col].set_title(f"{with_warming(pathway)} -- SAF (fixed share)")
        for ax in (axes[0, col], axes[1, col]):
            ax.set_xlim(2020, 2050)
    for ax in axes[:, 1:].ravel():
        ax.set_ylabel("")
    save_fig(fig, name="doc_breakdown")
```

*Operating cost. Energy cost per RPK, with and without SAF, for each carbon price, split into fossil
kerosene, bio-SAF and e-SAF. Hatches separate fuel cost, taxes and carbon tax. SAF costs more under
SSP2-4.5 and much less under SSP2-1.9. The dashed line represents the energy costs passed onto
passengers after a delay of around one year, following the approach in {cite:t}`costaalves_wctr`.*

### Temperature impacts and contrail avoidance strategies

The figure below shows the warming of each scenario, with the contributions of CO₂ and contrails and
the split of total warming by mechanism. While all scenarios achieve significant reductions in CO₂
emissions, at least half of their 2050 warming still comes from non-CO₂ effects, mainly contrails.

```{code-cell} python
:tags: [hide-input]

T_TOTAL = "temperature_increase_from_aviation"
T_CONTRAILS = "temperature_increase_from_contrails_from_aviation"
T_CO2 = "temperature_increase_from_co2_from_aviation"

# CO2 warming carries its own uncertainty, smaller than the non-CO2 one. The
# climate model runs one central FaIR configuration, so the range is taken from
# the transient climate response to cumulative CO2 emissions (TCRE), to which
# CO2-induced warming is proportional: IPCC AR6 WG1 (SPM D.1.1) gives a likely
# range of 1.0 to 2.3 K per 1000 PgC around a best estimate of 1.65. The central
# run is scaled by the ratio of each bound to the best estimate.
TCRE_BEST, TCRE_LIKELY = 1.65, (1.0, 2.3)
CO2_BAND = tuple(bound / TCRE_BEST for bound in TCRE_LIKELY)

band_csv = HERE / "climate_analysis" / "baseline_uncertainty_results.csv.gz"
bands_tidy = pd.read_csv(band_csv)
band_scenarios = list(bands_tidy["scenario"].unique())

fig, axes = plt.subplots(4, len(band_scenarios), figsize=(15.6, 13.6), sharex=True,
                         layout="constrained")
for column, scenario in enumerate(band_scenarios):
    subset = bands_tidy[bands_tidy["scenario"] == scenario]

    def band(key, column_name):
        rows = subset[subset["band_key"] == key]
        return rows.set_index("year")[column_name]

    # row 1: CO2 warming. The non-CO2 bands leave it unchanged, so its band is the
    # TCRE range above, applied to the scenario's own stored climate outputs.
    ax = axes[0, column]
    view = scenarios.get(scenario)
    if view is not None:
        co2 = view.data["climate_outputs"][T_CO2]
        ax.fill_between(co2.index, 1000 * co2 * CO2_BAND[0], 1000 * co2 * CO2_BAND[1],
                        alpha=0.25, color="#4C72B0")
        ax.plot(co2.index, 1000 * co2, color="#4C72B0", linewidth=2)
    ax.set_title(f"{scenario} - CO$_2$ warming", fontsize=9)
    ax.grid(alpha=0.3)
    if column == 0:
        ax.set_ylabel("Warming [mK]")

    # rows 2 and 3: the same envelope, on contrails then on the total. The total also
    # carries the CO2 uncertainty, the low-warming band taking the low TCRE and the
    # high-warming band the high one, as Table 4 lists them.
    for row, (metric, title) in enumerate(
        ((T_CONTRAILS, "Contrail warming"), (T_TOTAL, "Total warming from aviation")), start=1
    ):
        ax = axes[row, column]
        low, central, high = (band(k, metric) for k in ("low", "central", "high"))
        if metric == T_TOTAL and view is not None:
            low = low + (CO2_BAND[0] - 1.0) * co2.reindex(low.index)
            high = high + (CO2_BAND[1] - 1.0) * co2.reindex(high.index)
        ax.fill_between(low.index, 1000 * low, 1000 * high, alpha=0.25, color="#4C72B0")
        ax.plot(central.index, 1000 * central, color="#4C72B0", linewidth=2)
        ax.set_title(title, fontsize=9)
        ax.grid(alpha=0.3)
        if column == 0:
            ax.set_ylabel("Warming [mK]")

    # row 4: what the central case is made of, stacked by mechanism
    ax = axes[3, column]
    view = scenarios.get(scenario)
    if view is not None:
        climate = view.data["climate_outputs"]
        years = climate.index
        stack = [group_temperature(climate, years, group) * 1000 for group in MECHANISM_GROUPS]
        ax.stackplot(years, *stack, labels=list(MECHANISM_GROUPS),
                     colors=[MECHANISM_COLORS[g] for g in MECHANISM_GROUPS])
        ax.axhline(0, color="0.3", linewidth=0.8)
        ax.set_xlim(years[0], years[-1])
    ax.set_title("Central case, by mechanism", fontsize=9)
    ax.set_xlabel("Year")
    ax.grid(alpha=0.3)
    if column == 0:
        ax.set_ylabel("Warming [mK]")
        ax.legend(fontsize=6, loc="upper left")

# One scale across all twelve panels. The bottom is left free rather than pinned
# at zero, because the mechanism decomposition carries genuinely negative terms
# and clipping them would misreport the stack.
flat_axes = [ax for row in axes for ax in row]
low = min(ax.get_ylim()[0] for ax in flat_axes)
high = max(ax.get_ylim()[1] for ax in flat_axes)
for ax in flat_axes:
    ax.set_ylim(low, high)
save_fig(fig, name="climate_bands_and_decomposition")
```

*Temperature impacts of scenarios. Warming due to CO₂ and to contrails, total warming, and the
breakdown of warming by each mechanism for each scenario. Solid line represents the central case for
climate system parameters, and the shaded bands correspond to the low and high warming variations of
the non-CO₂ assumptions table. The uncertainty band of one scenario, CO₂ included, is about four
times wider than the spread between scenarios.*

In 2050, the warming from aviation reaches 91 [45, 138], 75 [38, 119] and 71 [36, 113] mK for S0, S1
and S2, of which CO₂ accounts for 39 [24, 55], 35 [21, 49] and 35 [21, 49] mK. The 20 mK between the
central values of the scenarios is about four times smaller than the uncertainty band of any of them,
where contrail forcing and efficacy weigh more than the SAF benefit on contrails. For comparison,
{cite:t}`zheng_aviation_2025` report 60 mK of added warming between 2025 and 2050 for a continuation
of historical trends, against 46, 30 and 26 mK for the reproduced S0, S1 and S2.

None of the editions include contrail mitigation, even though contrails are the largest warming term
in 2050 in every scenario. The figure below applies three measures to S1: low-risk diversion,
small-scale diversion of about 1.7 % of flights, and combustor technology reducing soot emissions.
By 2050, small-scale diversion avoids 44 [47, 41] % of contrail warming, combustor technology
41 [46, 29] % and low-risk diversion 15 [16, 14] %. Combustor technology has the highest final
effectiveness, but as it depends on fleet renewal and starts five years later, it avoids less by
2050. The fuel penalty of diversion raises CO₂ by 0.014 %, in proportion to the extra fuel, which
also incorporates SAF through its blending share. In absolute terms, small-scale diversion avoids
14 [4, 26] mK, meaning that contrail avoidance could lead to similar reductions in climate impact as
the gap in warming between S0 and the S1/S2 scenarios.

```{code-cell} python
:tags: [hide-input]

# Every non-CO2 measure in a row, the same experiment each time: the lever
# applied to S1 across the three bands, against the same scenario without it at
# the same band. Pairing each variant with a reference at its own band matters,
# since otherwise the band's own change in forcing would read as something the
# measure achieved. The left column is the share of contrail warming removed,
# which is what makes the three bands comparable, and the right column the total
# warming that follows; both columns share their scale down the figure.
LEVEL_STYLE = {"Low": ":", "Central": "-", "High": "--"}
BANDS = ("Low", "Central", "High")
CO2_SCALE = {"Low": CO2_BAND[0], "Central": 1.0, "High": CO2_BAND[1]}

variants = pd.read_csv(HERE / "climate_analysis" / "contrail_variants_results.csv.gz")


def _band_rows(frame, family, level, column):
    rows = frame[(frame["family"] == family) & (frame["level"] == level)]
    return rows.set_index("year")[column]


MEASURES = [(family, variants) for family in variants["family"].unique() if family != "No mitigation"]

# One column per measure: the share of contrail warming avoided on the top row,
# total warming on the bottom one, each row on one scale.
fig, grid = plt.subplots(
    2, len(MEASURES), figsize=(4.2 * len(MEASURES), 6.6), sharex=True, layout="constrained"
)
all_axes = list(zip(grid[0], grid[1]))
for row, (family, frame) in enumerate(MEASURES):
    share_axis, warming_axis = all_axes[row]
    for level in BANDS:
        treated = _band_rows(frame, family, level, T_CONTRAILS)
        reference = _band_rows(frame, "No mitigation", level, T_CONTRAILS)
        with np.errstate(invalid="ignore", divide="ignore"):
            share = 100 * (reference - treated) / reference.where(reference.abs() > 1e-12)
        share_axis.plot(share.index, share, color="#C44E52", linewidth=1.8,
                        linestyle=LEVEL_STYLE[level], label=f"{level} band")

        # CO2 uncertainty on the total, at the TCRE bound of the same band.
        tcre = CO2_SCALE[level]
        total = _band_rows(frame, family, level, T_TOTAL) + (tcre - 1.0) * _band_rows(
            frame, family, level, T_CO2
        )
        reference_total = _band_rows(frame, "No mitigation", level, T_TOTAL) + (
            tcre - 1.0
        ) * _band_rows(frame, "No mitigation", level, T_CO2)
        warming_axis.plot(total.index, 1000 * total, color="#4C72B0", linewidth=1.8,
                          linestyle=LEVEL_STYLE[level], label=f"{level} band")
        warming_axis.plot(reference_total.index, 1000 * reference_total, color="0.6",
                          linewidth=1.0, linestyle=LEVEL_STYLE[level])

    share_axis.set_title(family, fontsize=10)
    if row == 0:
        share_axis.set_ylabel("Contrail warming avoided [%]", fontsize=9)
        warming_axis.set_ylabel("Total warming [mK]", fontsize=9)
    for axis in (share_axis, warming_axis):
        axis.grid(alpha=0.3)
        axis.set_xlim(2024, 2050)

all_axes[0][0].legend(fontsize=8, loc="upper left")
all_axes[0][1].legend(fontsize=8, loc="upper left")
for axis in grid[1]:
    axis.set_xlabel("Year")

# One scale per row, so a measure is read against the others rather than against
# its own axis: the share row starts at zero, and the warming row spans every
# band of every measure.
share_top = max(axes[0].get_ylim()[1] for axes in all_axes)
warming_low = min(axes[1].get_ylim()[0] for axes in all_axes)
warming_top = max(axes[1].get_ylim()[1] for axes in all_axes)
for axes in all_axes:
    axes[0].set_ylim(0.0, share_top)
    axes[1].set_ylim(warming_low, warming_top)
save_fig(fig, name="contrail_strategies")
```

*Contrail avoidance strategies. Share of contrail warming avoided (top) and total warming (bottom)
for low-risk diversion, small-scale diversion and combustor technology across the low, central, and
high warming cases.*

## Discussion

### Limitations of current practices of aviation prospective scenarios

The Paris Agreement sets a global temperature goal, which requires net-zero emissions across the
whole economy around the middle of this century {cite:p}`ipcc_ar6_wg3`. From this goal, countries
set their emission reduction plans as Nationally Determined Contributions (NDCs), which include
domestic aviation. International aviation is excluded from NDCs and is handled by the International
Civil Aviation Organization (ICAO) through CORSIA, which only aims to keep CO₂ emissions below 85 % of
their 2019 level. Under current policies, S0 follows this goal instead of ATAG's ambition towards
net-zero as a form of modelling realism given the current political landscape on climate goals: its
offsets cover 28 % of its 2050 emissions, and 930 Mt of net TtW CO₂ remain.

Furthermore, a sector at net-zero CO₂ still warms the climate if its non-CO₂ effects are left
unabated. Aviation scenarios must therefore follow stricter rules to be called aligned with the Paris
Agreement, for instance by limiting its cumulative emissions and temperature impacts to remain below
a share of total allowable impacts, determining such a share is therefore left as a political
decision depending on societal arbitrations.

Besides the climate, sustainability also encompasses other dimensions such as resource usage. The
figure below compares what each scenario uses with the share allocated to aviation for four budgets
{cite:p}`planes_aeromaps_2023`: warming, CO₂, biomass and electricity. Allocations follow the current
weight of the sector: 3.8 % of the warming left before 2 °C, 2.6 % of the carbon budget, and 5 % of
the biomass and electricity available worldwide in 2050. All scenarios exceed their share of the
carbon budget, by 2.0 times for S0 and 1.4 times for S1 and S2. S0 also uses 1.6 times its share of
warming, while S2 stays just under it. S1 and S2 reach these results by using 14 % of the world's
biomass, 2.8 times their share, and 7 % of its electricity. The reports, on the other hand, use the
sector's difficulty for direct electrification to justify priority access to biomass and renewable
electricity, allowing the sector to consume between 15 and 20 % of global availability, three to
four times the 5 % used here. Yet, such priority has important implications for the land use of the
sector and in the capability of other economic sectors to mitigate their climate impacts
{cite:p}`becken_implications_2023`.

```{code-cell} python
:tags: [hide-input]

# What each scenario asks of four shared budgets, drawn with the framework's own
# multidisciplinary assessment plot: warming from 2019 to 2050 against the 0.8 K
# left to 2 C, cumulative CO2 over 2019 to 2050 against the 2 C carbon budget, and
# the biomass and electricity the fuels use in 2050 against global availability.
# The allocations to aviation are the framework's grandfathering defaults: 3.8 %
# of the warming, 2.6 % of the carbon budget, 5 % of biomass and electricity.
#
# The light S0 and the full S1 and S2 were run with different global
# availabilities (164 against 617.5 EJ of biomass, 250 against 224.1 EJ of
# electricity), so comparing their shares as stored would compare the inputs as
# much as the scenarios. All three are put on one basis before drawing.
#
# Biomass takes the world supply of the third edition (pp. 20, 48, 50): 27.1 EJ a
# year of feedstock for SAF in 2050, stated as 15 to 20 % of the world's
# sustainable supply, so about 155 EJ (135 to 181) at the middle of that range.
# The framework's own "Realistic" preset, 164 EJ, is the median of estimates of
# technical potential (IRENA and others, see the impacts documentation), close in
# total but reached another way. The share given to aviation stays at the
# framework's 5 %, not the reports' 15 to 20 %. Electricity keeps the preset.
from copy import deepcopy
from types import SimpleNamespace

from aeromaps.plots.single_scenario.sustainability_assessment import (
    MultidisciplinaryAssessmentPlot,
)

BIOMASS_BASIS = "atag"  # or "aeromaps"
BIOMASS = {
    "aeromaps": (164.01e12, 0.05),
    "atag": (27.1e12 / 0.175, 0.05),
}
ELECTRICITY = (200.0e12, 0.05)


def harmonised(view):
    data = deepcopy(view.data)
    vectors = data["vector_outputs"]
    for resource, (available, share) in (("biomass", BIOMASS[BIOMASS_BASIS]),
                                         ("electricity", ELECTRICITY)):
        vectors[f"{resource}_availability_global"] = available
        vectors[f"{resource}_availability_aviation_allocated"] = share * available
    return SimpleNamespace(data=data, pathways_manager=None)


fig, axes = plt.subplots(1, len(scenarios), figsize=(4.0 * len(scenarios), 4.4),
                         subplot_kw={"projection": "polar"})
shares = {}
for ax, (name, view) in zip(np.atleast_1d(axes), scenarios.items()):
    MultidisciplinaryAssessmentPlot(harmonised(view), fig=fig, ax=ax, legend=False)
    ax.set_title(name, fontsize=11, y=1.08)
    # The first four bars are the uses, drawn at their share of the world budget.
    shares[name] = [bar.get_height() for bar in ax.patches][:4]
# One radial scale, so a panel reads against the others.
top = max(max(v) for v in shares.values()) * 1.05
for ax in np.atleast_1d(axes):
    ax.set_ylim(0, top)
handles, labels = np.atleast_1d(axes)[0].get_legend_handles_labels()
fig.legend(handles, ["Used by the scenario", "Allocated to aviation"], loc="lower center", ncol=2)
fig.subplots_adjust(wspace=0.45, bottom=0.14, top=0.82)
save_fig(fig, name="multidisciplinary_assessment")

print(pd.DataFrame(shares, index=["climate", "co2", "biomass", "electricity"]).round(1))
```

*Multidisciplinary assessment regarding cumulative emissions, temperature impact, biomass and
electricity consumption. Use of each scenario (orange) against the share allocated to aviation
(green), as a percentage of the world budget. Climate: warming from 2019 to 2050, central case,
against the 0.8 K left before 2 °C. CO₂: WtW emissions from 2019 to 2050, before offsets, against the
2 °C carbon budget. Biomass and electricity: use in 2050 against 155 and 200 EJ available worldwide.
S0 uses no electricity, as its SAF is modelled as biomass only.*

Another limitation of prospective scenarios is the employment of *ceteris paribus* analysis, i.e.
all else remaining equal. One symptom of this can be observed in the way scenarios split emission
reductions by lever, for example take two measures that each cut 50 % of 100 Mt: the one counted
first gets 50 Mt, the other only 25 Mt. In S2, battery-electric aircraft avoid 218 Mt in 2050 when
counted before SAF, but only 6 Mt when counted after it. Furthermore, the assumptions of each lever
are made separately, while levers interact over time, which a sequential approach cannot capture. The
case of demand is one of the clearest examples of this and its effects are explored here: SAF and
carbon prices raise the cost of flying, which lowers traffic and changes the emissions left for each
lever to avoid. In the context of climate mitigation, these simplifications on how parts of the
system interact can also be called the avoided emissions fallacy, where relative emission reductions
coming from different sources are attributed relative to a baseline scenario, yet this simulated
baseline is found by not allowing the other parts of the system to respond to the effects of absence
of policies.

The ATAG Waypoint 2050 reports are also subject to this limitation in their analysis of avoided
emissions due to past efficiency gains. The third edition states that efficiency gains have avoided
14.6 Gt of CO₂ since 1990, but the baseline emissions are found by fixing 1990 efficiency with
observed traffic that increased, partly due to these efficiency gains. Simulating these past avoided
emissions with a similar method yields a similar value of 14.9 Gt. However, with fixed 1990
efficiencies, the energy cost per RPK would have been 2.3 times higher in 2019. With the demand model
of the [coupling section](#coupling-air-traffic-and-fuel-prices), driven by population, income and
the energy cost per RPK, traffic would have been 24 % lower in 2019, and the avoided emissions fall
to 8.8 Gt, 41 % less. This is not a critique of avoiding emissions through efficiency gains (which
still allow for lowering emissions overall), but rather of the way they are credited without
accounting for their role in fostering further activity growth. The retrospective is computed in the
companion document `avoided_emissions/index.md`.

### Limitations of models used in the present work

The demand model is aggregated at the global level and cannot provide any distributional effects. It
gives total traffic from world population, income and energy cost per RPK, and no further
granularity can be achieved regarding: regions, income groups, and travel purposes. The elasticity is
also constant, and calibrated on the energy costs seen between 1990 and 2023. Future costs may lie
well outside this range, and the response of demand may change with income or with new alternatives.

The climate analysis regarding non-CO₂ effects is not resolved by trajectory. Contrail forcing scales
with the total distance flown, so the network, flight altitudes and weather are assumed to stay as
they are today. Contrail avoidance and the effect of SAF on contrails are applied to the whole fleet,
even if they are based on avoiding the few flights that form most warming contrails, or giving SAF to
those flights {cite:p}`teoh2020,teoh_targeted_2022`.

Uncertainty is explored as a sensitivity study with a best, central and worst case, not as a full
uncertainty quantification and propagation. Each case combines the extremes of every effect: the
high band pairs the strongest contrail forcing and efficacy with the weakest SAF benefit and the
highest CO₂ response. In reality, the worst case of one effect will not always correlate to the worst
case of another, so the bands likely overstate the uncertainty, and the ratio of about four between
the band and the spread of scenarios is an upper bound. Propagating probability distributions would
give likely ranges instead, and is left for future work.

## Conclusion

This work reproduced the ATAG Waypoint 2050 scenarios lever by lever in the open-source AeroMAPS
framework. The technology scenarios match the reports within 0.6 to 2.3 %, but several results
depend on choices the reports do not state: which policies are assumed, how reductions are split
between levers, and which background assumptions are used. Scenarios that inform policy should
publish their models, data and assumptions.

The first takeaway for policy is the implementation gap. With only the SAF policies countries have
adopted, S0 emits 1290 Mt of residual TtW CO₂ in 2050, four to five times more than S1 and S2, of
which CORSIA offsets only 360 Mt. Reaching net-zero requires extra policies at the country level,
above all in Asia, where the gap between current policies and the sector's goal is largest
{cite:p}`salgas_pledges_2026`. Yet, achieving stronger ambition regarding emission goals also has to
address other dimensions of sustainability, such as temperature increase, biomass and electricity
consumption.

The second takeaway is that carbon prices and mandates must be combined. A carbon tax without
mandates penalizes flying but builds no low-carbon fuel supply, so it gives no lasting CO₂
reduction: under SSP2-1.9 without SAF, traffic falls by 42 % and 2050 emissions still reach 1270 Mt.
A mandate without a carbon tax only penalizes airlines and passengers relative to fossil kerosene:
under the weak carbon price of SSP2-4.5, SAF remains more expensive than kerosene up to 2050.
Combined, SAF becomes cheaper than taxed kerosene between 2029 and 2040, highlighting the need to
time both policies together, so that the carbon price rises as mandates ramp up.

For scenario makers, the sequential approach should give way to coupled models. The demand-price
feedback alone changes 2050 traffic by 2 to 22 %, as much as technology and operations together. MDO
solves such loops at little extra implementation burden, but requires a higher initial effort for
framework development. Also, formulating dynamic hypotheses and testing them against history can be
greatly beneficial to avoid the common pitfalls of prospective analysis, such as the avoided
emissions fallacy.

Finally, global policies are set on temperature targets, while regional and sectoral commitments
target CO₂. For aviation, specifically, non-CO₂ effects cause at least half of the 2050 warming of
every scenario, but their uncertainty is wider than the spread between scenarios. Yet, the way
forward should not be to use these to delay action, rather science, industry, and governments must
engage in reducing uncertainties, when possible, and crafting policies that are robust to incomplete
knowledge of the system.

## Appendix: additional figures

The paper reports TtW emissions, like the reports; the WtW versions of the technology and lever
figures are exported beside them, on the same scales. The SAF pathway figure below details the SAF
production of each scenario; the fuel cost and emissions figure is drawn in the demand-side section,
where the cost breakdown needs it.

```{code-cell} python
:tags: [hide-input]

# BiofuelMixComparisonPlot needs a live pathways_manager to know which carriers
# are biomass drop-ins, and falls back to an empty stack without one, which is
# why this panel used to render blank against committed data. The pathway names
# are recoverable from the outputs themselves: every deployed carrier writes a
# {pathway}_energy_consumption series, and the light edition collapses them into
# one generic carrier.
BIOMASS_PATHWAYS = [
    "hefa_oil_crops_trees", "hefa_waste_residue_lipids", "atj_cellulosic_cover_crops",
    "atj_agricultural_residues", "atj_waste_gas", "ft_woody_biomass",
    "ft_municipal_solid_waste", "generic_biofuel", "generic_saf",
]
# One colour per pathway across the panels. The generic carriers of the light
# edition take a grey the production pathways do not use, so S0's single band is
# not read as one of S1's or S2's.
PATHWAY_COLOURS = dict(zip(BIOMASS_PATHWAYS[:7], plt.cm.tab10.colors[:7]))
PATHWAY_COLOURS.update({"generic_biofuel": "#7f7f7f", "generic_saf": "#7f7f7f"})

if scenarios:
    fig, axes = plt.subplots(1, len(scenarios), figsize=(15.6, 4.2), sharey=True,
                             layout="constrained")
    for ax, (name, view) in zip(np.atleast_1d(axes), scenarios.items()):
        vectors = view.data["vector_outputs"]
        years = np.arange(2000, 2000 + len(vectors["energy_consumption_dropin_fuel"]))
        stack, labels, colours = [], [], []
        for pathway in BIOMASS_PATHWAYS:
            column = f"{pathway}_energy_consumption"
            if column not in vectors:
                continue
            series = np.nan_to_num(np.asarray(vectors[column], dtype=float)) * 1e-12
            if series.sum() > 0:
                stack.append(series)
                labels.append(pathway.replace("_", " "))
                colours.append(PATHWAY_COLOURS[pathway])
        if stack:
            ax.stackplot(years, *stack, labels=labels, colors=colours)
            ax.legend(fontsize=6, loc="upper left")
        ax.set_xlim(2020, years[-1])
        ax.set_title(name)
        ax.set_xlabel("Year")
        ax.grid(alpha=0.3)
    np.atleast_1d(axes)[0].set_ylabel("Biomass SAF energy [EJ]")
    save_fig(fig, name="biofuel_mix")
```

*SAF pathways. SAF production by pathway in each scenario. Life-cycle emissions differ by a factor of
eight between pathways.*

(reproducibility)=
## Reproducibility

Every result maps to a notebook, and every notebook writes its outputs to a committed
`data_outputs/` file that this document reads.

| Result | Produced by |
|---|---|
| Reproduced S0 | `3rd_edition_light/s0.ipynb` |
| Reproduced S1, S2 | `3rd_edition_full/s1.ipynb`, `s2.ipynb` |
| Technology calibration | `3rd_edition_full/validation.ipynb` |
| Full 144-combination lever sweep | `3rd_edition_variants/sweep.ipynb` |
| Demand–price coupling, fixed SAF volume | `3rd_edition_full_coupled_demand/ssp_comparison.ipynb` |
| Demand–price coupling, fixed SAF share | `3rd_edition_full_coupled_demand/ssp_comparison_share.ipynb` |
| Kerosene price variants of S0, S1, S2 | `3rd_edition_full_coupled_demand/kerosene_variants.py` |
| Climate, editions, contrail avoidance | `climate_analysis/climate_analysis.ipynb` |
| Non-CO₂ uncertainty on the baseline scenarios | `climate_analysis/baseline_uncertainty.ipynb` |
| Emissions avoided since 1990 | `avoided_emissions/index.md` |

Scenario configurations and their inputs ship with the package, under
`aeromaps/resources/scenarios/`: one folder per scenario, holding `config_files/` and
`data_inputs/`, with the shared traffic definitions in `markets/` beside them. Each folder carries a
`scenario.yaml` giving its name, its category and its tags, and
`aeromaps.utils.scenarios.list_scenarios` reads them. The results those configurations produce stay
here, in each edition's `data_outputs/`, because a result belongs to the work that reports it. The
environment is pinned by the repository's `uv.lock`.

```{note}
The figures on this page are produced by code cells that read the committed `data_outputs/` files.
No model is run while the page builds. If an output file is missing, the cell prints
`PENDING: run <notebook>` instead of failing, so a missing figure reads as missing data rather than
a broken build.
```
