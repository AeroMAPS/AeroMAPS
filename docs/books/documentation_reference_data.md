# Reference data

The set of reference data and associated sources is given in the following. The detailed value can also be found on 
the graphical user interface in the tab <b>Data</b>.

## Air transport

The various air traffic data are derived from the ICAO (International Civil Aviation Organisation), such as annual 
passenger numbers, Revenue Passenger Kilometrer (RPK) or aircraft load factor. 
    
The data on world kerosene consumption by the aviation sector are from the 
<a href="https://www.iea.org/sankey/#?c=World&s=Final%20consumption" target="_blank">International Energy Agency (IEA)</a>. 
However, not all kerosene is consumed by commercial aviation alone. According to {cite}`gossling2020global`, 
military aviation consumes 8% of kerosene and general and private aviation 4%. 
    
Then, the coefficients for the different pollutants (also called EI for Emission Index) were taken from 
{cite}`lee2021contribution`. They make it possible to obtain different emissions (NO<sub>x</sub>, SO<sub>x</sub>...) 
depending on fuel consumption (or emissions of CO<sub>2</sub>). 
    
Finally, the coefficient corresponding to other life cycle emissions (excluding combustion and fuel production), 
of the order of 2%, was obtained by taking an intermediate value from {cite}`pinheiro2020sustainability`.

Using these data and including indirect CO<sub>2</sub> emissions, commercial aviation was responsible for 2.6% of 
global CO<sub>2</sub> emissions in 2019. Also including non-CO<sub>2</sub> effects, aviation (including private and 
military) generated 3.8% of the effective radiative forcing between 1750 and 2018 and commercial aviation is 
responsible for 5.1% of the increase in effective radiative forcing over a more recent period (2000-2018).
    

## Effective radiative forcing

Data on effective radiative forcing of aviation are obtained using {cite}`lee2021contribution`.
This paper quantifies the effects of aviation on the climate using the notion of effective radiative forcing. Thus, 
the climate impact of each contributor can be approximated by multiplying the amount of emissions (or the total 
distance for contrails) with a factor obtained from the data of Lee et al. The factors considered are as follows:
<ul>
<li>One for CO<sub>2</sub> emissions, considering cumulative and not annual emissions to take into account the long lifetime of this gas in the atmosphere, expressed in $W/m^2/gCO_{2cum}$</li>
<li>One for NO<sub>x</sub> emissions, expressed in $W/m^2/gNOx$</li>
<li>One for water vapour emissions, expressed in $W/m^2/gH_2O$</li>
<li>Two for aerosols: one for SO<sub>x</sub> emissions, expressed in $W/m^2/gSO_2$; one for black carbon emissions, expressed in $W/m^2/gBC$</li>
<li>One for contrails, expressed in $W/m^2/km$ where the distance corresponds to the total distance travelled by aircraft annually</li>
</ul>

## Others

The coefficients to obtain the CO<sub>2</sub> emissions associated with the production and combustion of kerosene 
have been extracted from the <a href="https://www.bilans-ges.ademe.fr/docutheque/docs/%5BBase%20Carbone%5D%20Documentation%20g%C3%A9n%C3%A9rale%20v11.5.pdf" target="_blank">carbon base</a>
from Agence française de la transition écologique called ADEME. The annual global CO<sub>2</sub> emissions, including 
fossil fuel combustion and deforestation activities, come from <a href="https://www.globalcarbonproject.org/" target="_blank">Global Carbon Project</a>
while annual global GHG emissions, including land-use change, are from <a href="https://www.globalcarbonproject.org/" target="_blank">*Emissions Gap Report 2020* from ONU</a>.

