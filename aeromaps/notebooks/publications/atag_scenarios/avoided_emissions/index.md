---
title: Rewriting the past
subtitle: The avoided-emissions fallacy in aviation transition scenarios
authors:
  - name: Ian Costa-Alves
exports:
  - format: typst
    output: exports/avoided-emissions.pdf
kernelspec:
  name: python3
  display_name: Python 3
---

## Abstract

Page 16 of the third edition of ATAG *Waypoint 2050* {cite:p}`atag2026_waypoint` reports that
"efficiency measures have already saved 14.6 Gt of CO2 since 1990". The number is the area between observed emissions and a
counterfactual in which 1990 efficiency is frozen while traffic follows its observed path. This
paper reproduces that figure inside the open reproduction of the same report's scenarios, and then
takes it apart. The construction reproduces to +2.1 %, and reproducing it recovers the four choices
the report does not state: all three intensity factors are held at 1990 and the counterfactual is
scaled by observed revenue passenger-kilometres, the series is tank-to-wake, the window ends in
2023, and the 1990 anchor is the observed emission level rather than the one the figure's own 2050
label implies. Varying those four choices alone, without touching a single behavioural assumption,
moves the same claim across **6.7 to 17.9 Gt**: the published value is one cell of a grid whose
range is two and a half times its own width. Two internal inconsistencies fall out of the
reproduction. Load factor is inside the retrospective efficiency credit and is credited again as a
forward mitigation lever, a double count worth **3.81 Gt**, a quarter of the headline. And the
report's own stated component gains, 29 % from technology and 25 % from operations, are added rather
than composed to reach the 54 % it quotes, which overstates the combined gain by 7 percentage points.

The deeper problem is not arithmetic. A frozen-1990-efficiency world is one in which flying costs
substantially more per passenger-kilometre, and the construction asserts that it would have been
flown exactly as much: the direct rebound is set to zero. Relaxing that single assumption and
nothing else, holding fleet and technology frozen exactly as the report does, lowers the avoided
figure to **10.4 Gt** at an elasticity of -0.9 and **9.2 Gt** once airlines are also allowed to fill
the aircraft they already own. Turning the question around, the elasticity at which the published
14.6 Gt is recoverable is **-0.056**, an order of magnitude below the least elastic estimate in the
published literature. Defending the figure therefore requires defending a demand curve that is
almost perfectly vertical, which no study of air travel supports. The critique is not specific to
aviation: it is the known failure mode of a class of methods {cite:p}`ekchajzer2024`, applied to a
sector whose own efficiency gains the rebound literature already treats as a destination for other
sectors' savings {cite:p}`pigosso2024_reboundless`.

## Authorship of this draft

The companion paper {cite:p}`costa-alves_reviewing_2026` uses a colour convention to separate the
author's manuscript prose from text drafted to fill its placeholders. That convention does not apply
here yet, because there is no manuscript behind this document: every word below is a draft for the
author to accept, rewrite or discard. Once the author's own prose lands, it will be set in black and
whatever remains drafted will be recoloured to match the companion paper.

What is not a draft is the arithmetic. Every number quoted in the text is read from a committed
output of `retrospective/frozen_baseline.ipynb`, and every figure is drawn from the same files. The
notebook asserts the reproduction against the four quantities the published figure labels before any
counterfactual built on top of it is reported, so a number that moved would fail the build rather
than quietly change the argument.

## Introduction

An avoided-emissions claim is a difference between two worlds: one in which some intervention
happened, and a reference world in which it did not. The reference world is never observed. That is
not a defect peculiar to any one study, it is the definitional structure of the method, and it is
why the literature on net-impacts accounting describes reference scenarios as "non-verifiable
fictional situations" and treats their construction as the point where such assessments succeed or
fail {cite:p}`ekchajzer2024`.

The method class is now large and consequential. Corporate guidance for claiming avoided emissions
{cite:p}`wbcsd2025_avoided,wri2019_comparative` and net-zero standards that admit such claims
alongside inventory reductions {cite:p}`sbti_netzero_2021` have made the construction routine, and
its outputs are addressed to exactly the audiences that a sectoral roadmap addresses: policymakers
setting regulation, and investors allocating capital. Reviewing nine such methods, Ekchajzer et al.
{cite:p}`ekchajzer2024` judge them against Ekvall's five criteria for an environmental accounting
method used in a decision context {cite:p}`ekvall2020`: it should be *feasible*, *accurate*,
*comprehensible*, *inspiring* and *robust*. Their conclusion is that by collapsing a complex and
uncertain dynamic into a single aggregated figure, these methods hide from decision makers the very
uncertainty that should condition the decision. Their recommendation is specific, and this paper
takes it literally: compare several scenarios against each other rather than comparing one to a
hypothetical baseline.

The particular reference world at issue here has an additional problem, and it is one the rebound
literature named a century and a half ago {cite:p}`jevons1865`. Freezing 1990 efficiency while
letting traffic follow its observed path assumes that a doubling of fuel burn per
passenger-kilometre would have changed nothing about how much anyone flew. Rebound effects, defined
as the negative consequences of an intervention arising from induced changes in system behaviour
{cite:p}`hertwich2005,pigosso2024_reboundless`, are estimated to offset roughly 40 % of the intended
sustainability gains of efficiency measures across sectors, of which the direct component alone is
10 to 30 % {cite:p}`binswanger2001`. For personal car mobility the published range of direct rebound
estimates spans 0 to 87 % {cite:p}`greening2000,sorrell2009`. The ATAG figure reports a point drawn
from the extreme corner of that range, and does not report it as a choice.

There is an irony in the particular sector. The standard textbook example of an *indirect* rebound
is a household re-spending the money saved by a fuel-efficient car on long-distance flights
{cite:p}`pigosso2024_reboundless`. Aviation appears in that literature as the place other sectors'
efficiency savings end up. A claim that aviation's own efficiency savings went nowhere is therefore
a claim about a mechanism the sector is elsewhere the standard illustration of.

This paper asks a narrow, answerable question. Can the page-16 figure be reproduced from open data
and an open model; what does reproducing it reveal about how it was constructed; and how much of it
survives when the one assumption it cannot defend is relaxed? The reproduction runs inside AeroMAPS
{cite:p}`planes_aeromaps_2023`, on top of the lever-by-lever reproduction of the same report's
scenarios developed in {cite:p}`costa-alves_reviewing_2026`, so the observed leg and the 2050 anchors
are the same objects that paper already validated.

```{code-cell} python
:tags: [hide-input]

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path.cwd()
RETROSPECTIVE = HERE / "retrospective"
OUTPUTS = RETROSPECTIVE / "data_outputs"

FIGURES = []


def save_fig(fig=None, name=None):
    """Number every figure in document order and write it to exports/ for the PDF build.

    Execution order equals document order in a MyST build, so the numbering the
    reader sees and the numbering on disk are the same. exports/ is gitignored,
    so none of these enter a commit.

    A `name` additionally writes exports/<name>.pdf, which is what the
    manuscript references, so adding or dropping a figure here does not
    silently repoint every \\includegraphics in the LaTeX.
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


def output(name, loader=json.load):
    """Read a committed output, or explain what to run if it is not there yet."""
    path = OUTPUTS / name
    if not path.exists():
        print(f"PENDING: {path.relative_to(HERE)} has not been generated yet.\n"
              f"         Run retrospective/frozen_baseline.ipynb to produce it.")
        return None
    if name.endswith(".csv"):
        return pd.read_csv(path, index_col=0 if name in ("series.csv", "forward.csv") else None)
    with path.open(encoding="utf-8") as handle:
        return loader(handle)


R0 = output("r0.json")
R1 = output("r1.json")
R2 = output("r2.json")
SERIES = output("series.csv")
GRID = output("grid.csv")
CURVE = output("elasticity_curve.csv")
HORIZONS = output("horizons.csv")
FORWARD = output("forward.csv")

# The published figure's own labels, so the document never hard-codes a number
# the notebook did not also check against.
REPORTED = {row["quantity"]: row for row in R0["gate"]} if R0 else {}

# The curve columns are every cell of the method grid; the three named runs sit
# alongside them and are excluded from the envelope.
VARIANTS = [c for c in SERIES.columns if "|" in c] if SERIES is not None else []

print(f"loaded {sum(x is not None for x in (R0, R1, R2))}/3 runs, "
      f"{len(VARIANTS)} grid curves, {0 if GRID is None else len(GRID)} grid cells")
```

## The construction on page 16

The figure {cite:p}`atag2026_waypoint` carries a headline, a standfirst and four labelled
quantities. The headline is
"Efficiency improvements have been impressive, more work is needed". The standfirst states that
"efficiency measures have already saved 14.6 Gt of CO2 since 1990, but further work is needed to get
the sector down to the industry goal in 2050". The chart plots CO2 in millions of tonnes against
years from 1990 to 2050 and draws five things: observed emissions as a solid line; a red dashed
"Frozen 1990 efficiency" line reaching an endpoint marked "≈5,200 Mt" in 2050; the area between them
from 1990 to 2023, labelled as the 14.6 Gt already avoided; a dashed continuation of the observed
line to "2050 emissions without additional efforts: ≈2,400 Mt"; and the area below that, labelled
"Required emissions reductions" and badged with the report's four forward levers, technology,
operations, fuels and market-based measures.

One detail of the drawing is worth naming before anything is computed. **The frozen-efficiency line
dips in 2020.** A counterfactual world with 1990 technology has no reason to share the pandemic's
timing unless it is observed traffic scaled by a frozen intensity, which is exactly what it is. The
construction is therefore not a scenario; it is an arithmetic rescaling of the observed record.

### Reproducing the four labelled quantities

```{code-cell} python
:tags: [hide-input]

if R0 is not None:
    gate = pd.DataFrame(R0["gate"])
    gate["error"] = gate["error_pct"].map(lambda value: f"{value:+.1f} %")
    display(
        gate[["quantity", "reported", "reproduced", "unit", "error"]]
        .round({"reported": 1, "reproduced": 1})
        .style.hide(axis="index")
    )
```

*The four quantities the page-16 figure labels, against their reproduction on the 1990 to 2023
window. Produced by `retrospective/frozen_baseline.ipynb`, which asserts all four within 3 % before
reporting anything downstream of them.*

The agreement is close enough that the reproduction is measuring the same object, and the two
residuals that are not zero say the same thing. The 2050 frozen endpoint reproduces to better than a
tenth of a percent, but only at a 1990 anchor of 441 Mt, which is 3.5 % below the observed 1990
emission level of 457 Mt on the same accounting scope. The 2019 observed value reproduces 2.5 %
above what the figure labels. Both are consistent with a single explanation: the report's observed
CO2 series sits two to three percent below this reproduction's throughout, which is well inside the
range that different coverage definitions of "aviation" produce. That is a difference in inventory
scope rather than a disagreement about the world, but it moves the headline by about a gigatonne,
which is why the anchor is carried as a parameter rather than settled.

```{important}
**The scope factor is a single constant, and it is what identifies the accounting basis.** The
reports headline tank-to-wake emissions, following the CORSIA methodology, while the open
reproduction carries full life-cycle emission factors and is therefore well-to-wake. One factor,
**0.8320**, reconciles the 2019 observed value, the 2050 frozen endpoint and the 2050 no-effort
value simultaneously. It is not fitted to any one of them: it is the ratio the companion
reproduction already established between the two scopes, and its holding across three independent
labels on the same page is what rules out the alternative reading in which the published series is
well-to-wake.

**The 1990 anchor is genuinely ambiguous and is carried as a parameter.** The data-derived anchor is
Kloewer's observed 1990 aviation CO2 {cite:p}`klower2021_data` times the scope factor, 457 Mt. The
figure-derived anchor is whatever level makes the frozen line hit its own labelled 2050 endpoint,
441 Mt. They differ by 3.5 %. Neither is resolved by fiat here; both are run, and the spread is
propagated into every result below.
```

### What the reproduction rules out

The report's text distinguishes two sources of the gain: "an estimated ~29 % fuel efficiency
improvement per unit of RPK traffic" from aircraft technology, and "a 25 % improvement in efficiency
since 1990" from operational efficiency, the latter explicitly including "higher load factors and
optimised aircraft cabin usage". Whether load factor sits inside or outside the frozen counterfactual
is therefore not a matter of interpretation, and it is also testable: if only the fuel-side
intensities were frozen and load factor were allowed to improve as it actually did, the
counterfactual would be scaled by available seat-kilometres rather than by revenue
passenger-kilometres, and it would land far below the figure's own 2050 label.

```{code-cell} python
:tags: [hide-input]

if R0 is not None and HORIZONS is not None:
    reading = (
        HORIZONS.assign(method=HORIZONS["variant"].str.split("|").str[0],
                        anchor=HORIZONS["variant"].str.split("|").str[1])
        .query("anchor == 'endpoint'")
        .groupby("method")["frozen_2050_mt"].first()
    )
    published = REPORTED["Frozen 1990 efficiency at 2050"]["reported"]
    for method, value in reading.items():
        print(f"{method:>22} scaled counterfactual at 2050: {value:7.0f} Mt "
              f"({100 * (value / published - 1):+5.1f} % vs the labelled {published:.0f} Mt)")
    # The aircraft-km reading has no row here on purpose: there is no projected
    # aircraft-km series to extend it on, so it has no 2050 value to compare.
    print()
    print(f"load factor credited twice: {R0['load_factor_double_count_gt']:.2f} Gt, "
          f"{100 * R0['load_factor_double_count_gt'] / R0['avoided_gt']:.0f} % of the headline")
```

```{important}
**Load factor is counted on both sides of the ledger.** It sits inside the retrospective efficiency
credit, because only the revenue-passenger-kilometre scaling reaches the figure's own 2050 endpoint,
and the report's text places it inside the operational gain in any case. It is then credited a
second time as one of the four forward mitigation levers the same figure badges. The overlap is
worth **3.81 Gt over 1990 to 2023, a quarter of the 14.6 Gt headline**, and it is an accounting
error rather than a modelling judgement: no parameter choice makes it go away.
```

A second internal check falls out of the same text. Two efficiency gains compose multiplicatively,
not additively.

```{code-cell} python
:tags: [hide-input]

if R0 is not None:
    composition = R0["stated_gain_composition"]
    print(f"stated technology gain        {100 * composition['stated_technology']:5.1f} %")
    print(f"stated operations gain        {100 * composition['stated_operations']:5.1f} %")
    print(f"stated combined gain          {100 * composition['stated_combined']:5.1f} %")
    print(f"  the two composed properly   {100 * composition['multiplicative']:5.1f} %")
    print(f"  the two simply added        {100 * composition['additive']:5.1f} %")
    print(f"  reading implied             {composition['reading']}")
    print()
    print(f"overstatement                 {100 * composition['overstatement']:5.2f} percentage points")
    print(f"frozen-to-observed ratio implied by the stated 54 %: "
          f"{composition['implied_frozen_ratio_stated']:.2f}")
    print(f"                       by composing 29 % and 25 %: "
          f"{composition['implied_frozen_ratio_multiplicative']:.2f}")
```

The stated 54 % is the arithmetic sum of 29 % and 25 %. Composed as the two multiplicative factors
they are, the same components give 46.8 %, so the headline overstates the combined gain by 7.25
percentage points. This is the same non-additivity that makes the report's lever-by-lever forward
attribution ordering-dependent, appearing in the retrospective headline, where it is easier to see
because both components and their claimed total are printed on the same page.

## Materials and methods

### The Kaya chain, and what freezing selects

Emissions decompose along a nested chain of activity metrics:

$$
E \;=\; \underbrace{\mathrm{RPK}}_{\text{traffic}}
\;\times\; \underbrace{\frac{1}{\mathrm{LF}}}_{\text{load factor}}
\;\times\; \underbrace{\frac{1}{s}}_{\text{seats per aircraft}}
\;\times\; \underbrace{\frac{\text{energy}}{\text{aircraft-km}}}_{\text{fuel-side intensity}}
\;\times\; \underbrace{\frac{\mathrm{CO_2}}{\text{energy}}}_{\text{carbon intensity}}
$$

Holding a factor at its 1990 value removes it from the counterfactual; leaving it free lets its
observed path move the counterfactual. Because the chain is nested, the set of frozen factors picks
out exactly one observed activity series to scale the frozen 1990 intensity by, and there are three
such sets:

| Frozen at 1990 | Driver | Reading |
|---|---|---|
| load factor, gauge, fuel-side, carbon | `rpk` | everything the report calls efficiency, including load factor |
| gauge, fuel-side, carbon | `ask` | fuel-side efficiency only, load factor free |
| fuel-side, carbon | aircraft-km | fuel-side efficiency only, load factor and aircraft size free |

One naming note, because the distinction matters and is easy to get wrong. The step from available
seat-kilometres to aircraft-kilometres is average seats per aircraft, that is, up-gauging. Stage
length is not that step: it is already inside aircraft-kilometres, which are departures times mean
stage length.

### The four undeclared choices

Reproducing the published line requires fixing four things the report does not state, and each is a
grid axis here rather than a constant:

1. **which factors are frozen**, from the three readings above;
2. **the 1990 anchor**, 441 Mt from the figure's own endpoint or 457 Mt from the observed record;
3. **the integration window**, ending 2019, 2023 or 2024;
4. **where the observed series is spliced**, since no single source covers 1990 to 2024.

The fourth deserves a note, because it is the one choice that is invisible in the published figure
and is nonetheless worth over a gigatonne. Kloewer's observed series ends in 2018 and the
reproduction begins in 2000, so the observed leg is spliced. Over the nine years they overlap the two
sources differ by a near-constant 7 to 8 %, so splicing at 2019, which uses the observational series
wherever it exists, leaves a step at the seam. The step is in the direction that enlarges the avoided
area, because it makes observed emissions lower before 2019 than the reproduction says they were.

```{code-cell} python
:tags: [hide-input]

if R0 is not None:
    config = R0["config"]
    print(f"splice year                {config['splice_year']}")
    print(f"seam discontinuity         {100 * config['seam_discontinuity']:+.1f} % at "
          f"{config['splice_year'] - 1}/{config['splice_year']}")
    print(f"Kloewer rescale available  {config['klower_rescale_spread']:.4f} spread over the overlap")
    print()
    span = R0["grid_span_gt"]
    print(f"the whole grid spans       {span[0]:.2f} to {span[1]:.2f} Gt "
          f"for the same claim, a factor {span[1] / span[0]:.1f}")
```

### R0, R1 and R2

Three counterfactuals, each relaxing one more assumption than the last, so that the difference
between any two is attributable to the assumption that separates them.

**R0** is the published construction verbatim: observed activity, 1990 intensity, and the assertion
that the two are independent. In rebound terms it sets the direct rebound to zero.

**R1** relaxes that and nothing else. Frozen 1990 intensity means more fuel burned per
passenger-kilometre than actually was; at the jet fuel price of the day that is a proportionally
higher fuel cost; the fuel share of the fare passes it through to the ticket; and a
constant-elasticity demand curve converts the fare ratio into a traffic ratio. Fleet and technology
stay frozen exactly as in R0, so **R0 minus R1 is the direct rebound in isolation**. Both fares are
evaluated within the same year, so the comparison is deflator-free and the absolute price level
never enters.

**R2** adds the cheapest supply-side response available to an airline that is forbidden from buying a
better aircraft: filling the one it has. A bounded share of the observed load-factor gain is allowed
back, which lowers the counterfactual without conceding any technological progress, so R2 stays
inside the report's own frozen-technology premise. The recovery is applied before the demand
response rather than after, because a cheaper seat implies a smaller fare premium and therefore a
milder suppression; computing the two independently would double-count the saving.

R1 and R2 bracket a consistent counterfactual. R0 sits outside that bracket, which is the argument
of this paper in one sentence.

```{important}
**Every parameter that could be tuned is declared in one file.** The elasticity, the fare
pass-through and the fuel share of the fare live in `params_elasticity.yaml`, together with the
published ranges they are checked against {cite:p}`brons2002,intervistas2007,gossling_humpe_2020`.
It is the single audited source for all three, and the prospective half of this work will read it
as well. That is
deliberate: a critique of avoided-emissions accounting that used one elasticity to shrink a
historical baseline and a different one to shrink a forecast would be committing the error it
describes. The central value, -0.9, is the same one the companion paper's coupled-demand
configuration uses.

The fuel share of the fare, 0.20, is the most consequential of the three and is swept. It is also
chosen conservatively: a *smaller* fuel share means a smaller fare response and therefore a *larger*
avoided figure, so 0.20 is the assumption most favourable to the number under critique among those
that are not zero.
```

### Data

No file is fetched for this analysis. Observed traffic and every Kaya factor come from the
repository's A4A/ICAO series, 1929 to 2024. Observed CO2 comes from Kloewer
{cite:p}`klower2021_data` spliced to the companion paper's committed reproduction, which after its
re-baselining is driven by *observed* traffic in the post-2019 years rather than by a simulated
recovery. The jet fuel price is the EIA US Gulf Coast spot series {cite:p}`fred_jetfuel`, monthly
from April 1990, averaged to calendar years. The 2050 anchors are read from the companion paper's
committed outputs. Full provenance is in `retrospective/data_inputs/SOURCES.md`.

## Results

### The figure, redrawn as a family

```{code-cell} python
:tags: [hide-input]

if SERIES is not None and R0 is not None:
    years = SERIES.index.to_numpy()
    observed = SERIES["observed"].to_numpy()
    envelope = SERIES[VARIANTS]
    lo, hi = envelope.min(axis=1).to_numpy(), envelope.max(axis=1).to_numpy()
    published_line = SERIES["freeze-all|klower|splice2019"].to_numpy()
    window_end = R0["config"]["window"][1]
    mask = years <= window_end

    fig, (ax, side) = plt.subplots(
        1, 2, figsize=(13.0, 5.0), width_ratios=[1.75, 1.0], layout="constrained"
    )

    # --- left: the page-16 chart, element for element ------------------------
    # The shaded avoided area, drawn over the same window the report shades.
    ax.fill_between(years[mask], observed[mask], published_line[mask],
                    color="#c00000", alpha=0.13, lw=0)
    # Everything the four undeclared choices allow, as a band around it.
    ax.fill_between(years, lo, hi, color="#c00000", alpha=0.20, lw=0,
                    label=f"R0 across all {len(VARIANTS)} method choices")
    ax.plot(years, published_line, "--", color="#c00000", lw=1.9,
            label="R0, frozen 1990 efficiency (published reading)")

    for name, colour, label in (
        ("R1", "#d97706", "R1, demand responds to the counterfactual fare"),
        ("R2", "#0f766e", "R2, R1 plus load-factor recovery"),
    ):
        ax.plot(years, SERIES[name].to_numpy(), "--", color=colour, lw=1.6, label=label)

    ax.plot(years, observed, "-", color="#1f3864", lw=2.3, label="Observed CO2 (tank-to-wake)")

    # The report's own two forward legs, read from the companion reproduction.
    if FORWARD is not None:
        ax.plot(FORWARD.index, FORWARD["net_zero"], "-", color="#1f3864", lw=1.6, alpha=0.75,
                label="Reproduced S1, reaching net zero in 2050")
        ax.plot(FORWARD.index, FORWARD["no_effort"], ":", color="#1f3864", lw=1.8,
                label="Reproduced T0, no additional efforts")

    # The frozen line beyond the observed record. There is no observed driver
    # after 2024, so this is drawn as a straight connector to the endpoint the
    # figure itself labels, and marked as an interpolation rather than a result.
    if HORIZONS is not None:
        ends = HORIZONS.set_index("variant")["frozen_2050_mt"]
        for name, colour in (("R0", "#c00000"), ("R1", "#d97706"), ("R2", "#0f766e")):
            ax.plot([window_end + 1, 2050], [SERIES[name].to_numpy()[-1], ends[name]],
                    ls=(0, (1, 3)), color=colour, lw=1.3)
        grid_ends = ends.drop(["R0", "R1", "R2"])
        ax.vlines(2050, grid_ends.min(), grid_ends.max(), color="#c00000", lw=5, alpha=0.3)

    for value, colour, text, offset in (
        (REPORTED["Frozen 1990 efficiency at 2050"]["reported"], "#c00000", "≈5,200 Mt", (-8, 6)),
        (REPORTED["2050 without additional efforts"]["reported"], "#1f3864", "≈2,400 Mt", (-8, 8)),
    ):
        ax.plot([2050], [value], "o", color=colour, ms=7, zorder=5)
        ax.annotate(text, (2050, value), xytext=offset, textcoords="offset points",
                    ha="right", fontsize=8.5, color=colour, fontweight="bold")

    ax.set_xlim(1990, 2053)
    ax.set_ylim(0, 6200)
    ax.set_xlabel("Year")
    ax.set_ylabel("CO2 (millions of tonnes)")
    ax.set_title("The page-16 chart, redrawn")
    ax.legend(fontsize=7.5, loc="upper left", framealpha=0.92)

    # --- right: the integral, as a function of where you stop ---------------
    cumulative = envelope.sub(SERIES["observed"], axis=0).cumsum() / 1000.0
    side.fill_between(years, cumulative.min(axis=1), cumulative.max(axis=1),
                      color="#c00000", alpha=0.20, lw=0, label="across all method choices")
    side.plot(years, (published_line - observed).cumsum() / 1000.0, color="#c00000", lw=1.9,
              label="R0, published reading")
    for name, colour in (("R1", "#d97706"), ("R2", "#0f766e")):
        side.plot(years, (SERIES[name].to_numpy() - observed).cumsum() / 1000.0,
                  color=colour, lw=1.5, label=name)
    reported_gt = REPORTED["Avoided since 1990"]["reported"]
    side.axhline(reported_gt, color="#1f3864", lw=1.3, ls="--")
    side.annotate(f"{reported_gt} Gt reported", (1991, reported_gt), xytext=(0, 5),
                  textcoords="offset points", fontsize=8, color="#1f3864")
    side.axvline(window_end, color="0.45", lw=1.0, ls=":")
    side.annotate(f"window closes {window_end}", (window_end, 0.6), xytext=(-6, 0),
                  textcoords="offset points", rotation=90, ha="right", fontsize=7.5, color="0.35")
    side.set_xlim(1990, 2024)
    side.set_xlabel("Year the window is closed")
    side.set_ylabel("Cumulative avoided CO2 (Gt)")
    side.set_title("The same claim, integrated")
    side.legend(fontsize=7.5, loc="upper left")

    save_fig(fig, name="page16_reproduction")
```

*Left: the page-16 chart redrawn from the open reproduction, element for element. The single red
dashed line the report publishes is kept, and the band around it is the same construction under every
combination of the four choices the report leaves unstated. The two dashed lines below it relax one
behavioural assumption each. The report's own two forward legs are drawn from the companion
reproduction's committed scenarios rather than digitised: the solid trajectory is S1, whose 352 Mt
residual in 2050 is what the report's offsets are there to cancel, and the dotted one is T0, the
frozen fleet. The thick red bar at 2050 is the range of frozen endpoints the same four choices
produce, against the single "≈5,200 Mt" the figure prints; the fine dotted segments reaching it are
straight interpolations, because there is no observed activity series after 2024 to scale. Right: the
same claim integrated as a function of where the window is closed, with the reported 14.6 Gt drawn as
a line. Under the published reading it is reached in 2023, which is where the report closes it.*

```{code-cell} python
:tags: [hide-input]

# A compact version of the chart above, for the companion paper on the scenarios,
# where there is room for one figure only: the report's construction against the
# same construction once traffic follows the WCTR demand model, which responds to
# income, population and the energy cost per RPK. Both are read from the outputs
# retrospective/write_wctr.py writes, the second with the elasticity and delay of
# the calibrated model that the coupled scenarios use.
WCTR = output("r1_wctr.json")
WCTR_SERIES = output("series_wctr.csv")
if WCTR is not None and WCTR_SERIES is not None and R0 is not None:
    curves = WCTR_SERIES.set_index(WCTR_SERIES.columns[0])
    reported_gt = REPORTED["Avoided since 1990"]["reported"]

    fig, ax = plt.subplots(figsize=(4.4, 3.3), layout="constrained")
    ax.fill_between(curves.index, curves["observed"], curves["report_method"], color="#c00000",
                    alpha=0.12, lw=0)
    ax.fill_between(curves.index, curves["observed"], curves["wctr"], color="#d97706",
                    alpha=0.25, lw=0)
    ax.plot(curves.index, curves["report_method"], "--", color="#c00000", lw=1.9,
            label=f"Report method: {WCTR['report_method_avoided_gt']:.1f} Gt "
                  f"(printed {reported_gt:.1f})")
    ax.plot(curves.index, curves["wctr"], "--", color="#d97706", lw=1.9,
            label=f"With price sensitivity: {WCTR['avoided_gt']:.1f} Gt")
    ax.plot(curves.index, curves["observed"], "-", color="#1f3864", lw=2.2, label="Observed")
    ax.set_xlim(curves.index.min(), curves.index.max())
    ax.set_ylim(0, None)
    ax.set_xlabel("Year")
    ax.set_ylabel("CO2 (millions of tonnes)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7, loc="upper left", framealpha=0.92)

    save_fig(fig, name="avoided_emissions_compact")
```

*The page-16 construction in one panel, for the companion paper. The avoided total is the area
between observed emissions and the counterfactual, over 1990 to 2023.*

Three features of the redrawn figure carry the argument. The band is wide, and the reported value
sits inside it rather than at an edge, so the published number is not conservative in any direction
that can be demonstrated. The counterfactual is not a scenario: it dips in 2020 because observed
traffic did, which is the signature of an arithmetic rescaling rather than of a modelled world. And
part of the sharp rise in the observed line into 2019 is the seam rather than growth: 7.8 percentage
points of it are the gap between the two observed sources, and every year before it sits lower than
the reproduction says it should, inside the area the seam therefore enlarges.

The 2020 dip carries a smaller point. The counterfactual falls further than observed emissions do, to
a ratio of 1.39 against 2.23 the year before, because revenue passenger-kilometres collapsed harder
than emissions did while load factors collapsed with them. A construction that scales one year's
intensity by another year's traffic inherits every such compositional shift and reports it as
efficiency.

### The traffic that world implies

```{code-cell} python
:tags: [hide-input]

if SERIES is not None and R0 is not None and R1 is not None:
    fig, (left, right) = plt.subplots(1, 2, figsize=(12.0, 4.4), layout="constrained")

    ratio = SERIES["freeze-all|klower|splice2019"] / SERIES["observed"]
    left.plot(SERIES.index, ratio, color="#c00000", lw=2.1,
              label="R0 emissions, counterfactual over observed")
    for name, colour in (("R1", "#d97706"), ("R2", "#0f766e")):
        left.plot(SERIES.index, SERIES[f"{name}_traffic_ratio"], color=colour, lw=1.7,
                  label=f"{name} traffic, counterfactual over observed")
    left.axhline(1.0, color="0.4", lw=0.9, ls=":")
    stated = R0["stated_gain_composition"]["implied_frozen_ratio_stated"]
    proper = R0["stated_gain_composition"]["implied_frozen_ratio_multiplicative"]
    for value, text, colour in (
        (stated, f"{stated:.2f}, implied by the stated 54 % gain", "#1f3864"),
        (proper, f"{proper:.2f}, implied by composing 29 % and 25 %", "#6b7280"),
    ):
        left.axhline(value, color=colour, lw=1.1, ls="--")
        left.annotate(text, (1991, value), xytext=(0, 4), textcoords="offset points",
                      fontsize=8, color=colour)
    left.set_xlim(1990, 2024)
    left.set_ylim(0.7, 2.95)
    left.set_xlabel("Year")
    left.set_ylabel("Ratio to observed")
    left.set_title("What the frozen world implies")
    left.legend(fontsize=8, loc="upper left", framealpha=0.92)

    if CURVE is not None:
        reported_gt = REPORTED["Avoided since 1990"]["reported"]
        low = min(value[0] for value in R1["literature_ranges"].values())
        high = max(value[1] for value in R1["literature_ranges"].values())
        # One span per source, so the overlap darkens where the sources agree.
        for source in R1["literature_ranges"].values():
            right.axvspan(source[0], source[1], color="#1f3864", alpha=0.11, lw=0)

        right.plot(CURVE["elasticity"], CURVE["avoided_gt"], color="#0f766e", lw=2.1)
        right.axhline(reported_gt, color="#c00000", lw=1.3, ls="--")

        star = R1["epsilon_star"]
        right.plot([star], [reported_gt], "o", color="#c00000", ms=8, zorder=5)

        top = CURVE["avoided_gt"].max()
        bottom = CURVE["avoided_gt"].min()
        head = bottom + 0.94 * (top - bottom)
        right.annotate(f"{reported_gt} Gt reported", (-1.78, reported_gt), xytext=(0, -12),
                       textcoords="offset points", fontsize=8.5, color="#c00000")
        right.annotate(f"ε* = {star:.3f}", (star, reported_gt), xytext=(-10, -18),
                       textcoords="offset points", ha="right", fontsize=10,
                       color="#c00000", fontweight="bold")
        right.annotate("published estimates for aggregate air travel demand",
                       (0.5 * (low + high), head), ha="center", va="top",
                       fontsize=8.5, color="#1f3864")
        right.plot([R1["config"]["elasticity"]], [R1["avoided_gt"]], "s",
                   color="#d97706", ms=7, zorder=5)
        right.annotate(f"R1 at ε = {R1['config']['elasticity']}, "
                       f"{R1['avoided_gt']:.1f} Gt",
                       (R1["config"]["elasticity"], R1["avoided_gt"]), xytext=(8, -4),
                       textcoords="offset points", fontsize=8.5, color="#d97706")

        right.set_xlim(-1.85, 0.05)
        right.set_xlabel("Price elasticity of demand")
        right.set_ylabel("Avoided CO2 1990-2023 (Gt)")
        right.set_title("What elasticity the reported figure needs")

    save_fig(fig, name="counterfactual_and_elasticity")
```

*Left: the frozen world in ratios. The red line is counterfactual emissions over observed, which
reaches 2.28 in 2023 and 2.38 in 2024, bracketing the 2.17 the report's own stated 54 % combined
efficiency gain implies and sitting well above the 1.88 those same components give when composed
properly rather than added. The two lower lines are the traffic that world would actually have
carried once the fare it implies is allowed to matter: 81 % of observed under R1 and 84 % under R2 in
2023. Right: the avoided figure as a function of the elasticity assumed, with the shaded
regions covering the ranges published for aggregate air travel demand and darkening where those
sources agree. The square marks R1 at the elasticity this repository already uses. The reported
14.6 Gt is recoverable only at ε\* = -0.056, an order of magnitude inside the least elastic published
estimate {cite:p}`brons2002,intervistas2007,gossling_humpe_2020`, which is the sense in which the
figure is not defensible at any plausible parameterisation rather than merely wrong at ours.*

```{code-cell} python
:tags: [hide-input]

if R0 is not None and R1 is not None and R2 is not None:
    table = pd.DataFrame([
        {"run": name,
         "assumption relaxed": text,
         "avoided 1990-2023 (Gt)": run["avoided_gt"],
         "counterfactual 2023 (Mt)": run["counterfactual_mt"][-1],
         "traffic vs observed 2023": run["demand_ratio"][-1]}
        for name, run, text in (
            ("R0", R0, "none, the published construction"),
            ("R1", R1, "traffic responds to price"),
            ("R2", R2, "and airlines fill their aircraft"),
        )
    ])
    display(table.round({"avoided 1990-2023 (Gt)": 2, "counterfactual 2023 (Mt)": 0,
                         "traffic vs observed 2023": 3}).style.hide(axis="index"))

    reported = R0["gate"][3]["reported"]
    print(f"\nthe reported {reported} Gt is "
          f"{100 * (reported / R1['avoided_gt'] - 1):.0f} % above R1 and "
          f"{100 * (reported / R2['avoided_gt'] - 1):.0f} % above R2")
    print(f"epsilon* = {R1['epsilon_star']:.4f}; the least elastic published estimate is "
          f"{max(high for _, high in R1['literature_ranges'].values())}")
    for row in R1["epsilon_star_by_fuel_share"]:
        print(f"   fuel share of fare {row['fuel_cost_share']:.2f} -> "
              f"epsilon* = {row['epsilon_star']:.4f}")
```

At the elasticity the companion paper's coupled configuration already uses, the avoided figure falls
from 14.90 Gt to 10.43 Gt: **the published number is 40 % above the value its own construction gives
once traffic is allowed to respond to the price its own counterfactual implies.** Allowing airlines
to fill their aircraft as well brings it to 9.20 Gt. The direction is not sensitive to any of the
three declared parameters, and neither is the magnitude of the conclusion: across the swept range of
the fuel share of the fare, ε\* moves between -0.11 and -0.04, and every value in that interval is
an order of magnitude inside the published estimates.

### The grid

```{code-cell} python
:tags: [hide-input]

if GRID is not None and R0 is not None:
    fig, ax = plt.subplots(figsize=(10.0, 4.0), layout="constrained")
    # Published reading first, so it reads top to bottom in the drawn figure.
    methods = list(dict.fromkeys(GRID["method"]))[::-1]
    palette = {"freeze-all": "#c00000", "fuel-side": "#1f3864",
               "fuel-side-and-gauge": "#0f766e"}
    rng = np.random.default_rng(0)
    for index, method in enumerate(methods):
        subset = GRID.query("method == @method")
        ax.scatter(subset["avoided_gt"],
                   index + rng.uniform(-0.22, 0.22, len(subset)),
                   s=38, alpha=0.75, color=palette.get(method, "0.4"),
                   edgecolor="white", linewidth=0.5)
    reported = REPORTED["Avoided since 1990"]["reported"]
    ax.axvline(reported, color="0.2", lw=1.4, ls="--")
    ax.annotate(f"{reported} Gt reported", (reported, len(methods) - 0.55),
                xytext=(7, 0), textcoords="offset points", fontsize=9, va="center")
    ax.set_yticks(range(len(methods)))
    ax.set_yticklabels(methods)
    ax.set_ylim(-0.6, len(methods) - 0.4)
    ax.set_xlabel("Avoided CO2 since 1990 (Gt)")
    ax.set_title(f"Every cell of the method grid ({len(GRID)} readings of one claim)")
    save_fig(fig, name="method_grid")
```

*Each point is one reading of "efficiency has saved X Gt of CO2 since 1990", differing only in the
four choices the report does not state, with no behavioural assumption varied anywhere. The dashed
line is the published value. The grid spans 6.7 to 17.9 Gt, and the choice of where in it to stand
is not documented on page 16 or anywhere else in the report.*

## Discussion

Ekvall's five criteria for an environmental accounting method used in a decision context
{cite:p}`ekvall2020,ekchajzer2024` provide the frame. Taking them in turn against the page-16 figure:

**Feasible.** The construction passes easily, and that is part of the problem. It requires only an
observed activity series and a 1990 intensity, which is why it is reproducible here to within 3 %
from open data in a few hundred lines. Cheapness is not a virtue when the cheap thing and the correct
thing point in different directions.

**Accurate.** The figure fails, in a way that is demonstrable rather than arguable. Its reference
world is a "non-verifiable fictional situation" in the general sense {cite:p}`ekchajzer2024`, but it
is worse than merely unverifiable: it is internally inconsistent. It posits emissions 2.28 times
observed in 2023, which is to say fuel costs more than twice as high per passenger-kilometre, and
simultaneously posits that every one of those passenger-kilometres was flown. The traffic in the
numerator was made affordable by the efficiency in the denominator. Two further errors run in the
same direction and are independent of any behavioural assumption: the 3.81 Gt of load factor counted
on both sides of the ledger, and the seam in the observed leg that lowers pre-2019 emissions by
around 7 %.

**Comprehensible.** The figure passes, and this is the criterion on which such constructions earn
their place. One number and one shaded area communicate immediately. But comprehensibility bought by
suppressing a 6.7 to 17.9 Gt method range is comprehension of the wrong object.

**Inspiring**, in Ekvall's sense of producing knowledge that leads to action. The figure fails. It
identifies no lever, supports no comparison between strategies, and cannot say whether anything is
compatible with a transition pathway; it can only certify that past effort was large. Its audience,
in the terms of Ekchajzer et al.'s decision-situation taxonomy, is the political decision maker and
the investor, the two contexts in which a single aggregated figure narrows the decision space to a
binary. A roadmap that opens by quantifying how much has already been avoided, and closes by
assigning the remainder to four levers measured against a baseline built the same way, has used its
accounting to argue for the sufficiency of its trajectory rather than to test it.

**Robust.** The figure fails. Every undeclared choice in the construction runs in the same direction:
the frozen-factor set that maximises the credit, the splice that lowers observed emissions before
2019, the zero-rebound assumption, and the additive rather than multiplicative composition of the two
stated component gains. None of these is individually large enough to be obviously wrong, and no
safeguard in the construction would have caught any of them, because the method has no
error-correcting structure at all: it produces one number, and one number cannot disagree with
itself.

The remedy Ekchajzer et al. propose is to compare several scenarios against each other rather than
comparing one to a hypothetical baseline, and to present ranges where ranges exist, following
Stirling's argument that plural and conditional methods keep decision makers exposed to dissenting
interpretations rather than to a single authoritative-looking value {cite:p}`stirling2010`. This
paper's method is that remedy applied to its own object. The band in the redrawn figure is not a
confidence interval and is not offered as one: it is the set of answers the published method gives
when its own undeclared choices are enumerated, and its width is a property of the method rather than
of the data.

One caveat is owed to R2. The load-factor recovery it allows is a bounded judgement, calibrated on
the observed record but not derivable from it, and a reviewer may reasonably contest its size. The
argument does not depend on it. R1 is the defensible floor, it relaxes exactly one assumption, and
the conclusion survives on R1 alone. Nor does the argument depend on any particular elasticity, which
is the point of reporting ε\* rather than a point estimate: a defence of the published figure must
now name a number and defend it, and the number it must defend is a demand curve for air travel that
is very nearly vertical. The wider point that efficiency policy has to be evaluated against the
demand it induces, rather than against a frozen counterpart of itself, is not new
{cite:p}`gillingham2016`; what is new here is that a sectoral roadmap can be shown to have assumed
the opposite, in a figure it reproduces on its own terms.

## Conclusion

The 14.6 Gt on page 16 reproduces. That is the first result, and it matters, because it means the
critique is of a construction that has been recovered rather than guessed at. What reproducing it
shows is that the number is one reading among many of an underspecified method: the same claim,
computed the same way, spans 6.7 to 17.9 Gt across choices the report never states.

Two of the errors inside it need no theory at all. Load factor is credited as past efficiency and
again as a future lever, worth 3.81 Gt or a quarter of the headline. The report's own two component
gains are added rather than composed, overstating the combined efficiency improvement by seven
percentage points.

The rest is the rebound. The construction credits efficiency with avoiding the emissions of flights
that efficiency itself made affordable, which is to assume the direct rebound in air travel is zero
in a literature where the comparable range for personal mobility is 0 to 87 %. Relaxing that single
assumption removes about 30 % of the claim; the elasticity at which the published figure is
recoverable is -0.056, roughly a twentieth of the meta-analytic central estimate for air travel.

The narrower conclusion is that this figure should not be used. The broader one is that the same
construction underlies the report's forward analysis, where mitigation levers are scored against a
traffic forecast unaffected by the sustainable fuel premium and the rising carbon price those very
levers impose. The retrospective case is the easier one to settle, because the counterfactual can be
tested against an observed record. That is why it is settled first.

## Reproducibility

Every result on this page reads a committed file. No model is executed while the document builds.

| Result | Produced by | Read from |
|---|---|---|
| R0 gate, method grid, double count, stated-gain composition | `retrospective/frozen_baseline.ipynb` | `data_outputs/r0.json`, `grid.csv` |
| R1, ε\* and its sensitivity to the fuel share | same | `data_outputs/r1.json`, `elasticity_curve.csv` |
| R2 | same | `data_outputs/r2.json` |
| Every curve in the figures | same | `data_outputs/series.csv`, `horizons.csv` |

The elasticity, the fare pass-through and the fuel share of the fare are set in
`params_elasticity.yaml` and nowhere else. Input provenance is in
`retrospective/data_inputs/SOURCES.md`, and each output file records the SHA-256 of every input it
was built from, so a changed input is detectable rather than silent.

The companion reproduction's scenario outputs are read and never written. The notebook asserts this
mechanically at the end of its run, by asking git whether anything outside `avoided_emissions/`
moved.

```{note}
The figures on this page are produced by code cells that read the committed `data_outputs/` files. If
an output file is missing, the cell prints `PENDING: run retrospective/frozen_baseline.ipynb` instead
of failing, so a missing figure reads as missing data rather than a broken build.
```
