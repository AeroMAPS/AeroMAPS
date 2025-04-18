[![image](https://img.shields.io/pypi/v/aeromaps.svg)](https://pypi.python.org/pypi/aeromaps)
[![image](https://img.shields.io/pypi/pyversions/aeromaps.svg)](https://pypi.python.org/pypi/aeromaps)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

![Tests](https://github.com/AeroMAPS/AeroMAPS/workflows/tests/badge.svg)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/AeroMAPS/AeroMAPS/HEAD)

AeroMAPS: Multidisciplinary Assessment of Prospective Scenarios for air transport
=================================================================================

AeroMAPS is a framework for performing Multidisciplinary Assessment of Prospective Scenarios for air transport. For
instance, it allows simulating and analyzing scenarios for reducing aviation climate impacts through various levers of
action. It is intended to become a sectoral Integrated Assessment Model (IAM) taking into account technological,
environmental, sociological, economic and other considerations. It aims to assess the sustainability of simulated air
transport transition scenarios on multiple criteria.

AeroMAPS is licensed under the [GPL-3.0](https://www.gnu.org/licenses/gpl-3.0.en.html) license.

A [documentation](https://aeromaps.github.io/AeroMAPS/) is available for more details on AeroMAPS.


Quick start
-----------

For a quick start in order to discover the different features of AeroMAPS,
a graphical user interface has been developed for facilitating the first uses.
It is available at the following address: https://aeromaps.isae-supaero.fr/
Another solution is to use the [Binder-hosted graphical user interface](https://mybinder.org/v2/gh/AeroMAPS/AeroMAPS/HEAD?urlpath=voila%2Frender%2Faeromaps%2Fapp.ipynb).


Quick installation
------------------

The use of the Python Package Index ([PyPI](https://pypi.org/)) is the simplest method for installing AeroMAPS.
More details and other solutions are provided in the documentation.

**Prerequisite**: AeroMAPS needs at least Python 3.9.0.

You can install the latest version with this command:

``` {.bash}
$ pip install --upgrade aeromaps
```

If you also want to use the life cycle assessment models, it requires at least Python 3.10.0. In this case, you can install the latest version with this command:

``` {.bash}
$ pip install --upgrade aeromaps[lca]
```


Citation
--------

If you use AeroMAPS in your work, please cite the following reference. Other references are available in the
documentation.

Planès, T., Delbecq, S., Salgas, A. (2023).
AeroMAPS: a framework for performing multidisciplinary assessment of prospective scenarios for air transport.
Submitted to Journal of Open Aviation Science.
