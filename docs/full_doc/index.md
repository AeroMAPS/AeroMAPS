# AeroMAPS Models

This section describes all the AeroMAPS models implemented in the framework.

!!! note "Nota bene"
    A simpler API reference, covering only user-facing functions and classes, can be found in the [API Reference](../api/) section of the documentation.

The navigation in this documentation is organized by package:

- **Package**
- **Core**: AeroMAPSProcess execution-related methods, GEMSEO integration, and
  configuration file handling.
- **GUI**: graphical user interface-related methods.
- **Utils**: utility functions for data handling, other
  general-purpose methods.
- **AeroMAPS Models**: disciplinary models implemented in AeroMAPS, organized
  into subpackages:
    - *Base, constants, parameters*: common building blocks shared across models.
    - *Air transport*: traffic, aircraft fleet and operations, and related submodels.
    - *Impacts*: emissions, climate impacts, costs, life cycle assessment, and
      other impact models.
    - *Sustainability assessment*: climate and equivalent carbon budgets.
    - *Optimisation*: elementary models to define constraints used in optimisation problems.

Each subpage is auto-generated from the Python docstrings using mkdocstrings.

