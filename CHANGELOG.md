# Changelog

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
    - Updated voilà minimum version. (#38)

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