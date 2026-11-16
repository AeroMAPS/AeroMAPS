# Changelog

## Unversioned

-  New unit system (`aeromaps/utils/units.py`): controlled vocabulary of unit symbols, parsing of compound expressions, validation, and conversions (`convert`, `convert_factor`) with dimensional checks.
- Variable metadata (unit, description, source) moved from `data_information.csv` to `data_information.yaml`, with exact entries plus ordered glob patterns for dynamically named variables (energy pathways, processes, climate species, LCA). All units are validated against the vocabulary at load time.
- Full metadata coverage: every variable of the tested configurations is now documented (previously ~1350 variables had no unit/description), enforced by the test suite.|
- New config key `data.inputs.data_information_file`; `csv_data_information_file` is deprecated but still read.
- New API: `process.get_variable_information(name)` to query the unit/description of a variable.
- Variable metadata now lives on the GEMSEO grammars: models declare units and descriptions (`declare_input`/`declare_output` for custom models, the class-level `UNITS` mapping for auto models, docstrings for descriptions), the wrappers validate every unit when the discipline is built and fall back to `data_information.yaml` for undeclared names. The process fails at assembly if a coupling variable is produced and consumed in different units, MJ against EJ included, since values are exchanged without conversion. `process.list_registry_resolved_variables()` lists what still relies on the registry.
- New `aeromaps schema` command and `process.export_schema()`: JSON Schema (draft-07) of the process inputs and outputs derived from the grammars, with type, unit, description, source, default value, consumers and producer of every variable. The data information table (Excel sheet, `get_dataframes()["data_information"]`) is derived from the same resolution.
- Units and metadata exposed to users: `aeromaps.utils.units` added to the API reference, and the basic example notebook shows `get_variable_information` and checked conversions.
- Metadata realigned on the generic markets refactoring (#145): market-scoped variables (`<market_id>_<leaf>`, `cagr_rpk_<market_id>`, ...) are now covered by pattern rules instead of hard-coded per-market entries, so user-defined markets are documented automatically.

## Version 1.2.0

Changed:
- Added the ATAG Waypoint 2050 scenarios: reproduction of the three editions, decomposition into the report's pillars, tank-to-wake twins, demand-price coupling, lever sweep and climate analysis. (#144, #170)
- Added a bottom-up variant of the ATAG third-edition scenarios and an ATAG lever order for the detailed CO2 plot. (#170)
- Moved the reference scenarios into the package, with metadata to list and filter them. (#144, #170)
- Added a decomposition of the CO2 levers into sub-levers (per aircraft, operational concept, pathway, offsetting scheme and market), with new plots and a tutorial. (#163)
- Added generic operations and offsets modules. (#163)
- Added comparison plots for background-scenario drivers and fuel-switching quantities, and made comparison utilities usable on committed JSON results. (#144)
- Validated energy configuration files at load time and documented quantity mandates in the energy templates. (#158)
- The MDA now raises when it does not converge, and `unified_mda` uses the same tolerance as a single region. (#157)
- Added a `regionalisation.global_models` block for disciplines coupled across regions. (#157)
- Pinned `gemseo` to `>=6.2.0,<6.3.0`. (#157)
- Stripped outputs from tracked notebooks. (#144)
- Migrated from Poetry to uv. (#166, #172)

Fixed:
- Corrected the first-order delay on the price seen by demand, which shifted projected traffic. (#144)
- Corrected silent zeros in the generic energy model from misspelled or unregistered keys, including process emission factors. (#144, #158)
- Corrected intensity curves reading zero before their first reference year. (#144)
- Corrected a double count of green electricity and DAC-CO2 in electrofuel cost and emissions. (#144)
- Corrected the ATAG re-baseline having modified the default parameters of every scenario. (#144)
- Corrected the ATAG decomposition order, the post-2035 offset trajectory and several figures. (#144)
- Corrected `aggregate_regions_to_single_process`, `compare_json_files`, historic contrail forcing and the envelope mode of comparison plots. (#144)
- Restored pathway-aware plots on results loaded from JSON. (#144)
- Fixed kerosene selectivity being ignored and inverted in the bottom-up model, and an unrecognised `mandate_type` now raises. (#158)
- Fuel subsidies and energy taxes now reach the airfare; this changes results for scenarios that use them. (#157)
- Fixed NaN sources in the MDA: sentinel values in the coupling vector, disciplines mutating their inputs, non-positive airfares, zero-traffic DOC means and duplicated columns on repeated `compute()`. (#157)
- Fixed changing `end_year` after `create_process`. (#107, #167)
- Fixed the markets global block overwriting the IAM model selector, and stale share keys in two markets files.


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

Fixed:
- Fixed drop_in_macc_curve plot: updated variable names to match generic energy model naming convention. (#136)
- Corrected reference outputs of JOAS notebook. (#143)
- Corrected docs and workflow. (#155)


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