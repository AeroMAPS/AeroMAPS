# Architecture

!!! warning "This part of the documentation is deprecated. It describes AeroMAPS in late 2023"
    It will be updated soon.!

The simplified current architecture of AeroMAPS is given in Fig.1.

![](figs/architecture.png)
*Fig.1 Simplified architecture of AeroMAPS.*

First, the future air transport system is modeled. Three main elements are considered to represent it: an air traffic 
volume (freight or passengers), an aircraft fleet that operates the traffic, and that is powered by an energy mix. For
each of these elements, exogenous data to represent future evolutions and developments are used.

Secondly, the impacts associated with future air transport are assessed. Currently, only environmental assessments 
are performed, estimating for example the climate impacts of aviation (via CO<sub>2</sub> emissions and 
non-CO<sub>2</sub> effects) and the consumption of energy resources. A specific module for economic impacts, 
such as fuel costs or direct operation costs, is currently under development. 

Lastly, these impacts are compared to different sustainability targets. For this purpose, exogenous choices 
of environmental target allocations are considered, in order to directly compare the impacts of aviation with 
sector-specific targets. 

