"""
Module to compute effective carbon abatement for each energy pathway.
"""

import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class EnergyAbatementEffective(AeroMAPSModel):
    """
    This class computes the effective carbon abatement (i.e CO2 "avoided" by an option) for a given pathway.

    Parameters
    ----------
    name : str
        Name of the model instance ('f"{pathway_name}_abatement_effective"' by default).
    pathway_name : str
        Name of the energy pathway for which to compute the effective abatement.

    Attributes
    ----------
    input_names : dict
        Dictionary of input variable names populated at model initialisation before MDA chain creation.
    output_names : dict
        Dictionary of output variable names populated at model initialisation before MDA chain creation.
    """

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
        Compute the abatement effective due to the pathway.

        Parameters
        ----------
        input_data
            Dictionary containing all input data required for the computation, completed at model instantiation with information from yaml files and outputs of other models.

        Returns
        -------
        output_data
            Dictionary containing all output data resulting from the computation. Contains outputs defined during model instantiation.
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
