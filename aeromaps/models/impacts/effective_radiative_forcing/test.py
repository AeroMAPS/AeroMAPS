from aeromaps.models.parameters import AllParameters
from aeromaps.models.impacts.emissions.non_co2_emissions import NonCO2Emissions
from aeromaps.models.impacts.effective_radiative_forcing.effective_radiative_forcing import (
    ERF,
)
from aeromaps.models.impacts.effective_radiative_forcing.effective_radiative_forcing import (
    DetailedERF,
)
from aeromaps.core.gemseo import AeromapsModelWrapper
from gemseo.api import create_discipline, generate_n2_plot

disc1 = AeromapsModelWrapper(model=NonCO2Emissions(parameters=AllParameters()))
disc2 = AeromapsModelWrapper(model=ERF(parameters=AllParameters()))
disc3 = AeromapsModelWrapper(model=DetailedERF(parameters=AllParameters()))

disciplines = [disc1, disc2, disc3]

generate_n2_plot(disciplines)

process = create_discipline("MDOChain", disciplines=disciplines)

outputs = process.execute()

print(outputs)
