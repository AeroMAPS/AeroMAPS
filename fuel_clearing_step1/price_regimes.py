"""Measurement 4.5.2 of the brief: price regimes across the reachability boundary.

Usage::

    poetry run python -m fuel_clearing_step1.price_regimes          # run, then plot
    poetry run python -m fuel_clearing_step1.price_regimes --plot   # plot the saved run

The brief asks for a multiplier on the obligation swept from 0.5 to 2, with the ramp-up
at the value the inventory found, recording: the compliance price, the unmet volume, the
years where the ramp-up bites, the ramp-up price, the delivered price, and the traffic.
Traffic only exists once the market is inside the chain, so every point here is a full
two-region MDA.

**This is not the same measurement as REPORT.md section 8.3**, which until now carried
the 4.5.2 label. That section measures whether the coupled fixed point is reached, which
is a real finding but is not what 4.5 asked for. The label is corrected and this is the
measurement.

What it is for: the brief's third question -- *how do prices behave when the obligation
becomes unreachable?* Below the boundary the obligation is met by building and the
compliance price is a substitution cost; above it the ramp-up runs out, the shortfall
has to be bought out, and the compliance price is pinned at the release price. The sweep
crosses that boundary.
"""

from __future__ import annotations

import json
import logging
import re
import sys
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import yaml  # noqa: E402

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "scenario" / "regionalisation_market.yaml"
CARRIERS = HERE / "scenario" / "energy_carriers_step1.yaml"
RESULTS = HERE / "price_regimes.json"
FIGURES = HERE / "figures"

REGION = "region_A"
PATHWAY = "hefa_fog"

# The ramp-up the inventory found, as section 8 uses it, plus the demand slope that lets
# w > 0 converge and the loop tolerance the market's own precision can support (8.7).
SETTINGS = dict(
    rampup_limit=0.20,
    rampup_seed_share=0.005,
    capacity=1.1e13,
    buyout_price=0.30,
    saturation_intensity=1.0,
    saturation_stiffness=4.0,
    demand_elasticity=0.5,
)
MDA_TOLERANCE = 1.0e-8
MULTIPLIERS = (0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0)

# The obligation, verbatim from energy_carriers_step1.yaml. Scaling is done on this
# rather than by re-parsing the file, because the block carries a `!AeroMapsCustomDataType`
# tag that a safe loader will not construct.
BASE_VALUES = [0.0, 2.0, 6.0, 20.0, 34.0, 42.0, 70.0]
_VALUES_LINE = re.compile(
    r"(mandate_share: !AeroMapsCustomDataType\n\s*years: \[[^\]]*\]\n\s*values: \[)[^\]]*(\])"
)


def _scaled_carriers(multiplier: float) -> str:
    """The carriers file with the obligation scaled, as text.

    Clipped at 100 %: the obligation is a percentage of demand and the kernel refuses
    anything outside [0, 1] rather than silently normalising it.
    """
    text = CARRIERS.read_text()
    scaled = [min(100.0, round(v * multiplier, 6)) for v in BASE_VALUES]
    # Always a decimal point. With "%g" the list comes out as [0, 3.5, 10.5, 35, ...],
    # GEMSEO's grammar infers the element type from the first entry, calls the series
    # integer-valued, and then rejects 3.5 at validation. Mixed int/float is the trap.
    replacement = r"\g<1>" + ", ".join(f"{v:.4f}" for v in scaled) + r"\g<2>"
    patched, count = _VALUES_LINE.subn(replacement, text)
    if count != 1:
        raise RuntimeError(
            f"expected exactly one mandate_share block in {CARRIERS.name}, patched {count}. "
            "The obligation moved; this measurement would otherwise sweep nothing."
        )
    return patched


def _run_one(multiplier: float):
    """One full MDA at a scaled obligation, reduced to what the brief asks for."""
    import aeromaps.core.multi_regional_process as mrp

    tag = f"{multiplier:g}".replace(".", "p")
    carriers = CARRIERS.parent / f"_regimes_{tag}_carriers.yaml"
    carriers.write_text(_scaled_carriers(multiplier))

    config = yaml.safe_load(CONFIG.read_text())
    config["regionalisation"]["mda_tolerance"] = MDA_TOLERANCE
    config["regionalisation"]["global_models"]["settings"] = {"fuel_clearing": SETTINGS}
    target = CONFIG.parent / f"_regimes_{tag}.yaml"
    config_text = yaml.safe_dump(config)
    target.write_text(config_text)

    # Each region's config names the carriers file by relative path, so the scaled copy
    # is pointed at by rewriting that one line in a scratch copy of each region config.
    region_files = []
    try:
        for region in ("region_A", "region_B"):
            source = CONFIG.parent / region / "config.yaml"
            scratch = CONFIG.parent / region / f"_regimes_{tag}.yaml"
            scratch.write_text(
                source.read_text().replace("../energy_carriers_step1.yaml", f"../{carriers.name}")
            )
            region_files.append(scratch)
        config["regionalisation"]["regions"] = {
            region: {"config_file": f"{region}/_regimes_{tag}.yaml"}
            for region in ("region_A", "region_B")
        }
        target.write_text(yaml.safe_dump(config))

        process = mrp.MultiRegionalProcess(str(target))
        process.compute()
        out = process.data["vector_outputs"]

        years = out[f"{REGION}:fuel_market_compliance_price"].index
        prospective = years >= 2024
        compliance = out[f"{REGION}:fuel_market_compliance_price"]
        unmet = out[f"{REGION}:fuel_market_unmet_obligation"]
        demand = out[f"{REGION}:energy_consumption_dropin_fuel"]
        return dict(
            ok=True,
            multiplier=multiplier,
            compliance_max=float(compliance.max()),
            compliance_2050=float(compliance.loc[2050]),
            unmet_share=float(unmet[prospective].sum() / demand[prospective].sum()),
            unmet_years=int((unmet[prospective] > 1e-6 * demand[prospective].max()).sum()),
            delivered_2050=float(out[f"{REGION}:dropin_fuel_mean_mfsp"].loc[2050]),
            rpk_2050=float(out[f"{REGION}:rpk"].loc[2050]),
            co2_2050=float(out[f"{REGION}:co2_emissions_passenger"].loc[2050]),
            share_2050=float(out[f"{REGION}:{PATHWAY}_share_dropin_fuel"].loc[2050]),
            compliance_series=[float(v) for v in compliance[prospective]],
            unmet_series=[float(v) for v in unmet[prospective]],
            years=[int(y) for y in years[prospective]],
        )
    except Exception as exc:  # a point that does not converge is a result
        return dict(ok=False, multiplier=multiplier, error=f"{type(exc).__name__}: {exc}"[:220])
    finally:
        target.unlink(missing_ok=True)
        carriers.unlink(missing_ok=True)
        for path in region_files:
            path.unlink(missing_ok=True)


def run():
    warnings.resetwarnings()
    warnings.simplefilter("ignore")
    logging.disable(logging.INFO)

    results = []
    for multiplier in MULTIPLIERS:
        record = _run_one(multiplier)
        results.append(record)
        if record["ok"]:
            print(
                f"x{multiplier:<5g} compliance max {record['compliance_max']:.5f}  "
                f"unmet {100 * record['unmet_share']:6.3f}%  "
                f"delivered {record['delivered_2050']:.6f}  "
                f"rpk {record['rpk_2050']:.4e}",
                flush=True,
            )
        else:
            print(f"x{multiplier:<5g} FAILED: {record['error'][:90]}", flush=True)
        RESULTS.write_text(json.dumps(results, indent=1))
    return results


def plot(results=None):
    results = results or json.loads(RESULTS.read_text())
    ok = [r for r in results if r["ok"]]
    if not ok:
        print("no converged points to plot")
        return results

    multipliers = [r["multiplier"] for r in ok]
    figure, axes = plt.subplots(1, 3, figsize=(13.5, 4.2), constrained_layout=True)

    buyout = SETTINGS["buyout_price"]
    axes[0].plot(
        multipliers,
        [r["compliance_max"] for r in ok],
        "-o",
        color="#a93226",
        markersize=4,
        label="peak over the horizon",
    )
    axes[0].plot(
        multipliers,
        [r["compliance_2050"] for r in ok],
        "--s",
        color="#1f5f8b",
        markersize=4,
        label="2050",
    )
    axes[0].axhline(buyout, linestyle=":", color="0.45", linewidth=1.2)
    axes[0].annotate(
        "release price caps the dual",
        xy=(multipliers[0], buyout),
        xytext=(3, 4),
        textcoords="offset points",
        fontsize=8,
        color="0.35",
    )
    axes[0].annotate(
        "and then FALLS: a higher obligation\nearlier leaves a bigger base, so the\nlast step costs less",
        xy=(multipliers[-1], ok[-1]["compliance_max"]),
        xytext=(multipliers[1], 0.23),
        fontsize=8,
        color="0.3",
        ha="left",
        va="top",
        arrowprops=dict(
            arrowstyle="->", color="0.45", linewidth=0.9, connectionstyle="arc3,rad=-0.25"
        ),
    )
    axes[0].set_ylabel("compliance price")
    axes[0].set_title("What compliance costs", fontsize=10)
    axes[0].legend(frameon=False, fontsize=8, loc="lower right")

    # The buy-out never engages anywhere in this sweep: `unmet` is at solver noise,
    # around 1e-9 % of demand. Plotting it would draw a shape out of rounding error --
    # the first version of this figure did exactly that, on a 1e-9 axis. What is worth
    # drawing instead is HOW the obligation is met, which is entirely by volume.
    required = [min(100.0, 70.0 * m) for m in multipliers]
    achieved = [r["share_2050"] for r in ok]
    axes[1].plot(multipliers, required, "--", color="0.45", linewidth=1.4, label="obligation, 2050")
    axes[1].plot(
        multipliers, achieved, "-o", color="#2f6b4f", markersize=4, label="eligible fuel delivered"
    )
    axes[1].axhline(100.0, color="0.75", linestyle=":", linewidth=1.2)
    worst = max(100 * r["unmet_share"] for r in ok)
    axes[1].annotate(
        f"the buy-out never engages:\nunmet $\\leq$ {worst:.0e} % of demand,\nwhich is solver noise",
        xy=(multipliers[0], 55),
        fontsize=8.5,
        color="0.3",
    )
    axes[1].set_ylabel("% of drop-in energy, 2050")
    axes[1].set_ylim(0, 115)
    axes[1].set_title("How the obligation is met: by volume, throughout", fontsize=10)
    axes[1].legend(frameon=False, fontsize=8, loc="lower right")

    reference = ok[[r["multiplier"] for r in ok].index(1.0)] if 1.0 in multipliers else ok[0]
    axes[2].plot(
        multipliers,
        [100 * (r["delivered_2050"] / reference["delivered_2050"] - 1) for r in ok],
        "-o",
        color="#1f5f8b",
        markersize=4,
        label="delivered price",
    )
    axes[2].plot(
        multipliers,
        [100 * (r["rpk_2050"] / reference["rpk_2050"] - 1) for r in ok],
        "--s",
        color="#2f6b4f",
        markersize=4,
        label="traffic",
    )
    axes[2].axhline(0.0, color="0.7", linewidth=1, linestyle=":")
    # Above x1.43 the 2050 obligation clips at 100 %, so every 2050 quantity stops
    # moving and the remaining information is in the earlier years, not here.
    axes[2].axvline(100.0 / 70.0, color="0.75", linestyle=":", linewidth=1.2)
    axes[2].annotate(
        "beyond here the 2050\nobligation is already 100 %,\nso 2050 stops moving",
        xy=(100.0 / 70.0, 5),
        xytext=(6, 0),
        textcoords="offset points",
        fontsize=8,
        color="0.35",
    )
    axes[2].set_ylabel("vs the obligation as written, %")
    axes[2].set_title("What the chain does about it", fontsize=10)
    axes[2].legend(frameon=False, fontsize=8, loc="center left")

    for axis in axes:
        axis.set_xlabel("multiplier on the obligation")
        axis.spines[["top", "right"]].set_visible(False)
    figure.suptitle(
        "Measurement 4.5.2: price regimes across the obligation's reachability boundary, "
        "coupled, region A",
        fontsize=11,
    )

    FIGURES.mkdir(parents=True, exist_ok=True)
    target = FIGURES / "price_regimes.png"
    figure.savefig(target, dpi=150)
    plt.close(figure)
    print(f"wrote {target}")
    return results


if __name__ == "__main__":
    plot() if "--plot" in sys.argv else plot(run())
