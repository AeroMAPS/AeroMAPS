# Welcome to AeroMAPS Documentation!

The objective of this documentation is to provide the main elements concerning AeroMAPS.

In particular, see:  
- [Overview](books/index.md) — general principles of AeroMAPS.  
- [Installation](books/installation.md) — quick use and installation processes.  
- [API Reference](full_doc/index.md) — understanding the intended use of user-facing functions and classes.  
- [AeroMAPS Models](full_doc/index.md) — details on each model used by the framework.  
- [Examples](notebooks/examples_basic.ipynb) — several example applications.



## About AeroMAPS

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


## Authors

- Thomas Planès, Associate Professor at ISAE-SUPAERO
- Scott Delbecq, Associate Professor at ISAE-SUPAERO
- Antoine Salgas, postdoctoral researcher at ISAE-SUPAERO and the Institute for Sustainable Aviation (ISA)
- Félix Pollet, postdoctoral researcher at ISAE-SUPAERO and the Institute for Sustainable Aviation (ISA)

## Citations

Please cite this article when using AeroMAPS in your research works:

Planès, T., Delbecq, S., Salgas, A. (2023).
AeroMAPS: a framework for performing multidisciplinary assessment of prospective scenarios for air transport.
Submitted to Journal of Open Aviation Science.

```
@article{planes2023aeromaps,
  title={AeroMAPS: a framework for performing multidisciplinary assessment of prospective scenarios for air transport},
  author={Plan{\`e}s, Thomas and Delbecq, Scott and Salgas, Antoine},
  journal={Journal of Open Aviation Science},
  volume={1},
  number={1},
  year={2023}
}

```
Other publications from our research group that describe specific methods and models implemented in AeroMAPS can be found in the
[References](books/references.md) section of the documentation.



## Contact

[aeromaps@isae-supaero.fr](mailto:aeromaps@isae-supaero.fr)



This site is built with [MkDocs](https://www.mkdocs.org/) and [mkdocstrings](https://mkdocstrings.github.io/).
