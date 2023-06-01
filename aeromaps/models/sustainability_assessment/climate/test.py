from gemseo.core.discipline import MDODiscipline

from aeromaps.models.parameters import AllParameters
from aeromaps.models.sustainability_assessment.climate.carbon_budgets import GrossCarbonBudget
from aeromaps.models.sustainability_assessment.climate.equivalent_carbon_budgets import (
    EquivalentGrossCarbonBudget,
)
from aeromaps.models.sustainability_assessment.energy.resources_availability import (
    BiomassAvailability,
    ElectricityAvailability,
)
from aeromaps.core.gemseo import AeromapsModelWrapper
from gemseo.api import create_discipline, generate_n2_plot, create_mda

disc1 = AeromapsModelWrapper(model=GrossCarbonBudget(parameters=AllParameters()))
disc2 = AeromapsModelWrapper(model=EquivalentGrossCarbonBudget(parameters=AllParameters()))
disc3 = AeromapsModelWrapper(model=BiomassAvailability(parameters=AllParameters()))
disc4 = AeromapsModelWrapper(model=ElectricityAvailability(parameters=AllParameters()))

disciplines = [disc1, disc2, disc3, disc4]

# generate_n2_plot(disciplines)

# process = create_discipline(
#     "MDOChain", disciplines=disciplines, grammar_type=MDODiscipline.SIMPLE_GRAMMAR_TYPE
# )
process = create_mda(
    "MDAChain", disciplines=disciplines, grammar_type=MDODiscipline.SIMPLE_GRAMMAR_TYPE
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
