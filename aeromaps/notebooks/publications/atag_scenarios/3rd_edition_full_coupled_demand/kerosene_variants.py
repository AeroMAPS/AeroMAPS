"""Rerun the uncoupled S0, S1 and S2 at the three kerosene price levels.

The published reproduction carries the report-era kerosene price. Where costs are
compared with the coupled runs, the uncoupled scenarios need the same kerosene
price uncertainty the coupled pathways carry: the lower quartile, the mean and the
upper quartile of the weekly EIA spot price over the last 20 years, held flat from
2026 (see ``make_energy_files.py``). Traffic is exogenous in these runs, so the
price moves costs only; emissions and warming are unchanged.

Only the series the figures read are kept, in one tidy table:
``data_outputs/kerosene_variants.csv.gz``.

Run from this directory::

    python kerosene_variants.py
"""

from pathlib import Path

import pandas as pd

from aeromaps import create_process
from aeromaps.utils.scenarios import find_scenario
from make_energy_files import KEROSENE_LEVELS
from ssp_runs import set_kerosene_level

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "data_outputs" / "kerosene_variants.csv.gz"

SCENARIOS = {
    "S0": find_scenario("atag_3rd_edition_light").config_dir / "config_s0.yaml",
    "S1": find_scenario("atag_3rd_edition_full").config_dir / "config_s1.yaml",
    "S2": find_scenario("atag_3rd_edition_full").config_dir / "config_s2.yaml",
}
SERIES = (
    "non_discounted_net_energy_expenses",
    "doc_net_energy_per_rpk_mean",
    "fossil_kerosene_mean_mfsp",
)


def main():
    rows = []
    for scenario, config in SCENARIOS.items():
        for case, level in KEROSENE_LEVELS.items():
            print(f"computing {scenario} at the {case} kerosene price ...", flush=True)
            process = create_process(configuration_file=str(config))
            set_kerosene_level(process, level)
            process.compute()
            vectors = process.data["vector_outputs"]
            for year in vectors.index:
                row = {"scenario": scenario, "kerosene": case, "year": int(year)}
                row.update({name: float(vectors.loc[year, name]) for name in SERIES})
                rows.append(row)
    table = pd.DataFrame(rows)
    table.to_csv(OUTPUT, index=False)
    print(f"wrote {OUTPUT.name}: {len(table)} rows")


if __name__ == "__main__":
    main()
