---
title: Reviewing the ATAG Waypoint 2050 scenarios
subtitle: A lever-by-lever reproduction in AeroMAPS, extended to demand feedback and contrails
authors:
  - name: Ian Costa-Alves
exports:
  - format: typst
    output: exports/waypoint2050-reproduction.pdf
kernelspec:
  name: python3
  display_name: Python 3
---

## Abstract

Several actors have drafted diverging visions for the future climate impact of air transport. This
paper aims to: to review ATAG Waypoint 2050 scenarios across the three editions of the report, while
quantifying emissions reductions achieved from each of the mitigation levers presented. The
methodology behind reproduction is described, scenarios are simulated using the AeroMAPS open-source
framework, and extensions of the Waypoint scope is presented by: coupling traffic growth to rising
energy costs, and incorporating contrails avoidance.
 {raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The three published scenarios are reproduced with well-to-wake residual emissions of about 1,820, 420 and 360 MtCO₂ in 2050, and of 1,510, 350 and 260 Mt on the tank-to-wake basis adopted by the reports. Sweeping the full lever grid places these three points within a range spanning 208 to 2,359 Mt, so that the published scenarios constitute a sparse sample of their own design space rather than its bounds. Closing the demand-price loop left open by the reports reduces 2050 traffic by 1 to 15 % depending on the carbon price, a range which brackets the 14 to 16 % quoted by the reports themselves from other studies before the question is set aside. Regarding climate impacts, extending the accounting beyond CO₂ yields a sharper result: the non-CO₂ uncertainty band carried by a single scenario is roughly 3.2 times wider than the entire spread between the published scenarios, so that the choice between them is, on current knowledge, a smaller question than the uncertainty each of them carries.</span>{raw:typst}`]`
While the ATAG reports address the modeling methods used for the quantification of aviation
emissions, there is limited transparency in the provenance of data, calibration methodology, and
mathematical formulation, which further difficult comparisons and their overall impact for policy
purposes. On this front, authors advocate for the use of open-source and open-data, which are
greatly beneficial to explicit assumptions and finding a common ground for high-level decision
making.

## Authorship of this draft

This document follows the structure of the manuscript in preparation. Text in **black** is the
author's own, carried across unchanged apart from mechanical transcription from LaTeX to MyST
(`\cite{key}` becomes `` {cite:p}`key` ``, `$\text{CO}_2$` becomes CO2, and so on).

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Text in this colour was drafted by an AI assistant, filling the `+` placeholders left in the manuscript. Every value reported in it is read from a committed scenario output and is reproducible from the notebook named alongside it. The prose surrounding those values constitutes a draft, to be accepted, rewritten or discarded by the author.</span>{raw:typst}`]`

Two mechanical notes. `lee_contribution_2021` is cited here as `lee2021`, the same paper under the
key this repository already uses. And the citations filling the author's inline `+cite` markers are
set in black rather than colour, because a colour span containing nothing but a citation does not
survive the PDF export; the references chosen at those four markers are
{cite:p}`euets_nonco2_text` for non-CO2 monitoring, {cite:p}`teoh_mitigating_2020,corsia_text` for contrail
avoidance crediting, {cite:p}`lee_contribution_2021,teoh2024,icct_vision_2022` for the missing climate
accounting, and {cite:p}`gossling_humpe_2020,destination2050_2021` for demand feedback.

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
than that of CO₂ {cite:p}`lee_contribution_2021`. Furthermore, while mitigation levers that tackle CO₂ may also
reduce non-CO₂ to some extent, this is still subject to ongoing research.

Achieving the Paris Agreement targets requires deep, rapid, and sustained emissions reductions
across all economic sectors. Aviation is considered a hard-to-abate sector whose mitigation relies
on a few levers with opposing effects on the cost of flying {cite:p}`delbecq_sustainable_2023`:
Sustainable Aviation Fuels (SAF) and carbon pricing and Market-based measures (MBM) raise this cost,
while operational and vehicle efficiency are expected to lower the impact of increased fuel prices
to airlines and travelers. Besides its decarbonization policy, specific measures to tackle non-CO₂
are currently being formulated for monitoring these effects {cite:p}`euets_nonco2_text` and for
allowing airlines to claim carbon allowances from contrail avoidance strategies
{cite:p}`teoh_mitigating_2020,euets_contrails_2026`.

Among the numerous industrial {cite:p}`gifas_2022,atag2026_waypoint,iata2024,airbus2025gmf,boeing2025cmo`, institutional {cite:p}`icao_ltag_2022,iea_netzero_2021,icct_vision_2022`, and academic
{cite:p}`sgouridis_air_2011,terrenoire_contribution_2019,grewe_evaluating_2021,klower_quantifying_2021,gossling_net-zero_2024,dray_aim_2019,franz_wide_2022,brazzola_definitions_2022,bergero_pathways_2023,sacchi_how_2023,costa-alves_numerical_2026` scenarios that have been made for aviation, the Air Transport Action Group (ATAG) Waypoint
2050 stands as the industry vision of the transition of the sector up until 2050. While the three
different editions of the report {cite:p}`atag2020_waypoint,atag2021_waypoint,atag2026_waypoint`
are rich in detail and figures for the future 25 years, the underlying methods and assumptions are
not always explicit nor reproducible. In the context where national and international policies are
derived from such, we argue for more openness regarding: models, data, background assumptions,
limitations, and uncertainties. Furthermore, as highlighted by many academic works, these industry
and institutional scenarios lack accounting of the full climate impacts of aviation
{cite:p}`grewe_evaluating_2021,klower_quantifying_2021,brazzola_definitions_2022,sacchi_how_2023,icct_vision_2022`, and for the feedback of policy-induced cost increases on traffic demand
{cite:p}`dray_aim_2019,gossling_net-zero_2024,costa-alves_modeling_2026`.

This work asks whether the ATAG third-edition scenarios can be reproduced transparently, lever by
lever, in the AeroMAPS {cite:p}`planes_aeromaps_2023` open-source framework. Furthermore, extra
capabilities of the framework are employed to demonstrate two points that lack in all ATAG
reports: analysis of demand-side impacts of transition costs, and quantification of temperature
impacts of scenarios with different strategies for contrail avoidance.

### ATAG Waypoint Reports

The first edition of the ATAG Waypoint 2050 report {cite:p}`atag2020_waypoint` was launched in
September 2020 during the COVID-19 crisis, when aviation experienced its greatest drop in traffic
levels seen in recent history. The report frames the pandemic as an opportunity for a "green
recovery" as the social function of air travel was put in question. By then, the official target was
to halve 2005 emission levels by 2050, and the sector's position as a hard to abate sector is
emphasized, mentioning that net zero could be achieved by 2060-2065. Four prospective scenarios are
presented:

- **S0: baseline/continuation of current trends**  
  Central range for traffic forecasts,
  conservative operational and technology improvements with a new generation of new aircraft to
  entry into service by 2030-2035, deployment of SAF based on current rates, and carbon offsets are
  used as the principal lever to align emissions to emission reduction goals;
- **S1: pushing technology and operations**  
  Ambitious operational and technological improvements
  with unconventional aircraft (hybrid-electric) to entry into service by 2035-2040, deployment of
  SAF is supposed to align scenario to industry goal by 2050, and offsets are used as a transition
  mechanism until 2050;
- **S2: aggressive sustainable fuel deployment**  
  Ambitious operational and technological
  improvements with disruptive aircraft configurations (blended wing body), but only using
  conventional propulsion based on jet-fuel, SAF deployment is accelerated and is supposed to align
  scenario to goals by 2035, offsets are used as a transition mechanism until 2035;
- **S3: aspirational and aggressive technology perspective**  
  Very ambitious technology
  improvements with larger deployment of unconventional aircraft (liquid hydrogen and
  hybrid-electric), SAF deployment is slower and partially aligns emissions to goals by 2050,
  offsets are used as a transition mechanism until 2050.

By 2021, IATA member airlines increased their climatic ambition by adopting net-zero emissions by
2050 as a target {cite:p}`iata2021_netzero`, and a new edition was published on the same year
{cite:p}`atag2021_waypoint`. The second edition reuses the same scenario definitions as the first
one, but when quantifying the role of each mitigation lever, it lowers expected emissions reductions
for operations and technology, and significantly increases the expected reductions from deploying
SAF, the need of carbon offsets is also revised upwards as no scenario reaches the new goal of net
zero without recurring to them.

Finally, the third edition was launched in 2026, as traffic levels are reaching all-time records
after the recovery from the pandemic crisis, and assumes a position more focused on practical
implementation of policies and the necessary regulatory framework to turn vision into reality. This
edition removes the S3 scenario, to reflect delayed expectations for aircraft with unconventional
propulsion systems, and switched the ordering and naming of scenarios: the **S1: focus on SAF
deployment** is inspired on the S2 of previous versions, and **S2: technology-centric market**
similar to the previous S1. Regarding the extent of each of the mitigation levers, both operations
and technology display similar expectations compared to their analogous scenario in the previous
version, SAF deployment is revised to reflect delays due to policy coordination failures and
investment bottlenecks, but is still seen as the main lever for emissions reductions and delays are
compensated by assuming a stronger ramp-up of production volumes. The role of offsets is also
revised upwards and with more detailed modeling to reflect current policies: regionally-resolved
offsets are estimated based on the implementation of CORSIA for international aviation until 2035,
and an extra policy is assumed to be put in place after that to allow for reaching net-zero by 2050.

The figure below shows the contribution of each of the modeled mitigation levers for the S0
baseline scenario for each of the three editions of the report. Overall, with every new edition the
expected emissions reductions attributable to fleet renewal, next generation aircraft technology,
and operational efficiency are revised downwards, while the attributable to SAF is revised upwards.
The second edition increased expected baseline emissions, while increasing ambition regarding
emissions reductions, for which the role of SAF increased (both in low and high SAF cases). The
third edition, also increased the role of SAF in the low case, but revised the high SAF back to
expectations of the first edition.

"Omitting key variables simply because data are lacking is effectively equivalent to assigning them
a value of zero, arguably the only value that is certain to be incorrect"
{cite:p}`sterman_business_2009`. Besides the over-reliance of the Waypoint scenarios on SAF, two
methodological critiques are also made regarding the analysis carried by ATAG:

- **Exogenous demand:** air traffic demand follows central industry forecasts unaffected by
  transition costs, even though energy carrier several times costlier than kerosene has been in
  recent history and future carbon prices are expected to rise steeply to align with scenarios
  compatible with the Paris Agreement. The emissions reductions attributed to each lever are
  therefore estimated supposing traffic volumes are the same regardless of how strong SAF and
  carbon pricing policies are. "Accurate assessment of demand impacts across multiple market types,
  in multiple currencies and very different dynamics was not a task undertaken for the Waypoint 2050
  global analysis. Scenarios in this analysis, therefore, do not include feedback effects on global
  aviation traffic from potential costs of decarbonization" {cite:p}`atag2026_waypoint`;
- **Climate impacts:** besides CO₂ emissions, non-CO₂ effects carry the majority of aviation's
  historical forcing and are dominated by contrail cirrus, for which operational strategies exist
  and are not expected to be costly relative to decarbonization. The report's conclusion that "the
  current priority for industry and government climate action should continue to be CO2 emissions
  reduction (where there is high scientific certainty)" {cite:p}`atag2026_waypoint` is not in line
  with the scientific literature that states that, despite their high associated uncertainties,
  contrail avoidance is shown to allow for significant reductions in climate impact, all while being
  cheaper and easier to scale relative to SAF.

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
was reached from a past state, as well as which future realities may be reached from current state.
Furthermore, in the case where disruptions in past trends are foreseen, possible evolution paths of
associated drivers must be quantified as well as their system-level impacts. In doing so, if impacts
are great enough to invalidate assumptions established by the mathematical model, a new model
proposition has to be made, and the cycle is repeated.

This means that both the analysis and the models used for it are continuously improved, however,
most prospective groups treat the problem as a sequential problem: models are calibrated based on
the past, future drivers are quantified, impacts are assessed, and model assumptions remain
unchanged regardless of the intensity of such impacts. Different exercises of the same method differ
only on which novel data and insights are accounted for, but they do not inform on the goodness of
the exercise itself.

Methodologically, this paper employs a similar sequential approach for reproducing ATAG Waypoint
scenarios with the AeroMAPS framework. First a reference air traffic forecast is used based on
annual growth rates of Revenue Passenger Kilometers (RPK), then fuel-burn reductions per Available
Seat Kilometers (ASK) supply provided due to improved technology developments from renewal of
current fleets as well as the deployment of future aircraft concepts, operational and infrastructure
improvements also result in fuel-burn reductions per ASK and also by decreasing total ASK supply for
a given RPK demand due to increased seat occupancy. Besides the efficiency levers that intend to
decouple demand to fuel/energy consumption, the incorporation of SAF intends to reduce the carbon
content per unit of fuel consumed by using alternative production pathways for kerosene-like
molecules, then residual unabatted emissions are adressed by MBMs by financing out-of-sector offsets
or negative emissions technologies.

Scenario variants are developed for each lever: high/central/low traffic (H/C/L),
frozen/baseline/conservative/new configurations/non-drop in aircraft technology (T0-T4),
low/mid/high operational improvements (O1-O3), stated policies/agressive deployment/technology-centric
SAF deployment (F1-F3). The three published scenarios correspond to points on that grid: S0 combines
central traffic, conservative aircraft technology and operational improvements, and stated policies
for SAF production (C·T2·O2·F1); S1 increases ambition regarding aircraft, operations, and SAF
(C·T3·O3·F2); and S2 increases ambition, relative to S1, regarding aircraft technology and decreases
ambition regarding SAF (C·T4·O3·F3). Market-based measures are not swept independently, since they
are computed as the residual required to reach the stated target and therefore do not represent an
extra degree of freedom. The full factorial scenario exploration, sweeping all possible combination
of levers, is also not carried in the ATAG analysis, but can be drawn after a full reproduction of
these assumptions.

Finally, the framework is also employed to demonstrate how to break out of the sequential approach
by removing one key assumption kept by all three editions: that traffic growth won't be affected by
rising transition costs, which creates a demand-price coupling that cannot be solved with purely
sequential approaches.

### AeroMAPS

Employing open-source tools to simulate policy scenarios can be highly beneficial for making
modelling assumptions explicit, improving the reproducibility of policy objectives, and supporting a
common ground for high-level decision-making. In this context, the present work uses AeroMAPS
{cite:p}`planes_aeromaps_2023`, an open-source sectoral integrated assessment framework for air
transport designed to represent prospective aviation scenarios and their environmental impacts
across multiple disciplinary fields.

AeroMAPS is organised as a graph of small declarative modules that are solved together based on the
GEMSEO library {cite:p}`gallard_gems_2018`: modules explicitly define their inputs and outputs
through variable names, allowing the solver to automatically handle model integration, execution
sequence, numerical couplings and feedback loops (necessary features for the demand-price coupling
showcased later). The framework was developed to be relatively easy to use and widely distributable
among academic, institutional, and industrial stakeholders, while enabling sectoral environmental
sustainability assessments and the evaluation of transition strategies. Its modular architecture
also facilitates the integration of models from different disciplinary fields, furthermore it is
also responsible for allowing for dynamic model assemble, which means simulation can be tailored to
analysis of different scopes regarding:

- **Geographic coverage:** a scenario can be simulated either with a single global or regional
  (continent, country) level depending on the analysis geographic scope, or with multiple
  simultaneous regions solved together, where each has a tailored traffic, fleet and fuel policy,
  which are then aggregated together. Both are used here: the third-edition S1 and S2 scenarios are
  global, while the S0 reference is an aggregation of a twenty-region run with country-level SAF
  mandates based on current policies {cite:p}`salgas_pledges_2026`;
- **Market segmentation:** the split of global traffic into segmented markets is also left open,
  each with its own traffic driver, energy intensity and, where the demand-price coupling is active,
  its own price elasticity. The reproduction uses four: short, medium and long range passenger
  traffic in Revenue Passenger Kilometers (RPK), and freight in Revenue Tonne Kilometers (RTK);
- **Fleet renewal:** within each market, fleet-wise reductions in fuel-burn can be either modeled
  based on market-aggregated efficiency gains figures (top-down) or by splitting supply among
  different aircraft categories/subcategories/models each with its own energy consumption, market
  penetration, and subject to fleet renewal rates (bottom-up);
- **Energy production pathways:** each carrier is resolved into named production pathways carrying
  their own cost, emission factor and upstream resource demand, so that the fleet-average costs and
  carbon intensity follows the mix of several different production pathways. For instance, the S0
  scenario (which does not specify which types of SAF are expected to be deployed) aggregates the
  biomass pathways into a single generic carrier, the SAF-focused S1 scenario deploys seven biomass
  pathways, alongside electrofuel, and fossil kerosene, while technology-focused S2 scenario also
  adds liquid hydrogen and battery charging to the carriers set;
- **Emission scopes:** the standard accounting method in the ATAG reports is tank-to-wake (TtW)
  following the CORSIA methodology, which includes only emissions from combustion, however AeroMAPS
  default is to report them in well-to-wake (WtW) scope, which include emissions that happen
  upstream in the fuel production lifecycle. Every scenario considered here is run in both scopes,
  as a pair of otherwise identical configurations;
- **Cost analysis:** fuel production costs, aircraft direct operating costs, carbon prices and
  marginal abatement costs are available, at a top-down resolution taking an aggregate cost per unit
  energy, or at a bottom-up one built from plant capital expenditure, operating costs and
  construction lead times. The top-down formulation is used throughout this reproduction, since it
  corresponds to the resolution published by the reports.

For more details on the software architecture, simulation workflow, and some model components
readers are referred to {cite:p}`planes_aeromaps_2023`. New developments have been carried since
then to keep up with and advance the state-of-the-art regarding modeling: energy economics
{cite:p}`salgas_cost_2023,salgas_marginal_2024`, fleet renewal {cite:p}`viry_empirical_2024`,
temperature impacts {cite:p}`arriolabengoa_lightweight_2024`, prospective life-cycle assessment
{cite:p}`pollet_comprehensive_2024`, long-term behavioral impacts of policies on traffic demand
{cite:p}`costa-alves_modeling_2026`, and the impact of country-level SAF policies
{cite:p}`salgas_pledges_2026`. The manuscript's architecture figure summarizes the resulting modules
and the data flow between them, as well as the demand-price coupling explored in the following
sections.

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Three modules compose the architecture. Air transport defines future traffic per market, the efficiency gains delivered by future aircraft, fleet renewal and operations, and the energy carriers supplied to the engines. Impacts estimates the consequences of the simulated policies in terms of resources, economics, emissions, temperature increase, and further environmental indicators obtained by life-cycle assessment. Assessment then compares those impacts against economy-wide targets of resource allocation, carbon and temperature budgets, and marginal abatement costs. A soft link to a background scenario supplies the carbon price trajectory, which acts directly on airline costs and on the airfares passed on to travellers, together with population and per-capita income, from which future traffic is estimated. Since airfares in turn act on traffic, the coupling between the two constitutes a fixed-point problem solved numerically, and it is that feedback which the reproduced scenarios of the following sections deliberately leave open before it is closed in the results.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The scenario definition lives entirely in declarative files: a YAML configuration selecting the module chain and its data files, a JSON file of parameter trajectories, and YAML descriptions of energy carriers, processes and resources. No scenario presented in this paper required writing model code, which is what renders the lever-by-lever reproduction auditable, every quoted value being traceable to a committed input file and a committed output file.</span>{raw:typst}`]`

### Validation

Reproducing a scenario whose assumptions are partially published requires being explicit regarding
the origin of input values. Four classes are distinguished, in decreasing order of confidence:
values read directly from the text (operational assumptions), values digitized from published
figures (traffic, load factor, SAF production per pathway), values calibrated so that outcomes
reproduces its digitized trajectory (annual efficiency improvements from fleet renewal and next
generation aircraft technology), and values left at the defaults of the framework where the reports
disclose nothing that would constrain them (kerosene cost, carbon prices, electricity emission
factor).

The calibration of efficiency improvements was carried based on the aircraft technology lever. Even
though the ATAG reports detail which technologies are expected to decrease the consumption of future
models, their expected energy consumption, market shares, and renewal rates are not explicit, which
motivated the choice for a top-down fleet model instead of the bottom-up one. All markets are
considered to have the same annual efficiency gains, whose values are chosen in order to reproduce
the emissions trajectory of technology-only scenarios:

- **T0 - Frozen Fleet Efficiency:** illustrative scenario with no further renewal of old aircraft
  models;
- **T1 - Baseline:** old aircraft are replaced by existing aircraft, but no new models are deployed;
- **T2 - Conservative:** new generation of tube-and-wing aircraft with conventional propulsion;
- **T3 - New configurations:** new propulsion systems (open-fan) up to 300 seat categories, radical
  aircraft configurations (blended wing-body, high aspect-ratio wings) in the 211-300 seat category;
- **T4 - Towards non-drop in energies:** batteries and liquid-hydrogen aircraft below 100 seat,
  hybrid propulsion systems in remaining seat categories.

These scenarios allow to reproduce efficiency gains and emission reductions achieved by aircraft
technology alone, without the addition of any other mitigation levers. The technology-scope figure
below compares values obtained after the calibration of annual efficiency gains against the report's
own curves in both accounting scopes.

With regards to the resolution at which SAF is published differs across the scenarios: the S1 and S2
fuel levels are displayed per-pathway resulting in eleven energy carrier types overall, whereas the
S0 level publishes a total volume with no pathway breakdown and is therefore modelled as a single
generic carrier which include both stated policies and goals for SAF. The present work, instead,
derives the S0 baseline scenario from stated policies alone, based on a multi-regional aggregation
of country-level SAF policies {cite:p}`salgas_pledges_2026`, and yields lower volumes than the ATAG
analysis.

Finally, another assumption that make these scenarios stray further away from a pure reproduction of
ATAG is regarding MBMs. Up until 2035, the third edition estimates offsets regionally based on
CORSIA, whose ambition is only to reach a stabilization of emissions instead of decreasing residuals
until reaching net-zero in 2050. From 2035 onwards, ATAG reports assumes extra policies that offsets
increasing shares of residual emissions such that net-zero is reached by 2050. This work also
reproduces regionally-resolved offsets based on CORSIA and EU-ETS up to 2035, from then until 2050
scenarios are assumed to reduce net-emissions in a linear pace until net-zero. While the report may
vary this pace depending on each scenario, this work chooses to harmonize this assumption across
scenarios and to report deviations in terms of residual emissions, as there is little visibility on
the future policies targeting net-emissions beyond 2035.

Each lever maps onto a single parameter of the framework, which is the correspondence both the
reproduction and the systematic sweep presented later rely on:

| Lever | Variants | AeroMAPS knob |
|---|---|---|
| Traffic | low / central / high | `markets/markets_{low,central,high}.yaml` |
| Technology | T0–T4 | efficiency series in `*_inputs.json` |
| Operations | O1 / O2 / O3: 0.00 / 0.10 / 0.20 %/yr | `operations_gain_reference_years_values` |
| SAF | F0 / F1 / F2 / F3 | `energy_carriers_model_data_file` |
| Market-based measures | M1 / M2 / M3 | computed as the residual to the target |


### Coupling air traffic and fuel prices

Transportation research links many economic, demographic, and geographic factors as drivers to
passenger and freight demand {cite:p}`european_conference_of_ministers_of_transport_managing_2003`.
In the context of climate mitigation scenarios, a specific focus is drawn to quantifying the impact
of variables that are affected by climate policies and climate damages, such as population,
per-capita income, and prices. These global analysis are the subject of the Working Group 3 (WG3) of
the Intergovernmental Pannel on Climate Change (IPCC), and the quantitative data obtained from
scenarios analysed in their 6th Assessment Report (AR6) is openly available {cite:p}`ar6_database`.

In order to couple the costs of future policies to demand, a model of aggregate Revenue Passenger
Kilometers (RPK) demand has been formulated and calibrated on historical data
{cite:p}`costa-alves_modeling_2026`. The model uses: S-curves to estimate trend per-capita demand
from GDP per capita accounting for the stabilization of demand growth as emergent aviation markets
mature, long-run price sensitivity accounting for fluctuations of fuel prices and the historical
decrease in energy intensity, and delays between perceived airline costs and transmission of
airfares onto travelers. One limitation of this approach is that the price elasticity only accounts
for energy/fuel prices in the airfare, the calibrated fuel cost elasticity of -0.345 would yield an
airfare-equivalent price elasticity of -1.456 supposing 23.7 % of the airfare is composed of fuel.

Two additions are made relative to the standard AeroMAPS simulation: first a background is chosen
based on a scenario from the AR6 scenario database {cite:p}`ar6_database` impacting the future GDP,
population, and carbon price trajectories; and a bidirectional coupling is made between airline
costs and air traffic, where costs are estimated based on supply volumes and demand volume is
estimated based on supply cost.

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The mechanism constitutes a closed loop rather than a correction applied afterwards. A carbon price raises the energy component of direct operating cost per available seat-kilometre, which propagates to the net cost per revenue passenger-kilometre. A first-order lag then converts cost into the fare actually faced by travellers, a price index relative to a reference year drives demand through the calibrated elasticity, and the resulting traffic feeds back into fuel burn, energy demand, and therefore cost again. The loop is closed by the MDA solver of the framework as a fixed point, so that the reported traffic remains consistent with the cost of achieving the abatement of the scenario itself.</span>{raw:typst}`]`


### Climate response and contrail avoidance

Broadening the scope from decarbonization into full climate mitigation requires including non-CO₂
effects like contrails and NOx emissions, furthermore it requires a unified impact metric in order
to compare the short-lived and highly uncertain non-CO₂ warming with that CO₂, which is long-lived
and with less uncertainties. The issue, however, is that there is no consensus on which measures to
compare them, and this choice may inherently emphasize some climate effects over others
{cite:p}`megill_alternative_2024`.

This work bypasses the need for such CO₂-equivalence metrics by using climate emulators based on the
FaIR models {cite:p}`millar_fair_2017,leach_fair2_2021`, which are able to compare mitigation
strategies in terms of temperature impacts, and are lightweight enough to allow for propagating
climate-system uncertainties {cite:p}`arriolabengoa_lightweight_2024`. Emission models are
disaggregated per gas species considered as a climate forcer, these enter as sources in a set of gas
pools (stocks that accumulate a share of emissions and deplete their own stock based on a
characteristic lifetime), atmospheric concentrations increase if sources outweigh sinks when
accounting for all gas pools, changes in concentrations lead to imbalances in terms of Effective
Radiative Forcing (ERF), which warm a climate system discretized into thermal boxes, yielding
changes in global mean temperatures, finally, the timescale of emission sinks have to adjust to
state of the climate system at each instant (concentration, temperature, and total stocked volume in
sinks).

Even though contrails have a net warming impact on the climate, they are not considered as
greenhouse gases and therefore cannot have an associated atmospheric concentration. Therefore, the
estimation of its radiative forcing is based on the total flight distance
{cite:p}`lee_contribution_2021` and also on the overall particle number of the engine exhaust
{cite:p}`burkhardt_mitigating_2018`. Indeed, blending SAF with fossil kerosene can lead to a
reduction in soot emissions due to their lower aromatic content {cite:p}`voigt_cleaner_2021`,
resulting in a reduction in overall contrail impact aside from the CO₂. One limitation of this
aggregated approach is the inability to separate effects of different individual flights, which is
not suited for simulating SAF targeting strategies {cite:p}`teoh2022` where SAF concentrated in few
flights instead of spread over many flights for minimizing climate impact with a limited supply.

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Emissions are converted into warming by a reduced-complexity climate model of the FaIR family, run per forcing mechanism rather than on CO₂ alone, so that CO₂, contrail cirrus, the four NOx pathways, water vapour, soot and sulfur each yield their own effective radiative forcing and their own contribution to the temperature response. The decomposition is verified rather than assumed, the sum of the mechanism groups reproducing the reported total to machine precision in every scenario, as asserted in `climate_analysis/climate_analysis.ipynb`.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Contrail forcing is driven by distance flown rather than by fuel burn, which is a necessary condition for contrail avoidance to be representable at all, since a strategy lengthening routes in order to avoid ice-supersaturated regions reduces forcing while increasing fuel consumption, and the two effects must therefore be able to move in opposite directions. A mitigation lever scales that forcing by a final gain phased in along a logistic ramp from a start year, together with a paired overconsumption penalty, both parameterised from Teoh et al. {cite:p}`teoh_mitigating_2020` in `contrail_variants.yaml`.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Fuel composition enters through soot. Cleaner fuels emit fewer non-volatile particles, seeding fewer and larger ice crystals, and the model represents this effect as a scaling of contrail forcing with the square root of the particle number emission index, weighted by the massic share of each pathway. The square-root form allows the percentage reductions in contrail forcing reported in the literature to be mapped directly onto an emission index.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Two independent uncertainties are propagated rather than fixed. The first concerns how strongly contrails warm at all. Lee et al. {cite:p}`lee_contribution_2021` give a 2018 contrail radiative forcing whose 95 % interval spans roughly a factor of six, whereas Teoh et al. {cite:p}`teoh2024` simulate actual trajectories and obtain a 2019 central value well below it, with a sensitivity range of 34.8 to 74.8 mW m⁻². The second concerns how much cleaner fuel reduces that forcing, the modelling literature surveyed by Teoh et al. {cite:p}`teoh2022` spanning a 15 % reduction at one end and 50 % at the other for fleet-wide adoption. Both bounds are recorded with their sources in `climate_analysis/non_co2_uncertainty.yaml` and combined into three bands named by climate impact, so that the high band pairs the largest contrail sensitivity with the weakest fuel benefit and the low band the reverse. The central band retains the calibrated values of the repository on both axes, so that the centre of every band reproduces the published scenarios exactly.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The wider context for treating this as a first-order question rather than as a refinement is set by the ICCT's *Aviation Vision 2050* {cite:p}`icct_vision_2022` and by {cite:p}`arriolabengoa_lightweight_2024`. According to their accounting, the majority of the warming that aviation can still avoid between now and 2050 is short-lived, and contrail avoidance rather than fuel substitution constitutes the largest single contributor to it.</span>{raw:typst}`]`

## Results

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The reproduction is presented lever by lever, following the order adopted by the reports, and is then extended in two directions placed out of scope by them. Every figure below reads a committed scenario output, no model being executed while this document builds, and each result names the notebook that produced it.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Across the three editions the physical levers moved remarkably little, whereas the accounting surrounding them moved a great deal. Traffic forecasts are essentially unchanged in shape, differing mainly in where the COVID recovery is anchored, and technology and operations were revised *downwards* between the first and second editions before being held roughly constant into the third. What changed is the allocation of the residual, since as the target was raised from halving 2005 emissions to net zero, the additional burden fell almost entirely on SAF and on market-based measures, that is, on the two levers whose feasibility depends least on aircraft engineering and most on energy supply, capital and policy. A roadmap that redraws its baseline while holding its terminal target will report shifting lever contributions even when nothing physical has changed, so that cross-edition comparisons are comparisons between accounting conventions at least as much as between technical expectations.</span>{raw:typst}`]`

```{important}
**Read the accounting scope before comparing residuals.** The reports headline *tank-to-wake*
emissions, following the CORSIA methodology: SAF is credited through a lower life-cycle factor, but
the figure quoted is combustion. The scenarios reproduced here are *well-to-wake*: they carry each
pathway's full life-cycle emission factor, so their residuals are **expected to sit above** the
report's numbers, not alongside them. Both scopes are now available from committed outputs, so the
comparison can be made directly rather than argued: S1 reproduces at 424 Mt well-to-wake and 352 Mt
tank-to-wake in 2050, against a reported ~400 Mt; S0 at 1,816 Mt and 1,511 Mt against
~1,150–1,350 Mt. The tank-to-wake twins are derived from the well-to-wake files by
`aeromaps.utils.emission_scopes`, following the CORSIA accounting the reports describe.

This is worth stating explicitly because the opposite pattern was, for a while, exactly what this
reproduction produced. A misspelled key (`co2_emission_factor_without_resource` where the model
reads `mean_co2_emission_factor_without_resource`) meant every biomass SAF pathway was silently
assigned a **zero** emission factor, the model resolving a missing key to a null series rather than
raising. S1 then read 386 Mt, which sat comfortably next to the reported ~400 Mt and looked like
agreement. It was not: a well-to-wake figure matching a tank-to-wake one is the anomaly, and it went
unremarked because the number looked right. The same class of defect was found twice more while
this document was being written, both in electrofuel and both in the same direction: its
report-derived cost and its report-derived emission factor are life-cycle figures that already
include the green electricity and DAC-CO2 behind them, and the model was charging for both a second
time. Correcting the emission factor alone removes about a third of the 2050 residual of S1 and S2.
```

```{code-cell} python
:tags: [hide-input]

# One figure for the three scenarios: a row each, tank-to-wake on the left and
# well-to-wake on the right. Every panel shares one y-axis, across the pair and
# down the column, so both the scope difference and the scenario difference are
# readable as distances rather than inferred from tick labels.
TRIPLETS = [
    ("S0", S0_TTW, S0), ("S1", S1_TTW, S1), ("S2", S2_TTW, S2),
]
available = [(name, ttw, wtw) for name, ttw, wtw in TRIPLETS if ttw is not None and wtw is not None]

if available:
    fig, all_axes = plt.subplots(len(available), 2, figsize=(13.0, 12.6), sharey=True,
                                 sharex=True, layout="constrained")
    all_axes = np.atleast_2d(all_axes)
    for (name, ttw, wtw), axes in zip(available, all_axes):
        # The legend goes on the first row only: the bands are the same in all
        # three, and repeating it would cover the wedges it describes.
        ttw.plot("mitigation_wedges", fig=fig, ax=axes[0],
                 anchors=(T0_TTW, T1_TTW),
                 legend=name == available[0][0],
                 title=f"{name} - tank-to-wake")
        wtw.plot("mitigation_wedges", fig=fig, ax=axes[1],
                 anchors=(T0, T1), legend=False,
                 title=f"{name} - well-to-wake")
        axes[1].set_ylabel("")

    # One scale for all six panels, taken from the drawn data and applied before
    # anything is written, so no curve is clipped and the exported PDF agrees
    # with the page. Reading the limits back only works because the helper
    # leaves autoscaling alone.
    top = max(ax.get_ylim()[1] for axes in all_axes for ax in axes)
    for axes in all_axes:
        for ax in axes:
            ax.set_ylim(0, top)
    for ax in all_axes[:-1].ravel():
        ax.set_xlabel("")
    save_fig(fig, name="atag_decomposition")
```

*Annual CO2 emissions decomposed by mitigation lever, following the pillars and colours ATAG uses. One row per reproduced scenario, tank-to-wake on the left and well-to-wake on the right, with all six panels on one vertical axis so that both the gap between scopes and the gap between scenarios read as distances.. All six panels share one vertical axis, so both the gap between the two accounting scopes and the gap between scenarios read as distances. Each band is what one pillar removes from the frozen-fleet baseline (dotted). Fleet renewal is the T0-to-T1 distance and next generation technology everything below it, which is where battery-electric aircraft sit rather than in the fuel band; the dashed line is emissions net of market-based measures. Offsetting after 2035 is an assumption rather than a reproduction, because the policy the reports invoke to reach net zero does not exist: CORSIA-derived offsets are modelled through 2035, and from 2036 net emissions are taken to fall linearly to zero at 2050 from wherever 2035 leaves them. That is the shape all three published scenarios draw, and it is what makes the dashed line continuous at the handover. One caveat on reading the bands: the wedges sum to a determinate total, but how that total divides between the technology and fuel pillars depends on the order they are peeled off in, by a factor of 35 on S2. See the Discussion.*

```{important}
**How the tank-to-wake panels are built.** The reports headline tank-to-wake emissions, and the
third edition does not publish a per-pathway CORSIA-scope table, so those panels are derived
rather than read off. Each drop-in pathway takes the fossil combustion baseline scaled by its
published carbon-intensity ratio, TtW = 73.8 x (CI / 88.7), which is the CORSIA accounting the
report describes and the same method the second edition's own tank-to-wake files already use:
its electrofuel reads 7.38, exactly 73.8 x 0.10. Anything not combusted reads zero. The
transform is in `aeromaps.utils.emission_scopes`, so the twins are regenerated from the well-to-wake files
rather than maintained by hand, and the result reproduces the report's own stated reductions:
electrofuel comes out 84.9 % below fossil in 2025 and 91.4 % in 2050, against the 85 % and 91 %
the carbon-intensity table states.
```

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
    fig, (ax_ttw, ax_wtw) = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True, layout="constrained")
    assemble_processes(tech_ttw).plot("co2_emissions_comparison", fig=fig, ax=ax_ttw)
    assemble_processes(tech_wtw).plot("co2_emissions_comparison", fig=fig, ax=ax_wtw)

    for index, (name, curve) in enumerate(sorted(report["technology_scenarios"].items())):
        ax_ttw.plot(curve["years"], curve["values"], ":", color=f"C{index}", linewidth=1.6,
                    label=f"{name} - report")
    ax_ttw.legend(fontsize=7, ncol=2)

    ax_ttw.set_title("Tank-to-wake, against the report")
    ax_wtw.set_title("Well-to-wake")
    ax_wtw.set_ylabel("")
    y_max = max(ax_wtw.get_ylim()[1], ax_ttw.get_ylim()[1])
    ax_ttw.set_ylim(0, y_max)
    ax_wtw.set_ylim(0, y_max)
    save_fig(fig, name="technology_scopes")

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

*The five technology-only scenarios, tank-to-wake on the left and well-to-wake on the right, sharing a vertical axis. Both panels run identical scenarios, so the distance between them is the accounting scope alone. The dotted curves on the left are the report's own published trajectories, digitised from its charts; they are tank-to-wake, which is why they appear on that panel and not the other. Agreement at 2050 runs from 0.6 % on T2 to 2.3 % on T4, and it is the closest thing to an external check this reproduction has, since these are the only curves the report publishes at a resolution that can be read off. `make_tables.py` gives the same comparison at 2030 and 2040 and over the cumulative period.*

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Each scenario is drawn as the reports draw it, that is, as a rising frozen-technology baseline followed by successive wedges for fleet renewal, next-generation technology, operations and load factor, SAF, and finally market-based measures closing the gap to the target. The share carried by each wedge is the value headlined by the reports, and it is where the editions differ most.</span>{raw:typst}`]`


{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Two observations follow directly. On one hand, the energy lever dominates, carrying several times the combined technology, operations and load-factor wedges, which constitutes a statement regarding fuel supply and capital rather than regarding aircraft engineering. On the other hand, the technology, operations and load-factor wedges are near-identical between S1 and S2, confirming that the two published scenarios differ almost exclusively in how much SAF is deployed and how fast. The nominal distinction between a "SAF-focused" and a "technology-centric" scenario is therefore, in the quantities reaching the atmosphere, mostly a distinction in fuel volume.</span>{raw:typst}`]`


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

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Beyond the three published points, the remainder of the lever grid is left unexplored by the reports. Sweeping all 144 combinations of traffic, technology, operations and SAF places the published scenarios within a considerably wider range, and the position they occupy within it is itself informative, since they occupy neither the optimistic nor the pessimistic corner while not constituting a designed sample of the space either. Three scenarios cannot express which combinations are jointly plausible, nor how much of the spread originates from each lever. The bundle is coloured by technology rather than by SAF, since substituting the fuel changes what a joule emits rather than how many of them are burned, which would leave the two energy panels undifferentiated. Even so, those panels resolve only three bands out of four technology levels, because T3 and T4 consume identical energy and differ only regarding what carries it.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">This constitutes the practical argument for moving from a handful of named scenarios to a systematic sweep. A named scenario communicates a narrative while hiding the sensitivity, whereas a sweep exposes the sensitivity while losing the narrative. The reports require the narrative, but forming policy expectations also requires knowing that the difference between the published scenarios is small compared with the range that their own levers can produce, and, as the climate results below show, small compared with the uncertainty attached to any one of them.</span>{raw:typst}`]`

### Traffic, technology, operations and SAF, in detail

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The three published scenarios constitute single points on the lever grid, and the sweep above shows the grid without showing what each lever looks like on its own. This section presents each lever in isolation, holding the others at the published S1 cell, and states for each of them whether the trajectory is read directly from the report or fitted to a digitised curve, following the same provenance distinction adopted in the validation notebooks.</span>{raw:typst}`]`




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

if scenarios:
    fig, axes = plt.subplots(1, len(scenarios), figsize=(15.6, 4.2), sharey=True,
                             layout="constrained")
    for ax, (name, view) in zip(np.atleast_1d(axes), scenarios.items()):
        vectors = view.data["vector_outputs"]
        years = np.arange(2000, 2000 + len(vectors["energy_consumption_dropin_fuel"]))
        stack, labels = [], []
        for pathway in BIOMASS_PATHWAYS:
            column = f"{pathway}_energy_consumption"
            if column not in vectors:
                continue
            series = np.nan_to_num(np.asarray(vectors[column], dtype=float)) * 1e-12
            if series.sum() > 0:
                stack.append(series)
                labels.append(pathway.replace("_", " "))
        if stack:
            ax.stackplot(years, *stack, labels=labels)
            ax.legend(fontsize=6, loc="upper left")
        ax.set_xlim(2020, years[-1])
        ax.set_title(name)
        ax.set_xlabel("Year")
        ax.grid(alpha=0.3)
    np.atleast_1d(axes)[0].set_ylabel("Biomass SAF energy [EJ]")
    save_fig(fig, name="biofuel_mix")
```

*The biomass SAF mix by pathway, as deployed in each scenario, one panel each on a shared vertical axis. Each band is one production pathway; their relative shares set the fleet-average carbon intensity behind the SAF wedge of the first three figures, and the pathways differ by roughly a factor of eight in life-cycle emissions, so the mix matters as much as the volume. The light edition collapses all seven biomass pathways into one generic carrier, which is why its panel carries a single band.*

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">SAF is presented as the biofuel mix reached under each of F1, F2 and F3, that is, the single generic carrier of S0 against the per-pathway breakdown of S1 and S2, the resolution difference already noted above. This is the lever most revised by the reports between editions, and the one varied most widely by the sweep presented here, consistently with it carrying the largest share of the abatement wedge shown in the levers-of-action figure above.</span>{raw:typst}`]`


{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Offsets constitute the residual rather than an independent assumption, being computed as whatever volume closes the gap between the combined effect of the other four levers and the stated target of the scenario. Their trajectory is therefore a direct readout of how much the other levers under-deliver relative to the goal, which corresponds to the accounting property discussed below.</span>{raw:typst}`]`

### Demand-side impacts of transition costs

The reports hold traffic exogenous and say so explicitly, citing Destination 2050
{cite:p}`destination2050_2021` (about −16 % demand by 2050) and a national roadmap (−14 % in 2050),
before placing the question out of scope. Omitting a feedback because it is hard to estimate assigns
it the value zero, which is the one value certain to be wrong {cite:p}`sterman_business_2009`. The point bites
here because the instruments delivering the abatement are the same instruments raising the cost of
flying: each lever is scored against a traffic volume it helps prevent.

$$
\text{carbon tax} \rightarrow \text{energy DOC per ASK} \rightarrow \text{net DOC per RPK}
\rightarrow \text{price lag} \rightarrow \text{price index} \rightarrow \text{RPK}
$$

```{important}
**The reports leave the mandate ambiguous, and it matters.** *Waypoint 2050* reports SAF as a 2050
*volume*, and never says what would happen to that volume if traffic grew more slowly. Two readings
are defensible, and once demand responds to price they diverge:

- **fixed volume**: the mandated SAF quantity is unchanged when demand falls, so the blend share
  rises on its own, by more the harder demand is hit;
- **fixed share**: the blend percentage is held and SAF volume falls with demand. This is how real
  mandates (ReFuelEU Aviation, the UK and Brazilian schemes) are actually written.

Both are run, in `ssp_comparison.ipynb` and `ssp_comparison_share.ipynb` respectively.
```

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

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Demand falls by 1 to 15 % by 2050, and by more the harder carbon is priced: −1.0 % under SSP2-4.5, −4.6 % under SSP2-2.6 and −15.0 % under SSP2-1.9. The range brackets those quoted by the reports themselves before the question is set aside, Destination 2050 reporting about −16 % and a national roadmap −14 %, which those two figures approach only under the carbon price consistent with the Paris Agreement. The response scales with the extent to which the transition raises the cost of flying, and correcting the electrofuel double-count lowered that cost substantially, since the same coupling run against the uncorrected fuel price gave 11 to 20 %, in apparent agreement with the cited studies for the wrong reason. What survives is therefore the direction and the ordering rather than a match in magnitude, the elasticity having in any case been calibrated jointly with a price reference that has since been re-anchored.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The two mandate readings cross over, which constitutes the main result of this comparison. Under a strong carbon price the fixed volume covers a larger share of a reduced demand and leaves *less* residual CO₂ than a fixed share, namely 372.0 against 406.1 Mt under SSP2-1.9, an advantage of 34.1 Mt. Under weak carbon prices the ordering reverses, and by considerably more, with 643.6 against 475.7 Mt under SSP2-2.6 and 797.0 against 500.4 Mt under SSP2-4.5, a penalty of 296.6 Mt. A fixed volume constitutes a constraint of absolute size, so that it tightens automatically as demand falls and slackens as demand grows, whereas a fixed share does neither. Which of the two readings applies therefore determines whether a mandate becomes more or less demanding exactly when the carbon price moves, and the reports do not state which one they intend.</span>{raw:typst}`]`


Traffic, cost and CO2 for S1's three carbon-tax pathways, **restricted to the fixed-share
reading**, which is how real mandates are written and the only reading that stays well posed when
demand responds to price, against its own fuel counterfactual with every drop-in SAF mandate
zeroed. Each family is shown as an envelope across its three pathways rather than as separate
lines, since what matters here is the width the carbon price opens up within each family, not
which SSP sits where; SAF is drawn dark green, no SAF dark red, so the two are told apart by
colour before the legend is read.

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

# The reports' own traffic forecasts, drawn on the traffic panel as the exogenous
# reference the coupling departs from. They are the same three variants the sweep
# uses, and they carry no demand response at all.
EXOGENOUS_TRAFFIC = {
    "ATAG low": "3rd_edition_full/data_outputs/s1-traffic-low.json",
    "ATAG central": "3rd_edition_full/data_outputs/s1.json",
    "ATAG high": "3rd_edition_full/data_outputs/s1-traffic-high.json",
}
EXOGENOUS_STYLE = {"ATAG low": ":", "ATAG central": "-", "ATAG high": "--"}

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
DEMAND_GROUP_LINEWIDTH = {"SAF (fixed share)": 1.5, "No SAF": 0.9}

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
            ax.set_xlim(2000, 2050)

    # The exogenous references are drawn thinner than the coupled pathways, so
    # that the reference reads as background and the result as foreground. This
    # is done by keeping them thin rather than by thickening the coupled lines
    # in this panel alone, which would have given a group two different widths
    # depending on which panel it was read in.
    for label, path in EXOGENOUS_TRAFFIC.items():
        exogenous = load_results(HERE / path, name=label)
        series = np.asarray(exogenous.data["vector_outputs"]["rpk"], dtype=float) * 1e-12
        years = np.arange(2000, 2000 + len(series))
        all_axes[1][0].plot(years, series, color="black", linewidth=1.0,
                            linestyle=EXOGENOUS_STYLE[label], label=label, zorder=5)

    all_axes[0][0].legend(fontsize=8)
    all_axes[1][0].legend(fontsize=7, loc="upper left")
    save_fig(fig, name="coupled_demand_share")
```

*The coupled runs, drawn as two bands across the same three SSP pathways: dark green under the
**fixed-share SAF mandate**, dark red under its **no-SAF counterfactual**, everything else held
identical. The top row is the background the scenarios are given, and the bottom row is what
follows from it. Population is identical across the three and across both families, and GDP per
capita nearly so, since SSP2 is a single socioeconomic pathway and neither family touches the
background; the two bands collapse onto one line there, leaving the carbon price, which spans a
factor of 24 at 2050, as the only driver separating the six pathways below. The traffic panel also
carries the reports' own three exogenous forecasts as thin black lines, which carry no demand
response at all. Line weight ranks the three: the SAF mandate heaviest, the exogenous
forecasts next, and the no-SAF counterfactual lightest, each keeping its weight in every
panel so a family reads the same wherever it is met. The gap
between the two bands is what the SAF mandate's own cost does to traffic, and it grows with the
carbon price precisely because fossil kerosene is both the cheapest and the dirtiest pathway
available: at 2050, removing SAF turns a 15.0 % demand reduction into a 35.6 % one under SSP2-1.9,
a 4.6 % reduction into an 8.0 % one under SSP2-2.6, and a 1.0 % reduction into a 13.8 % *increase*
under SSP2-4.5, where the carbon price is too weak to offset cheaper, dirtier fuel. Residual CO₂
follows the same split: 406 against 1,392 Mt under SSP2-1.9, 476 against 1,997 Mt under SSP2-2.6,
and 500 against 2,458 Mt under SSP2-4.5. All six panels carry the observed period as well as the
projection.*

The panel above gives the total cost per revenue passenger-kilometre. What it does not show is
what that total is made of, and the split matters: a carbon price and a fuel-price premium reach the
traveller through the same channel but respond to different policy. The committed outputs carry both
components separately, so the breakdown is read from them directly, starting with the property that
belongs to the fuel rather than to any one scenario.

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
COUPLED_INPUTS = HERE / "3rd_edition_full_coupled_demand" / "data_inputs"
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

    # Both panels resolve the same pathways, so one legend serves them; placing it
    # outside to the right stops it covering the curves it names.
    handles, labels = price_axes[1].get_legend_handles_labels()
    price_axes[1].legend(handles, labels, loc="center left", bbox_to_anchor=(1.02, 0.5),
                         frameon=False, fontsize=8)
    save_fig(fig, name="fuel_price_intensity")
```

*What a megajoule of each production pathway costs to produce, excluding the carbon tax, and what
emitting it releases; pathways the scenario does not deploy are drawn dotted and labelled as
unused. Fossil kerosene is the cheapest and the dirtiest of them, at 88.7 gCO2/MJ in 2050 against
5.2 to 48.8 for the alternative pathways, a spread of roughly a factor of nine among the
alternatives themselves, and the mandate is what displaces it. Only one scenario is shown, because
under a fixed-share mandate the blend follows the mandate rather than the carbon price, so all
three deliver identical fuel at identical cost, 0.0231 EUR/MJ and 20.459 gCO2/MJ in 2050,
bit-identical across the three. Neither panel depends on the no-SAF counterfactual either, since
removing the mandate changes how much of each pathway is burned, not what a megajoule of it costs
or emits.*

What the fuel itself costs is only half the story: the other half is the mandate that decides how
much of the expensive pathway a scenario is forced to burn, against the counterfactual of burning
none of it at all.

```{code-cell} python
:tags: [hide-input]

# No-SAF on top, S1's SAF blend below, one column per pathway ordered weakest to
# strongest carbon price. Both rows are the same plot on different views, so the
# only thing that changes down a column is which mandate applied, and the only
# thing that changes across a row is the carbon price.
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
                                 legend=col == 0)
        share_only[pathway].plot("doc_net_energy_per_rpk_breakdown", fig=fig, ax=axes[1, col],
                                 legend=col == 0)
        axes[0, col].set_title(f"{with_warming(pathway)} -- no SAF")
        axes[1, col].set_title(f"{with_warming(pathway)} -- SAF (fixed share)")
        for ax in (axes[0, col], axes[1, col]):
            ax.set_xlim(2020, 2050)
    for ax in axes[:, 1:].ravel():
        ax.set_ylabel("")
    save_fig(fig, name="doc_breakdown")
```

*The resulting energy direct operating cost per revenue passenger-kilometre, resolved into
production pathways, one column per SSP pathway ordered from the weakest carbon price to the
strongest, all six panels sharing one vertical axis so the rows are comparable as drawn. The top row is the no-SAF counterfactual, fossil kerosene alone; the bottom row is S1's
fixed-share SAF blend. Within a row the fuel is identical across columns, so what separates the
three panels is carbon tax alone; within a column the fuel differs instead, so what separates the
two rows is the SAF mandate's own price premium against the tax fossil kerosene alone would carry.
That premium changes sign with the carbon price, mirroring the fixed-volume/fixed-share crossover
above. Under the weak carbon price of SSP2-4.5, SAF costs more than doing nothing: 0.0187 EUR/RPK
against a no-SAF 0.0123, a premium of 0.0064. Under SSP2-2.6 the ordering has already reversed, SAF
costing less at 0.0214 against 0.0240, and by SSP2-1.9 the reversal is large, SAF at 0.0345 against
a no-SAF 0.0808, a saving of 0.0463 EUR/RPK: taxing fossil kerosene outright costs more than
switching away from it. Stacked by carrier with the cost components distinguished by hatch and the
total drawn in black over a dashed line for the delayed cost travellers actually perceive.*

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The demand response operates through the cost side of the same loop. Energy expenses rise steeply as the SAF mandate ramps, since the mandated fuel is several times costlier per unit energy than the kerosene it displaces, and that increase reaches the traveller through direct operating cost. This is the mechanism left unmodelled by the reports, and it does not constitute a second-order correction, a demand reduction of 1 to 15 % by 2050 being comparable in magnitude to what the technology and operations levers are together assumed to deliver. Removing SAF entirely, rather than merely leaving its cost unmodelled, shows how much of that mechanism the mandate itself is responsible for: the SAF-versus-no-SAF comparison above is the sharper counterfactual, isolating what the mandate's own cost does to traffic from everything the exogenous forecast already leaves out.</span>{raw:typst}`]`

### Temperature impacts and contrail avoidance strategies

```{code-cell} python
:tags: [hide-input]

T_TOTAL = "temperature_increase_from_aviation"
T_CONTRAILS = "temperature_increase_from_contrails_from_aviation"

band_csv = HERE / "climate_analysis" / "baseline_uncertainty_results.csv.gz"
bands_tidy = pd.read_csv(band_csv)
band_scenarios = list(bands_tidy["scenario"].unique())

fig, axes = plt.subplots(3, len(band_scenarios), figsize=(15.6, 10.4), sharex=True,
                         layout="constrained")
for column, scenario in enumerate(band_scenarios):
    subset = bands_tidy[bands_tidy["scenario"] == scenario]

    def band(key, column_name):
        rows = subset[subset["band_key"] == key]
        return rows.set_index("year")[column_name]

    # rows 1 and 2: the same envelope, on contrails then on the total
    for row, (metric, title) in enumerate(
        ((T_CONTRAILS, "Contrail warming"), (T_TOTAL, "Total warming from aviation"))
    ):
        ax = axes[row, column]
        low, central, high = (band(k, metric) for k in ("low", "central", "high"))
        ax.fill_between(low.index, 1000 * low, 1000 * high, alpha=0.25, color="#4C72B0")
        ax.plot(central.index, 1000 * central, color="#4C72B0", linewidth=2)
        ax.set_title(f"{scenario} - {title}" if row == 0 else title, fontsize=9)
        ax.grid(alpha=0.3)
        if column == 0:
            ax.set_ylabel("Warming [mK]")

    # row 3: what the central case is made of, stacked by mechanism
    ax = axes[2, column]
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

# One scale across all nine panels. The bottom is left free rather than pinned
# at zero, because the mechanism decomposition carries genuinely negative terms
# and clipping them would misreport the stack.
flat_axes = [ax for row in axes for ax in row]
low = min(ax.get_ylim()[0] for ax in flat_axes)
high = max(ax.get_ylim()[1] for ax in flat_axes)
for ax in flat_axes:
    ax.set_ylim(low, high)
save_fig(fig, name="climate_bands_and_decomposition")
```

*Three readings of the same three scenarios, one column each. The top row is contrail warming with
its uncertainty band, the middle row the total warming from aviation with the same band, and the
bottom row what the central case is made of, stacked by forcing mechanism. The band combines the
two independent non-CO2 uncertainties, how strongly contrails warm and how much cleaner fuel
reduces that warming, so its width is what a single scenario carries. Two things read directly off
the figure: the band on any one scenario is wider than the distance between the three columns, and
the stack shows CO2 to be the minority of the total in 2050 in every scenario, with contrail
cirrus the largest single term.*

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Decarbonisation does not act on non-CO₂ effects in proportion to its action on CO₂, and the two diverge sharply by 2050. Every reproduced scenario drives CO₂ emissions steeply down, yet the warming each of them still causes remains dominated by non-CO₂ terms, principally contrail cirrus. A CO₂ target and a temperature target are therefore not interchangeable statements regarding the same trajectory, since a scenario can approach net-zero CO₂ while the majority of its contribution to warming remains untouched by the levers that brought it there.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">A partial coupling nevertheless exists, and it operates through soot. Cleaner fuels emit fewer non-volatile particles, which seeds fewer and larger ice crystals and reduces contrail forcing, an effect represented in the model as a scaling of contrail forcing with the square root of the particle number emission index, weighted by the mass share of each pathway. However, the magnitude of that benefit remains genuinely open. For fleet-wide SAF adoption, the modelling literature surveyed by Teoh et al. {cite:p}`teoh2022` spans a 15 % reduction in contrail net radiative forcing at one end and 50 % at the other, with their own estimate at 44 %, and one regional study reporting a possible *increase*.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">That uncertainty compounds with a larger one, concerning how much contrails warm at all. Lee et al. {cite:p}`lee_contribution_2021` give a contrail radiative forcing for 2018 with a 95 % interval spanning roughly a factor of six, whereas Teoh et al. {cite:p}`teoh2024`, simulating actual trajectories rather than extrapolating, obtain a 2019 central value 44 % below that estimate, with a sensitivity analysis spanning 34.8 to 74.8 mW m⁻². Both uncertainties bear directly on scenario results, so that `climate_analysis/baseline_uncertainty.ipynb` propagates them jointly, as three bands named by climate impact: the high band pairs the largest contrail sensitivity with the weakest fuel benefit, the low band the reverse, and the central band reproduces the published scenarios exactly.</span>{raw:typst}`]`


{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The result reframes the comparison between the scenarios. In 2050 the central estimates of total warming from aviation amount to 105, 89 and 84 mK for S0, S1 and S2, a spread of 21 mK between the most and the least ambitious published scenario. The uncertainty band carried by any *single* one of them amounts to about 70 mK, roughly 3.2 times wider. Decomposing that band, the contrail sensitivity contributes about 54 mK and the SAF benefit about 15 mK, so that the dominant term is how strongly contrails warm rather than how much cleaner fuel helps. Choosing between the published scenarios therefore constitutes, on current knowledge, a smaller question than the uncertainty carried by whichever one is chosen, which is an argument for reporting bands rather than points, and not for delaying action.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Contrail mitigation is absent from all three editions, every scenario being run with the contrail lever switched off, in accordance with the stated scope of the reports, the third edition being explicit that contrail quantification carries low confidence. Since contrails nevertheless constitute the largest single warming term in 2050 in every reproduced scenario, the omission is worth quantifying rather than inheriting. `climate_analysis/climate_analysis.ipynb` runs three strategy families parameterised on Teoh et al. {cite:p}`teoh_mitigating_2020`: low-risk diversion, small-scale diversion of about 1.7 % of flights, and combustor technology reducing black carbon emissions, each across the same three bands.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Three findings survive the checks carried in that notebook. First, **diversion buys contrail reduction by burning more fuel**, and under a fixed-quantity SAF mandate the marginal fuel is fossil kerosene, so that CO₂ rises by proportionally more than energy does. Second, **timing prevails over ultimate effectiveness on a 2050 horizon**, combustor technology being the stronger measure while depending on fleet renewal and starting five years later, which suffices to reverse the ranking against small-scale diversion by 2050. Third, **the value of avoidance scales with the uncertainty**, since the high band starts from considerably more contrail warming, so that the same strategies avoid several times more absolute warming there than in the low band. Avoidance is therefore worth most precisely in the cases where contrails turn out to be worst, which is an argument for treating it as insurance rather than as a central-estimate investment.</span>{raw:typst}`]`

```{code-cell} python
:tags: [hide-input]

LEVEL_STYLE = {"Low": ":", "Central": "-", "High": "--"}

variants = pd.read_csv(HERE / "climate_analysis" / "contrail_variants_results.csv.gz")
mitigating = [f for f in variants["family"].unique() if f != "No mitigation"]


def no_mitigation(level, column):
    """The no-mitigation run at one band: the like-for-like reference for that level."""
    rows = variants[(variants["family"] == "No mitigation") & (variants["level"] == level)]
    return rows.set_index("year")[column]


fig, axes = plt.subplots(2, len(mitigating), figsize=(15.6, 8.4), sharex=True,
                         layout="constrained")
for column, family in enumerate(mitigating):
    top, bottom = axes[0, column], axes[1, column]
    for level in ("Low", "Central", "High"):
        rows = variants[(variants["family"] == family) & (variants["level"] == level)]

        total = rows.set_index("year")[T_TOTAL]
        top.plot(total.index, 1000 * total, color="#4C72B0", linestyle=LEVEL_STYLE[level],
                 label=f"{level} band")
        reference_total = no_mitigation(level, T_TOTAL)
        top.plot(reference_total.index, 1000 * reference_total, color="0.6",
                 linestyle=LEVEL_STYLE[level], linewidth=1)

        # Share of the contrail warming that would otherwise have occurred, so the
        # bands are comparable where the absolute figure is not.
        contrails = rows.set_index("year")[T_CONTRAILS]
        reference = no_mitigation(level, T_CONTRAILS)
        with np.errstate(invalid="ignore", divide="ignore"):
            share = 100 * (reference - contrails) / reference.where(reference.abs() > 1e-12)
        bottom.plot(share.index, share, color="#C44E52", linestyle=LEVEL_STYLE[level],
                    label=f"{level} band")

    top.set_title(family, fontsize=9)
    top.grid(alpha=0.3)
    bottom.set_xlabel("Year")
    bottom.grid(alpha=0.3)
    bottom.set_xlim(2024, 2050)
axes[0, 0].set_ylabel("Total warming from aviation [mK]")
axes[0, 0].legend(fontsize=8)
axes[1, 0].set_ylabel("Contrail warming avoided [%]")

# Each row on its own common scale, so the families are comparable across the
# row; the share row starts at zero, since a share below it has no meaning here.
for row, bottom in ((0, 0.0), (1, 0.0)):
    top = max(axes[row, column].get_ylim()[1] for column in range(len(mitigating)))
    for column in range(len(mitigating)):
        axes[row, column].set_ylim(bottom, top)
save_fig(fig, name="contrail_strategies")
```

*Each contrail-mitigation family in a column, read two ways. The top row is total warming from
aviation under the strategy, in blue, against the no-mitigation run at the same non-CO2 band, in
grey; the bottom row is the share of contrail warming the strategy removes, as a percentage of the
contrail warming that would otherwise have occurred at that band. Line style encodes the band:
dotted Low, solid Central, dashed High. Pairing each variant with a reference at its own band
matters, since otherwise the band's own reduction in forcing would read as something the
mitigation achieved. Taking the bottom row as a share rather than in millikelvin is what makes the
three bands comparable, and it is where the timing result shows: the combustor family depends on
fleet renewal and starts five years later, so it crosses the diversion families only after 2050.*


{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">For external comparison, the ICCT's *Aviation Vision 2050* {cite:p}`icct_vision_2022` reports added aviation warming over 2025–2050 in the same units. Its historical-trends case adds 60 mK, whereas the S0 reference reproduced here adds 55 mK centrally, S1 and S2 being lower at 39 and 34 mK, as their mitigation would imply. The scenario definitions and the climate models differ, so that this constitutes an indicative check rather than a validation, but the reproduction falls within the same range.</span>{raw:typst}`]`

Offsets deserve a separate note. They carry a growing share of the residual abatement in the
reports' accounting, but they act outside the sector's physical emissions: swapping the entire
offset treatment moves the modelled temperature trajectory by *exactly* zero. That is asserted, not
asserted-in-passing, in the climate notebook.

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">A fourth critique belongs with the three above, and it is the one this reproduction is best placed to quantify, namely that the scenarios do not model non-CO₂ effects at all. The third edition states its position plainly:</span>{raw:typst}`]`

> Significant research to improve scientific understanding as well as understanding of the potential
> mitigation options (operations, technologies, fuels) is currently ongoing.

> The current priority for industry and government climate action should continue to be CO2
> emissions reduction.

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The first sentence is correct, whereas the second does not follow from it. Uncertainty regarding a warming term is an argument for continued research and for reporting bands rather than points, and not for assigning that term the value zero, which is the effect of leaving it out of a scenario. Furthermore, the uncertainty is not symmetric in its consequences, the reproduction presented here finding that contrail avoidance is worth several times more warming avoided in the high band than in the low one, so that the case for acting on contrails is strongest precisely in the cases where the science turns out worst. Nor is the sign of the benefit in doubt, only its magnitude. The ICCT reach the same conclusion from a different direction {cite:p}`icct_vision_2022`, attributing the majority of avoidable warming to short-lived effects and placing contrail mitigation ahead of fuel substitution on that basis, on the grounds that avoidance and hydrotreating are relatively mature whereas e-fuels are not, and that CO₂ already emitted remains for centuries.</span>{raw:typst}`]`

## Discussion

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The Paris Agreement sets a global temperature goal rather than a sectoral one, and translating it into an expectation for aviation requires a choice that no amount of modelling can make. Reproducing the scenarios renders the size of that choice explicit, since a sector reaching net-zero CO₂ by 2050 while its non-CO₂ warming continues largely unabated is not thereby consistent with any particular temperature outcome. The framing adopted by the ICCT, namely aviation's share of the remaining carbon budget, is more demanding than a net-zero CO₂ target and produces a different ranking of levers, placing contrail avoidance ahead of fuel substitution in terms of near-term warming avoided per unit cost.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Between the first and the third editions the goal was raised from a 50 % cut to net zero, the scenario set was reduced, and lever contributions were substantially reallocated, while the physical content moved little and, where it moved, moved downwards. The removal of the aspirational-technology scenario constitutes an unusually explicit correction of technological optimism, but its accounting counterpart is less visible, since the abatement previously assigned to unconventional propulsion was not deleted but reassigned to SAF and to market-based measures. Optimism was therefore relocated rather than reduced, and relocated towards levers whose limits are less legible to an aeronautical audience than those of an airframe.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The baseline against which reductions are measured moves between editions as well. A roadmap redrawing its own frozen-technology baseline while keeping the same terminal target will report changing lever contributions even when nothing physical has changed, so that percentage contributions quoted across editions are not directly comparable. This does not constitute a criticism unique to these reports, but rather a generic hazard of scenario accounting, which only becomes visible once the scenarios are rebuilt from their inputs.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The avoided-emissions framing deserves particular scrutiny, since the demand coupling quantifies its central weakness. When each lever is credited against a counterfactual traffic volume that the levers themselves would have suppressed, the credited abatement is inflated, the fuel that a carbon price prevents from being burned being counted as abated by the SAF that was never required to replace it. Closing the loop moves 2050 traffic down by 1 to 15 %, which is of the same order as the technology and operations levers combined, so that the double-count does not constitute a rounding error.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">A second and sharper form of the same fallacy is built into the wedge chart itself. A decomposition of this kind does not measure what each lever contributed, but rather what each lever contributed *given an order*, the order being chosen by whoever draws the chart. The levers overlap, since SAF and a battery-electric fleet decarbonise the same joule, so that whichever of them is peeled off first is credited with it while the other is credited with what remains. Measured on S2 at 2050, where the energy term amounts to 1,475 MtCO₂, taking SAF first gives SAF 1,469 Mt and alternative aircraft 6 Mt, taking alternative aircraft first gives 1,257 and 218 Mt, and a Shapley value, that is, the symmetric attribution averaging over orders, gives 1,363 and 112 Mt. The fleet is identical in all three cases, nothing physical distinguishing them. The alternative-aircraft pillar therefore moves by a factor of 35 on the strength of a presentational choice, whereas the same fleet change in the T4 technology scenario, where no SAF competes for the credit, amounts to 247 Mt.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The lever table makes the same point without needing a counterfactual reordering, since it runs each lever both on its own and inside a published scenario. The operations lever, set to the reports' own 6 % cumulative gain and 88.389 % load factor, removes 275.6 Mt acting on the T1 fleet and 242.6 Mt acting inside S1 or S2, some 12 % less, because a more efficient fleet leaves less fuel for a fuller aircraft to save. The next generation pillar shows the converse: the battery-electric fleet is worth 247.0 Mt in T4 alone and 218.1 Mt inside S2, where SAF has already lowered the carbon intensity of the joules it displaces. Neither number is an error, and the mechanism behind them is exact rather than approximate, since each lever removes a fixed proportion of whatever remains when it is applied: operations takes 11.6703 % of the post-technology baseline in the standalone run and in both published scenarios alike, identical to six decimal places. Only the quantity it is applied to differs, and that quantity is fixed by the levers ordered before it.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The fuel rows isolate what makes a lever behave this way, and it is not the technology. F2 and F3 reproduce the SAF wedges of S1 and S2 exactly, 1,412.9 and 1,257.2 Mt against 1,412.9 and 1,257.1, despite standing on a less efficient fleet carrying no operations improvement, because the third edition states those fuel volumes in absolute terms and a fixed volume of displaced fossil kerosene does not depend on how much fuel is burned in total. F1 does depend on it, falling from 194.9 Mt alone to 163.4 Mt inside S0, because the first edition states its fuel level as a blending share instead. Whether a lever's contribution is context-dependent is therefore a property of how the commitment is drafted rather than of what it deploys, which is the same distinction that separates the fixed-volume and fixed-share readings of the SAF mandate above, and it is the drafting rather than the technology that determines whether a quoted contribution survives being moved into a different scenario.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">This does not mean that the decomposition is worthless, but rather that its total and its split have different status. The total is determinate, since whatever the order the wedges sum to the same distance between the frozen-fleet baseline and the realised trajectory, and that distance constitutes a physical statement. What is indeterminate is the split, and therefore any single quoted percentage. The figures presented in this document take alternative aircraft before SAF, since the chart stacks them in the technology pillar above the fuel pillar and an attribution contradicting its own drawing order would be indefensible, the choice being stated in `atag_decomposition.py` rather than left to be inferred. The headline lever contributions of the reports themselves are produced by exactly this construction and inherit exactly this indeterminacy, which is worth keeping in view whenever a single value is quoted as the share of abatement delivered by one lever.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Finally, the reproduction inherits limits from its sources, and should be read accordingly. First, digitisation error is bounded without being eliminated. Second, calibrated parameters demonstrate consistency rather than identifiability, since different technology and fleet combinations produce identical emissions paths. Third, agreement between two models does not constitute validation against reality. What the exercise establishes is narrower and nevertheless useful, namely that the published trajectories are reproducible from stated assumptions, and that the assumptions which are *not* stated can be bounded.</span>{raw:typst}`]`

## Conclusion

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Institutional scenarios increasingly function as inputs to regulation, and their influence has outgrown the transparency with which they are published. The three editions of *Waypoint 2050* are detailed and internally coherent, but their data provenance, calibration and formulation cannot be inspected, so that a reader cannot distinguish a revision driven by evidence from one driven by accounting. Reproducing them in an open framework, with every input traceable to a stated origin, constitutes the minimum condition for the scrutiny that decisions of this consequence warrant. Open models and open data do not constitute an academic preference in this context, but rather the condition under which disagreement becomes productive.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The sequential structure shared by these exercises constitutes a limitation rather than merely a convention. Calibrating on the past, projecting drivers, applying levers and stopping leaves out precisely the couplings that determine whether a scenario is self-consistent, most obviously the fact that the instruments delivering abatement also modify the demand being abated. Treating the problem as a multidisciplinary analysis, in which such loops are resolved to a fixed point, changes the answer by a margin comparable to whole mitigation levers, and is computationally cheap enough that no practical reason remains to avoid it.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Most importantly, scenarios reporting single trajectories misrepresent the state of knowledge they summarise. The non-CO₂ uncertainty band surrounding any one scenario reproduced here is several times wider than the difference between the published scenarios, and that uncertainty is irreducible on policy-relevant timescales. Reporting bands rather than points does not weaken the case for action, but rather relocates it, from choosing the right trajectory to choosing measures that perform acceptably across the range, which is an argument for near-term, reversible and high-leverage measures such as contrail avoidance, whose value is greatest in exactly those futures where the uncertainty resolves badly.</span>{raw:typst}`]`

## Reproducibility

Every result maps to a notebook, and every notebook writes its outputs to a committed
`data_outputs/` file that this document reads.

| Result | Produced by |
|---|---|
| Reproduced S0 | `3rd_edition_light/s0.ipynb` |
| Reproduced S1, S2 | `3rd_edition_full/s1.ipynb`, `s2.ipynb` |
| Technology calibration | `3rd_edition_full/validation.ipynb` |
| Full 108-cell lever sweep | `3rd_edition_variants/sweep.ipynb` |
| Demand–price coupling, fixed SAF volume | `3rd_edition_full_coupled_demand/ssp_comparison.ipynb` |
| Demand–price coupling, fixed SAF share | `3rd_edition_full_coupled_demand/ssp_comparison_share.ipynb` |
| Climate, editions, contrail avoidance | `climate_analysis/climate_analysis.ipynb` |
| Non-CO₂ uncertainty on the baseline scenarios | `climate_analysis/baseline_uncertainty.ipynb` |

Scenario configurations live in each edition's `config_files/`, inputs in `data_inputs/`, and the
shared traffic definitions in `markets/`. The environment is pinned by the repository's
`poetry.lock`.

```{note}
The figures on this page are produced by code cells that read the committed `data_outputs/` files.
No model is run while the page builds. If an output file is missing, the cell prints
`PENDING: run <notebook>` instead of failing, so a missing figure reads as missing data rather than
a broken build.
```
