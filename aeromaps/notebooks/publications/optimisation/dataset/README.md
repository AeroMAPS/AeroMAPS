# ReFuelEU optimisation — scenario dataset

The results of the 78 AeroMAPS runs the paper uses, EU aviation, 2000–2050: 74
optimisations of the biofuel and electrofuel blending mandates, and 4 fixed-mandate
references. It lets every scenario be explored without running the optimisations, and it
is all `02_results.ipynb` reads to draw the paper's figures and Table 3.

## Files

| file | one row per | content |
|---|---|---|
| `scenarios.csv` | scenario | family, case, label, parameters, feasibility of the optimum |
| `timeseries.csv` | scenario × variable | yearly values 2000–2050, IAMC layout |
| `variables.csv` | variable | unit and description |
| `optima.csv` | scenario × quantity × year | design variables and constraint values at the optimum |

## Loading

From this folder's parent, with the readers of `helpers/dataset.py`:

```python
from helpers import dataset as D

D.scenarios()                               # one row per scenario, with its parameters
outputs, scalars = D.load("opt_main_refueleu")   # yearly outputs, one column per variable
outputs["generic_biofuel_share_dropin_fuel"].loc[2050]
D.read_constraints("opt_main_refueleu")     # design variables and G1-G6 at the optimum
```

Or with pandas or [pyam](https://pyam-iamc.readthedocs.io) directly, since
`timeseries.csv` uses the IAMC layout (`model, scenario, region, variable, unit`, then one
column per year):

```python
import pyam
df = pyam.IamDataFrame("timeseries.csv")
```

`02_results.ipynb` starts with a table of every scenario's main results.

## Scenarios

The `family` column of `scenarios.csv`:

- **budget ladder** (55): `opt_<case>_<budget>`, the mandate minimising the discounted
  surplus loss under a cumulative CO₂ budget of 2.0 to 3.8 % of the world aviation budget
  (`opt_main_2_6` is 2.6 %), and `opt_<case>_mincarb`, the minimum-CO₂ end point. The
  cases are `main` (10 % of world biomass allocated to aviation), `B5`, `B75`, `B15` (5,
  7.5, 15 %) and `pess` (a pessimistic efficiency roadmap, 0.91 %/yr instead of 1.35, at
  10 %).
- **central budget** (5): `opt_<case>_refueleu`, each case at the cumulative CO₂ of
  ReFuelEU (linear), 3.1226 % of the world budget (3.8656 GtCO₂ on the EU perimeter).
  `opt_main_refueleu` is the optimum discussed in §4.1 of the paper.
- **sensitivity A–D** (14): one parameter varied at a time around `base`, at that same
  central budget: price elasticity `eps_*` (A), fixed demand (A′), ramp-up rate `rate_*`
  (B) and volume `vol_*` (B′) caps, dedicated-wind electrofuel `efuel_wind` (C), social
  discount rate `r_*` (D).
- **reference** (4): fixed-mandate runs, no optimisation: fossil BAU for `main` and
  `pess`, and ReFuelEU for `main`, interpolated linearly (`refueleu_main`) or held in
  steps as legislated (`refueleu_step`).

## Notes

- **Perimeter.** Carbon budget and resource shares in `scenarios.csv` are shares of the
  *world* totals; every run is downscaled to the EU perimeter (15.49 % of world traffic).
  Shares of the drop-in blend are in % of drop-in fuel energy; other units are in
  `variables.csv`.
- **Surplus loss.** `cumulative_total_surplus_loss_discounted`, the objective, sums
  2025–2050 (the years a mandate can act), discounted to 2020. It is measured against 2019
  unit economics applied to the exogenous traffic, not against a no-policy scenario, so it
  is negative even for the fossil BAU: only differences between scenarios are policy
  costs. The fixed-demand run has no demand curve, hence no surplus.
- **Two points per optimisation.** `timeseries.csv` holds the outputs of the optimiser's
  final iterate, which is what the paper reports. `optima.csv` and `feasible` describe the
  point GEMSEO selects as its optimum, the best one within its 1e-4 feasibility tolerance.
  For 14 of the 74 optimisations that is the iterate before the last, at most 0.037
  percentage points of mandate away.
- **Infeasible runs** (`feasible == False`) are budgets the ramp-up limits cannot reach;
  their time series are a best effort, not an optimum.

## Rebuilding and extending

`python -m helpers.dataset`, from the paper folder, rebuilds these files from the raw run
outputs in `runs/` (the last cell of `01_optimisation_runs.ipynb`). To add a run, save it
under `runs/<folder>/` (`<name>.json`, plus `<name>.hdf` for an optimisation, as the
drivers do), declare it in `ADDED` in `helpers/dataset.py`, and rebuild. It then appears in
`scenarios.csv` with family `added`. Variables exported are those listed in `VARIABLES`
there.
