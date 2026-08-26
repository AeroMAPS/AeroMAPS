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
 {raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The three published scenarios reproduce to 
well-to-wake residuals of about 1,820, 420 and 360 MtCO₂ in 2050, and to 1,510, 350 and 260 Mt on the tank-to-wake 
basis the reports headline. Sweeping the full lever grid places those three points inside a range spanning 208 to 
2,164 Mt, so the published scenarios are a sparse sample of their own design space rather than its bounds. Closing the 
demand–price loop the reports leave open reduces 2050 traffic by 2 to 12 % depending on the carbon price, less than the
14 to 16 % the reports themselves quote from other studies before setting the question aside. Extending the climate 
accounting shows the sharper result: the non-CO₂ uncertainty band on a single scenario is about 3.2 times wider than 
the entire spread between the published scenarios, so the choice between them is currently a smaller question than the 
uncertainty each carries.</span>{raw:typst}`]`
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

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Text in this colour was drafted by an AI assistant,
filling the `+` placeholders left in the manuscript. Every number in it is read from a committed scenario output and is 
reproducible from the notebook named alongside it; the prose around those numbers is a draft for the author to accept, 
rewrite or discard.</span>{raw:typst}`]`

Two mechanical notes. `lee_contribution_2021` is cited here as `lee2021`, the same paper under the
key this repository already uses. And the citations filling the author's inline `+cite` markers are
set in black rather than colour, because a colour span containing nothing but a citation does not
survive the PDF export; the references chosen at those four markers are
{cite:p}`eu_nonco2_mrv` for non-CO2 monitoring, {cite:p}`teoh2020,icao_corsia_2022` for contrail
avoidance crediting, {cite:p}`lee2021,teoh2024,icct_vision2050_2022` for the missing climate
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
than that of CO₂ {cite:p}`lee2021`. Furthermore, while mitigation levers that tackle CO₂ may also
reduce non-CO₂ to some extent, this is still subject to ongoing research.

Achieving the Paris Agreement targets requires deep, rapid, and sustained emissions reductions
across all economic sectors. Aviation is considered a hard-to-abate sector whose mitigation relies
on a few levers with opposing effects on the cost of flying {cite:p}`delbecq_sustainable_2023`:
Sustainable Aviation Fuels (SAF) and carbon pricing and Market-based measures (MBM) raise this cost,
while operational and vehicle efficiency are expected to lower the impact of increased fuel prices
to airlines and travelers. Besides its decarbonization policy, specific measures to tackle non-CO₂
are currently being formulated for monitoring these effects {cite:p}`eu_nonco2_mrv` and for allowing airlines to claim 
carbon allowances from contrail avoidance strategies {cite:p}`teoh2020,icao_corsia_2022`.

Among the numerous industrial, institutional, and academic scenarios have been made for aviation,
the Air Transport Action Group (ATAG) Waypoint 2050 stands as the industry vision of the transition
of the sector up until 2050. While the three different editions of the report
{cite:p}`atag2020_waypoint,atag2021_waypoint,atag2026_waypoint` are rich in detail and figures for
the future 25 years the methods and underlying assumptions are not always explicit nor reproducible.
In the context where national and international policies are derived from such, we argue for more
openness regarding: models, data, background assumptions, limitations, and uncertainties.
Furthermore, as highlighted by many academic works, these institutional scenarios also lack
accounting of the full climate impacts of aviation {cite:p}`lee2021,teoh2024,icct_vision2050_2022`, and for the feedback
of policy-induced price increases on traffic demand {cite:p}`gossling_humpe_2020,destination2050_2021`.

This work asks whether the ATAG third-edition scenarios can be reproduced transparently, lever by
lever, in the AeroMAPS {cite:p}`planes_aeromaps_2023` open-source framework.
Furthermore, extra capabilities of the framework are employed to demonstrate two points that lack in
all ATAG reports: analysis of demand-side impacts of transition costs, and quantification of
temperature impacts of scenarios with different strategies for contrail avoidance.

### ATAG Waypoint Reports

The first edition of the ATAG Waypoint 2050 report {cite:p}`atag2020_waypoint` was launched in
September 2020 during the COVID-19 crisis, when aviation experienced its greatest drop in traffic
levels seen in recent history. The report frames the pandemic as an opportunity for a "green
recovery" as the social function of air travel was put in question. By then, the official target was
to halve 2005 emission levels by 2050, and the sector's position as a hard to abate sector is
emphasized, mentioning that net zero could be achieved by 2060-2065. Four prospective scenarios are
presented:

- **S0: baseline/continuation of current trends** — Central range for traffic forecasts,
  conservative operational and technology improvements with a new generation of new aircraft to
  entry into service by 2030-2035, deployment of SAF based on current rates, and carbon offsets are
  used as the principal lever to align emissions to emission reduction goals;
- **S1: pushing technology and operations** — Ambitious operational and technological improvements
  with unconventional aircraft (hybrid-electric) to entry into service by 2035-2040, deployment of
  SAF is supposed to align scenario to industry goal by 2050, and offsets are used as a transition
  mechanism until 2050;
- **S2: aggressive sustainable fuel deployment** — Ambitious operational and technological
  improvements with disruptive aircraft configurations (blended wing body), but only using
  conventional propulsion based on jet-fuel, SAF deployment is accelerated and is supposed to align
  scenario to goals by 2035, offsets are used as a transition mechanism until 2035;
- **S3: aspirational and aggressive technology perspective** — Very ambitious technology
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

Besides this critique of the Waypoint scenarios, two methodological critiques are also made
regarding the analysis carried by ATAG:

- **Exogenous demand:** {raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">traffic is exogenous in all three editions. Demand follows central industry forecasts unaffected by transition costs, even though the same reports assume an energy carrier several times costlier than kerosene and a carbon price rising to hundreds of dollars per tonne. Each lever is therefore scored against a traffic volume it would itself help suppress, which overstates the abatement the levers must deliver. The reports quote demand responses of about 16 % and 14 % from other studies before placing the question out of scope; closing the loop here gives 2 to 12 % by 2050, smaller than those figures but the same order as the technology and operations levers combined.</span>{raw:typst}`]`
- **Climate impacts:** {raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">the scenarios account for CO2 alone. Non-CO2 effects, which carry the majority of aviation's historical forcing and are dominated by contrail cirrus, are absent from every scenario, and contrail mitigation is absent from the lever set. The third edition states that the priority should remain CO2 because the science is still developing, but uncertainty about a warming term is an argument for reporting a range rather than for assigning it zero. Quantified here, the non-CO2 uncertainty band on a single scenario is about 3.2 times wider than the entire spread between the published scenarios.</span>{raw:typst}`]`


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

sys.path.insert(0, str(HERE))
from atag_decomposition import plot_atag_decomposition  # noqa: E402

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
unchanged. Different exercises of the same method differ only on which novel data and insights are
accounted for, but they do not inform on the goodness of the exercise itself.

Methodologically, this paper employs the similar sequential approach for reproducing ATAG Waypoint
scenarios with the AeroMAPS framework, as well as for calibrating model parameters which are omitted
by the reports. Furthermore, the framework is employed to demonstrate how to break out of the
sequential approach by removing one key assumption kept by all three editions: that traffic growth
won't be affected by rising transition costs. "Omitting key variables simply because data are
lacking is effectively equivalent to assigning them a value of zero, arguably the only value that is
certain to be incorrect" {cite:p}`sterman2000`.

### AeroMAPS

Employing open-source tools to simulate policy scenarios can be highly beneficial for making
modelling assumptions explicit, improving the reproducibility of policy objectives, and supporting a
common ground for high-level decision-making. In this context, the present work uses AeroMAPS
{cite:p}`planes_aeromaps_2023`, an open-source sectoral integrated assessment framework for air transport designed to
represent prospective aviation scenarios and their environmental impacts across multiple
disciplinary fields.

AeroMAPS is organised as a graph of small declarative modules that are solved together based on the
GEMSEO library {cite:p}`gemseo`: modules explicitly define their inputs and outputs through
variable names, allowing the solver to automatically handle model integration, execution sequence,
numerical couplings and feedback loops (necessary features for the demand-price coupling showcased
later). The framework was developed to be relatively easy to use and widely distributable among
academic, institutional, and industrial stakeholders, while enabling sectoral environmental
sustainability assessments and the evaluation of transition strategies. Its modular architecture
also facilitates the integration of models from different disciplinary fields, furthermore it is
also responsible for allowing for dynamic model assemble, which means simulation can be tailored to
analysis of different scopes regarding:

- **Geographic coverage:** {raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">a scenario runs either as one global region or as several regions solved together, each carrying its own traffic, fleet and fuel policy, with an aggregation step that collapses a multi-regional run into the equivalent single-region process. Both are used here: the third-edition scenarios are global, while the S0 reference of the light edition is aggregated from a twenty-region run whose regional SAF mandates differ.</span>{raw:typst}`]`
- **Market segmentation:** {raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">markets are declared rather than hard-coded, each with its own traffic driver, energy intensity and, where the coupling is active, its own price elasticity. The reproduction uses four: short, medium and long range passenger traffic in revenue passenger-kilometres, and freight in revenue tonne-kilometres.</span>{raw:typst}`]`
- **Energy production pathways:** {raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">each carrier is resolved into named production pathways carrying their own cost, emission factor and upstream resource demand, so the fleet-average carbon intensity follows the mix and not a single assumed value. The full edition deploys seven biomass pathways, spanning roughly a factor of eight in life-cycle emissions, alongside electrofuel, fossil kerosene, liquid hydrogen and battery-electric aircraft; the light edition collapses the biomass pathways into one generic carrier, which is the resolution that edition publishes.</span>{raw:typst}`]`
- **Emission scopes:** {raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">the same scenario can be accounted tank-to-wake, as the reports headline, or well-to-wake, which is what a fuel-switching scenario has to be measured in if the upstream emissions of the replacement fuel are to appear anywhere. Every scenario here is run in both, as a pair of otherwise identical configurations. Beyond CO₂, the emissions modules carry the non-CO₂ species and feed a climate module returning effective radiative forcing and temperature.</span>{raw:typst}`]`
- **Cost analysis:** {raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">fuel production costs, aircraft direct operating costs, carbon prices and marginal abatement costs are all available, at a top-down resolution taking an aggregate cost per unit energy or a bottom-up one built from plant capital expenditure, operating costs and construction lead times. This reproduction uses the top-down formulation throughout, because that is the resolution at which the reports themselves publish, and the cost chain is what makes the demand response of the coupled scenarios computable at all.</span>{raw:typst}`]`

For more details on the software architecture, simulation workflow, and some model components
readers are referred to {cite:p}`planes_aeromaps_2023`. New developments have been carried since then to
keep up with and advance the state-of-the-art regarding modeling: energy economics
{cite:p}`salgas_techno-economic_2025,salgas_macc_2024`, fleet renewal, temperature impacts {cite:p}`arriolabengoa_climate_2024`, prospective life-cycle assessment {cite:p}`pollet_lca_2024`, and long-term behavioral impacts of policies on traffic demand {cite:p}`costa-alves_modeling_2026`.

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The scenario definition lives entirely in declarative files: a YAML configuration selecting the module chain and its data files, a JSON file of parameter trajectories, and YAML descriptions of energy carriers, processes and resources. No scenario in this paper required writing model code, which is what makes the lever-by-lever reproduction auditable: every number quoted below is traceable to a committed input file and a committed output file.</span>{raw:typst}`]`

### Validation

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Reproducing a scenario whose inputs are not 
published requires being explicit about where every number came from, because the provenance changes what agreement can
be claimed. Four classes are distinguished here, in decreasing order of confidence.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">**Read from the text.** Operational assumptions are
stated numerically in the reports and are used as given: the operations lever is defined as a cumulative efficiency gain
of 0.00, 0.10 and 0.20 % per year to 2050 for its three variants, entering the model directly as 
`operations_gain_reference_years_values`.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">**Digitised from published figures.** Traffic, load
factor and SAF deployment trajectories appear only as charts, and were digitised point by point. Digitisation error is 
bounded by the resolution of the published figures but is not eliminated, and it propagates into every downstream 
result.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">**Calibrated to match figures.** Annual fuel-burn 
efficiency gains and the deployment schedules for battery-electric and liquid-hydrogen aircraft are never disclosed as 
values. They were fitted so that each technology variant's emissions trajectory reproduces the digitised one while 
staying inside published literature ranges. Agreement here demonstrates *consistency*, not recovery of the report's 
actual assumptions: different technology–fleet combinations produce identical emissions paths, and no identifiability is
claimed.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">**AeroMAPS defaults.** Fleet renewal rates and the
aircraft-level performance model are the framework's own, because the reports disclose nothing that would constrain 
them.</span>{raw:typst}`]`

```{important}
**SAF resolution differs across the grid.** F2 and F3 are published as quantities *per pathway*, so
they map onto the eleven-carrier energy files. F1 publishes only a *total* volume with no pathway
breakdown, so it is modelled as a single generic SAF carrier, reusing the light edition's S0 energy
file rather than inventing a pathway split. Pathway-level outputs are therefore undefined for F1, and
comparisons across the SAF axis stay on totals.
```

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The reports define their scenarios as combinations
of five levers, and each maps onto a single knob in AeroMAPS. That correspondence is what makes both the reproduction and the systematic sweep tractable.</span>{raw:typst}`]`

| Lever | Variants | AeroMAPS knob |
|---|---|---|
| Traffic | low / central / high | `markets/markets_{low,central,high}.yaml` |
| Technology | T0–T4 | efficiency series in `*_inputs.json` |
| Operations | O1 / O2 / O3: 0.00 / 0.10 / 0.20 %/yr | `operations_gain_reference_years_values` |
| SAF | F1 / F2 / F3 | `energy_carriers_model_data_file` |
| Market-based measures | M1 / M2 / M3 | computed as the residual to the target |

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The three published scenarios are points on this 
grid: **S0** = C·T2·O2·F1·M1, **S1** = C·T3·O3·F2·M2, **S2** = C·T4·O3·F3·M3. Market-based measures are not swept independently because they are computed as the residual needed to reach the stated target, so they carry no free degree of freedom.</span>{raw:typst}`]`

### Coupling traffic and prices

Elasticity calibrated on a global level, based on jet fuel prices, efficiency gains, population, and
per-capita income {cite:p}`gossling_humpe_2020,brons2002,intervistas2007,gillingham2016`.

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The mechanism is a closed loop rather than a 
correction applied afterwards. A carbon price raises the energy component of direct operating cost per available 
seat-kilometre; that propagates to net cost per revenue passenger-kilometre; a first-order lag converts cost into the 
fare travellers actually face; a price index relative to a reference year drives demand through the calibrated 
elasticity; and the resulting traffic feeds back into fuel burn, energy demand and therefore cost again. The loop is 
closed by the model's MDA solver as a fixed point, so the reported traffic is self-consistent with the cost of achieving
the scenario's own abatement.</span>{raw:typst}`]`

### Climate response and contrail representation

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Emissions are converted to warming by a reduced-complexity climate model of the FaIR family, run per forcing mechanism rather than on CO2 alone, so that CO2, contrail cirrus, the four NOx pathways, water vapour, soot and sulfur each yield their own effective radiative forcing and their own contribution to the temperature response. The decomposition is checked rather than assumed: the sum of the mechanism groups reproduces the reported total to machine precision in every scenario, which is asserted in `climate_analysis/climate_analysis.ipynb`.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Contrail forcing is driven by distance flown rather than by fuel burn, which is what makes contrail avoidance representable at all: a strategy that lengthens routes to avoid ice-supersaturated regions reduces forcing while increasing fuel consumption, and the two effects must be able to move in opposite directions. A mitigation lever scales that forcing by a final gain phased in on a logistic ramp from a start year, with a paired overconsumption penalty, both parameterised from Teoh et al. {cite:p}`teoh2020` in `contrail_variants.yaml`.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Fuel composition enters through soot. Cleaner fuels emit fewer non-volatile particles, seeding fewer and larger ice crystals, and the model represents this as a scaling of contrail forcing with the square root of the particle number emission index, weighted by the massic share of each pathway. The square-root form is what lets the literature's percentage reductions in contrail forcing be mapped onto an emission index directly.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Two uncertainties are propagated rather than fixed, and they are independent. The first is how strongly contrails warm at all: Lee et al. {cite:p}`lee2021` give a 2018 contrail radiative forcing whose 95 % interval spans roughly a factor of six, while Teoh et al. {cite:p}`teoh2024` simulate actual trajectories and obtain a 2019 central value well below it, with a sensitivity range of 34.8 to 74.8 mW m⁻². The second is how much cleaner fuel reduces that forcing: the modelling literature surveyed by Teoh et al. {cite:p}`teoh2022` spans a 15 % reduction at one end and 50 % at the other for fleet-wide adoption. Both bounds are recorded with their sources in `climate_analysis/non_co2_uncertainty.yaml` and combined into three bands named by climate impact, so that the high band pairs the largest contrail sensitivity with the weakest fuel benefit and the low band the reverse. The central band is left at the repository's calibrated values on both axes, so every band's centre reproduces the published scenarios exactly.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The wider context for treating this as a first-order question rather than a refinement is set by the ICCT's *Aviation Vision 2050* {cite:p}`icct_vision2050_2022` and by {cite:p}`arriolabengoa_climate_2024`: on their accounting the majority of the warming aviation can still avoid between now and 2050 is short-lived, and contrail avoidance rather than fuel substitution is the largest single contributor to it.</span>{raw:typst}`]`

## Results

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The reproduction is presented lever by lever, in 
the order the reports themselves use, and then extended in two directions the reports place out of scope. Every figure 
below reads a committed scenario output; no model is executed while this document builds, and each result names the 
notebook that produced it.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Across the three editions the physical levers moved
remarkably little while the accounting around them moved a great deal. Traffic forecasts are essentially unchanged in 
shape, differing mainly in where the COVID recovery is anchored. Technology and operations were revised *downwards* 
between the first and second editions and then held roughly constant into the third. What changed is the allocation of 
the residual: as the target was raised from halving 2005 emissions to net zero, the additional burden fell almost 
entirely on SAF and on market-based measures, the two levers whose feasibility depends least on aircraft engineering 
and most on energy supply, capital and policy. A roadmap that redraws its baseline while holding its terminal target 
will report shifting lever contributions even when nothing physical has changed, so cross-edition comparisons are 
comparisons between accounting conventions at least as much as between technical expectations.</span>{raw:typst}`]`

```{important}
**Read the accounting scope before comparing residuals.** The reports headline *tank-to-wake*
emissions, following the CORSIA methodology: SAF is credited through a lower life-cycle factor, but
the figure quoted is combustion. The scenarios reproduced here are *well-to-wake*: they carry each
pathway's full life-cycle emission factor, so their residuals are **expected to sit above** the
report's numbers, not alongside them. Both scopes are now available from committed outputs, so the
comparison can be made directly rather than argued: S1 reproduces at 424 Mt well-to-wake and 352 Mt
tank-to-wake in 2050, against a reported ~400 Mt; S0 at 1,816 Mt and 1,511 Mt against
~1,150–1,350 Mt. The tank-to-wake twins are derived from the well-to-wake files by
`make_ttw_twins.py`, following the CORSIA accounting the reports describe.

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

# One figure per scenario, tank-to-wake on the left and well-to-wake on the
# right. Every panel shares one y-axis, across the pair and across the three
# scenarios, so both the scope difference and the scenario difference are
# readable as distances rather than inferred from tick labels.
TRIPLETS = [
    ("s0", S0_TTW, S0), ("s1", S1_TTW, S1), ("s2", S2_TTW, S2),
]
decomposition = []
for slug, ttw, wtw in TRIPLETS:
    if ttw is None or wtw is None:
        continue
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 4.4), sharey=True, layout="constrained")
    plot_atag_decomposition(ttw, T0_TTW, T1_TTW, ax=axes[0], legend=True,
                            title=f"{wtw.name} - tank-to-wake")
    plot_atag_decomposition(wtw, T0, T1, ax=axes[1], legend=False,
                            title=f"{wtw.name} - well-to-wake")
    axes[1].set_ylabel("")
    decomposition.append((slug, fig, axes))

# One scale for all six panels, taken from the drawn data and applied before
# anything is written, so no curve is clipped and the exported PDFs agree with
# the page. Reading the limits back only works because the helper leaves
# autoscaling alone.
if decomposition:
    top = max(ax.get_ylim()[1] for _, _, axes in decomposition for ax in axes)
    for _, _, axes in decomposition:
        for ax in axes:
            ax.set_ylim(0, top)
    for slug, fig, _ in decomposition:
        save_fig(fig, name=f"atag_decomposition_{slug}")
```

*Annual CO2 emissions decomposed by mitigation lever, following the pillars and colours ATAG uses, for each reproduced scenario: tank-to-wake on the left, well-to-wake on the right. All six panels share one vertical axis, so both the gap between the two accounting scopes and the gap between scenarios read as distances. Each band is what one pillar removes from the frozen-fleet baseline (dotted). Fleet renewal is the T0-to-T1 distance and next generation technology everything below it, which is where battery-electric aircraft sit rather than in the fuel band; the dashed line is emissions net of market-based measures. Its step at 2036, where CORSIA-derived offsets hand over to the prescribed residual shares, is an artefact of that handover: the assumption adopted here is that 2036 offsetting levels net emissions with 2019, which halves the discontinuity without removing it. One caveat on reading the bands: the wedges sum to a determinate total, but how that total divides between the technology and fuel pillars depends on the order they are peeled off in, by a factor of 35 on S2. See the Discussion.*

```{important}
**How the tank-to-wake panels are built.** The reports headline tank-to-wake emissions, and the
third edition does not publish a per-pathway CORSIA-scope table, so those panels are derived
rather than read off. Each drop-in pathway takes the fossil combustion baseline scaled by its
published carbon-intensity ratio, TtW = 73.8 x (CI / 88.7), which is the CORSIA accounting the
report describes and the same method the second edition's own tank-to-wake files already use:
its electrofuel reads 7.38, exactly 73.8 x 0.10. Anything not combusted reads zero. The
transform is in `make_ttw_twins.py`, so the twins are regenerated from the well-to-wake files
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

*The five technology-only scenarios, tank-to-wake on the left and well-to-wake on the right, sharing a vertical axis. Both panels run identical scenarios, so the distance between them is the accounting scope alone. The dotted curves on the left are the report's own published trajectories, digitised from its charts; they are tank-to-wake, which is why they appear on that panel and not the other. Agreement at 2050 runs from 0.3 % on T2 to 2.7 % on T0, and it is the closest thing to an external check this reproduction has, since these are the only curves the report publishes at a resolution that can be read off.*

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Each scenario is drawn as the reports draw it: a 
rising frozen-technology baseline, then successive wedges for fleet renewal, next-generation technology, operations and 
load factor, SAF, and finally market-based measures closing the gap to the target. The share each wedge carries is the 
number the reports headline, and it is where the editions differ most.</span>{raw:typst}`]`


{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Two things follow directly. The energy lever 
dominates, carrying several times the combined technology, operations and load-factor wedges, a statement about fuel 
supply and capital rather than about aircraft engineering. And the technology, operations and load-factor wedges are 
near-identical between S1 and S2, confirming that the two published scenarios differ almost exclusively in how much SAF
is deployed and how fast. The nominal distinction between a "SAF-focused" and a "technology-centric" scenario is, in the
quantities that reach the atmosphere, mostly a distinction in fuel volume.</span>{raw:typst}`]`


```{code-cell} python
:tags: [hide-input]

import sys

sys.path.insert(0, str(HERE / "3rd_edition_variants"))
try:
    import sweep

    tidy = sweep.read_results()
    summary = sweep.summarise(tidy, year=2050)
    residual = summary.set_index(["traffic", "technology", "operations", "saf"])["co2_emissions"]
    print(f"2050 residual CO2 across the 108-cell grid [Mt]")
    print(f"  min    {residual.min():8.0f}   ({residual.idxmin()})")
    print(f"  median {residual.median():8.0f}")
    print(f"  max    {residual.max():8.0f}   ({residual.idxmax()})")
    for name, cell in sweep.PUBLISHED_CELLS.items():
        print(f"  {name}     {residual.loc[cell]:8.0f}   ({cell})")
    sweep.plot_grid(tidy)
    save_fig(name="lever_sweep")
except FileNotFoundError:
    print("PENDING: the sweep results have not been generated yet.\n"
          "         Run 3rd_edition_variants/sweep.ipynb to produce them.")
```

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Beyond the three published points, the rest of the 
lever grid is unexplored by the reports. Sweeping all 108 combinations of traffic, technology, operations and SAF places
the published scenarios inside a far wider range, and the position they occupy within it is itself informative: they are
neither the optimistic nor the pessimistic corner, but they are also not a designed sample of the space. Three scenarios
cannot express which combinations are jointly plausible, nor how much of the spread comes from each 
lever.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">This is the practical argument for moving from a 
handful of named scenarios to a systematic sweep. A named scenario communicates a narrative and hides the sensitivity; 
a sweep exposes the sensitivity and loses the narrative. The reports need the narrative, but a reader forming policy 
expectations needs to know that the difference between the published scenarios is small compared with the range their 
own levers can produce; and, as the climate results below show, small compared with the uncertainty attached to any one
of them.</span>{raw:typst}`]`

### Traffic, technology, operations and SAF, in detail

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The three published scenarios are single points on
the lever grid; the sweep above shows the grid, but not what each lever looks like on its own. This section shows each 
lever in isolation, holding the others at the S1 published cell, and states for each whether the trajectory is read 
directly from the report or fitted to a digitised curve -- the same provenance distinction used in the validation 
notebooks.</span>{raw:typst}`]`




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

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">SAF is shown as the biofuel mix reached under each
of F1, F2 and F3 -- S0's single generic carrier against S1 and S2's per-pathway breakdown, the resolution difference 
already noted above. This is the lever the reports revise most between editions and the one this reproduction's sweep 
varies most widely, consistent with it carrying the largest share of the abatement wedge seen in the levers-of-action 
figure earlier.</span>{raw:typst}`]`


{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Offsets are the residual, not an independent 
assumption: they are computed as whatever volume closes the gap between the other four levers' combined effect and the 
scenario's stated target, so their trajectory is a direct readout of how much the other levers under-deliver relative to
the goal, which is exactly the accounting property flagged in the Discussion below.</span>{raw:typst}`]`

### Demand-side impacts of transition costs

The reports hold traffic exogenous and say so explicitly, citing Destination 2050
{cite:p}`destination2050_2021` (about −16 % demand by 2050) and a national roadmap (−14 % in 2050),
before placing the question out of scope. Omitting a feedback because it is hard to estimate assigns
it the value zero, which is the one value certain to be wrong {cite:p}`sterman2000`. The point bites
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
READINGS = {"fixed volume": "", "fixed share": "_share"}

coupled = {}
for reading, suffix in READINGS.items():
    for pathway in PATHWAYS:
        path = COUPLED / f"{pathway}{suffix}.json"
        if path.exists():
            label = f"{pathway.upper().replace('_', '-')} ({reading})"
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

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Demand falls by 2 to 12 % by 2050, by more the 
harder carbon is priced: −2.5 % under SSP2-4.5, −6.7 % under SSP2-2.6 and −11.9 % under SSP2-1.9. That is below the 
figures the reports themselves quote before setting the question aside, Destination 2050 at about −16 % and a national 
roadmap at −14 %, and the gap is informative rather than a failure of the coupling. The response scales with how much 
the transition raises the cost of flying, and correcting the electrofuel double-count lowered that cost substantially: 
the same coupling run against the uncorrected fuel price gave 11 to 20 %, in apparent agreement with the cited studies 
for the wrong reason. What survives is the direction and the ordering, not a match in magnitude, and the elasticity was 
in any case calibrated jointly with a price reference that has since been re-anchored.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The two mandate readings cross over, and the 
crossing is the result. Under a strong carbon price the fixed volume covers a larger share of a reduced demand and 
leaves *less* residual CO₂ than a fixed share: 402 against 416 Mt under SSP2-1.9, a 14 Mt advantage. Under weak carbon 
prices the ordering reverses, and by far more: 609 against 467 Mt under SSP2-2.6, and 727 against 486 Mt under 
SSP2-4.5, a 241 Mt penalty.
A fixed volume is a constraint of absolute size, so it tightens automatically as demand falls and slackens as demand 
grows; a fixed share does neither. Which reading applies therefore decides whether a mandate becomes more or less 
demanding exactly when the carbon price moves, and the reports do not say which they mean.</span>{raw:typst}`]`


Traffic, cost and CO2 for S1's three carbon-tax pathways, **restricted to the fixed-share
reading**, which is how real mandates are written and the only reading that stays well posed when
demand responds to price. The three pathways are shown as an envelope rather than as separate
lines, since what matters here is the width the carbon price opens up, not which SSP sits where.

```{code-cell} python
:tags: [hide-input]

# The fixed-share reading only. A share mandate is how ReFuelEU Aviation, the UK
# and Brazilian schemes are actually written, and it is the reading that stays
# well posed once demand responds to price, so it is the one drawn here; the
# fixed-volume reading survives only in the crossover comparison above.
share_only = {k: v for k, v in coupled.items() if "(fixed share)" in k}

SHARE_PANELS = [
    ("rpk", "Traffic [RPK]", 1e-12, "Revenue passenger-kilometres [trillion]"),
    ("doc_net_energy_per_rpk_mean", "Energy DOC per RPK", 1.0, "Energy DOC per RPK [EUR/RPK]"),
    # CO2 from the climate outputs, not the vector ones: the vector series is
    # prospective-only and NaN before 2023, which is why this panel used to start
    # where the other two did not. Its index runs from 1940, not 2000.
    ("co2_emissions", "Residual CO2", 1.0, "Annual CO2 [MtCO2]"),
]
CLIMATE_START = 1940

# The background the three pathways share, and the one thing that separates
# them. SSP2 is a single socioeconomic pathway, so population is identical
# across the three and GDP per capita nearly so; only the carbon price differs,
# and it differs by a factor of 24 by 2050. Drawn as one line per pathway rather
# than an envelope, which on two of these panels would collapse to a line and
# hide the variable that actually drives the row below.
BACKGROUND_PANELS = [
    ("population", "Population", 1e-9, "Population [billion]"),
    ("gdp_per_capita", "GDP per capita", 1.0, "GDP per capita [USD]"),
    ("exogenous_carbon_price_trajectory", "Carbon price", 1.0, "Carbon price [USD/tCO2]"),
]

if share_only:
    fig, all_axes = plt.subplots(2, 3, figsize=(15.6, 8.4), layout="constrained")

    for ax, (column, title, scale, ylabel) in zip(all_axes[0], BACKGROUND_PANELS):
        for offset, (label, view) in enumerate(sorted(share_only.items())):
            series = np.asarray(view.data["vector_outputs"][column], dtype=float) * scale
            years = np.arange(2000, 2000 + len(series))
            ax.plot(years, series, color=f"C{offset}", linewidth=1.8,
                    label=label.split(" ")[0])
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.3)
    all_axes[0][2].legend(fontsize=8)

    axes = all_axes[1]
    for ax, (column, title, scale, ylabel) in zip(axes, SHARE_PANELS):
        curves = []
        for view in share_only.values():
            block = "climate_outputs" if column == "co2_emissions" else "vector_outputs"
            series = np.asarray(view.data[block][column], dtype=float) * scale
            if block == "climate_outputs":
                series = series[2000 - CLIMATE_START :]
            curves.append(series)
        years = np.arange(2000, 2000 + len(curves[0]))
        band = np.vstack(curves)
        # The observed period is shown as well as the forecast: the three
        # pathways coincide there by construction, so the envelope collapses to
        # a single line and the reader can see where the projection departs from
        # history rather than having to take the starting point on trust.
        history = years < 2024
        ax.plot(years[history], np.median(band, axis=0)[history], color="black", linewidth=2,
                label="Observed")
        forecast = years >= 2023
        ax.fill_between(years[forecast], band.min(axis=0)[forecast], band.max(axis=0)[forecast],
                        color="#4C72B0", alpha=0.25, label="Across SSP pathways")
        ax.plot(years[forecast], np.median(band, axis=0)[forecast], color="#4C72B0", linewidth=2,
                label="Median pathway")
        ax.set_title(title)
        ax.set_xlabel("Year")
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.3)
    axes[0].legend(fontsize=8)
    save_fig(fig, name="coupled_demand_share")
```

*The coupled runs **under the fixed-share reading only**. The top row is the background the three SSP pathways run on, one line each: population and GDP per capita are near-identical across them, since SSP2 is a single socioeconomic pathway, and the carbon price is what actually separates them, by a factor of 24 at 2050. The bottom row is what follows, drawn as an envelope across the three: traffic on the left, energy cost per revenue passenger-kilometre in the middle, residual CO2 on the right, with the median picked out. Reading the bottom row in order gives the mechanism, since a higher carbon price raises the middle panel, which lowers the left, which lowers the right. All six panels carry the observed period as well as the projection.*

The panel above gives the total cost per revenue passenger-kilometre. What it does not show is
what that total is made of, and the split matters: a carbon price and a fuel-price premium reach the
traveller through the same channel but respond to different policy. The committed outputs carry both
components separately, so the breakdown is read from them directly.

```{code-cell} python
:tags: [hide-input]

if share_only:
    fig, ax = plt.subplots(figsize=(7.6, 4.2), layout="constrained")
    width = 0.6 / max(len(share_only), 1)
    for offset, (label, view) in enumerate(sorted(share_only.items())):
        vectors = view.data["vector_outputs"]
        base = vectors["doc_energy_per_ask_mean"]
        tax = vectors["doc_energy_carbon_tax_per_ask_mean"]
        position = [year + (offset - 1) * width for year in (2030, 2040, 2050)]
        pathway = label.split(" ")[0]
        ax.bar(position, [base.loc[y] for y in (2030, 2040, 2050)], width=width,
               color=f"C{offset}", label=f"{pathway}, fuel")
        ax.bar(position, [tax.loc[y] for y in (2030, 2040, 2050)], width=width,
               bottom=[base.loc[y] for y in (2030, 2040, 2050)],
               color=f"C{offset}", alpha=0.45, hatch="//",
               label=f"{pathway}, carbon price")
    ax.set_xticks([2030, 2040, 2050])
    ax.set_xlabel("Year")
    ax.set_ylabel("Energy DOC per ASK [EUR/ASK]")
    ax.set_title("Energy cost per seat-kilometre, fuel against carbon price")
    ax.legend(fontsize=8, ncol=3)
    ax.grid(axis="y", alpha=0.3)
    save_fig(fig, name="doc_breakdown")
```

*Energy direct operating cost per available seat-kilometre under the fixed-share mandate, split into the fuel price itself (solid) and the carbon price levied on the residual emissions (hatched), at 2030, 2040 and 2050. One colour per SSP pathway. The solid part grows because the mandate displaces kerosene with a fuel several times costlier per unit energy; the hatched part grows with the carbon price and shrinks as the residual emissions it is levied on fall. This is the same fixed-share reading drawn above, so the two figures decompose one trajectory rather than two.*

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The cost side of the same loop is what makes the 
demand response possible. Energy expenses rise steeply as the SAF mandate ramps, because the mandated fuel is several 
times costlier per unit energy than the kerosene it displaces, and that increase reaches the traveller through direct 
operating cost. This is the mechanism the reports leave unmodelled, and it is not a second-order correction: a demand 
reduction of 2 to 12 % by 2050 is comparable in magnitude to what the technology and operations levers together are 
assumed to deliver.</span>{raw:typst}`]`

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

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Decarbonisation does not act on non-CO₂ in 
proportion to its action on CO₂, and the two diverge sharply by 2050. Every reproduced scenario drives CO₂ emissions 
steeply down, yet the warming each still causes remains dominated by non-CO₂ terms, principally contrail cirrus. A CO₂ 
target and a temperature target are therefore not interchangeable statements about the same trajectory: a scenario can 
approach net-zero CO₂ while the majority of its contribution to warming is untouched by the levers that got it 
there.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">There is a partial coupling, and it runs through 
soot. Cleaner fuels emit fewer non-volatile particles, which seeds fewer and larger ice crystals and reduces contrail 
forcing; the model represents this as a scaling of contrail forcing with the square root of the particle number emission
index, weighted by the mass share of each pathway. But how large that benefit is remains genuinely open. For fleet-wide
SAF adoption, the modelling literature surveyed by Teoh et al. {cite:p}`teoh2022` spans a 15 % reduction in contrail net
radiative forcing at one end and 50 % at the other, with their own estimate at 44 % and one regional study reporting a
possible *increase*.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">That uncertainty compounds with a larger one: how 
much contrails warm at all. Lee et al. {cite:p}`lee2021` give a contrail radiative forcing for 2018 with a 95 % interval
spanning roughly a factor of six, and Teoh et al. {cite:p}`teoh2024`, simulating actual trajectories rather than 
extrapolating, obtain a 2019 central value 44 % below that estimate, with their own sensitivity analysis spanning 34.8
to 74.8 mW m⁻². Both uncertainties bear directly on scenario results, so `climate_analysis/baseline_uncertainty.ipynb` 
propagates them jointly, as three bands named by climate impact: the high band pairs the largest contrail sensitivity 
with the weakest fuel benefit, the low band the reverse, and the central band reproduces the published scenarios 
exactly.</span>{raw:typst}`]`


{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The result reframes the comparison between the 
scenarios. In 2050 the central estimates of total warming from aviation are 105, 89 and 84 mK for S0, S1 and S2, a 
spread of 21 mK between the most and least ambitious published scenario. The uncertainty band on any *single* one of
them is about 70 mK, roughly 3.2 times wider. Decomposing it, the contrail sensitivity contributes about 54 mK and the 
SAF benefit about 15 mK, so the dominant term is how strongly contrails warm, not how much cleaner fuel helps. Choosing
between the published scenarios is, on current knowledge, a smaller question than the uncertainty carried by whichever 
one is chosen, which is an argument for reporting bands rather than points, not for delaying 
action.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Contrail mitigation is absent from all three 
editions: every scenario runs with the contrail lever switched off, matching the reports' stated scope, and the third 
edition is explicit that contrail quantification carries low confidence. Because contrails are nonetheless the largest 
single warming term in 2050 in every reproduced scenario, the omission is worth quantifying rather than inheriting. 
`climate_analysis/climate_analysis.ipynb` runs three strategy families parameterised on Teoh et al. {cite:p}`teoh2020` :
low-risk diversion, small-scale diversion of about 1.7 % of flights, and combustor technology reducing black carbon 
emissions, each across the same three bands.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Three findings survive the checks in that notebook.
**Diversion buys contrail reduction by burning more fuel**, and under a fixed-quantity SAF mandate the marginal fuel is
fossil kerosene, so CO₂ rises by proportionally more than energy does. **Timing beats ultimate effectiveness on a 2050 
horizon**: combustor technology is the stronger measure but depends on fleet renewal and starts five years later, which
is enough to reverse the ranking against small-scale diversion by 2050. And **the value of avoidance scales with the 
uncertainty**: because the high band starts from far more contrail warming, the same strategies avoid several times 
more absolute warming there than in the low band. Avoidance is worth most precisely in the cases where contrails turn
out to be worst, which is an argument for treating it as insurance rather than as a central-estimate 
investment.</span>{raw:typst}`]`

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


{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">For external comparison, the ICCT's *Aviation 
Vision 2050* {cite:p}`icct_vision2050_2022` reports added aviation warming over 2025–2050 in the same units. Its 
historical-trends case adds 60 mK; the S0 reference reproduced here adds 55 mK centrally, with S1 and S2 lower at 39 and
34 mK as their mitigation would imply. The scenario definitions and climate models differ, so this is an indicative 
check rather than a validation, but the reproduction lands in the same range.</span>{raw:typst}`]`

Offsets deserve a separate note. They carry a growing share of the residual abatement in the
reports' accounting, but they act outside the sector's physical emissions: swapping the entire
offset treatment moves the modelled temperature trajectory by *exactly* zero. That is asserted, not
asserted-in-passing, in the climate notebook.

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">A fourth critique belongs with the three above, and it is the one this reproduction is best placed to quantify: the scenarios do not model non-CO2 at all. The third edition states its position plainly, that</span>{raw:typst}`]`

> Significant research to improve scientific understanding as well as understanding of the potential
> mitigation options (operations, technologies, fuels) is currently ongoing.

> The current priority for industry and government climate action should continue to be CO2
> emissions reduction.

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The first sentence is correct and the second does not follow from it. Uncertainty about a warming term is an argument for continued research and for reporting bands rather than points; it is not an argument for assigning that term the value zero, which is what leaving it out of a scenario does. The uncertainty is also not symmetric in consequence: the reproduction here finds that contrail avoidance is worth several times more warming avoided in the high band than in the low one, so the case for acting on contrails is strongest precisely in the cases where the science turns out worst. Nor is the sign of the benefit in doubt, only its magnitude. The ICCT reach the same conclusion from a different direction {cite:p}`icct_vision2050_2022`, attributing the majority of avoidable warming to short-lived effects and placing contrail mitigation ahead of fuel substitution on that basis, on the grounds that avoidance and hydrotreating are relatively mature while e-fuels are not and CO2 already emitted stays for centuries.</span>{raw:typst}`]`

## Discussion

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The Paris Agreement sets a global temperature goal,
not a sectoral one, and translating it into an expectation for aviation requires a choice that no amount of modelling 
can make. Reproducing the scenarios makes the size of that choice explicit: a sector that reaches net-zero CO₂ by 2050 
while its non-CO₂ warming continues largely unabated is not thereby consistent with any particular temperature outcome.
The ICCT's framing, aviation's share of the remaining carbon budget, is more demanding than a net-zero CO₂ target and 
produces a different ranking of levers, placing contrail avoidance ahead of fuel substitution on near-term warming 
avoided per unit cost.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Between the first and third editions the goal was 
raised from a 50 % cut to net zero, the scenario set was reduced, and lever contributions were substantially reallocated,
while the physical content moved little and, where it moved, moved downwards. The removal of the 
aspirational-technology scenario is an unusually explicit correction of technological optimism, but its accounting 
counterpart is less visible: the abatement previously assigned to unconventional propulsion was not deleted, it was 
reassigned to SAF and to market-based measures. Optimism was relocated rather than reduced, and relocated towards levers
whose limits are less legible to an aeronautical audience than those of an airframe.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The baseline against which reductions are measured 
moves between editions as well. A roadmap that redraws its own frozen-technology baseline while keeping the same 
terminal target will report changing lever contributions even when nothing physical has changed, and percentage 
contributions quoted across editions are therefore not directly comparable. This is not a criticism unique to these 
reports; it is a generic hazard of scenario accounting that only becomes visible when the scenarios are rebuilt from 
their inputs.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The avoided-emissions framing deserves particular 
scrutiny, because the demand coupling quantifies its central weakness. When each lever is credited against a 
counterfactual traffic volume that the levers themselves would have suppressed, the credited abatement is inflated: the
fuel that a carbon price prevents from being burned is counted as abated by the SAF that was never needed to replace it.
Closing the loop moves 2050 traffic down by 2 to 12 %, which is the same order as the technology and operations levers combined, so the double-count is not a rounding error.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">A second and sharper form of the same fallacy is built into the wedge chart itself. A decomposition of this kind does not measure what each lever contributed; it measures what each lever contributed *given an order*, and the order is chosen by whoever draws it. The levers overlap, because SAF and a battery-electric fleet decarbonise the same joule, so whichever is peeled off first is credited with it and the other is credited with what remains. Measured on S2 at 2050, where the energy term is 1,475 MtCO2: taking SAF first gives SAF 1,469 Mt and alternative aircraft 6 Mt; taking alternative aircraft first gives 1,257 and 218 Mt; a Shapley value, the symmetric attribution that averages over orders, gives 1,363 and 112 Mt. The fleet is identical in all three, and nothing physical distinguishes them. The alternative-aircraft pillar moves by a factor of 35 on the strength of a presentational choice, and the same fleet change in the T4 technology scenario, where no SAF competes for the credit, is worth 246 Mt.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The conclusion is not that the decomposition is worthless. The total is determinate: whatever the order, the wedges sum to the same distance between the frozen-fleet baseline and the realised trajectory, and that distance is a physical statement. What is indeterminate is the split, and therefore any single quoted percentage. The figures in this document take alternative aircraft before SAF, because the chart stacks them in the technology pillar above the fuel pillar and an attribution that contradicts its own drawing order would be indefensible; the choice is stated in `atag_decomposition.py` rather than left for a reader to infer. The reports' own headline lever contributions are produced by exactly this construction and inherit exactly this indeterminacy, which is worth keeping in view when a single number is quoted as the share of abatement one lever delivers.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Finally, the reproduction inherits limits from its
sources and should be read with them. Digitisation error is bounded but not eliminated; calibrated parameters 
demonstrate consistency rather than identifiability, since different technology–fleet combinations produce identical 
emissions paths; and agreement between two models is not validation against reality. What the exercise establishes is 
narrower and still useful: that the published trajectories are reproducible from stated assumptions, and that the 
assumptions which are *not* stated can be bounded.</span>{raw:typst}`]`

## Conclusion

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Institutional scenarios increasingly function as 
inputs to regulation, and their influence has outgrown the transparency with which they are published. The three 
editions of *Waypoint 2050* are detailed and internally coherent, but their data provenance, calibration and formulation
cannot be inspected, so a reader cannot distinguish a revision driven by evidence from one driven by accounting. 
Reproducing them in an open framework, with every input traceable to a stated origin, is the minimum condition for the 
scrutiny that decisions of this consequence warrant. Open models and open data are not an academic preference here; 
they are what makes disagreement productive.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">The sequential structure these exercises share is
itself a limitation, not merely a convention. Calibrating on the past, projecting drivers, applying levers and stopping 
leaves out precisely the couplings that determine whether a scenario is self-consistent, most obviously that the 
instruments delivering abatement also change the demand being abated. Treating the problem as a multidisciplinary 
analysis, in which such loops are resolved to a fixed point, changes the answer by a margin comparable to whole 
mitigation levers, and is computationally cheap enough that there is no longer a practical reason to avoid 
it.</span>{raw:typst}`]`

{raw:typst}`#text(fill: rgb("#c00000"))[`<span style="color:#c00000">Most importantly, scenarios that report single 
trajectories misrepresent the state of knowledge they summarise. The non-CO₂ uncertainty band around any one scenario 
reproduced here is several times wider than the difference between the published scenarios, and that uncertainty is 
irreducible on policy-relevant timescales. Reporting bands rather than points does not weaken the case for action; it 
relocates it, from choosing the right trajectory to choosing measures that perform acceptably across the range, which 
is an argument for near-term, reversible, high-leverage measures such as contrail avoidance, whose value is greatest in
exactly the futures where the uncertainty resolves badly.</span>{raw:typst}`]`

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
