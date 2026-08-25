# Bug memo — kerosene selectivity is ignored, and inverted, in the bottom-up environmental model

**Repo:** AeroMAPS (backend)
**Verified against:** this checkout, branch `atag_scenario` (clean tree). Also reproduced on the released 1.1.0 wheel.
**Found by:** investigation from the AeroMAPS web app, while wiring up the MACC chart
**Impact:** resource-budget outputs (`*_necessary_with_selectivity`, `*_necessary_global_share_with_selectivity`) are wrong for every bottom-up pathway. Affects the `trd_macc_2025` and `salgas_phd_2025` publication scenarios and the bottom-up tutorial.

There are **two independent bugs**. The first masks the second, so fixing only the obvious one makes the output visibly worse. Please read §3 before patching.

---

## 1. Bug A — the model reads a parameter name that no data file writes

`aeromaps/models/impacts/generic_energy_model/bottom_up/environmental.py:257`

```python
kerosene_selectivity = _get_value_for_year(
    input_data.get(f"{self.pathway_name}_eis_kerosene_selectivity"), year, 1.0
)
```

The top-down counterpart reads the **non-prefixed** name —
`aeromaps/models/impacts/generic_energy_model/top_down/environmental.py:193`:

```python
pathway_kerosene_selectivity = input_data.get(
    f"{self.pathway_name}_kerosene_selectivity", 1.0
)
```

**No YAML anywhere in the package writes `eis_kerosene_selectivity`.** Every shipped
config writes plain `kerosene_selectivity`, including the ones that declare
`environmental_model: "bottom-up"`. The `.get()` therefore misses, and selectivity
silently falls back to `1.0`.

```
$ grep -rl "eis_kerosene_selectivity" --include="*.yaml" .
(no matches)
```

## 2. Bug B — the bottom-up model applies selectivity in the wrong direction

`bottom_up/environmental.py:290` and `:343`:

```python
resources_consumption_with_selectivity = resources_consumption * kerosene_selectivity
```

`top_down/environmental.py:208` and `:244`:

```python
ressource_required_with_selectivity = ressource_consumption / pathway_kerosene_selectivity
```

One multiplies, the other divides. Division is the one that matches the quantity's
meaning: selectivity is the share of a plant's output that is aviation fuel, so
producing 1 MJ of jet fuel at 15 % selectivity requires mobilising **1/0.15 ≈ 6.67×**
the feedstock, not 0.15×. The downstream consumer confirms this reading —
`aeromaps/models/impacts/energy_resources/energy_resources.py:143` sums these into
`{resource}_total_necessary_with_selectivity` and divides by
`{resource}_availability_global` to report the share of the global resource that must
be mobilised.

Today Bug B is invisible because Bug A pins selectivity to `1.0`, where `×1` and `÷1`
agree.

## 3. Reproduction (uses only the repo's own tutorial data)

```bash
cd aeromaps/notebooks/tutorials/04_use_bottom_up_fuel_models/data
python - <<'PY'
from aeromaps import create_process
p = create_process(configuration_file="./config_BU.yaml"); p.compute()
df = p.data["vector_outputs"]
cons = df["hefa_fog_hefa_fog_biomass_total_consumption"]
mob  = df["hefa_fog_hefa_fog_biomass_total_mobilised_with_selectivity"]
print("float inputs matching 'selectivity':",
      [k for k in p.data["float_inputs"] if "selectivity" in k])
for y in (2035, 2045, 2050):
    print(y, "ratio mobilised/consumption =", round(mob[y] / cons[y], 4))
PY
```

`hefa_fog` declares `kerosene_selectivity: 0.15` (line 25 of
`energy_carriers_data-full_BU.yaml`), so the expected ratio is `1/0.15 = 6.6667`.

**Observed — Bug A:**

```
float inputs matching 'selectivity': ['hefa_fog_kerosene_selectivity', 'hefa_others_...',
                                      'ft_msw_...', 'ft_others_...', 'atj_...']
2035 ratio mobilised/consumption = 1.0
2045 ratio mobilised/consumption = 1.0
2050 ratio mobilised/consumption = 1.0
```

The parameter *is* registered — under the non-`eis_` name — and the model never looks
it up.

**Observed — Bug B.** Re-run after renaming the YAML key to `eis_kerosene_selectivity`
(the "obvious" fix for Bug A, and nothing else):

```
2035 ratio mobilised/consumption = 0.15
2045 ratio mobilised/consumption = 0.15
2050 ratio mobilised/consumption = 0.15
```

Inverted: 0.15 where it should be 6.6667 — a factor of ~44 in the wrong direction, and
it *understates* the resource footprint, which is the dangerous direction for a
sustainability budget. **Do not ship the rename on its own.**

## 4. Suggested fix

Both parts are needed:

1. **`bottom_up/environmental.py:290` and `:343`** — change `*` to `/`, matching the
   top-down convention, and guard against a zero selectivity.
2. **The lookup name** — decide one of:
   - *Recommended:* have the bottom-up model read `eis_kerosene_selectivity` and fall
     back to `{pathway}_kerosene_selectivity` when absent, then rename the key in the
     shipped bottom-up configs. Existing user configs keep working; the `eis_`
     convention (used by every other per-vintage input) is preserved.
   - Or drop the `eis_` prefix in the model, since selectivity is a plant property that
     no shipped config varies by commissioning year anyway. Simplest, but breaks the
     naming convention.

A regression test worth adding: assert that for a bottom-up pathway with
`kerosene_selectivity: s`, `*_total_mobilised_with_selectivity == *_total_consumption / s`,
and that the top-down and bottom-up models agree on the same input.

## 5. Blast radius

Fixing this **changes published numbers** — the resource-budget series, not the CO₂ or
cost series. Configs that declare `environmental_model: "bottom-up"` alongside a plain
`kerosene_selectivity`:

- `aeromaps/notebooks/tutorials/04_use_bottom_up_fuel_models/data/energy_carriers_data-full_BU.yaml`
- `aeromaps/notebooks/publications/trd_macc_2025/data/**/energy_carriers_data*.yaml` (6 files)
- `aeromaps/notebooks/publications/salgas_phd_2025/data/**/energy_carriers_data*.yaml` (6 files)
- `aeromaps/notebooks/publications/joas_2023/data/energy_carriers_data.yaml`

In each, the five biomass drop-in pathways (`hefa_fog`, `hefa_others`, `ft_msw`,
`ft_others`, `atj`) carry `kerosene_selectivity: 0.15`.

The `outputs_*.json` files checked in beside those configs will need regenerating, and
the biomass-budget figures in the affected papers will move. `tsas_2025` and the
packaged `resources/data/default_energy_carriers/energy_carriers_data.yaml` are
top-down and unaffected.

## 6. Unrelated minor finding

`pyproject.toml` still declares `version = "1.0.0"`, so the released 1.1.0 wheel reports
`importlib.metadata.version("aeromaps") == "1.0.0"` — the version string was never
bumped for the 1.1.0 release. Downstream
consumers that surface it (the web app shows "AeroMAPS model v1.0.0" in its footer for
a 1.1.0 install) report the wrong version.

---

*Line numbers are from branch `atag_scenario`; they differ by 2-3 lines on the released 1.1.0 wheel.*
