# Air transport modeling

!!! warning "This part of the documentation is deprecated. It describes AeroMAPS in late 2023"
    It will be updated soon.!

The air transport system model presented in the AeroMAPS architecture rely on the modeling of levers of 
action to reduce the environmental impacts of the sector. Before describing their implementation in AeroMAPS, these 
levers of action are identified.


## Identification of the main levers of action

The different levers of action to reduce environmental impacts from air transport are identified and linked using an 
approach based on an adaptation of the Kaya identity for CO<sub>2</sub> emissions. It allows for obtaining the three 
main elements of the air transport system described in the AeroMAPS architecture.

The Kaya identity allows decomposing the global CO<sub>2</sub> emissions through demographic (population $POP$), 
economic (GDP per capita $GDP/POP$), and technological factors (energy intensity $E/GDP$ which can be assimilated to 
an output and the CO<sub>2</sub> content $CO_2/E$) {cite}`kaya1997environment`. The interest of this identity is that 
it indicates different levers to act on CO<sub>2</sub> {cite}`friedl2003determinants, lamb2021review`. Different 
studies, often based on specific decomposition methods, justify the choice of relevant parameters for decomposing 
emissions {cite}`ang2000survey, wang2015driving`. Nevertheless, some parameters are interdependent and interpretations 
can be complex {cite}`schandl2016decoupling`.

$CO_2 = POP \times \frac{GDP}{POP} \times \frac{E}{GDP} \times \frac{CO_2}{E}$

This identity can be adapted to air transport in many ways. In this work, a simplified decomposition is proposed via 
the following equation. The different parameters are justified by other works related to transportation and aviation 
{cite}`andreoni2012european, bigo2020transports, liu2017drives, sharmina2021decarbonising`. The first factor $RPK$ 
corresponds to air traffic. The second factor $E/RPK$ represents the ratio between the energy $E$ consumed by the 
sector and the air traffic. It corresponds to the average energy consumption of aircraft per passenger and 
per kilometer. The last factor $CO_2/E$ is the ratio between the sector's CO<sub>2</sub> emissions and the energy 
it consumes. It represents the CO<sub>2</sub> content of the energy used by the aircraft. These parameters thus 
represent different levers of action to decarbonize the aviation sector. 

$CO_2 = RPK \times \frac{E}{RPK} \times \frac{CO_2}{E}$

This equation can be modified or expanded. For example, additional coefficients can be added to include indirect 
CO<sub>2</sub> emissions or non-CO<sub>2</sub> climate effects. Similarly, the energy efficiency factor can be 
decomposed to separate technological and operational levers (load factor, improved flight or ground operations). 
Finally, as with the original Kaya identity, economic parameters can be incorporated.

It is important to note that these different factors are not totally independent. For example, a change in energy 
carrier may lead to an increase in energy consumption per passenger and per kilometer. Similarly, the level of air 
traffic can affect the load factor. Only the main interactions are considered in the following.

Before modeling the evolution of these different parameters, it is interesting to plot their historical evolution. 
Fig.1 represents the factors of the Kaya decomposition for aviation by also integrating the load factor $RPK/ASK$. 
Despite significant improvements in fuel efficiency via technology and load factor, CO<sub>2</sub> emissions from the 
sector have doubled due to the large increase in traffic. The CO<sub>2</sub> content of the energy has not changed due 
to the almost exclusive use of fossil kerosene.

![](/figs/kaya_aviation.svg)

*Fig.1 Historical evolution of the different parameters of Kaya identity for aviation.*

This work thus allows identifying and linking the different levers of action to reduce emissions from aviation. 
In the following, deterministic models for estimating the following parameters are presented:
- usage evolution through the evolution of air traffic ;
- energy efficiency through improvements in energy intensity with various levers (fleet renewal for more efficient aircraft, operations, load factor) ;
- energy decarbonization through the incorporation of alternative energy carriers to replace fossil fuel.
These models are particularly focused on their links to the sector's CO<sub>2</sub> emissions, but some elements 
concerning strategies against non-CO<sub>2</sub> effects are also provided.


## Main historical data

Before detailing the different models for representing the evolution of the different elements of air transport, 
historical data used are briefly discussed. Various air traffic data used are derived from
<a href="https://www.icao.int/annual-report-2019/Pages/the-world-of-air-transport-in-2019-statistical-results.aspx" target="_blank">International Civil Aviation Organization (ICAO)</a>, 
such as annual passenger numbers, RPK, RTK (Revenue Tonne Kilometer), ASK (Available Seat Kilometer) or aircraft load 
factor. Then, the historical evolution of the term $\frac{E}{RPK}$ is obtained using the previous traffic data and data 
on world kerosene consumption by the aviation sector, extracted and adapted from 
<a href="https://www.iea.org/sankey/#?c=World&s=Final%20consumption" target="_blank">International Energy Agency (IEA)</a>. 
Indeed, not all kerosene is consumed by commercial aviation alone. According to {cite}`gossling2020global`, 
military aviation consumes 8% of kerosene and general and private aviation 4%. The consumption of alternative energy 
carriers is considered as negligible in the last decades. Lastly, the term $\frac{CO_2}{E}$ is considered as constant 
for the same reason. The values considered depend on the scope chosen, in particular the inclusion of emissions related 
to fossil kerosene production. Here, mean values from a review paper {cite}`jing2022understanding` are used: a direct 
emission factor of 74.0 gCO<sub>2</sub>-eq/MJ<sub>fuel</sub> and a global (including fuel production) emission factor 
of 88.7 gCO<sub>2</sub>-eq/MJ<sub>fuel</sub>. The global emission factor is considered by default to facilitate the 
comparison with alternative energy carriers. As a consequence, using these data and including indirect CO<sub>2</sub> 
emissions, commercial aviation was for instance responsible for 2.6% of world CO<sub>2</sub> emissions in 2019 
(compared with data from <a href="https://www.globalcarbonproject.org/" target="_blank">Global Carbon Project</a> 
including fossil fuel combustion and land use). See for instance {cite}`delbecq2022isae` for more details. 


## Air traffic: usage evolution

The parameter that represents the evolution of air traffic is the RPK. The air traffic modeling is based on 
the study of worldwide historical data. The models presented in this section can be applied to the fleet as a whole or 
to the different markets described below. Before detailing these models, the categorization and calibration of the 
aviation market used in AeroMAPS is presented.


### Categorization and calibration of the aviation market

In order to be able to model scenarios in detail, the aviation market is divided into several representative 
categories, corresponding to aircraft fleet. Indeed, some market shares are likely to evolve differently. Moreover, 
some aircraft architectures (hydrogen aircraft, electric aircraft) could only be available for short distance missions 
in the medium term. 

Aircraft categories can be defined according to the distance flown (short, medium and long-haul) or the type of 
aircraft (regional, single-aisle, wide-body, or other). In this work, the following categories are considered:
- short-haul: passenger aircraft that fly less than 1,500 km ;
- medium-haul: passenger aircraft that fly between 1,500 km and 4,000 km ;
- long-haul: passenger aircraft that fly more than 4,000 km ;
- freight: cargo aircraft (dedicated freighter aircraft) or passenger aircraft including freight (belly cargo).

These different categories are heterogeneous because they include different types of aircraft. For simplicity, 
representative aircraft types are considered in the following. It is assumed that the short-haul category is composed 
of regional aircraft (with turbojets or turboprops) and narrow-body aircraft. It is also assumed that the medium-haul 
category is composed of narrow-body aircraft while the long-haul category is composed of wide-body aircraft. Finally, 
for freight, no representative aircraft are considered. It is assumed that aircraft in this category are a 
weighted average of the previous representative aircraft.

The aircraft fleet is then modeled, which will be useful for modeling the evolution of the aircraft fleet. In order to 
calibrate the average characteristics of the different fleet categories in 2019, a specific procedure is adopted to 
obtain a representative fleet. It is important to note that this approach is a model and that the aircraft fleet is 
actually more complex. In the following, the method is illustrated for the passenger aircraft categories.

First, the energy consumption per ASK is estimated for each category. The value per ASK is used to isolate the 
influence of air traffic levels. For this purpose, emission factors in gCO<sub>2</sub>/RPK are used. These are 
derived from the analysis of {cite}`icctco2`. They are then converted to energy consumption per ASK 
using the average aircraft load factor in 2019 and the emission factors from the previous section. The results are 
given in Tab.1.

| **Category**             | **Emission factor**       | **Energy consumption**    |
|--------------------------|---------------------------|---------------------------|
| Short-haul - Regional    | 172.8 gCO<sub>2</sub>/RPK | 1.95 MJ/ASK               |
| Short-haul - Narrow-body | 98.8 gCO<sub>2</sub>/RPK  | 1,11 MJ/ASK               |
| Medium-haul              | 76.9 gCO<sub>2</sub>/RPK  | 0.87 MJ/ASK               |
| Long-haul                | 89.9 gCO<sub>2</sub>/RPK  | 1.01 MJ/ASK               |

*Tab.1 Average aircraft fleet characteristics in 2019.*

Then, for each category, two representative planes are considered: one for the old generation, another for the 
most recent. The characteristics of these aircraft are constructed using a weighting of different aircraft on the 
market. This is done using data on the number of aircraft in service, their performance and their missions 
{cite}`icao18`. For example, for the medium-haul category, the older representative aircraft is a mix of Airbus and 
Boeing aircraft (A319, A320, A321, B737-700, B737-800, B737-900), while the newer representative aircraft is the 
Airbus A320neo. The results of energy consumption by ASK are then given in Tab.2.

| **Representative aircraft**   | **Energy consumption**   | **Representative distribution of the fleet**   |
|-------------------------------|--------------------------|------------------------------------------------|
| Mean aircraft                 | 0.87 MJ/ASK              | 100%                                           |
| Old aircraft                  | 0.92 MJ/ASK              | 77%                                            |
| Recent aircraft               | 0.70 MJ/ASK              | 23%                                            |

*Tab.2 Characteristics of representative aircraft for the medium-haul category.*

Finally, for each category, the representative distribution of old and recent aircraft is determined using the 
following equation. The results for the medium-haul category are, for example, given in the previous table. The values 
obtained are compared with the actual fleet to check the consistency of the selected representative aircraft.

$E_{mean} = x~E_{old} + (1-x)~E_{recent}$

where $E_{mean}$ is the average energy consumption per ASK for the fleet in the category, $E_{old}$ is the average 
energy consumption per ASK for the older representative aircraft, $E_{recent}$ is the average energy consumption 
per ASK for the newer representative aircraft, and $x$ is the representative share of older aircraft in the fleet.


### Air traffic evolution modeling

Historical data is used to derive the air traffic evolution model.
Fig.2 represents historical values since 1991 as well as a trend model. 
The latter was obtained using an exponential function with a fixed growth rate. The model is given in 
equation with $RPK_{1991}$ the value of RPK in 1991, $x$ the year and $\tau$ a 
smoothed growth rate. To determine $\tau$, an optimization is performed using the SLSQP method to minimize the 
Root Mean Square (RMS) error between the historical data and the model. This makes it possible to smooth out the 
values due to various political crises (September 11 attacks in the United States in 2001, 2008 financial crisis). 
The growth rate obtained is 5.5% over the period 1991--2019, with an RMS error of 0.032. By restricting the study 
to the last ten years, the growth rate obtained is then 6.5%, which shows an acceleration of air traffic growth 
in recent years.

$RPK(x) = RPK_{1991} ~ (1+\tau)^{x-1991}$

![](/figs/air_traffic.svg)

*Fig.2 Modeling the historical evolution of air traffic.*

This model is therefore relevant for modeling the evolution of air traffic. Therefore, the following model, indexed 
from 2019, is used to make projections on the evolution of air traffic. For more detailed scenarios, this model can 
be applied by decade using 
<a href="https://en.wikipedia.org/wiki/Compound_annual_growth_rate" target="_blank">Compound Annual Growth Rates (CAGR)</a>.

$RPK(x) = RPK_{2019} ~(1+\tau)^{x-2019}$

Nevertheless, the difficulty lies in estimating the future growth rate $\tau$. Indeed, the latter could be impacted for 
different reasons. For example, due to the saturation of certain markets (e.g. Europe), the industry anticipates a 
decline in this growth rate in the future. Similarly, this rate could become much lower or even negative (which 
means a decrease in air traffic) due to crises and/or economic, political, environmental or health measures such 
as the Covid-19 epidemic. Moreover, specific settings for the impact of the Covid-19 epidemic are proposed, defining a 
year of air traffic recovery compared to a certain level of air traffic compared to 2019.

Various industrial and institutional projections are available. Before the Covid-19 epidemic, Airbus and Boeing 
respectively projected an annual growth of the total distance flown of 4.4% and 4.7% from 2017 
{cite}`fichert2020aviation`. The ICAO projected an air traffic growth of 4.1% per year between 2015 and 2045. However, 
the Covid-19 epidemic has led to a downwards revision of these projections. ATAG now projects a 3.1% annual growth in 
air passenger traffic between 2019 and 2050 in its median scenario {cite}`atagwaypoint`, while Airbus projects a 3.6% 
annual growth for the period 2019-2041 {cite}`airbus`. Despite the Covid-19 health crisis, all the scenarios presented 
thus forecast a growth in air traffic in the coming decades.


## Aircraft fleet and operations: energy efficiency improvements

The parameter that represents the energy efficiency is the energy intensity per passenger per kilometer $E/RPK$. In 
this work, this parameter is influenced by three distinct levers: fleet renewal with more efficient aircraft, 
operations and load factor. In addition to these levers, specific measures for reducing non-CO<sub>2</sub> effects are
also modeled.

### Improvements of aircraft efficiency

Here, efficiency improvements through the use of more efficient aircraft are studied. The parameter modeled is thus 
the energy consumption per seat and per kilometer $E/ASK$. Two approaches are presented in the following. On the one 
hand, a so-called top-down approach is used to simply model the efficiency improvement via annual 
technological gains. On the other hand, an approach called bottom-up is used to model more finely the 
evolution of the fleet's energy efficiency by relying on gains per architecture and fleet renewal models. This more 
complex approach makes it possible to directly link aircraft design and prospective technological scenarios.


#### Top-down approach

In this approach, aircraft efficiency improvements are modelled via a gain in aircraft energy consumption per ASK. 
A fixed rate of change is chosen as a parameter. A positive rate implies a reduction in aircraft consumption per RPK. 
The negative case corresponding to a reduction in aircraft performance is not considered. This rate is expressed as 
a percentage (%). Fleet renewal is considered as regular and is therefore included in this rate. 

Thus, noting $E_{ASK}$ the energy consumed per ASK, $k$ a given year and $\tau$ the rate of technological improvement, 
the evolution of aircraft efficiency (per category) is given in the following equation.

$E_{ASK_{k+1}} = E_{ASK_{k}} (1-\tau)$

Hydrogen aircraft are taken into account considering specific models. For this, hydrogen aircraft introductions via 
logistic functions (detailed in the bottom-up approach) are used, correcting for the evolution of the energy efficiency 
of these architectures compared to conventional aircraft.

#### Bottom-up approach

In this second approach, the objective is to model the evolution of aircraft fleet energy efficiency using fleet 
renewal models. This approach is particularly interesting because it facilitates the links with aircraft design.

The fleet renewal models developed are based on logistic functions. A formulation of these functions is given 
in the following equation, with $A$, $k$ and $x_0$ parameters detailed in the following that allow to fit the model.

$f(x) = \frac{A}{1+e^{-k~(x-x_0)}}$

These functions, also called sigmoids or S-shaped curves, are particularly relevant to model the introduction of a 
product in a market. Consequently, they are used in multiple disciplinary fields 
{cite}`jarne2007s, kucharavy2011application, kucharavy2015application`: economics, sociology, demography, 
technology or even medicine. This type of functions has already been used in the scientific literature to study the 
renewal of aircraft fleets {cite}`grewe2021evaluating, hassan2017quantifying, hassan2015framework, hassan2018impact`.

In this work, the logistic functions correspond to the shares that different aircraft architectures represent in the 
fleet. In order to use these functions, a calibration of the different coefficients is necessary. The initialization 
of the data is performed using the approach with representative aircraft by category explained previously.

The coefficient $A$ represents the final value of the function. In this work, its value is initially set to 1 to model 
the fact that in the long run, a new aircraft architecture is totally imposed on the market. Then, the coefficient 
$k$ allows setting the speed of renewal of the fleet. It can be related to the duration $D$ to replace $(100-l)$% of 
the fleet using the following equation. Finally, the parameter $x_0$ is used to define the timing of the introduction
of the aircraft in the fleet. It can be computed from the following equation with $x_a$ the year of introduction of 
the aircraft, also called Entry-Into-Service (EIS).

$k = \frac{ln\left(\frac{100}{l}-1\right)}{D/2}$

$x_0 = x_a + D/2$

A limitation of these basic models is that they can only be directly used for a single homogeneous category. Indeed, 
it is not possible to model a category that is divided into two main architectures on the market. This aspect is 
however important to integrate specific architectures such as hydrogen aircraft on the short and medium-haul markets 
or narrow-body aircraft on the long-haul category (such as the Airbus A321XLR). Therefore, the models are adapted to 
allow the creation of subcategories. To do so, the $A$ coefficient is adjusted to vary the different market shares 
within the whole category.

Two examples of use are presented in the following. The medium-haul category is considered using representative 
aircraft detailed previously. A first simple example is given in Fig.3 which represents the distribution of 
different aircraft within a fleet. It is assumed that a new aircraft appears every 15 years with a period of 20 years 
for a replacement of 98% of the fleet, i.e. $l=2$. A second example is given in Fig.4. In addition to the previous 
assumptions, it is assumed that a new aircraft, representing a new sub-category, appears in 2035 and will eventually 
represent 50% of the market.

![](/figs/renewal_simple.svg)

*Fig.3 Basic use of fleet renewal models.*

![](/figs/renewal_complex.svg)

*Fig.4 Use of fleet renewal models including a subcategory.*

Knowing how the fleet is renewed from these models, it is possible to estimate the average energy consumption per 
seat and per kilometer of the $E_{mean}$ aircraft fleet for year $x$. The following equation is then used from the 
performance of each aircraft $E_i$ and the number of seat-kilometers achieved by each aircraft $ASK_i$. The latter
is obtained from the total ASK and the annual distribution from the fleet renewal models.

$E_{mean}(x) = \frac{\sum_{i} E_i ~ ASK_i(x)}{\sum_{i} ASK_i(x)}$

In addition to fuel consumption, the previous model can also be applied to other characteristics such as NO<sub>x</sub> 
or soot emissions. The fleet renewal models also allow to estimate the annual production of aircraft according to the 
traffic evolution.


### Improvements in aircraft operations

The improvement of operations concerns both the ground phases (taxiing, holding, etc.) and the flight phases (trajectory 
optimization, air traffic management, formation flights, etc.). The potential gains in fuel consumption estimated 
by the industry range from a few percent to about ten percent.

Regarding their modeling, it is complex to use historical data since they are often included in data on energy 
consumption per seat and per kilometer. Therefore, an approach based on estimates of future gains is considered using 
logistic functions as for fleet renewal models. This time, the parameter $A$ represents 
the achievable consumption gain. The parameter $k$ corresponds to the implementation speed of the operational measure, 
while the parameter $x_0$ allows to set the timing of the implementation. To model the improvement of the operations 
more finely, it is possible to superimpose different sigmoid functions, for example when the implementation times or 
the commissioning dates differ.


### Improvements in aircraft load factor

To model the evolution of the load factor, a similar approach to the one used for the 
energy consumption per ASK is used. The results are summarized in Fig.5. 

![](/figs/loadfactor_recap.svg)

*Fig.5 Modeling the trend projection of aircraft load factors.*

Historical data are modeled from the function given in the following equation for year $x$. The 
coefficients, given to three significant figures, were determined to minimize the RMS error between the historical 
data since 1991 and the model. A small value of 6.6.10<sup>-5</sup> is obtained. 

$LF(x) = 52.3 + \frac{36.7}{1+e^{-0.0776~(x-2000)}}$

The model is then used to obtain a trend projection of the load factor. It is interesting to note that the model 
converges towards a load factor of 89%, an ambitious value already reached by some airlines.

The projection finally is modeled using a second-order polynomial function because of its simplicity. The trend load 
factor $LF$ for year $x$ is then modeled using the following equation with parameters $a=-5.3.10^{-3}$ and $b=0.36$ 
(given with two significant figures). The RMS error obtained is then 5.3.10<sup>-7</sup>. 

$LF(x) = a~(x-2019)^2 + b~(x-2019) + 82.4$

Scenarios can thus be defined as for the energy consumption by ASK. For this, this model is used by modifying the 
parameters $a$ and $b$ in order to obtain the desired load factor in 2050.


### Improvements for reducing non-CO<sub>2</sub> effects

Specific strategies for reducing non-CO<sub>2</sub> effects through aircraft and operation improvements 
are also modeled. So far, only the main non-CO<sub>2</sub> effects (NO<sub>x</sub> and contrails) are studied.

Regarding NO<sub>x</sub> emissions, their reduction could lead to a reduction of the aviation effective radiative 
forcing, although there are still uncertainties about the future effect of NO<sub>x</sub> emissions on climate, 
depending in particular on NO<sub>x</sub> and methane background concentrations 
{cite}`skowron2021greater, terrenoire2022impact`. The reduction of emissions could nevertheless be achieved by reducing 
fuel consumption and/or lowering the NO<sub>x</sub> emission factor. Models similar to those for energy efficiency via 
fleet turnover are used to estimate the NO<sub>x</sub> emission factor. In particular, the equation for estimating the 
energy consumption in the bottom-up approach can be adapted by replacing the energy consumptions $E_i$ with the 
NO<sub>x</sub> emission factors per aircraft.

As far as contrails are concerned, several mitigation measures are studied. For instance, operational strategies, based 
on trajectory modification, are modeled since they represent promising strategies {cite}`gierens2008review`. These 
strategies could be applied on a reduced number of flights. Indeed, a study in the Japanese airspace shows that 2% of 
the flights are responsible for 80% of the contrails {cite}`teoh2020mitigating`. Another possibility is to modify 
the engines, in particular for reducing the amount of particles emitted {cite}`noppel2007overview`.
Overall, the implementation of operational strategies, possibly coupled with improved 
engines, could reduce the radiative forcing induced by condensation trails from 20% to more than 90%, for marginal 
additional fuel consumption {cite}`matthes2020climate, teoh2020mitigating`. In this work, simplified models, 
based on logistic functions as in fleet renewal models, are used to model the reduction of contrail-induced radiative 
forcing. This time, the parameter $A$ represents the final reduction allowed by the adopted measures. The parameter 
$k$ corresponds to the speed of implementation of the strategies, while the parameter $x_0$ allows to set the timing 
of the implementation.




## Aircraft energy: decarbonization of energy

The parameter that represents the decarbonization of energy is the CO<sub>2</sub> content of the energy $CO_2/E$. 
Its evolution is based on the introduction of alternative energy carriers in the fleet to replace fossil kerosene. The 
objective is therefore to estimate the emission factor of alternative energy carriers (only in the form of fuel so far) 
over their entire life cycle. The latter is expressed in gCO<sub>2</sub>-eq/MJ<sub>fuel</sub>, but the emissions will 
be directly assimilated to CO<sub>2</sub> for simplification purposes. In the following, two approaches are proposed. 
The first one is based on a detailed modeling of the fuels and their integration in the fleet. The second is a 
simplified approach based on a representative alternative energy carrier. However, the direct impact of alternative 
energy carriers on non-CO<sub>2</sub>, which is complex to evaluate {cite}`marquart2005upgraded, noppel2007overview`, 
is not directly considered so far because of the low maturity of the few models present in the literature 
{cite}`grewe2021evaluating, klower2021quantifying`.


### Detailed modeling

First, the objective is to estimate the main characteristics of alternative energy carriers. These are obtained by 
statistical analysis of data from the scientific literature. Many alternative energy carriers are considered to 
decarbonize aviation fuel. In this work, three main alternatives are studied: biofuels, hydrogen and electrofuels. 
Biofuels and electrofuels are drop-in fuels, while hydrogen requires specific aircraft architectures. The selectivity 
of fuels during their production is not directly considered.

Biofuels, also called BtL (Biomass-to-Liquid), are fuels derived from biomass. Estimating their emission factor is 
complex. In this work, several representative biofuels (not exhaustive) have been defined according to the resource and 
the production pathway. It is then possible to define a single representative biofuel by weighting. The resources 
considered in this work are waste (household waste or used cooking oil), forest residues, agricultural residues, 
dedicated energy crops (lignocellulose, sugar and starch-based materials or vegetable oils) and algae. Regarding the 
production pathways, HEFA (Hydroprocessed Esters and Fatty Acids), FT (Fischer-Tropsch) and ATJ (Alcohol-to-Jet) 
processes are considered. Not all routes and resources are directly compatible and the industrial production maturity 
of the different biofuels differs. 

The characteristics of these representative biofuels are statistically estimated to obtain the first quartile Q1, 
the median and the third quartile Q3. The data used are from 
{cite}`elgowainy2012development, prussi2021corsia, staples2014lifecycle, staples2018aviation, stratton2010life, zhao2021estimating` 
for emission factors, as well as from 
{cite}`de2015feasibility, han2013life, kreutz2008fischer, o2021estimating, pearlson2013techno, wise2017biojet` 
for other data. Emission factors and energy efficiencies are given in Tab. 3 and Tab.4 respectively. In addition, 
the HEFA process to convert oil to fuel requires the addition of hydrogen. A median value of 
9 MJ<sub>H</sub>2<sub></sub>/MJ</sub>fuel</sub> is used. 

| **Pathway** | **Resource**                     | **Q1** | **Median** | **Q3** |
|-------------|----------------------------------|--------|------------|--------|
| FT          | Municipal waste                  | -      | 27.6       | -      |
| FT          | Lignocelullose and residues      | 0.3    | 7.7        | 12.6   |
| ATJ         | Sugar and starch-based materials | 33.7   | 52.2       | 68.4   |
| HEFA        | Vegetable oils and algae         | 42.1   | 61         | 73.9   |
| HEFA        | Used cooking oil                 | -      | 20.7       | -      |
 
*Tab.3 Emission factors in gCO<sub>2</sub>-eq/MJ<sub>fuel</sub> for representative biofuels.*

| **Pathway**            | **Q1** | **Median** | **Q3** |
|------------------------|--------|------------|--------|
| FT                     | 0.4    | 0.46       | 0.49   |
| ATJ                    | 0.31   | 0.48       | 0.58   |
| HEFA -- Biomass to oil | 0.42   | 0.66       | 0.85   |
| HEFA -- Oil to fuel    | 0.71   | 0.88       | 0.92   |

*Tab.4 Energy efficiencies in MJ<sub>fuel</sub>/MJ<sub>biomass</sub> for representative biofuels.*

Hydrogen can be produced in several ways. In this work, five main pathways are considered. The estimated characteristics 
are derived from a statistical analysis of data from the references 
{cite}`aiehydrogen, dincer2016review, ji2021review, parkinson2019levelized, siddiqui2019well`. On the one hand, its 
production can be based on the use of fossil resources via the steam reformation of methane or the gasification of 
coal. These are the two most commonly used production methods today. The median values of the emission factors of 
these processes are respectively 100 gCO<sub>2</sub>-eq/MJ<sub>H<sub>2</sub></sub> and 
192 gCO<sub>2</sub>-eq/MJ<sub>H<sub>2</sub></sub>. The impact of these processes can be reduced by using carbon 
capture and storage solutions. In this case, the emission factors are respectively 
31 gCO<sub>2</sub>-eq/MJ<sub>H<sub>2</sub></sub> and 41 gCO<sub>2</sub>-eq/MJ<sub>H<sub>2</sub></sub>. On the other 
hand, hydrogen can be produced from electricity via the electrolysis of water. The emission factor of this hydrogen 
then depends on the emission factor of the electric mix and on a production energy efficiency with a median value of 
0.59. Finally, if the hydrogen is used in liquid state, additional losses must be taken into account for the 
liquefaction stage. 

Finally, electrofuels or e-fuels, also called PtL (Power-to-Liquid), are produced from electricity. They require 
hydrogen (obtained via electrolysis) and CO<sub>2</sub>, which could be captured directly from CO<sub>2</sub> emitting
plants or directly into the atmosphere. In this work, the emission factor of this type of fuel is obtained from the
emission factor of the electricity used and an energy efficiency of 0.4 {cite}`ueckerdt2021potential`.

In a second step, fleet introduction models are used for the drop-in fuels(biofuels and electrofuels). For this, 
reference values for the incorporation rates of these fuels in the fleet are chosen (every 10 years, every 5 years...). 
An interpolation with polynomial functions (linear, quadratic, cubic) is then performed to determine the annual values. 
An application with a quadratic interpolation, based on old objectives of the ReFuelEU initiative, is proposed on 
Fig.6. The knowledge of these incorporation rates and of the emission factors of the fuels thus makes it 
possible to determine the decarbonization rate of the fleet and thus the CO<sub>2</sub> content of the average energy 
used by the fleet annually. On the other hand, as far as hydrogen is concerned, specific models via the fleet renewal 
models are used, but the principle remains the same.

![](/figs/introduction_fuel.svg)

*Fig.6 Example scenario for introducing drop-in fuels into the fleet.*


### Simplified modeling (awaiting robust implementation)

A simplified approach is also possible. In the latter, an average alternative energy carrier is considered. The 
disadvantage of this approach is that it does not allow to distinguish different types of fuel, and in particular 
hydrogen which requires specific architectures. Moreover, it does not allow to easily model the evolution of the 
emission factor of a fuel, especially for those based on electricity.

First, the notion of decarbonization rate is introduced. The decarbonization rate of a fuel is defined as the reduction
of its CO content compared to fossil kerosene. For example, taking the emission factor of fossil kerosene of 
88.5 gCO<sub>2</sub>-eq/MJ<sub>fuel</sub> (including direct and indirect emissions), a decarbonization rate of a 
fuel of 75% means that its emission factor is 22.1 gCO<sub>2</sub>-eq/MJ<sub>fuel</sub>. More generally, the 
decarbonization rate of the aircraft fleet is defined as the reduction in the CO<sub>2</sub> content of the average 
energy used by the fleet compared to that of a similar fleet operating on fossil kerosene. 

In this approach, to model the rate of decarbonization of the fleet, logistic functions are used. This time, the 
parameter $A$ represents the final decarbonization rate of the fleet. This parameter corresponds to the 
decarbonization rate of the average alternative energy carrier considered. The parameter $k$ corresponds to the 
introduction speed of the alternative energy carriers in the fleet, while the parameter $x_0$ allows to set the 
integration timing. 
