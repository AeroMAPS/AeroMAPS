"""Brief 1, question 1 (continued): decompose the airfare at the iteration it goes negative.

`RPKElasticity` manufactures the NaN, but it is only the messenger: it raises a
NEGATIVE `airfare_per_rpk` to a fractional power. This script finds which cost
term drives the airfare below zero.
"""

import logging
import os
import sys
import warnings

import pandas as pd

warnings.filterwarnings("ignore")
logging.disable(logging.INFO)

CONFIG = "spike_unified_mda/scenario/regionalisation_spike.yaml"
PROJ = 2025
YEAR = 2050

os.environ["SPIKE_STIFFNESS"] = str(sys.argv[1] if len(sys.argv) > 1 else 0.3)
os.environ["SPIKE_GAMMA"] = str(sys.argv[2] if len(sys.argv) > 2 else 8.0)

from aeromaps.models.impacts.costs.airlines.total_airline_cost_and_airfare import (  # noqa: E402
    PassengerAircraftTotalCost,
)
from aeromaps.models.impacts.costs.airlines.direct_operating_costs import (  # noqa: E402
    PassengerAircraftDocEnergyCarbonTax,
)
from aeromaps.core.multi_regional_process import MultiRegionalProcess  # noqa: E402
from spike_unified_mda.mda_settings import rebuild  # noqa: E402

TERMS = [
    "doc_non_energy_per_ask_mean",
    "doc_energy_per_ask_mean",
    "non_operating_cost_per_ask",
    "indirect_operating_cost_per_ask",
    "noc_carbon_offset_per_ask",
    "operational_efficiency_cost_non_energy_per_ask",
    "load_factor_cost_non_energy_per_ask",
    "doc_carbon_tax_lowering_offset_per_ask_mean",
    "passenger_tax_per_ask",
]

COST = {"run": 0, "rows": [], "dumped": False}
TAX = {"rows": []}

_orig_cost = PassengerAircraftTotalCost.compute
_orig_tax = PassengerAircraftDocEnergyCarbonTax.compute


def probed_cost(self, input_data):
    COST["run"] += 1
    out = _orig_cost(self, input_data)
    tc = out["total_cost_per_ask"]
    proj = tc.loc[tc.index >= PROJ].to_numpy(dtype=float)
    row = {"run": COST["run"], "total_cost_per_ask_2050": float(tc.loc[YEAR])}
    for t in TERMS:
        v = input_data[t]
        row[t] = float(v.loc[YEAR]) if isinstance(v, pd.Series) else float(v)
    COST["rows"].append(row)

    if (proj < 0).any() and not COST["dumped"]:
        COST["dumped"] = True
        years = tc.loc[tc.index >= PROJ].index.to_numpy()
        neg = proj < 0
        print("\n" + "=" * 92)
        print(
            f"FIRST NEGATIVE total_cost_per_ask -- compute() call #{COST['run']}, "
            f"{int(neg.sum())} years, first {years[neg][0]}"
        )
        print("=" * 92)
        print(f"\ncost decomposition at {YEAR} [EUR/ASK]:")
        total = 0.0
        for t in TERMS:
            v = row[t]
            total += v
            print(f"  {t:<50} {v:>18.6g}")
        print(f"  {'-' * 50} {'-' * 18}")
        print(f"  {'sum (= total_cost_per_ask)':<50} {total:>18.6g}")
        print("=" * 92 + "\n")
    return out


def probed_tax(self, input_data):
    out = _orig_tax(self, input_data)
    co2 = input_data["co2_emissions"]
    off = input_data["carbon_offset"]
    co2s = co2.loc[self.historic_start_year : self.end_year]
    ratio = (co2s - off.fillna(0)) / co2s
    TAX["rows"].append(
        {
            "co2_emissions_2050": float(co2s.loc[YEAR]),
            "carbon_offset_2050": float(off.fillna(0).loc[YEAR]),
            "carbon_remaining_ratio_2050": float(ratio.loc[YEAR]),
            "doc_energy_carbon_tax_per_ask_mean_2050": float(
                out["doc_energy_carbon_tax_per_ask_mean"].loc[YEAR]
            ),
            "doc_carbon_tax_lowering_offset_per_ask_mean_2050": float(
                out["doc_carbon_tax_lowering_offset_per_ask_mean"].loc[YEAR]
            ),
        }
    )
    return out


PassengerAircraftTotalCost.compute = probed_cost
PassengerAircraftDocEnergyCarbonTax.compute = probed_tax

p = MultiRegionalProcess(CONFIG)
p.on_mda_failure = "warn"
rebuild(p)
p.compute()

cost = pd.DataFrame(COST["rows"])
tax = pd.DataFrame(TAX["rows"])
os.makedirs("spike_unified_mda/brief1_out", exist_ok=True)
cost.to_csv("spike_unified_mda/brief1_out/cost_terms.csv", index=False)
tax.to_csv("spike_unified_mda/brief1_out/carbon_tax_terms.csv", index=False)

print("carbon-tax offset chain at 2050, per compute() call (both regions interleaved):")
print(
    f"{'#':>4} {'co2_emissions':>16} {'carbon_offset':>16} {'remaining_ratio':>17} "
    f"{'tax/ASK':>13} {'offset tax/ASK':>16}"
)
for i, r in tax.head(40).iterrows():
    print(
        f"{i + 1:>4} {r['co2_emissions_2050']:>16.6g} {r['carbon_offset_2050']:>16.6g} "
        f"{r['carbon_remaining_ratio_2050']:>17.6g} "
        f"{r['doc_energy_carbon_tax_per_ask_mean_2050']:>13.6g} "
        f"{r['doc_carbon_tax_lowering_offset_per_ask_mean_2050']:>16.6g}"
    )
