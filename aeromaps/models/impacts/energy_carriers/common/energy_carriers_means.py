import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class EnergyCarriersMeanEmissions(AeroMAPSModel):
    """
    This model loops through the pathways and computes mean emissions
    """

    def __init__(
        self,
        name,
        configuration_data,
        pathways_manager,
        *args,
        **kwargs,
    ):
        super().__init__(
            name=name,
            model_type="custom",
            *args,
            **kwargs,
        )

        self.pathways_manager = pathways_manager

        self.input_names = {}
        self.output_names = {}

        for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
            self.output_names.update(
                {f"{aircraft_type}_mean_co2_emission_factor": pd.Series([0.0])}
            )
            for pathway in self.pathways_manager.get(aircraft_type=aircraft_type):
                self.input_names.update(
                    {
                        f"{pathway.name}_share_{aircraft_type}": pd.Series([0.0]),
                        f"{pathway.name}_co2_emission_factor": pd.Series([0.0]),
                    }
                )

        print(self.output_names)

    def compute(self, input_data) -> dict:
        """
        This function loops through different energy types and computes the mean emissions
        """
        output_data = {}

        for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
            # Get the share of each pathway for this aircraft type
            pathways = self.pathways_manager.get(aircraft_type=aircraft_type)
            mean_emission_factor = pd.Series([0.0])
            for pathway in pathways:
                share = input_data[f"{pathway.name}_share_{aircraft_type}"]
                emission_factor = input_data[f"{pathway.name}_co2_emission_factor"]
                mean_emission_factor = emission_factor * share / 100

            output_data[f"{aircraft_type}_mean_co2_emission_factor"] = mean_emission_factor

        self._store_outputs(output_data)
        print(output_data)
        return output_data
