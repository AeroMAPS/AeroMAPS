"""Shared machinery for the coupled-demand SSP runs.

The coupled scenario is run twice, under the two readings of the same published SAF
trajectory, because the reports do not say which one they mean:

``quantity``
    The mandate fixes a SAF *volume*. If demand falls, that volume is unchanged, so the
    blend share rises on its own -- and at a large enough demand response it saturates,
    with SAF displacing the entire drop-in fleet.

``share``
    The mandate fixes a SAF *percentage*. If demand falls, SAF volume falls with it and
    the blend share is unchanged. This is how real mandates (ReFuelEU Aviation, the UK
    and Brazilian schemes) are written.

Both are defensible readings of *Waypoint 2050*, which reports SAF as a 2050 volume
without stating what would happen to it under lower traffic. They give materially
different answers once demand is price-elastic, so both are carried explicitly rather
than one being chosen silently.

A third entry, ``nosaf``, is not another reading of the same question -- it is a
fuel-only counterfactual paired against ``share``: the same demand model and the
same background pathway, with every drop-in SAF mandate zeroed by
``make_energy_files.py`` so fossil kerosene supplies the whole drop-in fleet. It
lets the demand response be read against its own fuel baseline, which is a
sharper comparison than against the exogenous forecast alone, since the
exogenous forecast is not run under the same cost model at all.
"""

from pathlib import Path

from aeromaps import create_process

HERE = Path(__file__).resolve().parent

# All REMIND-MAgPIE 1.5 under SSP2, spanning roughly a factor of twenty-four in the
# 2050 carbon price (1033 / 212 / 43 US$2010 per tCO2).
#
# SSP2-34 is dropped: at 89 US$2010/tCO2 it sits between 2.6 and 4.5 without changing
# the conclusion, and three pathways read more clearly. SSP2-19 is kept because it is
# the only one on the far side of the volume/share pivot -- it is where a fixed SAF
# volume leaves *less* residual CO2 than a fixed share, so without it the two mandate
# readings converge but never actually cross.
PATHWAYS = ["SSP2-19", "SSP2-26", "SSP2-45"]

MANDATES = {
    "quantity": {
        "config": "./config_files/config_s1.yaml",
        "suffix": "",
        "label": "fixed SAF volume",
    },
    "share": {
        "config": "./config_files/config_s1_share.yaml",
        "suffix": "_share",
        "label": "fixed SAF share",
    },
    # Not a third mandate reading -- the fuel-only counterfactual paired
    # against "share": same demand model, same background pathway, same
    # everything except the energy carrier file, where make_energy_files.py
    # has zeroed every drop-in SAF mandate. Comparing the demand response
    # against this rather than only against the exogenous forecast isolates
    # what SAF's own cost does to traffic.
    "nosaf": {
        "config": "./config_files/config_s1_nosaf.yaml",
        "suffix": "_nosaf",
        "label": "no SAF",
    },
}


def build(pathway, ar6_data, ar6_years, mandate="quantity"):
    """A coupled process for one SSP pathway under one mandate reading.

    Population, GDP per capita and the carbon price all come from the same pathway, so
    each run is internally consistent: a world that prices carbon aggressively is also
    the world whose income trajectory the demand model sees.
    """
    process = create_process(configuration_file=MANDATES[mandate]["config"])
    for parameter, values in (
        ("population", ar6_data["population"][pathway]),
        ("gdp_per_capita", ar6_data["gdp_per_capita"][pathway]),
        ("carbon_tax", ar6_data["carbon_tax"][pathway]),
        ("exogenous_carbon_price", ar6_data["carbon_tax"][pathway]),
    ):
        setattr(process.parameters, f"{parameter}_reference_years", ar6_years)
        setattr(process.parameters, f"{parameter}_reference_years_values", values)
    return process


def output_path(pathway, mandate="quantity"):
    stem = pathway.lower().replace("-", "_") + MANDATES[mandate]["suffix"]
    return HERE / "data_outputs" / f"{stem}.json"


def run_all(ar6_data, ar6_years, mandate="quantity", write=True):
    """Compute every pathway under one mandate reading."""
    processes = {}
    for pathway in PATHWAYS:
        print(f"computing {pathway} ({MANDATES[mandate]['label']}) ...", flush=True)
        process = build(pathway, ar6_data, ar6_years, mandate)
        process.compute()
        if write:
            process.write_json(str(output_path(pathway, mandate)))
        processes[pathway] = process
    return processes


def summarise(processes, mandate="quantity"):
    """One row per pathway: demand response and the resulting SAF blend."""
    import pandas as pd

    rows = []
    for pathway, process in processes.items():
        vector = process.data["vector_outputs"]
        climate = process.data["climate_outputs"]
        coupled = vector.loc[2050, "rpk"]
        exogenous = vector.loc[2050, "rpk_no_elasticity"]
        dropin = vector.loc[2050, "energy_consumption_dropin_fuel"]
        fossil = vector.loc[2050, "dropin_fuel_fossil_energy_consumption"]
        rows.append(
            {
                "pathway": pathway,
                "mandate": MANDATES[mandate]["label"],
                "2050 RPK [T]": coupled / 1e12,
                "exogenous RPK [T]": exogenous / 1e12,
                "demand response [%]": 100 * (coupled / exogenous - 1),
                "2050 SAF share [%]": 100 * (1 - fossil / dropin) if dropin else float("nan"),
                "2050 CO2 [Mt]": climate.loc[2050, "co2_emissions"],
            }
        )
    return pd.DataFrame(rows).set_index("pathway")
