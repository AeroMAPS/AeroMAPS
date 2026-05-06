# Phase 5 Handoff — Migrate per-market JSON params to custom `markets.yaml`

**Status:** Partial. Configs + notebook param renames done. JSON key renames done. **Next step (NOT done): generate per-scenario `markets.yaml` files and remove migrated keys from JSONs.**

**Branch:** `fleet-refactoring`
**Plan reference:** [REFACTOR_MARKETS_PLAN.md](REFACTOR_MARKETS_PLAN.md) §3.5 + Phase 5

---

## What's already landed in this session (do NOT redo)

1. **Configs** — `markets: markets_data_file: default` block added to:
   - 21 tutorial config files (notebooks 03, 04, 06, 07, 08, 09)
   - 78 publication config files (under `aeromaps/notebooks/publications/`)

2. **Notebooks** — legacy `process.parameters.<old_name>` references renamed to market-prefix form in:
   - Tutorials: `04_use_bottom_up_fuel_models/top_down_cost_calibration.ipynb`, `08_use_variable_demand/examples_elasticity.ipynb`, `11_custom_markets_multi_regions/example_notebook.ipynb`
   - Publications: `joas_2023`, `nature_communications_earth_and_environment_2024`, `mea_2024`, `salgas_phd_2025`, `trd_macc_2025`, `optimisation` notebooks
   - `load_factor_end_year` (global) was expanded into one line per passenger market

3. **JSON inputs** — legacy keys renamed to new market-prefix convention in 52 JSON files (text-based regex, formatting preserved). E.g.:
   - `cagr_passenger_short_range_reference_periods` → `short_range_cagr_reference_periods`
   - `energy_per_ask_short_range_dropin_fuel_gain_reference_years` → `short_range_energy_per_ask_dropin_fuel_gain_reference_years`
   - `hydrogen_final_market_share_short_range` → `short_range_hydrogen_final_market_share`
   - … etc. (all per §3.5 of REFACTOR_MARKETS_PLAN.md)

---

## Remaining task — what GPT needs to do

The user wants the per-market parameters that are currently in JSON inputs to **move out of JSON** into a **custom `markets.yaml` per scenario**. This is the proper Phase 5 cleanup.

### High-level workflow per JSON file

For each unique JSON inputs file with per-market or legacy global keys:

1. **Generate** a custom `markets.yaml` in the same data folder as the JSON, populated from the JSON values.
2. **Update** every config that loads that JSON: replace `markets_data_file: default` with the relative path to the new `markets.yaml`.
3. **Strip** the migrated keys from the JSON (preserving formatting — text-based delete, **do not reformat**).

### Scope (47 unique JSONs, 84 configs)

Run this discovery script to get the live mapping:

```python
import yaml, glob, os, json, re
from collections import defaultdict

PER_MARKET_RE = re.compile(
    r"^(short_range|medium_range|long_range|freight)_("
    r"rpk_share_2019|rtk_share_2019|energy_share_2019|"
    r"cagr_reference_periods(_values)?|"
    r"reference_cagr_reference_periods(_values)?|"
    r"energy_per_ask_dropin_fuel_gain_reference_years(_values)?|"
    r"relative_energy_per_ask_(hydrogen|electric)_wrt_dropin_reference_years(_values)?|"
    r"hydrogen_(final_market_share|introduction_year)|"
    r"electric_(final_market_share|introduction_year)|"
    r"doc_non_energy_per_ask_dropin_fuel_(init|gain)|"
    r"relative_doc_non_energy_per_ask_(hydrogen|electric)_wrt_dropin|"
    r"measures_(start_year|final_impact|duration)|"
    r"load_factor_end_year|covid_(drop_start_year|end_year|end_year_reference_ratio|load_factor_2020)"
    r")$"
)
LEGACY_GLOBAL_RE = re.compile(
    r"^(covid_(rpk|rtk)_drop_start_year|covid_end_year_(passenger|freight)|"
    r"covid_end_year_reference_(rpk|rtk)_ratio|covid_load_factor_2020|"
    r"load_factor_end_year)$"
)

mapping = defaultdict(list)  # json_abs_path -> [config_paths]
for root in ["aeromaps/notebooks/tutorials", "aeromaps/notebooks/publications"]:
    for cfg in glob.glob(f"{root}/**/config*.yaml", recursive=True):
        if ".ipynb_checkpoints" in cfg: continue
        with open(cfg) as f: c = yaml.safe_load(f) or {}
        ji = (c.get("data") or {}).get("inputs", {}).get("json_inputs_file")
        if not ji: continue
        ja = os.path.normpath(os.path.join(os.path.dirname(cfg), ji))
        mapping[ja].append(cfg)
```

Distribution observed:
- 1 huge JSON (`tutorials/08_use_variable_demand/data_elasticity/parameters_elasticity.json`) with **66 per-market keys** (full override of all groups)
- Most ltag inputs (~16 per-market keys = CAGR + reference_cagr per market) + `load_factor_end_year` + `covid_end_year_passenger`/`covid_end_year_freight` globals
- `is3*` scenarios in ecats / tsas (~31 per-market keys = +efficiency + DOC overrides)
- Salgas_phd / trd_macc base scenarios (~8 per-market keys)
- Some configs share JSONs (1:N relationship — all configs pointing to the same JSON should reference the same generated markets.yaml)

### Implementation notes

**Default markets.yaml structure** (template) at [aeromaps/resources/data/default_markets/markets.yaml](aeromaps/resources/data/default_markets/markets.yaml):

```yaml
defaults:
  passenger:
    inputs:
      growth: { cagr_reference_periods: [], cagr_reference_periods_values: [3.0] }
      covid:  { covid_drop_start_year: 66.0, covid_end_year: 2024, covid_end_year_reference_ratio: 100.0 }
      load_factor: { load_factor_end_year: 85.0, covid_load_factor_2020: 65.2 }
      measures: { measures_final_impact: 0.0, measures_start_year: 2051, measures_duration: 5.0 }
      efficiency_simple: { ... }
      costs: { ... }
      reference: { reference_cagr_reference_periods: [], reference_cagr_reference_periods_values: [3.0] }
  freight:
    inputs:
      growth: { ... }
      covid: { ... }
      reference: { ... }

short_range:
  name: "Short Range"
  traffic_type: passenger
  traffic_unit: RPK
  inputs:
    initial: { rpk_share_2019: 27.2, energy_share_2019: 26.01 }
    costs: { doc_non_energy_per_ask_dropin_fuel_init: 0.048375 }

medium_range: { ... }   # rpk_share 35.1, doc_init 0.0301
long_range:   { ... }   # rpk_share 37.7, doc_init 0.024725
freight:
  name: "Freight"
  traffic_type: freight
  traffic_unit: RTK
  inputs:
    initial: { rtk_share_2019: 100.0, energy_share_2019: 15.0 }
```

**Loader behaviour** (see [process.py:979-1080](aeromaps/core/process.py#L979)):
- `defaults` block is deep-merged into each market's `inputs` (per-traffic_type)
- Per-market values override defaults at leaf level; lists replace wholesale
- Sub-group keys (`initial`, `growth`, `covid`, …) are **dropped** during flattening — leaves named `start_year`, `end_year`, `duration` carry their group prefix in YAML (e.g. `measures_start_year`, `covid_end_year`) so the flattened name stays self-describing

**Strategy for generation** (recommended):
1. Start from a **deep copy of default markets.yaml** parsed dict
2. For per-market JSON keys (`<market>_<suffix>`): set `custom[market]["inputs"][group][leaf] = value` using the suffix→(group,leaf) mapping below
3. For legacy globals: set in `custom["defaults"]["passenger"|"freight"]["inputs"][group][leaf]`
4. Dump back to YAML with **inline lists for short numeric arrays** (use a custom PyYAML representer — `ruamel.yaml` is **not installed**, neither in system nor poetry env)
5. Strip migrated keys from JSON using **text-based regex deletion** (see "JSON formatting" below)
6. Update each referencing config: change `markets_data_file: default` → `markets_data_file: "./<generated_filename>"`

**Suffix → (group, leaf) mapping for per-market keys**:

```python
PM_KEYS = {
    "rpk_share_2019":                              ("initial", "rpk_share_2019"),
    "rtk_share_2019":                              ("initial", "rtk_share_2019"),
    "energy_share_2019":                           ("initial", "energy_share_2019"),
    "cagr_reference_periods":                      ("growth", "cagr_reference_periods"),
    "cagr_reference_periods_values":               ("growth", "cagr_reference_periods_values"),
    "reference_cagr_reference_periods":            ("reference", "reference_cagr_reference_periods"),
    "reference_cagr_reference_periods_values":     ("reference", "reference_cagr_reference_periods_values"),
    "energy_per_ask_dropin_fuel_gain_reference_years":         ("efficiency_simple", "energy_per_ask_dropin_fuel_gain_reference_years"),
    "energy_per_ask_dropin_fuel_gain_reference_years_values":  ("efficiency_simple", "energy_per_ask_dropin_fuel_gain_reference_years_values"),
    "relative_energy_per_ask_hydrogen_wrt_dropin_reference_years":         ("efficiency_simple", "relative_energy_per_ask_hydrogen_wrt_dropin_reference_years"),
    "relative_energy_per_ask_hydrogen_wrt_dropin_reference_years_values":  ("efficiency_simple", "relative_energy_per_ask_hydrogen_wrt_dropin_reference_years_values"),
    "relative_energy_per_ask_electric_wrt_dropin_reference_years":         ("efficiency_simple", "relative_energy_per_ask_electric_wrt_dropin_reference_years"),
    "relative_energy_per_ask_electric_wrt_dropin_reference_years_values":  ("efficiency_simple", "relative_energy_per_ask_electric_wrt_dropin_reference_years_values"),
    "hydrogen_final_market_share":                 ("efficiency_simple", "hydrogen_final_market_share"),
    "hydrogen_introduction_year":                  ("efficiency_simple", "hydrogen_introduction_year"),
    "electric_final_market_share":                 ("efficiency_simple", "electric_final_market_share"),
    "electric_introduction_year":                  ("efficiency_simple", "electric_introduction_year"),
    "doc_non_energy_per_ask_dropin_fuel_init":     ("costs", "doc_non_energy_per_ask_dropin_fuel_init"),
    "doc_non_energy_per_ask_dropin_fuel_gain":     ("costs", "doc_non_energy_per_ask_dropin_fuel_gain"),
    "relative_doc_non_energy_per_ask_hydrogen_wrt_dropin": ("costs", "relative_doc_non_energy_per_ask_hydrogen_wrt_dropin"),
    "relative_doc_non_energy_per_ask_electric_wrt_dropin": ("costs", "relative_doc_non_energy_per_ask_electric_wrt_dropin"),
    "measures_start_year":                         ("measures", "measures_start_year"),
    "measures_final_impact":                       ("measures", "measures_final_impact"),
    "measures_duration":                           ("measures", "measures_duration"),
    "load_factor_end_year":                        ("load_factor", "load_factor_end_year"),
    "covid_load_factor_2020":                      ("load_factor", "covid_load_factor_2020"),
    "covid_drop_start_year":                       ("covid", "covid_drop_start_year"),
    "covid_end_year":                              ("covid", "covid_end_year"),
    "covid_end_year_reference_ratio":              ("covid", "covid_end_year_reference_ratio"),
}
```

**Legacy global → traffic_type defaults mapping**:

```python
LEGACY_PASS = {
    "load_factor_end_year":              ("load_factor", "load_factor_end_year"),
    "covid_load_factor_2020":            ("load_factor", "covid_load_factor_2020"),
    "covid_rpk_drop_start_year":         ("covid", "covid_drop_start_year"),
    "covid_end_year_passenger":          ("covid", "covid_end_year"),
    "covid_end_year_reference_rpk_ratio":("covid", "covid_end_year_reference_ratio"),
}
LEGACY_FREIGHT = {
    "covid_rtk_drop_start_year":         ("covid", "covid_drop_start_year"),
    "covid_end_year_freight":            ("covid", "covid_end_year"),
    "covid_end_year_reference_rtk_ratio":("covid", "covid_end_year_reference_ratio"),
}
```

**Generated markets.yaml filename rule** (suggested):
```python
def derive_name(json_path):
    stem = os.path.splitext(os.path.basename(json_path))[0]
    if stem == "inputs": return "markets.yaml"
    if stem.endswith("_inputs"): stem = stem[:-7]
    elif stem.startswith("inputs_"): stem = stem[7:]
    elif stem.startswith("parameters_"): stem = stem[11:]
    return f"markets_{stem}.yaml"
# Examples:
#   is0medium_inputs.json          -> markets_is0medium.yaml
#   inputs_base_scenario.json      -> markets_base_scenario.yaml
#   parameters_elasticity.json     -> markets_elasticity.yaml
#   partitioned_inputs_merged.json -> markets_partitioned_inputs_merged.yaml
```

**JSON formatting preservation when stripping keys**:

The user pushed back hard on this earlier. **DO NOT use `json.dump`** — it reformats the entire file. Instead, do text-based deletion:

```python
import re
# For each key to remove, delete the entire line including trailing comma
pattern = rf'^[ \t]*"{re.escape(key)}"\s*:[^\n]*,?\s*\n'
text = re.sub(pattern, '', text, flags=re.M)
# Be careful: removing the LAST entry of a dict requires removing the trailing comma from the previous line.
# Safer pattern: read line by line, drop matching lines, then fix trailing-comma issue if final entry was dropped.
```

Recommended approach: parse JSON with `json.loads(text)` to get the canonical key list, identify which keys to remove, then walk the original text line-by-line and drop matching `"key":` lines, **then re-validate with `json.loads`** to catch trailing-comma issues. If the result is invalid JSON, the issue is almost always a trailing comma — fix by removing the last `,` before the closing `}`.

**Config update**:

```python
# In each config that references the JSON, replace:
#   markets:
#     markets_data_file: default
# with:
#   markets:
#     markets_data_file: "./markets_<scenario>.yaml"
# (relative path from config dir to the markets.yaml location)

import re
with open(cfg_path) as f: text = f.read()
new = re.sub(
    r'(  markets:\n    markets_data_file:\s*)(default|"[^"]+")',
    rf'\1"{rel_path_from_config_to_markets_yaml}"',
    text, count=1
)
```

Note: many configs are in a different directory than the JSON they reference (e.g. `tsas_2025/data/config_files/config_is0medium.yaml` references `tsas_2025/data/ltag_data_inputs/is0medium_inputs.json`). The `markets.yaml` should sit next to the JSON, so the config path becomes something like `"../ltag_data_inputs/markets_is0medium.yaml"`. Use `os.path.relpath`.

### Edge cases / things to be careful about

1. **`partitioning_data_file` is NOT `json_inputs_file`** — it has a different schema (`other_float_data`, `other_vector_data`, `climate_data` top-level keys). Do **not** touch these — they're regenerated by the partitioning step. Only handle `json_inputs_file` references.

2. **`freight_init`** in `tutorial 03/data/partitioning_updated_inputs.json` and similar — this is a list (list of regions or sub-units), inside `other_float_data`/`other_vector_data`. Skip it.

3. **`covid_energy_intensity_per_ask_increase_2020`** — appears in `parameters_elasticity.json`. This is a global, not yet per-market in the markets schema. Leave it in JSON.

4. **`covid_start_year`** — global, not part of markets schema. Leave it in JSON.

5. **One JSON loaded by multiple configs** — many cases in ecats/tsas/salgas. Generate the markets.yaml once; update all configs to point to it.

6. **YAML lists**: PyYAML `safe_dump(default_flow_style=False, sort_keys=False)` produces block lists by default. The default markets.yaml uses inline `[3.0]`, `[]`. Use a custom representer:
   ```python
   import yaml
   class Dumper(yaml.SafeDumper): pass
   def list_repr(d, data):
       inline = all(isinstance(x, (int, float, str, bool)) or x is None for x in data)
       return d.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=inline)
   Dumper.add_representer(list, list_repr)
   yaml.dump(custom, stream, Dumper=Dumper, default_flow_style=False, sort_keys=False, allow_unicode=True)
   ```

7. **When deep-copying default + overriding**, the `defaults.passenger.inputs.load_factor.load_factor_end_year` legacy override needs to **propagate to all passenger markets** automatically via the loader's deep-merge. Test on one scenario before bulk-applying.

8. **Memory note** in [memory/feedback_testing_scope.md](/Users/a.salgas/.claude/projects/-Users-a-salgas-PycharmProjects-AeroMAPS/memory/feedback_testing_scope.md): user does NOT want full notebook suite to be run by default. Use `pytest` or only `01_basic` notebook for verification.

9. **Validate** at the end:
   - `json.loads()` every modified JSON
   - `yaml.safe_load()` every generated/modified YAML
   - Zero per-market or legacy-global keys remain in any `json_inputs_file`-referenced JSON
   - Optional: run `pytest aeromaps/tests/` to confirm no regressions; `01_run_a_basic_calculation` notebook should still execute

### Suggested implementation order

1. Prototype on **one** simple JSON first (e.g. `salgas_phd_2025/data/base/inputs_base_scenario.json` — only 8 per-market CAGR keys + 1 legacy `load_factor_end_year`). Verify the generated `markets.yaml` loads correctly via `MarketManager.from_yaml` and produces the same numerical values as before.
2. Then do the medium-complexity ltag scenarios (~16-31 keys each).
3. Last: the elasticity JSON (66 per-market keys + 4 legacy globals) — full override of all groups.
4. Run a final scan to confirm zero leftover keys.

---

## Useful file/path references

- Plan: [REFACTOR_MARKETS_PLAN.md](REFACTOR_MARKETS_PLAN.md)
- Default markets template: [aeromaps/resources/data/default_markets/markets.yaml](aeromaps/resources/data/default_markets/markets.yaml)
- MarketManager loader: [aeromaps/core/process.py:979-1080](aeromaps/core/process.py#L979)
- Existing custom-markets example (tutorial 12): [aeromaps/notebooks/tutorials/12_default_markets_test/data/custom_markets.yaml](aeromaps/notebooks/tutorials/12_default_markets_test/data/custom_markets.yaml)
- Tutorial 11 custom markets (different market ids: domestic/intra_eu/intercontinental): [aeromaps/notebooks/tutorials/11_custom_markets_multi_regions/data/markets.yaml](aeromaps/notebooks/tutorials/11_custom_markets_multi_regions/data/markets.yaml)

## Git state at handoff

- Branch: `fleet-refactoring`
- Many files modified but not committed (per session work). The user has not asked for a commit yet — wait for explicit request before committing.
