# Misspelled or misplaced YAML input keys silently resolve to zero

## Summary

Every input the generic energy models read is looked up with `input_data.get(key, default)`, where
`default` is a zero-filled series. A key that does not match — because it is misspelled, because it
lost a prefix, or because it sits in a block the reading model does not register — therefore
resolves to **zero** rather than raising.

Zero is a physically meaningful value for an emission factor, a cost or a consumption rate. Nothing
downstream complains, no warning is emitted, and the run completes with plausible-looking numbers.

We have now hit this **four times in production data and found three more latent instances in the
code**. The largest of them understated a scenario's 2050 CO₂ by roughly 40 % for an unknown length
of time. This issue proposes making the failure loud.

## Evidence

### Instances that produced wrong published numbers

| # | Location | Key written | Key read | Effect |
|---|---|---|---|---|
| 1 | all 12 ATAG `*_energy.yaml` | `co2_emission_factor_without_resource` | `..._mean_co2_emission_factor_without_resource` | All seven biomass SAF pathways modelled as **zero-carbon**. Scenario S1 2050 CO₂ read 386 Mt; correct value 644 Mt. |
| 2 | `top_down/environmental.py:287` | (data was correct) | process lookup missing the `mean_` prefix | Process emissions dropped **repo-wide**. Hydrogen liquefaction and electrolysis both read exactly 0.0000. |
| 3 | ATAG `*_energy.yaml` | intensity curves anchored later than the mandate | — | SAF produced at **zero cost and zero emissions** in the gap years. Five years wide in the 2nd edition. |
| 4 | `mea_2024/energy_carriers_data.yaml:388` | `resources_names` | `resource_names` | `hydrogen_electrolysis`'s `transport` resource silently dropped from cost and emissions. |

\#1 and \#2 are fixed. \#3 is fixed (see "Related fix" below). **\#4 is not fixed** — it is still
present on `main`. That file's own schema comment at line 25 uses the singular, as do its other
seven declarations; line 388 is the odd one out.

### Latent instances already written into the code

None of these fire today, because no current scenario uses subsidies, taxes, or the bottom-up
models. Each is the same mechanism, waiting.

| Location | Code reads | Loader/template produces |
|---|---|---|
| `top_down/cost.py:287` | `{process}_mean_unit_subsidy_without_resource`**s** | `processes_data.yaml:26` → `..._mean_unit_subsidie`**s**`_without_resource` |
| `top_down/cost.py:295` | `{process}_mean_unit_tax_without_resource`**s** | `processes_data.yaml:30` → `..._without_resource` |
| `top_down/cost.py:225,259` | `{resource}_subsidy` | `resources_data.yaml:23` documents `subsidies` |
| `bottom_up/environmental.py:405` | `{process}_eis_co2_emission_factor_without_resource`**s** | template and the top-down twin both use `..._without_resource` |

### A related gap that is live for any new user

`common/energy_use_choice.py:65-76` dispatches on the mandate type with
`if "quantity" ... elif "share" ...` and **no `else: raise`**. The shipped template documents

```yaml
mandate_type: "share"    # or "volume"
```

but the code never tests for `"volume"`. Anyone following the documented template gets a pathway
with no mandate at all, silently — it simply never deploys. `mandate_quantity`, the value the code
actually accepts, is undocumented.

## Why the obvious fix is wrong

**Making the lookups strict does not work.** Many of these inputs are genuinely optional, and this
was measured rather than assumed: of **505 pathways** across the repository, only **310** declare
`mean_co2_emission_factor_without_resource`. The other **195** legitimately omit it —
`fossil_kerosene` and the bottom-up carriers derive their emission factor elsewhere. Requiring the
key would break all of them.

## Proposed fix: reject unknown keys at load time

The distinguishing signal is that **a misspelling produces an _unknown_ key, whereas a legitimately
absent optional input produces _no_ key at all.** Those two cases are separable at load time, which
a strict `.get()` at lookup time cannot do.

In `aeromaps/utils/yaml.py`, when parsing an energy-carriers, processes or resources file:

1. Validate each block's keys (`mandate`, `technical`, `environmental`, `economics`) against an
   allow-list.
2. Raise on any key outside it, naming **file, carrier, block and key**.
3. Attach a **"did you mean"** suggestion via `difflib.get_close_matches`. Every instance above is a
   near-miss — a dropped `mean_` prefix, a stray plural — so this turns each one into a one-line
   actionable error.

### Build the allow-list from the code, not from the templates

The commented templates in `aeromaps/resources/data/default_energy_carriers/` are the closest thing
to a schema the project has, and they are **demonstrably not authoritative**: they disagree with the
code in the four places tabulated above, plus the `mandate_type` value. Deriving the allow-list from
them would encode the bugs it is meant to catch.

The observed vocabulary is small and closed:

- **environmental** — `mean_co2_emission_factor_without_resource`,
  `eis_co2_emission_factor_without_resource`, `emission_index`
- **technical** — `lhv`, `kerosene_selectivity`, `resource_names`, `processes_names`,
  `resource_specific_consumption`, `plant_lifespan`, `plant_load_factor`,
  `technology_introduction_year`, `technology_introduction_quantity` / `_volume`, and the `eis_` twins
- **economics** — `mean_mfsp_without_resource`, `eis_capex`, `eis_fixed_opex`, `eis_variable_opex`,
  `mean_unit_subsidy_without_resource`, `mean_unit_tax_without_resource`

### Block placement: a narrower rule than it first appears

Verified mechanics, which matter for getting this right:

- `_flatten_dict` (`utils/functions.py:64-72`) **discards the block name** — the prefix is the
  pathway name. So `environmental:` and `technical:` yield identical flattened keys.
- The environmental model registers `environmental` **+ `technical`**; the cost model registers
  `economics` **+ `technical`** (`top_down/environmental.py:53-64`, `top_down/cost.py:60-71`).

Consequently:

- A key under `technical:` is visible to **both** models. The `ecats_2026` files that put
  `mean_co2_emission_factor_without_resource` there are **harmless — do not "fix" them.**
- An emission-factor key under `economics:`, or an MFSP key under `environmental:`, is registered by
  only the *other* model and silently reads zero. **That** is the case worth rejecting.

### Also in scope

Add the missing `else: raise` to the `mandate_type` dispatch, and correct the template to document
`"quantity"` and `mandate_quantity`.

## Blast radius

**Expect the validator to fail on existing files** — instance \#4 at minimum, and possibly others
not yet found. That is the point, but it means the rollout order is:

1. Add the validator behind a flag, or as a warning.
2. Sweep the whole repository and fix every file it flags.
3. Re-run every publication and diff committed outputs; any movement is a bug this found.
4. Turn the validator into a hard error.

Publications to re-check: `wctr_2026`, `ecats_2026`, `icas_2024`, `joas_2023`, `mea_2024`,
`salgas_phd_2025`, and the ATAG scenario tree.

## Verification

1. Each of the four historical typos is rejected with a "did you mean" naming the correct key — one
   unit test per shape (dropped prefix, stray plural, wrong block).
2. A pathway legitimately omitting `mean_co2_emission_factor_without_resource` still loads. There
   are 195 such pathways; none may start failing.
3. Whole-repo load sweep: every `*energy*.yaml`, `processes*.yaml` and `resources*.yaml` parses
   clean once the offenders are fixed.
4. `mandate_type: "volume"` raises instead of silently producing a mandate-less pathway.
5. Full suite green.
