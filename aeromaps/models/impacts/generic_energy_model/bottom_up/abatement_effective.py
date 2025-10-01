import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class EnergyAbatementEffective(AeroMAPSModel):
    """ """

    def __init__(self, name, pathway_name, *args, **kwargs):
        super().__init__(
            name=name,
            model_type="custom",
            *args,
            **kwargs,
        )
        self.pathway_name = pathway_name

        # Inputs needed: discounted costs, unitary emissions, discounted emissions
        self.input_names = {
            f"{self.pathway_name}_energy_consumption": pd.Series([0.0]),
            f"{self.pathway_name}_mean_co2_emission_factor": pd.Series([0.0]),
            "cac_reference_co2_emission_factor": pd.Series([0.0]),
        }

        # Outputs: effective abatement volume (unit: tCO2)
        self.output_names = {
            f"{self.pathway_name}_abatement_effective": pd.Series([0.0]),
        }

    def compute(self, input_data) -> dict:
        """
        Compute the specific abatement cost and generic specific abatement cost for each vintage.
        """
        avoided_emission_factor = (
            input_data["cac_reference_co2_emission_factor"]
            - input_data[f"{self.pathway_name}_mean_co2_emission_factor"]
        )
        abatement_effective = (
            input_data[f"{self.pathway_name}_energy_consumption"]
            * avoided_emission_factor
            / 1000000
        )  # Convert to tCO2
        output_data = {f"{self.pathway_name}_abatement_effective": abatement_effective}

        self._store_outputs(output_data)
        return output_data
