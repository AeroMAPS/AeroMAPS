# Documentation


## Architecture

The simplified current architecture of AeroMAPS is given in Fig. 1.

![Texte alternatif](/figs/architecture.png "Fig.1 Simplified architecture of AeroMAPS.")

First, the future air transport system is modeled. It is considered that it is composed of three main elements: 
an air traffic in the form of passengers or freight, a fleet of aircraft that operate, and an energy mix to power 
the fleet. For each of these elements, exogenous data to represent future evolutions and developments are used. 

Secondly, the impacts associated with future air transport are assessed. Currently, only environmental assessments 
are performed, estimating for example the climate impacts of aviation (via CO2 emissions and non-CO2 effects) 
and the consumption of energy resources. A specific module for economic impacts, such as fuel costs 
or direct operation costs, is currently under development. 

Lastly, these impacts are compared to different sustainability targets. For this purpose, exogenous choices 
of environmental target allocations are considered, in order to directly compare the impacts of aviation with 
sector-specific targets. 

To assess the complexity behind the AeroMAPS process, the number of inputs and outputs are given here. AeroMAPS 
uses 24 input variables to allow users to define their own prospective scenarios. In addition, it uses 69 input 
parameters present in the models developed to perform the analyses proposed in AeroMAPS. These parameters 
are not meant to be modified by the user but rather updated when more recent literature and data are available. 
The AeroMAPS methodology can then compute and provide 88 outputs along with 35 different figures. 

Regarding the software development of the framework, AeroMAPS is developed using the Python programming language. 
The data and models are mainly manipulated and implemented using the Pandas package but also use other scientific 
computing package like GEMSEO and Scipy for solving implicit models for instance. The user interface uses ipywidgets 
for the widgets and ipympl for the graphs. The AeroMAPS software is deployed as a web application thanks to Voilà.