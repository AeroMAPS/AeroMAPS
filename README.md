[![image](https://img.shields.io/pypi/v/aeromaps.svg)](https://pypi.python.org/pypi/aeromaps)
[![image](https://img.shields.io/pypi/pyversions/aeromaps.svg)](https://pypi.python.org/pypi/aeromaps)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

![Tests](https://github.com/AeroMAPS/AeroMAPS/workflows/tests/badge.svg)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/AeroMAPS/AeroMAPS/HEAD)

AeroMAPS: Multidisciplinary Assessment of Prospective Scenarios for air transport
=================================================================================

AeroMAPS is an open-source Python framework for performing Multidisciplinary Assessment of Prospective Scenarios for air transport.
It is a simplified sectoral Integrated Assessment Model (IAM) focusing on air transport transition, aiming at assessing 
the sustainability of air transport transition scenarios on multiple criteria.
For instance, it allows simulating and analysing scenarios for reducing aviation climate impacts through various levers of 
action. 

The objective is to provide:

- a modular framework for research addressing aviation transitions and sustainability
- a simplified graphical user interface for teaching
- a tool to support decision-making by institutional, industrial or private stakeholders

AeroMAPS is developed by ISAE-SUPAERO (Université de Toulouse, France) since 2020 (formerly CAST). 
It is fed by research collaborations with several organisations (TU Delft, Airbus, DTU) and multidisciplinary 
research activities from the [Institute for Sustainable Aviation](https://isa-toulouse.com/) (TBS, CERFACS).
It relies on several open-source scientific packages, including in particular [GEMSEO](https://github.com/gemseo/gemseo), 
[AeroCM](https://github.com/AeroMAPS/AeroCM) and [lca-modeller](https://github.com/AeroMAPS/lca-modeller).

AeroMAPS is licensed under the [GPL-3.0](https://www.gnu.org/licenses/gpl-3.0.en.html) license.

A [documentation](https://aeromaps.github.io/AeroMAPS/) is available for more details on AeroMAPS.


Quick start
-----------

For a quick start in order to discover the simplest features of AeroMAPS,
a graphical user interface has been developed for facilitating the first uses.
It is available at the following address: [https://aeromaps.eu/](https://aeromaps.eu/)


Quick installation
------------------

The use of the Python Package Index ([PyPI](https://pypi.org/)) is the simplest method for installing AeroCM.

**Prerequisite**: AeroMAPS needs at least **Python 3.10.0**.

You can install the latest version with this command:

```
pip install --upgrade aeromaps
```

If you also want to use the custom life cycle assessment model (which requires a valid ecoinvent license), use the following command:

```
pip install --upgrade aeromaps[lca]
```

For developers
------------------

If you want to contribute to the development of AeroMAPS, you can clone the repository and install the package in a 
virtual environment using [Poetry](https://python-poetry.org/):

``` {.bash}
git clone https://github.com/AeroMAPS/AeroMAPS.git
cd aeromaps
poetry install
```

If you also want to run the custom life cycle assessment model (which requires a valid ecoinvent license), install 
the extra dependencies with this command:

``` {.bash}
poetry install -E lca
```


Citation
--------

If you use AeroMAPS in your work, please cite the following reference. Other references are available in the
documentation.

Planès, T., Delbecq, S., Salgas, A. (2023).
AeroMAPS: a framework for performing multidisciplinary assessment of prospective scenarios for air transport.
Submitted to Journal of Open Aviation Science.
