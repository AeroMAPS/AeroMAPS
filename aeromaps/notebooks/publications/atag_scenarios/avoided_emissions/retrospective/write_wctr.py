"""Write the WCTR counterfactual next to the other retrospective outputs.

Run from anywhere::

    python write_wctr.py

It writes ``data_outputs/r1_wctr.json`` (the run) and ``data_outputs/series_wctr.csv``
(the curves the document draws). Nothing else in ``data_outputs/`` is touched, so the
committed R0, R1 and R2 stay exactly as they were.
"""

import json
from pathlib import Path

import pandas as pd

from models import frozen_baseline as fb

OUTPUTS = Path(__file__).resolve().parent / "data_outputs"


def main():
    published = fb.frozen_baseline(frozen_factors=fb.FACTORS)
    wctr = fb.wctr_counterfactual()
    years = published["years"]

    series = pd.DataFrame(
        {
            "observed": published["observed"],
            "report_method": published["counterfactual"],
            "wctr": wctr["counterfactual"],
        },
        index=pd.Index(years, name="year"),
    )
    series.to_csv(OUTPUTS / "series_wctr.csv")

    record = {
        "config": {
            **wctr["config"],
            "frozen_factors": list(wctr["config"]["frozen_factors"]),
            "window": list(wctr["config"]["window"]),
        },
        "elasticity": wctr["elasticity"],
        "delay_years": wctr["delay_years"],
        "elasticity_basis": "energy cost per RPK",
        "avoided_gt": wctr["avoided_gt"],
        "report_method_avoided_gt": published["avoided_gt"],
        "reduction_pct": 100.0 * (1.0 - wctr["avoided_gt"] / published["avoided_gt"]),
        "demand_ratio": {
            str(int(y)): float(r)
            for y, r in zip(years, wctr["demand_ratio"])
            if int(y) in (1990, 2000, 2010, 2019, 2023)
        },
        "energy_cost_ratio": {
            str(int(y)): float(r)
            for y, r in zip(years, wctr["price_ratio"])
            if int(y) in (1990, 2000, 2010, 2019, 2023)
        },
        "model_years": [wctr["model_years"][0], wctr["model_years"][-1]],
    }
    with (OUTPUTS / "r1_wctr.json").open("w", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2)
    print(
        "avoided: %.2f Gt against %.2f Gt (%.0f %% lower)"
        % (wctr["avoided_gt"], published["avoided_gt"], record["reduction_pct"])
    )


if __name__ == "__main__":
    main()
