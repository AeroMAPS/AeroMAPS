import numpy as np
import pandas as pd
from aeromaps.models.base import AeroMAPSModel


class BottomUpCapacity(AeroMAPSModel):
    """
    Computes annual capacity additions required to follow an energy consumption trajectory.
    """

    def __init__(self, name, configuration_data, *args, **kwargs):
        super().__init__(
            name=name,
            model_type="custom",
            *args,
            **kwargs,
        )
        self.pathway_name = configuration_data["name"]
        # Inputs
        self.input_names = {
            f"{self.pathway_name}_energy_consumption": pd.Series([0.0]),
            f"{self.pathway_name}_plant_load_factor": 0.0,
            f"{self.pathway_name}_plant_lifespan": 0.0,
            f"{self.pathway_name}_technology_introduction_year": 0,
            f"{self.pathway_name}_technology_introduction_volume": 0.0,
        }
        # Outputs
        self.output_names = {
            f"{self.pathway_name}_plant_building_scenario": pd.Series([0.0]),
            f"{self.pathway_name}_plant_operating_capacity": pd.Series([0.0]),
            f"{self.pathway_name}_energy_unused": pd.Series([0.0]),
        }

    def compute(self, input_data) -> dict:
        # Get the energy consumption trajectory and capacity factor
        energy_required = input_data.get(f"{self.pathway_name}_energy_consumption")
        plant_load_factor = input_data.get(f"{self.pathway_name}_plant_load_factor")
        plant_lifespan = input_data.get(f"{self.pathway_name}_plant_lifespan")
        technology_introduction = input_data.get(
            f"{self.pathway_name}_technology_introduction_year"
        )
        technology_introduction_volume = input_data.get(
            f"{self.pathway_name}_technology_introduction_volume"
        )

        # The hard part in this model is to be able to reconstruct the commissioning history of plants
        # however, we do not have access to the energy consumption before the scenarios,
        # which influences the availability of plants, and thus the need to build new ones.
        # The idea of the code is therefore to construct a virtual energy demand since the technology introduction year,
        # if needed, and to concatenate it with the real energy demand from the historic start year.
        # NB: that is transparent for alternative pathways that start after the historic start year.

        if energy_required.loc[self.historic_start_year] > 1e-9:
            if not technology_introduction:
                raise ValueError(
                    f"Technology introduction year for {self.pathway_name} must be specified if there is energy consumption before the historic start year."
                )
            else:
                first_plant_year = technology_introduction
                first_plant_volume = technology_introduction_volume
                virtual_cagr = (
                    energy_required.loc[self.historic_start_year] / first_plant_volume
                ) ** (1 / (self.historic_start_year - first_plant_year)) - 1
                # populate the energy_required Series with virtual years
                for virtual_year in range(first_plant_year, self.historic_start_year):
                    virtual_demand = first_plant_volume * (1 + virtual_cagr) ** (
                        virtual_year - first_plant_year
                    )
                    energy_required.loc[virtual_year] = virtual_demand
                energy_required.sort_index(inplace=True)

        years = energy_required.index

        plant_building_scenario = pd.Series(np.zeros(len(years)), years)
        plant_available_scenario = pd.Series(np.zeros(len(years)), years)
        energy_produced = pd.Series(np.zeros(len(years)), years)
        energy_unused = pd.Series(np.zeros(len(years)), years)

        for year in years:
            missing_production = energy_required[year] - energy_produced[year]
            if missing_production <= 0.0:
                energy_unused[year] = missing_production
            else:
                # Calculate the required capacity to meet the energy demand
                required_capacity = (
                    missing_production / plant_load_factor / 365
                )  # Absolute output in MJ per day
                plant_building_scenario[year] += required_capacity
                # Update the available capacity and production for plant lifespan
                plant_available_scenario.loc[year : year + plant_lifespan - 1] += required_capacity
                energy_produced.loc[year : year + plant_lifespan - 1] += missing_production

        # restrict the outputs to prospective years
        plant_building_scenario = plant_building_scenario.loc[
            self.prospection_start_year : self.end_year
        ]
        plant_available_scenario = plant_available_scenario.loc[
            self.prospection_start_year : self.end_year
        ]
        energy_unused = energy_unused.loc[self.prospection_start_year : self.end_year]

        output_data = {
            f"{self.pathway_name}_plant_building_scenario": plant_building_scenario,
            f"{self.pathway_name}_plant_operating_capacity": plant_available_scenario,
            f"{self.pathway_name}_energy_unused": -energy_unused,
        }

        self._store_outputs(output_data)

        return output_data
