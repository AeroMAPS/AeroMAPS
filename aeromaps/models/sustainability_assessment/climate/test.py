from gemseo.core.discipline import Discipline

from aeromaps.models.parameters import AllParameters
from aeromaps.models.sustainability_assessment.climate.carbon_budgets import GrossCarbonBudget
from aeromaps.models.sustainability_assessment.climate.equivalent_carbon_budgets import (
    EquivalentGrossCarbonBudget,
)
from aeromaps.models.sustainability_assessment.energy.resources_availability import (
    BiomassAvailability,
    ElectricityAvailability,
)
from aeromaps.core.gemseo import AeroMAPSModelWrapper
from gemseo.api import create_mda

disc1 = AeroMAPSModelWrapper(model=GrossCarbonBudget(parameters=AllParameters()))
disc2 = AeroMAPSModelWrapper(model=EquivalentGrossCarbonBudget(parameters=AllParameters()))
disc3 = AeroMAPSModelWrapper(model=BiomassAvailability(parameters=AllParameters()))
disc4 = AeroMAPSModelWrapper(model=ElectricityAvailability(parameters=AllParameters()))

disciplines = [disc1, disc2, disc3, disc4]

# generate_n2_plot(disciplines)

# process = create_discipline(
#     "MDOChain", disciplines=disciplines, grammar_type=Discipline.SIMPLE_GRAMMAR_TYPE
# )
process = create_mda(
    "MDAChain", disciplines=disciplines, grammar_type=Discipline.SIMPLE_GRAMMAR_TYPE
)

outputs = process.execute()

print(outputs)

disc1.model.parameters.net_carbon_budget = 300.0

for disc in disciplines:
    disc.update_defaults()

# process._update_default_inputs()
process._set_default_inputs()

outputs = process.execute()

print(outputs)
