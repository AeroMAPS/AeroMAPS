# Building the ATAG Waypoint 2050 document

`index.md` is a standalone [MyST](https://mystmd.org) project, separate from the MkDocs site under
`docs/`. It builds to an HTML site and to a PDF through Typst. The two toolchains are independent:
`mkdocs build` never sees this directory, and `myst` never sees `docs/`.

Everything here runs from this directory:

```bash
cd aeromaps/notebooks/publications/atag_scenarios
```

## What you need

**1. The `paper` dependency group**, which supplies the `myst` command line tool:

```bash
poetry install --with paper
```

**2. Typst**, for the PDF only. It is a standalone binary, not a Python package, so Poetry does not
install it. Get it from [typst.app](https://github.com/typst/typst/releases), your package manager,
or `cargo install typst-cli`, and make sure `typst --version` answers. Without it the HTML build
works and the PDF export stops with `The typst CLI must be installed to build PDFs with typst`.

**3. A Jupyter server**, but only when you pass `--execute`. See below.

## Building

```bash
myst start                        # live preview at localhost:3000, no execution
myst build --html                 # static site into _build/
myst build --typst --execute      # the PDF
myst build --typst --html --execute
```

Without `--execute`, MyST renders the prose and reuses whatever execution cache is present. The
figures only regenerate when you pass `--execute`.

### Executing the document

MyST needs a Jupyter server to run the code cells and cannot always start one itself. If you see

```
⛔️ index.md Could not load Jupyter session manager to run executable nodes
```

start one yourself and point MyST at it:

```bash
python -m jupyter server --no-browser --port=8888 --IdentityProvider.token=mytoken
```

then, in the shell you build from:

```bash
export JUPYTER_BASE_URL=http://localhost:8888
export JUPYTER_TOKEN=mytoken
myst build --typst --html --execute
```

A clean run takes about half a minute. To force re-execution rather than reusing the cache, delete
`_build/execute` first.

## What comes out

| path | what it is |
| --- | --- |
| `exports/waypoint2050-reproduction.pdf` | the document |
| `exports/fig_N.pdf` | every figure, numbered in document order |
| `exports/<name>.pdf` | the same figures under stable names, for the manuscript |
| `_build/html/` | the HTML site |

`exports/` and `_build/` are both gitignored, so none of this is ever committed. The named copies
exist so a LaTeX manuscript can reference `atag_decomposition_s1.pdf` rather than `fig_2.pdf`, and
keep working when a figure is added or removed.

## What the document reads, and what it does not

The document **runs no model**. Every figure reads a committed `data_outputs/*.json`, plus
`climate_analysis/*.csv.gz` for the uncertainty bands and contrail variants, and
`report_data/atag_3rd_edition_figures.yaml` for the report's own digitised curves. This is what
keeps the build fast and reproducible, and it is why each result names the notebook that produced
it.

If a figure comes out empty or a cell prints `PENDING`, the corresponding output has not been
generated. Run the notebook named in the surrounding text.

## Regenerating the scenario outputs

Order matters, because later steps read what earlier ones write:

1. `3rd_edition_full/`: `s1.ipynb`, `s2.ipynb`, then `validation.ipynb` (which writes `t0`–`t4` and
   their tank-to-wake twins)
2. `3rd_edition_light/`: `s0.ipynb` first, since it aggregates the regional publication, then
   `s1.ipynb` and `s2.ipynb`, which aggregate the full edition
3. `3rd_edition_full_coupled_demand/`: `make_energy_files.py`, then `s1_coupled.ipynb`,
   `ssp_comparison.ipynb`, `ssp_comparison_share.ipynb`
4. `3rd_edition_variants/sweep.ipynb`
5. `climate_analysis/`: `climate_analysis.ipynb`, then `baseline_uncertainty.ipynb`

The scenarios themselves are not here. Configurations and inputs ship with the package, under
`aeromaps/resources/scenarios/`, one folder per scenario with a `scenario.yaml` naming and
classifying it:

```python
from aeromaps.utils.scenarios import list_scenarios

for scenario in list_scenarios(category="institutional"):
    print(scenario.folder, scenario.name, scenario.tags)
```

Each notebook opens by copying its scenario into `./workdir`, and runs against that copy:

```python
from aeromaps.utils.scenarios import prepare_scenario

SCENARIO = prepare_scenario("atag_3rd_edition_full")
```

This matters because these notebooks write: `process.write_json()` lands in the scenario's
`data_outputs/`, and each one regenerates its own tank-to-wake twin in `data_inputs/`. Run in
place, that would edit the installed AeroMAPS. In a sandbox it edits a copy, and `workdir/` is
gitignored.

```bash
cd 3rd_edition_full
python -m jupyter nbconvert --to notebook --execute --inplace s1.ipynb
```

The results then sit in `workdir/atag_3rd_edition_full/data_outputs/`. To refresh what this
document reads, copy them back deliberately:

```python
from aeromaps.utils.scenarios import publish_outputs

publish_outputs("workdir/atag_3rd_edition_full", "3rd_edition_full")
```

Results stay here rather than beside the scenario because a result belongs to the work that
reports it, and because these are 68 MB that have no business in an installed package.

Derived inputs are generated rather than hand-edited, and each script says what it writes.
The transforms themselves live in `aeromaps.utils`, so what is left in this folder is the
configuration that says which files feed which:

- the tank-to-wake energy and process files, from `aeromaps.utils.emission_scopes`
  (`lifecycle_to_corsia`), called by each scenario notebook for its own twin. The same
  module can convert a built process in place instead, via `apply_corsia_scope`
- `3rd_edition_full_coupled_demand/make_energy_files.py` — the coupled scenario's
  share-mandate and no-SAF energy files, via `aeromaps.utils.mandates`
- `make_offset_glide.py` — the post-CORSIA offset schedule, derived per scenario from its own
  gross trajectory via `aeromaps.utils.offsets`; run it after the scenarios exist, then
  re-run them. The share is scenario-specific: copying one scenario's schedule onto another
  makes net emissions rise after the handover rather than fall
- `make_lever_rows.py` — the standalone single-lever runs Table 2 reads
- `3rd_edition_variants/sweep.py` — the lever grid: axes, callbacks and published cells,
  run and plotted by `aeromaps.utils.sweep`
- `3rd_edition_variants/make_traffic_variants.py` — the low/high market files, solved onto
  the published 2050 endpoints via `aeromaps.utils.traffic_variants`
- `make_tables.py` — the manuscript's two LaTeX tables, read from the committed outputs;
  `--write DIR` emits `table.tex`
- `report_data/digitise_scenarios.py` — traces the report's own S0-S2 curves out of its
  charts, per pixel; `--write` merges them into `atag_3rd_edition_figures.yaml`
- `../../../resources/historical_data/extend_atag_baseline.py` — the observed-through-2023 baseline
  in the third-edition inputs

## Troubleshooting

**The wrong AeroMAPS gets imported.** If you have more than one clone, the one on
`site-packages/*.pth` wins whenever the working directory is a subdirectory like
`3rd_edition_full/`, and you get another checkout's model code without any warning. Pin it:

```bash
export PYTHONPATH=/path/to/this/checkout
```

A symptom worth recognising: `KeyError: 'co2_emission_factor_without_resource'`, which is a name
this checkout no longer uses.

**`EBUSY: resource busy or locked` on the PDF.** The export is open in a viewer. Close it; the
render itself already succeeded, and the file is in `_build/temp/*/`.

**`unknown directive: figure-md`.** Not a MyST directive. Figure captions here are plain italic
paragraphs under the cell, because mystmd will not embed a code cell's output into a `{figure}`.
