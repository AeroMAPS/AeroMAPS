"""
calibrate_fleet
===============
Fit the bottom-up fleet of each ATAG scenario to its technology-only run.

The fleet is deliberately minimal. Each market has the old and the recent reference
aircraft, and one new aircraft entering service in ``ENTRY_YEAR``. There is no
continuous improvement and no further generation. Two things are fitted:

1. The recent reference aircraft's energy per ASK relative to the old one, per market,
   on T1 (the renewal-only run, the same for every scenario). Stored in
   ``renewal_fit.json``.
2. One percentage, ``consumption_evolution``, applied to the new aircraft of every
   market with respect to the recent reference. It is fitted per scenario on the
   technology-only run that carries its technology: T2 for S0, T3 for S1 and T4 for S2. The
   energy per ASK of a market is close to linear in it, so two runs give the fit and a
   third checks it.

In S2, a battery-electric short-range aircraft with the same gain enters in
``ENTRY_YEAR`` too, with a fleet share fitted so that its 2050 share of the short-range
ASK matches the top-down run.

Fitting S0 and S2 the same way takes about twenty minutes, so by default they are derived
from S1 without any run (see ``derive``). ``renewal`` and ``s1`` fit with runs.

Run from this directory, after ``build_scenarios.py``::

    python calibrate_fleet.py [renewal] [s1] [derive]
"""

import json
import sys
from pathlib import Path

import numpy as np
import yaml

import aeromaps.utils.yaml  # noqa: F401  registers the custom data type representer
from aeromaps import create_process
from aeromaps.utils.scenarios import find_scenario, scenarios_root

HERE = Path(__file__).parent
ATAG = HERE.parent
TARGET = scenarios_root() / "atag_3rd_edition_bottom_up"
DEFAULT_FLEET = (
    Path(find_scenario("atag_3rd_edition_full").path).parents[1] / "data" / "default_fleet"
)
RENEWAL_FILE = TARGET / "data_inputs" / "renewal_fit.json"
FIT_FILE = TARGET / "data_inputs" / "new_aircraft_fit.json"

MARKETS = ("short_range", "medium_range", "long_range")
ENTRY_YEAR = 2035
YEARS = np.arange(2024, 2051)

TECHNOLOGY_RUN = {"s0": "t2", "s1": "t3", "s2": "t4"}
OUTPUTS = {
    run: ATAG / "3rd_edition_full" / "data_outputs" / f"{run}.json"
    for run in ("t1", "t2", "t3", "t4", "s2")
}

CONVENTIONAL = {
    "short_range": ("sr_conventional_nb", "sr_nb_2035"),
    "medium_range": ("mr_conventional_nb", "mr_nb_2035"),
    "long_range": ("lr_conventional_wb", "lr_wb_2035"),
}


def top_down_intensity(run):
    """Drop-in energy per ASK without operations of each market, 2024-2050."""
    outputs = json.loads(OUTPUTS[run].read_text(encoding="utf-8"))["vector_outputs"]
    return {
        market: np.asarray(
            outputs[f"energy_per_ask_without_operations_{market}_dropin_fuel"], dtype=float
        )[YEARS - 2000]
        for market in MARKETS
    }


def top_down_electric_share_2050():
    outputs = json.loads(OUTPUTS["s2"].read_text(encoding="utf-8"))["vector_outputs"]
    return float(outputs["ask_short_range_electric_share"][2050 - 2000])


def load_renewal():
    """Recent-reference energy per ASK as a fraction of the old one, per market."""
    if RENEWAL_FILE.exists():
        return json.loads(RENEWAL_FILE.read_text(encoding="utf-8"))
    return {market: 0.8 for market in MARKETS}


def build_fleet(name, evolution, electric_share=0.0, renewal=None):
    """Write the fleet and inventory of scenario ``name``.

    ``evolution`` is the energy gain [%] of every new aircraft with respect to the
    recent reference (negative is an improvement).
    """
    renewal = renewal or load_renewal()
    inventory = yaml.safe_load((DEFAULT_FLEET / "aircraft_inventory.yaml").read_text("utf-8"))
    references = {a["id"]: a for a in inventory["reference_aircraft"]}
    cards = {a["id"]: a for a in inventory["aircraft"]}

    subcategories, categories, aircraft, used = [], [], [], []
    for market in MARKETS:
        conventional, card_id = CONVENTIONAL[market]
        old = references[f"{conventional}_old"]["parameters"]["energy_per_ask"]
        recent = references[f"{conventional}_recent"]["parameters"]
        recent["energy_per_ask"] = old * float(renewal[market])
        recent.pop("continuous_improvement_factor_energy", None)

        def new_card(card_id_, name_, extra_card=None, **overrides):
            card = json.loads(json.dumps(cards[card_id]))
            card.update(id=card_id_, name=name_, reference_aircraft=f"{conventional}_recent")
            card.update(extra_card or {})
            card["parameters"].pop("energy_per_ask", None)
            card["parameters"].update(
                entry_into_service_year=ENTRY_YEAR, consumption_evolution=float(evolution)
            )
            card["parameters"].update(overrides)
            return card

        electric = market == "short_range" and electric_share > 0
        aircraft.append(new_card(f"{conventional}_new", f"New {market.replace('_', ' ')} aircraft"))
        refs = {"old_ref": f"{conventional}_old", "recent_ref": f"{conventional}_recent"}
        subcategories.append(
            {
                "id": conventional,
                "name": f"{market.replace('_', ' ')} conventional",
                "share": 100.0 - (electric_share if electric else 0.0),
                "reference_aircraft": refs,
                "aircraft": [f"{conventional}_new"],
            }
        )
        subs = [conventional]
        if electric:
            aircraft.append(
                new_card(
                    "sr_electric",
                    "New short-range battery-electric aircraft",
                    {"energy_type": "ELECTRIC"},
                    hybridization_factor=1.0,
                    soot_evolution=-100.0,
                    nox_evolution=-100.0,
                )
            )
            subcategories.append(
                {
                    "id": "sr_electric",
                    "name": "short range battery-electric",
                    "share": electric_share,
                    "reference_aircraft": refs,
                    "aircraft": ["sr_electric"],
                }
            )
            subs.append("sr_electric")
        categories.append(
            {
                "market_served": market,
                "parameters": {"life": 25, "limit": 2},
                "calibration_subcategory": conventional,
                "subcategories": subs,
            }
        )
        used += list(refs.values())

    inputs = TARGET / "data_inputs"
    (inputs / f"{name}_fleet.yaml").write_text(
        yaml.safe_dump({"subcategories": subcategories, "categories": categories}, sort_keys=False),
        encoding="utf-8",
    )
    (inputs / f"{name}_aircraft_inventory.yaml").write_text(
        yaml.safe_dump(
            {"reference_aircraft": [references[r] for r in used], "aircraft": aircraft},
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def run(name):
    process = create_process(configuration_file=str(TARGET / "config_files" / f"config_{name}.yaml"))
    process.compute()
    return process.data["vector_outputs"]


def market_intensity(vector, market):
    """Share-weighted energy per ASK of a market over its energy types."""
    total = 0.0
    for kind in ("dropin_fuel", "hydrogen", "electric"):
        share = vector[f"ask_{market}_{kind}_share"].loc[YEARS].to_numpy() / 100.0
        intensity = vector[f"energy_per_ask_without_operations_{market}_{kind}"].loc[YEARS]
        total = total + share * intensity.fillna(0.0).to_numpy()
    return total


def stacked_error(vector, target):
    return np.concatenate([market_intensity(vector, m) / target[m] - 1.0 for m in MARKETS])


def fit_renewal():
    """Fit the recent/old energy ratio of each market to T1, with no new aircraft."""
    target = top_down_intensity("t1")
    renewal = load_renewal()
    # The mean energy per ASK is linear in the ratio, market by market: two runs.
    probes = {}
    for ratio in (0.7, 0.9):
        build_fleet("s1", 0.0, 0.0, {m: ratio for m in MARKETS})
        vector = run("s1")
        probes[ratio] = {m: market_intensity(vector, m) for m in MARKETS}
    for market in MARKETS:
        slope = (probes[0.9][market] - probes[0.7][market]) / 0.2
        offset = probes[0.7][market] - slope * 0.7
        renewal[market] = float(np.sum(slope * (target[market] - offset)) / np.sum(slope**2))
    RENEWAL_FILE.write_text(json.dumps(renewal, indent=2), encoding="utf-8")
    build_fleet("s1", 0.0, 0.0, renewal)
    error = stacked_error(run("s1"), target)
    print("  renewal ratios", renewal, "rms error %.2f %%" % (100 * np.sqrt(np.mean(error**2))))


def fit(name):
    """Fit the new aircraft's gain on the technology-only run, then check it."""
    target = top_down_intensity(TECHNOLOGY_RUN[name])
    share = 0.0
    if name == "s2":
        # The 2050 electric share is close to linear in the fleet share: one probe.
        probe = 40.0
        build_fleet(name, -20.0, probe)
        reached = run(name)["ask_short_range_electric_share"].loc[2050]
        share = probe * top_down_electric_share_2050() / max(float(reached), 1e-6)
        print(f"  electric fleet share {share:.1f} % (probe reached {reached:.1f} %)")

    # The mean energy per ASK is close to linear in the gain: two runs fix it.
    gains = (-10.0, -40.0)
    errors = []
    for gain in gains:
        build_fleet(name, gain, share)
        errors.append(stacked_error(run(name), target))
    slope = (errors[1] - errors[0]) / (gains[1] - gains[0])
    gain = gains[0] - float(np.sum(slope * errors[0]) / np.sum(slope**2))

    build_fleet(name, gain, share)
    error = stacked_error(run(name), target)
    print(
        f"  new aircraft {gain:.2f} % vs recent reference; error vs "
        f"{TECHNOLOGY_RUN[name].upper()}: rms {100 * np.sqrt(np.mean(error**2)):.2f} %, "
        f"worst {100 * np.abs(error).max():.2f} %"
    )
    fits = json.loads(FIT_FILE.read_text("utf-8")) if FIT_FILE.exists() else {}
    fits[name] = {"consumption_evolution": gain, "electric_share": share}
    FIT_FILE.write_text(json.dumps(fits, indent=2), encoding="utf-8")


def derive():
    """S0 and S2 from the S1 fit, without any run.

    S0 is a degraded S1: the new aircraft's gain is S1's scaled by the ratio of the
    energy per ASK reductions that T2 and T3 achieve by 2050 over T1. S2 keeps S1's
    efficiency and adds the short-range battery-electric aircraft, whose fleet share is
    the 2050 electric ASK share of the scenario (70 % in the inputs).
    """
    fits = json.loads(FIT_FILE.read_text("utf-8"))
    final = {
        run: np.mean(
            [top_down_intensity(run)[m][-1] / top_down_intensity("t1")[m][-1] for m in MARKETS]
        )
        for run in ("t2", "t3")
    }
    scale = (1.0 - final["t2"]) / (1.0 - final["t3"])
    s1 = fits["s1"]["consumption_evolution"]
    fits["s0"] = {"consumption_evolution": s1 * scale, "electric_share": 0.0}
    fits["s2"] = {"consumption_evolution": s1, "electric_share": 70.0}
    FIT_FILE.write_text(json.dumps(fits, indent=2), encoding="utf-8")
    print(f"  S0 gain {fits['s0']['consumption_evolution']:.2f} % (scale {scale:.3f} of S1's)")


def write_fleets():
    fits = json.loads(FIT_FILE.read_text("utf-8"))
    for name, fit_ in fits.items():
        build_fleet(name, fit_["consumption_evolution"], fit_["electric_share"])


if __name__ == "__main__":
    for step in sys.argv[1:] or ["derive"]:
        print(step)
        if step == "renewal":
            fit_renewal()
        elif step == "derive":
            derive()
            write_fleets()
        else:
            fit(step)
