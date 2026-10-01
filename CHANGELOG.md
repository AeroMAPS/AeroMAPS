# Changelog

## Version 1.2.0

Changed:
- Corrected the first-order delay on the price demand responds to, which ran only from the
  prospection start year and entered the projection from that year's raw price. Every historic
  year was left unfiltered, so the effective price was not delayed at all over the period the
  model was calibrated against. This was not a transient: the price index is anchored on the
  same series at a reference year sitting on that boundary, so the cold start landed in the
  denominator and shifted projected demand permanently, by -2.6 % of 2050 traffic under
  SSP2-1.9 and +3.3 % under SSP2-4.5, in opposite directions. The recursion now starts at the
  first year of the series, which is the convention the calibration used. Because the memory is
  about 1.26 years the result does not depend on where the series begins: 2000, 2010, 2015 and
  2019 give the same effective price at 2024 to four decimals. The function was duplicated
  verbatim in the two demand models and now lives in one place. (#144)
- Reproduced the ATAG Waypoint 2050 scenarios lever by lever across the three editions of the
  report, with a MyST document that reads only committed outputs and names the notebook behind
  each result. (#144)
- Added a CO2 decomposition following the reports' own pillars: fleet renewal, next generation
  aircraft technology, operations and infrastructure, SAF, and market-based measures. Alternative
  aircraft are counted as technology rather than as fuel, and the technology split is anchored on
  the report's own T0 frozen-fleet and T1 renewal-only scenarios. (#144)
- Added tank-to-wake twins for the reported scenarios, derived from the well-to-wake files by the
  CORSIA scaling the reports describe, so both accounting scopes are available from committed
  outputs. Agreement with the report's published technology curves is 0.3 % to 2.6 % at 2050.
  (#144)
- Added demand-price coupling for the ATAG scenarios, closing the feedback the reports leave out,
  under both fixed-volume and fixed-share readings of a SAF mandate. (#144)
- Added a full lever sweep over traffic, technology, operations and fuel, placing the three
  published scenarios inside the range their own levers can produce. (#144)
- Added climate analysis for the ATAG scenarios: per-mechanism temperature decomposition, non-CO2
  uncertainty bands from the contrail-sensitivity and fuel-effect literature, and contrail
  avoidance strategies parameterised on Teoh et al. (2020). (#144)
- Re-baselined the third-edition scenarios on observed traffic through 2023, kept inside those
  scenarios' own inputs rather than in the packaged defaults. (#144)
- Made the scenario-comparison utilities usable against committed JSON, so results can be plotted
  without re-running a process. (#144)
- Stripped outputs from every tracked notebook and enforced the existing nbstripout hook. (#144)
- Energy carriers, processes and resources yaml files are validated at load time: a key no energy model reads is now rejected instead of silently resolving to zero. The accepted vocabulary is collected from the energy models themselves, each key belonging to exactly one `inputs` block. (#158)
- Moved `fossil_kerosene`'s emission factor from `technical:` to `environmental:` in the three `icas_2024` energy carriers files. It was read from either block, so no result changes. (#158)
- Documented `mandate_type: "quantity"` and `mandate_quantity`, and corrected the subsidy keys, in the shipped energy templates. (#158)
- Moved the reference scenarios into the package, at `aeromaps/resources/scenarios/`: one folder per scenario holding its configurations and inputs, with the shared market definitions beside them and a `scenario.yaml` giving each a name, a category (institutional, industrial or academic) and tags. `aeromaps.utils.scenarios` lists and filters them, and `prepare_scenario` copies one into a sandbox before it is run. That copy is the point: the scenario notebooks write, both their outputs and their regenerated tank-to-wake twins, so running one in place edited the installed package. The results those runs produce stay with the publication that reports them. Covers the ATAG editions and their coupled-demand and climate extensions, the ICAO LTAG scenarios from the ECATS study, and the coupled LTAG scenarios from the WCTR one. (#144)
- Moved the ATAG document and notebooks to `aeromaps/notebooks/publications/atag_scenarios/`, alongside the other publications, and removed the `notebooks/scenarios/` tree that held only them. No committed result changed. (#144)
- Dropped the duplicated `socioeconomic_drivers` custom model from the WCTR configurations and the test fixtures, which declared a file identical to the packaged model. The built discipline set is unchanged either way. (#144)

Fixed:
- Corrected a family of silent-zero defects in the generic energy model, where a misspelled or
  unregistered key resolved to a null series instead of raising: emission factors missing the
  `mean_` prefix, a plural `resources_names`, subsidy and tax lookups, and a process's own
  emission factor, which was read from `input_data` but never registered. (#144)
- Corrected intensity curves reading as zero before their first reference year. Emission factors
  and fuel prices are properties of a fuel and now clamp backwards, while mandates, which are
  quantities, still truncate. (#144)
- Corrected a double-count of electrofuel's green electricity and DAC-CO2, present in both its
  cost and its emission factor. The report-derived values are life-cycle figures that already
  include those resources, and charging for them again overstated the 2050 fuel price by 84 % and
  roughly a third of the third edition's 2050 residual. (#144)
- Corrected `aggregate_regions_to_single_process` writing machine-absolute paths into the
  configuration it generates, which resolved on one machine only. (#144)
- Corrected the ATAG re-baseline having been applied to `resources/data/parameters.json` and
  `partitioning_inputs.json`, which silently moved the baseline of every other scenario in the
  repository; no publication or tutorial output had been regenerated against it. The scenarios
  that want that baseline now state it themselves, and
  `aggregate_regions_to_single_process` takes a `region_baseline` so a caller can rebaseline a
  multi-regional publication without editing it. (#144)
- Corrected `compare_json_files` raising `IndexError` from inside its own tolerance filter when
  two JSON files held lists of different lengths, instead of reporting them as different. (#144)
- Corrected historic contrail forcing being zeroed, and ERF unit labels. (#144)
- Corrected the alternative-aircraft wedge of the ATAG decomposition, which computed the energy
  split with SAF taken first while drawing that pillar above the fuel band. The same
  battery-electric fleet was credited 246.3 Mt in T4, where no SAF competes for it, and 6.3 Mt
  in S2. The split now takes the alternative leg first, matching the stacking. Because no
  ordering of a nested decomposition is canonical, the module documents the measured
  indeterminacy rather than presenting the new order as correct. (#144)
- Corrected the discontinuity where CORSIA-derived offsets stop in 2035 and the prescribed
  residual shares begin in 2036. The prescribed shares were also too small for the scenarios with
  higher gross emissions, so net emissions rose between 2036 and 2040 before falling. Post-2035
  offsetting is now stated as a target on net emissions instead: a linear decline from the 2035
  level to zero at 2050, which is the shape all three published scenarios draw. `make_offset_glide.py`
  derives the schedule from each scenario's own gross trajectory, since copying one scenario's
  schedule to another is what caused the defect. (#144)
- Corrected the coupled-demand figure starting its CO2 panel at 2023, and added a background row
  showing the population, GDP per capita and carbon price behind each SSP pathway. (#144)
- Corrected envelope mode of the multi-scenario comparison plots dropping one member scenario
  and labelling none of them, so a grouped envelope drew n-1 lines under an empty legend.
  Members are now all drawn and labelled with their scenario name. (#144)
- Added a per-pixel digitisation of the third edition's own S0-S2 charts, tracing the boundary
  between the SAF and market-based bands, which is emissions before offsetting and therefore
  comparable with `co2_emissions_including_energy`. The validation table now covers the three
  headline scenarios as well as T0-T4. (#144)
- Replaced the hand-written bibliography, whose keys were invented locally and which cited no
  reference for GEMSEO or for fleet renewal, with entries taken from the author's own
  libraries. (#144)
- Added comparison plots for the background-scenario drivers, `population_comparison`,
  `gdp_per_capita_comparison` and `carbon_price_comparison`, so a figure mixing drivers with
  results can draw every panel through the same code path and share the grouping and envelope
  behaviour. These carry outputs that only exist under an income-driven demand model, so the
  registry test now skips a plot whose required outputs no test scenario produces, instead of
  failing it. (#144)
- Added `dropin_mfsp_without_carbon_tax_comparison` and `co2_per_energy_comparison`, which are
  the two quantities a fuel-switching lever acts on directly, and made `years_source`
  overridable per call. The cost plots default to the projection alone, which is right where a
  scenario only models cost forward and wrong where the historic part is populated and carries
  the calibration the projection starts from. (#144)
- Extracted `build_pathways_manager` from `AeroMAPSProcess`, so results loaded from committed
  JSON can reconstruct the pathway metadata from the same YAML the scenario ran against. Every
  pathway-aware plot previously fell back to an empty figure against stored results. `SimpleMFSP`
  takes an `mfsp_type` that skips its toggle, `ResultsView.plot` forwards keywords to the plot
  class, and the per-RPK cost breakdown honours `legend=False`, which together let those plots be
  used in a document built without a live kernel. (#144)
- Fixed kerosene selectivity being ignored, and inverted, in the bottom-up model. (#158)
- An unrecognised `mandate_type` now raises instead of giving a pathway no mandate at all. (#158)
- Process emission factors are now read: the environmental models registered no process `environmental` block and looked the factor up under a name no configuration writes, so hydrogen liquefaction and electrolysis emissions read exactly zero. Every process emission factor in the repository is 0.0, so no committed result moves. (#158)
- Corrected `resources_names` in the `mea_2024` energy carriers file, which silently dropped `hydrogen_electrolysis`'s `transport` resource from cost and emissions. (#158)
- Coupling seeds now follow an `end_year` set after `create_process`: the price-elastic demand seeded `airfare_per_rpk` only up to the end year the process was created with, so RPK went NaN beyond it and the climate model raised. A value set in `process.parameters` still wins over the seed.
- Changing the year bounds between two `compute()` calls now gives the results of a process created with them, instead of a `KeyError` or NaN emissions. The year index, the output frames, the disciplines' caches, the fleet model's dataframe and the MDA chain, whose coupling defaults and solver bounds are sized at its first run, were all kept at the previous years; `setup_mda()` no longer needs calling after such a change. (#107)


## Version 1.1.0

Changed:
- ECATS application. (#126)
- Improved error handling across the codebase. (#134)
- Added scenario comparison utilities and unit tests. (#128)
- Added multi-regionalisation in AeroMAPS. (#140)
- Added two new models for estimating air traffic demand for passengers. (#139)
- Improved configuration files documentation. (#147)
- Added custom workflow public pickup. (#150)
- Made prospection_start_year flexible. (#146, #149)
- Refactored markets in AeroMAPS for a fully generic yaml description, with interactions with fleet. (#145)
- Documentation update. (#154)
- Pinned `gemseo` to `>=6.2.0,<6.3.0`. The constraint had no lower bound, so an install without the lock file could resolve a version predating `max_consecutive_unsuccessful_iterations` and `SequenceTransformer.set_bounds` (6.1.0), or `inner_mda_settings` as a settings model (6.2.0) -- all of which the MDA code relies on. (#157)
- Added a `regionalisation.global_models` block, allowing non-namespaced disciplines coupled across regions in `unified_mda` mode. (#157)

Fixed:
- Fixed drop_in_macc_curve plot: updated variable names to match generic energy model naming convention. (#136)
- Corrected reference outputs of JOAS notebook. (#143)
- Corrected docs and workflow. (#155)
- Missing values no longer travel inside the MDA coupling vector. AeroMAPS series are legitimately undefined over the historical years, and a coupling belonging to an unused pathway is undefined throughout; GEMSEO has no notion of a missing value, so those NaNs were carried as an in-band `-999999` sentinel. A sentinel in the numeric channel is destroyed by any operation the solver is entitled to perform on that vector -- notably `set_bounds`, whose projection clips it to the bound so it never converts back, taking a converged solve (9 iterations, 1.27e-11) to a non-converged one (20 iterations, 6.88e-07) on a scenario with no excursion at all. The pattern is now held in a mask beside the vector, frozen after the solver's first complete sweep and scoped to that solve, so the vector carries only real numbers. Results are bit-identical; `set_bounds` works; a NaN at a position the mask says carries a value is reported as "converged on NaN" exactly rather than heuristically. (#157)
- Fixed disciplines mutating their MDA inputs in place, which corrupted GEMSEO's previous-iterate snapshot and pinned the normalised residual above the requested tolerance. (#157)
- Fixed multi-regional outputs being duplicated on every repeated `compute()`. (#157)
- An MDA that stops before reaching its convergence tolerance, or that reaches it only because its coupling variables have gone NaN, now raises instead of silently returning results that are not a solution of the coupled system. Set `process.on_mda_failure = "warn"` to keep the old behaviour. (#157)
- Multi-regional `unified_mda` mode now solves with the same MDA settings as a single-region process (`tolerance=1e-10`, `max_mda_iter=200`) instead of `tolerance=1e-5` and GEMSEO's default of 20 iterations. (#157)
- `RPKElasticity` no longer clips the airfare inside `compute`. It raises the airfare ratio to a fractional price elasticity, which numpy evaluates to NaN on a negative base, and it used to defend itself by substituting a clipped airfare -- so the physics ran on one value while the solver's residual was formed on another, and nothing downstream could tell. The physical domain is now *declared* by the model (`AIRFARE_BOUNDS_RELATIVE`, reaching the solver through `MDAChain.set_bounds`) and enforced by projecting the iterate, so solver and physics agree on what was evaluated. The projection governs the iterate carried between iterations, not a value passed producer-to-consumer within one Gauss-Seidel sweep; in that case the model now returns NaN and the run fails through the convergence check rather than returning a saturated number. Scenario results are unchanged. (#157)
- The global ASK-weighted DOC means no longer return NaN in a year where no market has any traffic, where they computed `0/0`. The weight for an average of per-ASK *intensities* is a share, and it is no longer reconstructed from the volumes at the point of use: `ASKAggregator` now publishes `ask_<market>_share`, and the six DOC means weight by it. Where there is traffic the two forms are the same number; in a year where no market flies, the split falls back to the `<market>_rpk_share_last_historical_year` the scenario declares, so the weighting is defined by construction rather than divided out of zero. Years where only some markets are empty are unaffected, and a pre-existing NaN is left alone. (#157)
- Fuel subsidies and fuel excise taxes now reach the airfare. `PassengerAircraftDocEnergySubsidy` and `PassengerAircraftDocEnergyTax` were netted into the reporting total `doc_total_per_ask_mean` but were not read by `PassengerAircraftTotalCost`, so a SAF subsidy moved the reported cost and left the fare -- and therefore price-elastic demand -- untouched. Energy taxes now join the carbon tax and the passenger tax in `total_extra_tax_per_*`; energy subsidies get their own category, `total_subsidy_per_ask` / `total_subsidy_per_rpk` (and per market), and are subtracted from `total_cost_per_*`. Both are applied on top of the supply function in `PassengerAircraftMarginalCost`, so they reach the fare at full pass-through and leave its base-year calibration untouched. Which side of the supply function each term now sits on, and the pass-through it therefore receives: *inside*, damped to `1/(1-a.eta)` (~0.95 on the shipped calibration), the energy DOC and hence the fuel price, the non-energy DOC, NOC, IOC, the carbon offset and the efficiency/load-factor cost terms; *outside*, at exactly 1.0, the carbon tax, the passenger tax, the energy tax and the energy subsidy. The tax wedge and the subsidy are applied at the same point with opposite signs, so equal amounts of the two cancel exactly. The carbon tax sitting outside is inherited from the previous code, not a new choice. **This changes results**: any scenario carrying an energy tax or subsidy now produces different traffic, because the channel from fuel policy to demand did not previously exist. Scenarios defining neither are unchanged. (#157)
- `OperationalEfficiencyCost` no longer returns NaN when `operations_final_gain` is zero, where it computed `0/0`. No operational measure is targeted, so the cost is now zero; with price-elastic demand the NaN reached the airfare and the run failed. Scenarios with a non-zero final gain are unchanged. (#157)


## Version 1.0.0

Changed:
- New documentation. (#111)
- Updated fleet models through the use of yaml files. (#112)
- Updated climate models using AeroCM. (#113)
- Use of new configuration files for a standardised use. (#113)
- Updated and alternative life cycle assessment models. (#114)

Fixed:
- Refactoring and import corrections. (#111)
- Notebooks corrections. (#113, #114)
- Correct configuration files. (#114)
- Management of tests. (#114)
- Minor documentation correction.


## Version 0.9.0-beta

Changed:
- Added scenario optimisation feature. (#104)


## Version 0.8.4-beta

Changed:
- Improved computation time. (#102)


## Version 0.8.3-beta

Fixed:
- Fixes poetry dynamic versioning. (#100)


## Version 0.8.2-beta

Changed:
- Switched binder to Python 3.9. (#96)
- Computation improvements for app. (#98)

Fixed:
- Fixes binder not running issue. (#97)


## Version 0.8.1-beta

Changed:
- Add a simple model for estimating CO2 emissions. (#94)

Fixed:
- Bug fixed for running a reduced number of models by providing vector inputs. (#93)


## Version 0.8.0-beta

Changed:
- Upgrade GEMSEO to 6.0.0. (#87)
- New models and application for TSAS conference. (#88)
- Minor additions to cost code and notebooks update. (#89)
- Life cycle assessment. (#90)
- New features and restructuring of the notebooks. (#91)

Fixed:
- Multiple error fixes. (#91)


## Version 0.7.1-beta

Changed:
- Feature added: simplified energy models. (#81)
- Gemseo upgrade. (#84)
- Update DevOps. (#85)

Fixed:
- Bug on electric aircraft cost. (#82)
- Corrections and updates for climate notebook. (#83)


## Version 0.7.0-beta

Changed:
- Add the capability of handling a custom model. (#67)
- Add the capability of handling a custom input file. (#69)
- Update climate models. (#72)
- Update cost models and add MACC models. (#74)
- Integrate scope partitioning using AeroSCOPE data. (#79)

Fixed:
- Improvement of basic notebooks. (#69)
- Electricity consumption of hydrogen liquefaction. (#74)
- Improvement of the creation of a process. (#76)
- Fleet refactoring. (#79)

## Version 0.6.2-beta

Changed:
- Data file management using configuration file. (#65)

## Version 0.6.1-beta

Changed:
- Provide the ability to vary annual efficiency gains in the top-down models. (#56)
- Add electric and hybrid-electric aircraft. (#57)
- Add new climate models using FaIR. (#60)

Fixed:
- Correct graphical user interface. (#59)
- Correct some errors for plots. (#62)

## Version 0.6.0-beta

Changed:
- Improve climate models based on GWP*. (#53) 
- Add detailed Excel file for references. (#53)

Fixed:
- Add hatches for carbon offset for sustainability assessment. (#52)

## Version 0.5.0-beta

- Changed:
    - Added carbon offsetting for MBM. (#40)
    - Added possibility to modify kerosene emission factor evolution. (#41)
    - Improved the way to handle non-CO2 emission index in fleet renewal models. (#43)
    - Updated dependencies (min. matplotlib 3.7 + allow Python 3.10). (#45)
    - Added a simpler way to modify end_year and allowed custom settings for interpolation and levelling. (#47)

- Fixed:
    - Corrected a few plots. (#44)

## Version 0.4.2-beta

- Changed:
    - Updated JOAS publication notebook with reviewers feedback. (#37)
    - Updated voilÃ  minimum version. (#38)

- Fixed:
    - Corrected soot calculation. (#36)

## Version 0.4.1-beta

- Changed:
    - Added cost model documentation. (#28)
    - Added possibility to use the fleet model with no new aircraft. (#31)
    - Updated the UI parameters to use fleet model. (#34)

- Fixed:
    - Fixed computation of hydrogen expenses. (#30)
    - Fixed computation of disciplines dependent of fleet model. (#32)
    - Corrected JOAS publication notebook. (#33)

## Version 0.4.0-beta

- Changed:
    - Added fuel consumption in liter. (#19)
    - Added cost models. (#20)
    - Added notebooks and corrections for JOAS application. (#21 and #22)

- Fixed:
    - Fixed minor plots and data on cost models. (#23)
    - Fixed release process. (#25)

## Version 0.3.1-beta

- Fixed:
    - Fixed run server command. (#16)
    - Fixed data tab update (#17)

## Version 0.3.0-beta

- Changed:
    - Added temperature increase due to CO2 and non-CO2 effects. (#10)
    - Added a simplified widget for setting air traffic growth. (#13)
    - Improved and added new figures. (#14)

- Fixed:
    - Fixed computation process to allow multiple run. (#12)

## Version 0.2.0-beta

- Changed:
    - Added cruise altitude parameter to fleet renewal model. (#8)
    - Added possibility to change the end year. (#8)

- Fixed:
    - Minor corrections in freight model. (#8)

## Version 0.1.1-beta

- Changed:
    - Kernel culling is set to 2 hours. (#3)
    - Updated fleet model. (#4)

- Fixed:
    - Fixed data file download. (#6)

## Version 0.1.0-beta

- First beta release