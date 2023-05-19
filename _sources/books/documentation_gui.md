# Use of the graphical user interface

This page guides the user through the handling of the AeroMAPS Graphical User Interface (GUI). It is recommended to use 
it on a computer. In a first step, a tutorial is provided for understanding the use of the GUI. In a second step, the 
default settings used on the GUI are provided.


## Tutorial

The AeroMAPS GUI is composed of 3 tabs: 
- **Simulator** which is the integrated simulator to directly simulate prospective scenarios for air transport ;
- **Data** which allows to visualize data and retrieve them in CSV format in order to post-process them ;
- **About AeroMAPS** which provides brief information, explanations and documentation about the framework

Moving on the tool and on the explanatory tabs is quite intuitive by clicking on the corresponding tabs. To adjust 
the size of the tool to the size of his screen, the user can use the zoom (out) functionalities on his browser. 
The display language can be chosen : English or French (coming soon).

To use the AeroMAPS simulator, the user must select the **Simulator** tab. Two distinct blocks then appear on the 
user's screen (see the following figure). 

![](/figs/tutorial_page.png)

On the one hand, three different graphs are available in the upper part of the screen, with the possibility of 
selecting specific figures using drop-down menus. A first graph allows plotting 
CO<sub>2</sub> emissions or effective radiative forcing from aviation. A second one provide figures concerning the 
assessment of the sustainability of a scenario, for instance in terms of climate. A last graph represents a set of 
figures for analyzing scenarios more deeply.

On the other hand, a set of sliders is available in the lower part of the screen for performing scenario simulation.
For facilitating the handling of the tool according to the user, the user can use three distinct modes of varying 
complexity. In the *Discovery mode*, the user uses directly sliders: this mode provides a good understanding of the 
sensitivities of the main levers of action. In the *Scenarios mode*, the user displays scenarios that have already been 
defined and parameterized: this is the easiest mode to use which only allows analyzing scenarios. Finally, the 
*Advanced mode*, not directly available on the GUI, links to the AeroMAPS GitHub to be able to manipulate in detail the 
AeroMAPS framework using Jupyter Notebooks.

> **_NOTE:_**  Additional information on the different levers of action on the *Discovery mode* is provided by hovering 
> the mouse over them (tooltip).

To illustrate the handling of AeroMAPS, an animation is given below. In this animation, the user tries out different 
AeroMAPS functionalities: moving on the tabs, using different simulator modes, displaying different figures, setting 
scenario parameters.

![](/figs/gif_tutorial.gif)




## Reference settings

The different default settings for using the interface are detailed in the following, both for the *Discovery mode* and
the *Scenarios mode*.


### *Discovery mode*

In this mode, the user can play with different sliders corresponding roughly to the AeroMAPS architecture. On the 
one hand, aviation settings are provided for modeling the air transport evolution through the air traffic, aircraft 
fleet and operations, and aircraft energy. On the other hand, environmental settings are given via climate and energy 
assumptions and allocations choices.

#### Air traffic

For making assumptions on air traffic evolution, the user can directly define mean air traffic growth rates on the 
period 2020--2050 for the four considered markets in the model: passenger short-range, passenger medium-range, 
passenger long-range and freight. By default, these values are fixed to 3% per year, i.e. values close to aviation
industry's projections {cite}`atagwaypoint`.

Moreover, by default, a modeling of Covid-19 epidemic is included. It significantly disrupted global air traffic
in 2020 and its consequences are likely to disrupt global traffic for several years. To take account of this 
epidemic, this option incorporates a 66% decline in traffic in 2020 compared with 2019 and a return to the 2019 level 
by 2024 according to 
<a href="https://www.iata.org/contentassets/6dfc19c3fdce4c9c8d5f1565c472b53f/2020-09-29-02-fr.pdf" target="_blank">IATA</a>. 
This option also takes into account the one-off change in the aircraft load factor in 2020, which has dropped to 
58.5% according to 
<a href="https://www.iata.org/contentassets/6dfc19c3fdce4c9c8d5f1565c472b53f/2020-09-29-02-fr.pdf" target="_blank">IATA</a>, 
against 82.4% in 2019. Thus, due to this deterioration in the aircraft load factor, a paradoxical situation is present 
on the tool. Indeed, the deterioration in the aircraft load factor, considered as a potential improvement in 
efficiency, leads here to an increase in emissions compared to those expected without modification of the 
efficiency levers of action. + E/ASK

LAST OPTION (TO BE DONE CORRECTED)

Lastly, a last option is provided for studying societal aspects on the distribution of flights. The results of this 
part are based on the work of S. Gössling and A. Humpe in 2020 in 
<a href="https://www.sciencedirect.com/science/article/pii/S0959378020307779" target="_blank">*The global scale, distribution and growth of aviation: Implications for climate change*</a>. 
The authors show that only 11% of the world's population flies, and only between 2 and 4% go abroad. Moreover, 
'frequent flyers', about 1% of the world's population who fly an average of 56,000 km per year (about 3 
long-range trips), are responsible for about 50% of aviation CO<sub>2</sub> emissions, taking into account their number of 
flights but also the more frequent use of upper classes. Therefore, if on average these 'frequent flyers' flew half 
as often, aviation emissions would be reduced by 25%.

#### Aircraft fleet and operations

#### Aircraft energy

#### Climate & Energy

#### Allocations

### *Scenarios mode*



