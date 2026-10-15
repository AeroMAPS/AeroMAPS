# ReFuelEU optimisation — scenario dataset

The results behind the paper's figures: 78 AeroMAPS runs of EU aviation, 2000–2050.
74 of them are optimisations of the biofuel and electrofuel mandates; the other 4 are
fixed-mandate references (fossil business-as-usual, the ReFuelEU regulation). Every
figure of `02_results.ipynb` is drawn from these files and nothing else.

## Files

| file | one row per | content |
|---|---|---|
| `scenarios.csv` | scenario | what the run is, its parameters, whether its optimum is feasible |
| `timeseries.csv` | scenario × variable | yearly values 2000–2050, IAMC layout |
| `variables.csv` | variable | unit and description |
| `optima.csv` | scenario × quantity × year | each optimisation's design variables and constraint values at its optimum |

`timeseries.csv` uses the IAMC layout (`model, scenario, region, variable, unit`, then one
column per year), so it loads directly into [pyam](https://pyam-iamc.readthedocs.io):

```python
import pandas as pd
ts = pd.read_csv("timeseries.csv")
meta = pd.read_csv("scenarios.csv", index_col="scenario")

# or, with pyam
import pyam
df = pyam.IamDataFrame("timeseries.csv")
```

## Scenarios

The `family` column of `scenarios.csv`:

- **budget ladder** (55): the carbon-budget sweep. For each of five cases, the mandates
  that minimise the discounted surplus loss under a cumulative CO₂ budget of 2.0 to 3.8 %
  of the world aviation budget, plus the minimum-CO₂ end point (`opt_<case>_mincarb`).
  The cases are `main` (10 % of world biomass allocated to aviation), `B5`, `B75`, `B15`
  (5, 7.5, 15 %) and `pess` (a pessimistic efficiency roadmap at 10 %).
- **central budget** (5): each case at the ReFuelEU-equivalent budget, 3.1226 % of the
  world budget (3.8656 GtCO₂ on the EU perimeter).
- **sensitivity A–D** (14): one parameter varied at a time around `base`, at that same
  central budget — price elasticity (A), fixed demand (A′), ramp-up rate (B) and volume
  (B′) limits, a dedicated-wind electrofuel pathway (C), the social discount rate (D).
- **reference** (4): fixed-mandate runs with no optimisation — fossil BAU for `main` and
  `pess`, and the ReFuelEU mandate for `main`, interpolated linearly or held in steps.

## Notes

- **Units** are in `variables.csv`. Shares of the drop-in blend are in % of drop-in fuel
  energy. Carbon budget and resource shares in `scenarios.csv` are shares of the *world*
  totals; every run is then downscaled to the EU perimeter (15.49 % of world traffic).
- **`cumulative_total_surplus_loss_discounted`** is measured against 2019 unit economics,
  not against a no-policy scenario, so it is negative even for fossil BAU. Policy costs
  are differences between two scenarios; for the sensitivities, each measured against a
  fossil BAU sharing its elasticity and discount rate, they are in
  `sweep/sweep_summary.csv`.
- **Two points per optimisation.** `timeseries.csv` holds the outputs of the optimiser's
  final iterate, which is what the paper reports. `optima.csv` and `feasible` describe
  the point GEMSEO selects as its optimum, the best one within its 1e-4 feasibility
  tolerance. For 14 of the 74 optimisations that is the iterate before the last, at most
  0.037 percentage points of mandate away.
- **Infeasible runs** (`feasible == False`) are budgets the ramp-up limits cannot reach;
  their time series are a best effort, not an optimum.

## Reproducing

`python -m helpers.dataset`, run from the paper folder, rebuilds these files from the
raw optimisation outputs, which `01_optimisation_runs.ipynb` describes how to regenerate.
