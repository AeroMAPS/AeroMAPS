"""Brief 1 deliverable: p_k against k, three stiffness levels."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

OUT = "spike_unified_mda/brief1_out"
BASE = 150.0

CASES = [
    ("0.3_g4.0", r"$\gamma=4$  — below the boundary", "#2f6f4e"),
    ("0.3_g8.0", r"$\gamma=8$  — just above", "#b3541e"),
    ("0.3_g16.0", r"$\gamma=16$ — far above", "#8c2f39"),
]

fig, axes = plt.subplots(2, 3, figsize=(15, 7.2), sharex=True)

for col, (tag, title, colour) in enumerate(CASES):
    em = pd.read_csv(f"{OUT}/emitted_s{tag}.csv")
    em = em[em.region == "region_A"].reset_index(drop=True)
    res = pd.read_csv(f"{OUT}/residual_s{tag}.csv")

    ax = axes[0, col]
    ax.plot(range(1, len(em) + 1), em.p_2050, lw=1.1, color=colour, marker="o", ms=2.4)
    ax.axhline(BASE, ls=":", lw=1, color="#666")
    ax.text(
        len(em) * 0.99,
        BASE,
        "floor = base_price ",
        ha="right",
        va="bottom",
        fontsize=7.5,
        color="#666",
    )
    ax.set_yscale("log")
    ax.set_title(title, fontsize=11)
    ax.set_ylabel(r"$p_k$ at 2050  [EUR/t]" if col == 0 else "")
    ax.grid(alpha=0.25, lw=0.5)

    ax2 = axes[1, col]
    ax2.plot(range(1, len(res) + 1), res.residual, lw=1.1, color=colour)
    ax2.axhline(1e-10, ls="--", lw=1, color="#444")
    ax2.set_yscale("log")
    ax2.set_xlabel("Gauss-Seidel iteration $k$")
    ax2.set_ylabel("MDA residual" if col == 0 else "")
    ax2.grid(alpha=0.25, lw=0.5)

    # Converged, or locked onto a limit cycle?
    label = None
    if res.residual.iloc[-1] <= 1e-10:
        label = f"converged in {len(res)} iterations"
    else:
        tail = em.p_2050.to_numpy()[-24:]
        for period in range(1, 13):
            a, b = tail[-2 * period : -period], tail[-period:]
            if len(a) == period and abs(a - b).max() / max(abs(b).max(), 1e-12) < 1e-6:
                label = f"period-{period} limit cycle"
                break
    if label:
        ax.text(
            0.03,
            0.90,
            label,
            transform=ax.transAxes,
            va="top",
            fontsize=9,
            color=colour,
            bbox=dict(fc="white", ec=colour, lw=0.7, alpha=0.9, pad=2.5),
        )

fig.suptitle(
    "Spike market price at 2050, plain Gauss-Seidel, stiffness = 0.3\n"
    "the iterates never grow without bound — beyond the boundary they lock onto a periodic orbit",
    fontsize=12,
)
fig.tight_layout(rect=(0, 0, 1, 0.93))
fig.savefig(f"{OUT}/pk_trajectories.png", dpi=160)
print(f"wrote {OUT}/pk_trajectories.png")

# --- second figure: the accelerated 0.3/8 case, raw vs bounded ------------------
fig2, axes2 = plt.subplots(1, 2, figsize=(12, 4.4))

raw_e = pd.read_csv(f"{OUT}/emitted_s0.3_g8.0_accel.csv")
raw_r = pd.read_csv(f"{OUT}/received_s0.3_g8.0_accel.csv")
raw_e = raw_e[raw_e.region == "region_A"].reset_index(drop=True)
raw_r = raw_r[raw_r.region == "region_A"].reset_index(drop=True)

ax = axes2[0]
ax.plot(
    raw_e.k,
    raw_e.p_2050.abs(),
    lw=1.1,
    color="#b3541e",
    marker="o",
    ms=2.6,
    label="emitted by SpikeFuelMarket",
)
ax.plot(
    raw_r.k,
    raw_r.p_2050.abs(),
    lw=1.1,
    color="#31558a",
    marker="s",
    ms=2.6,
    label="received after Alternate2Delta",
)
neg = raw_r[raw_r.p_2050 < 0]
ax.scatter(
    neg.k,
    neg.p_2050.abs(),
    s=52,
    facecolors="none",
    edgecolors="crimson",
    lw=1.4,
    zorder=5,
    label="received value is NEGATIVE",
)
ax.set_yscale("log")
ax.set_xlabel("iteration $k$")
ax.set_ylabel(r"$|p_k|$ at 2050  [EUR/t]")
ax.set_title(r"$\gamma=8$, acceleration on, no guard $\rightarrow$ NaN", fontsize=11)
ax.legend(fontsize=8, loc="lower right")
ax.grid(alpha=0.25, lw=0.5)

bnd_e = pd.read_csv(f"{OUT}/emitted_s0.3_g8.0_accel_bounded.csv")
bnd_e = bnd_e[bnd_e.region == "region_A"].reset_index(drop=True)
sat = pd.read_csv(f"{OUT}/sat_s0.3_g8.0_accel_bounded.csv")

ax = axes2[1]
ax.plot(bnd_e.k, bnd_e.p_2050, lw=1.1, color="#2f6f4e", marker="o", ms=2.4)
last_sat = int(sat.k.max())
ax.axvspan(0, last_sat, color="#c8b26b", alpha=0.28, lw=0)
ax.text(
    last_sat,
    ax.get_ylim()[1],
    f"  bound active, k ≤ {last_sat}",
    fontsize=8.5,
    va="top",
    color="#6b5a1e",
)
ax.set_yscale("log")
ax.set_xlabel("iteration $k$")
ax.set_ylabel(r"$p_k$ at 2050  [EUR/t]")
ax.set_title(r"$\gamma=8$, same run with a 0.1x–20x guard $\rightarrow$ converges", fontsize=11)
ax.grid(alpha=0.25, lw=0.5)

fig2.suptitle(
    "The domain exit is transient: the guard binds for 17 iterations, then releases", fontsize=12
)
fig2.tight_layout(rect=(0, 0, 1, 0.9))
fig2.savefig(f"{OUT}/domain_exit.png", dpi=160)
print(f"wrote {OUT}/domain_exit.png")
