"""Policy experiments on a five-fuel, two-region market with differing eligibility.

Usage::

    poetry run python -m fuel_clearing_step1.policy_cases

The step-1 bench has two fuels and identical policy in both regions, which is enough to
test the kernel and nothing else: with one sustainable pathway the market has no choice
to make, only a quantity to set. Five fuels and **different eligibility rules per
region** is the smallest setting where the market does what a market is for -- pick
between options -- and where the regions genuinely differ in something other than size.

The case is built after the real regulatory shape rather than invented: a
ReFuelEU-like region that **excludes crop-based feedstock**, against a region that
allows it, with the same headline obligation in both. Everything else is held
identical, so any difference between the regions is the eligibility rule and nothing
else.

Run at the kernel level, not through the MDA. That is deliberate: the traffic loop
scales every result by roughly a tenth (REPORT.md section 8.4) and at `w = 0` it does
not change any ordering, while an MDA per cell would cost minutes each and put the
`w > 0` convergence problem between the reader and the policy question.

Three caveats, all of which change how the results below should be read.

**One mandate per region.** The kernel has no *sub-mandate*, so ReFuelEU's separate
synthetic-fuel obligation cannot be expressed. Sub-mandates are the main reason a real
scenario has five fuels rather than two, so this is the first thing to add if these
cases are to be used for anything beyond illustration -- and note that a sub-mandate
would force e-fuel early, which is exactly the effect the exclusion produces here by
accident.

**2050 is the last year.** The obligation's steepest step (42 % to 70 %) is also the
horizon, so a market with perfect foresight has no reason to build past it. Every
result that turns on "what is built by the final step" is therefore partly a terminal
condition, and would soften in a scenario that ran past 2050.

**Region A and region B differ in traffic growth as well as eligibility** (3.0 against
4.5 % CAGR -- inherited from the step-1 bench, REPORT.md section 2b). The A-versus-B
figure therefore confounds the two. The clean comparison is `cost_of_exclusion`, which
runs the *same* region under both rules.
"""

from __future__ import annotations


import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from aeromaps.models.impacts.generic_energy_model.fuel_clearing.kernel import (  # noqa: E402
    ClearingInputs,
    clear_market,
)

from .figures import FIGURES, load_bench  # noqa: E402

# Pathway order is positional in the kernel's arrays; fixed here once.
FUELS = ["fossil_kerosene", "hefa_fog", "hefa_crop", "atj", "efuel"]
RESIDUAL = 0

# Costs in EUR/MJ. Kerosene and HEFA-FOG are the bench's measured values; the other
# three are placed in the usual ordering (crop oil cheaper than waste oil at scale,
# alcohol-to-jet above both, power-to-liquid dearest). They are illustrative, and the
# conclusions below are about ORDERING and exclusion, which do not depend on the exact
# figures -- the sensitivity to that ordering is the third figure.
COST = {
    "fossil_kerosene": 0.0120,
    "hefa_crop": 0.0190,
    "hefa_fog": 0.0232,
    "atj": 0.0300,
    "efuel": 0.0550,
}

# Capacity scale as a fraction of peak demand, i.e. how far each can be pushed before
# it starts costing more at the margin. Waste oil is the feedstock-limited one; crop
# oil is bounded by land; alcohol-to-jet by residues; power-to-liquid effectively by
# electricity, so it is the only one that scales.
CAPACITY_SHARE = {
    "fossil_kerosene": np.inf,
    "hefa_fog": 0.08,
    "hefa_crop": 0.25,
    "atj": 0.20,
    "efuel": 1.50,
}
SATURATION = {"fossil_kerosene": 0.0, "hefa_fog": 2.0, "hefa_crop": 1.5, "atj": 1.5, "efuel": 0.5}

# Region A is the ReFuelEU-like one: crop-based feedstock does not count towards its
# obligation. Region B counts everything. Same headline mandate in both.
ELIGIBLE = {
    "region_A": ["hefa_fog", "atj", "efuel"],
    "region_B": ["hefa_fog", "hefa_crop", "atj", "efuel"],
}

RAMPUP = 0.25
SEED_SHARE = 0.015  # the calibrated value, see REPORT.md section 9.2
BUYOUT = 0.20


def build(mandate_scale=1.0, eligible=None, capacity_share=None, cost=None):
    """A five-fuel, two-region case on the bench's demand and obligation."""
    bench = load_bench()
    demand = bench["demand"]
    regions_list = list(bench["regions"])
    regions, years = demand.shape
    pathways = len(FUELS)
    peak = float(demand.max())

    eligible = eligible or ELIGIBLE
    capacity_share = {**CAPACITY_SHARE, **(capacity_share or {})}
    cost_map = {**COST, **(cost or {})}

    is_sustainable = np.zeros((regions, pathways), dtype=bool)
    for r, region in enumerate(regions_list):
        for p, fuel in enumerate(FUELS):
            is_sustainable[r, p] = fuel in eligible[region]

    cost_array = np.zeros((regions, pathways, years))
    capacity = np.full((regions, pathways, years), np.inf)
    sat_gamma = np.zeros((regions, pathways))
    rampup_limit = np.zeros((regions, pathways))
    rampup_seed = np.zeros((regions, pathways))
    q_init = np.zeros((regions, pathways))

    for p, fuel in enumerate(FUELS):
        cost_array[:, p, :] = cost_map[fuel]
        share = capacity_share[fuel]
        if np.isfinite(share):
            capacity[:, p, :] = share * demand
        sat_gamma[:, p] = SATURATION[fuel]
        if p != RESIDUAL:
            rampup_limit[:, p] = RAMPUP
            rampup_seed[:, p] = SEED_SHARE * peak
    q_init[:, RESIDUAL] = demand[:, 0]

    return ClearingInputs(
        demand=demand,
        cost=cost_array,
        is_sustainable=is_sustainable,
        mandate_share=np.clip(bench["reference_share"] * mandate_scale, 0.0, 1.0),
        buyout_price=np.full((regions, years), BUYOUT),
        capacity=capacity,
        sat_gamma=sat_gamma,
        sat_n=4.0,
        rampup_limit=rampup_limit,
        rampup_seed=rampup_seed,
        q_init=q_init,
        discount_rate=0.04,
        pricing_weight=0.0,
        residual_pathway=RESIDUAL,
    )


def _delivered(outputs):
    total = outputs.volume.sum(axis=1)
    return np.sum(outputs.market_mfsp * outputs.volume, axis=1) / np.where(total > 0, total, 1.0)


COLOURS = {
    "fossil_kerosene": "#6b7280",
    "hefa_fog": "#2f6b4f",
    "hefa_crop": "#b9a44c",
    "atj": "#1f5f8b",
    "efuel": "#a93226",
}
LABELS = {
    "fossil_kerosene": "fossil kerosene",
    "hefa_fog": "HEFA, waste oil",
    "hefa_crop": "HEFA, crop oil",
    "atj": "alcohol-to-jet",
    "efuel": "e-fuel",
}


def fuel_mix():
    """What each region builds, when one of them may not count crop feedstock."""
    bench = load_bench()
    years, regions = bench["years"], list(bench["regions"])
    outputs = clear_market(build())

    figure, axes = plt.subplots(1, 2, figsize=(12.0, 4.4), constrained_layout=True, sharey=True)
    for r, (axis, region) in enumerate(zip(axes, regions)):
        shares = 100 * outputs.volume[r] / bench["demand"][r]
        axis.stackplot(
            years,
            *[shares[p] for p in range(len(FUELS))],
            colors=[COLOURS[f] for f in FUELS],
            labels=[LABELS[f] for f in FUELS],
        )
        axis.plot(
            years,
            100 * bench["reference_share"][r],
            color="black",
            linestyle="--",
            linewidth=1.4,
            label="obligation",
        )
        allowed = ", ".join(LABELS[f] for f in ELIGIBLE[region] if f != "fossil_kerosene")
        axis.set_title(f"{region}\neligible: {allowed}", fontsize=9)
        axis.set_xlabel("year")
        axis.set_xlim(years[0], years[-1])
        axis.set_ylim(0, 100)
        axis.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("share of drop-in energy, %")
    axes[1].legend(loc="upper left", frameon=False, fontsize=8)
    figure.suptitle(
        "Same obligation, different eligibility: what each region ends up burning", fontsize=11
    )
    FIGURES.mkdir(parents=True, exist_ok=True)
    target = FIGURES / "policy_fuel_mix.png"
    figure.savefig(target, dpi=150)
    plt.close(figure)
    print(f"wrote {target}")

    for r, region in enumerate(regions):
        mix = {FUELS[p]: 100 * outputs.volume[r, p, -1] / bench["demand"][r, -1] for p in range(5)}
        top = ", ".join(f"{LABELS[f]} {v:.0f} %" for f, v in mix.items() if v > 0.5)
        print(f"  {region} 2050: {top}")
        print(
            f"    compliance {outputs.compliance_price[r].max():.5f}"
            f"   delivered {_delivered(outputs)[r, -1]:.5f}"
        )
    return outputs


def cost_of_exclusion():
    """What the crop-feedstock exclusion costs, year by year.

    Reported as a trajectory, not as a maximum over years. The maximum hides the whole
    result: the exclusion is dearer in every year until the last, and cheaper in the
    last, so a single number reports whichever effect happens to be larger.
    """
    bench = load_bench()
    years = bench["years"]
    permissive = {"region_A": ELIGIBLE["region_B"], "region_B": ELIGIBLE["region_B"]}
    strict = clear_market(build())
    loose = clear_market(build(eligible=permissive))

    figure, axes = plt.subplots(1, 2, figsize=(12.0, 4.4), constrained_layout=True)
    axes[0].plot(years, strict.compliance_price[0], "-", color="#a93226", label="crop excluded")
    axes[0].plot(years, loose.compliance_price[0], "--", color="#2f6b4f", label="crop allowed")
    axes[0].set_ylabel("compliance price, EUR/MJ")
    axes[0].set_title("Region A: what the obligation costs to meet", fontsize=10)
    axes[0].legend(frameon=False, fontsize=8)

    # The share of demand met by the pathway that scales -- the reason for the reversal.
    efuel = FUELS.index("efuel")
    axes[1].plot(
        years,
        100 * strict.volume[0, efuel] / bench["demand"][0],
        "-",
        color="#a93226",
        label="crop excluded",
    )
    axes[1].plot(
        years,
        100 * loose.volume[0, efuel] / bench["demand"][0],
        "--",
        color="#2f6b4f",
        label="crop allowed",
    )
    axes[1].set_ylabel("e-fuel share of drop-in energy, %")
    axes[1].set_title("...and how much of the scalable option it has built", fontsize=10)
    axes[1].legend(frameon=False, fontsize=8)

    for axis in axes:
        axis.set_xlabel("year")
        axis.set_xlim(2025, years[-1])
        axis.spines[["top", "right"]].set_visible(False)
    figure.suptitle(
        "Excluding crop feedstock costs more every year -- until the last one", fontsize=11
    )
    FIGURES.mkdir(parents=True, exist_ok=True)
    target = FIGURES / "policy_exclusion_cost.png"
    figure.savefig(target, dpi=150)
    plt.close(figure)
    print(f"wrote {target}")

    for year in (2030, 2035, 2040, 2045, 2050):
        i = int(np.where(years == year)[0][0])
        a, b = strict.compliance_price[0, i], loose.compliance_price[0, i]
        gap = 100 * (a - b) / b if b > 0 else float("nan")
        print(f"  {year}: excluded {a:.5f}   allowed {b:.5f}   {gap:+7.1f} %")
    return strict, loose


def feedstock_squeeze(shares=(0.04, 0.06, 0.08, 0.12, 0.20, 0.40)):
    """More waste oil is not straightforwardly cheaper, and the reason is the ramp-up.

    Cheap feedstock displaces the pathway that actually scales, so the region arrives at
    the steepest part of the obligation with less of it built. The 2050 compliance price
    therefore RISES with waste-oil availability over part of the range -- an ordering a
    static cost-merit model cannot produce.
    """
    bench = load_bench()
    final, mid, mix = [], [], {f: [] for f in FUELS if f != "fossil_kerosene"}
    midpoint = int(np.where(bench["years"] == 2040)[0][0])
    for share in shares:
        outputs = clear_market(build(capacity_share={"hefa_fog": share}))
        final.append(outputs.compliance_price[0, -1])
        mid.append(outputs.compliance_price[0, midpoint])
        for p, fuel in enumerate(FUELS):
            if fuel != "fossil_kerosene":
                mix[fuel].append(100 * outputs.volume[0, p, -1] / bench["demand"][0, -1])

    figure, axes = plt.subplots(1, 2, figsize=(11.5, 4.2), constrained_layout=True)
    x = [100 * s for s in shares]
    axes[0].plot(x, mid, "-o", color="#1f5f8b", label="2040 (mid-trajectory)")
    axes[0].plot(x, final, "-s", color="#a93226", label="2050 (steepest step)")
    axes[0].set_ylabel("compliance price, EUR/MJ")
    axes[0].set_title("Cheap feedstock helps mid-way, not at the end", fontsize=10)
    axes[0].legend(frameon=False, fontsize=8)
    for fuel, values in mix.items():
        axes[1].plot(x, values, "-o", color=COLOURS[fuel], label=LABELS[fuel], markersize=4)
    axes[1].set_ylabel("share of drop-in energy in 2050, %")
    axes[1].set_title("What it displaces", fontsize=10)
    axes[1].legend(frameon=False, fontsize=8)
    for axis in axes:
        axis.set_xlabel("waste-oil capacity, % of peak demand")
        axis.axvline(8, color="0.7", linestyle=":", linewidth=1.2)
        axis.spines[["top", "right"]].set_visible(False)
    figure.suptitle("Region A: more of the cheap fuel, less of the one that scales", fontsize=11)
    target = FIGURES / "policy_feedstock_squeeze.png"
    figure.savefig(target, dpi=150)
    plt.close(figure)
    print(f"wrote {target}")
    for i, share in enumerate(shares):
        composition = ", ".join(f"{LABELS[f]} {mix[f][i]:.0f} %" for f in mix if mix[f][i] > 0.5)
        print(
            f"  waste oil {100 * share:5.1f} %: 2040 {mid[i]:.5f}  2050 {final[i]:.5f}   {composition}"
        )
    return mid, final, mix


if __name__ == "__main__":
    fuel_mix()
    print()
    cost_of_exclusion()
    print()
    feedstock_squeeze()
