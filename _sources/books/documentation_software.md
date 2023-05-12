# Software developments

To assess the complexity behind the AeroMAPS process, the number of inputs and outputs are given here. AeroMAPS 
uses 24 input variables to allow users to define their own prospective scenarios. In addition, it uses 69 input 
parameters present in the models developed to perform the analyses proposed in AeroMAPS. These parameters 
are not meant to be modified by the user but rather updated when more recent literature and data are available. 
The AeroMAPS methodology can then compute and provide 88 outputs along with 35 different figures. 

Regarding the software development of the framework, AeroMAPS is developed using the Python programming language. 
The data and models are mainly manipulated and implemented using the Pandas package but also use other scientific 
computing package like GEMSEO and Scipy for solving implicit models for instance. The user interface uses ipywidgets 
for the widgets and ipympl for the graphs. The AeroMAPS software is deployed as a web application thanks to Voilà.