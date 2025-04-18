import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class EnergyCarriersMeans(AeroMAPSModel):
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
                        f"{pathway.name}_net_mfsp": pd.Series([0.0]),
                        f"{pathway.name}_net_mfsp_without_carbon_tax": pd.Series([0.0]),
                        f"{pathway.name}_mfsp": pd.Series([0.0]),
                    }
                )

    def compute(self, input_data) -> dict:
        """
        This function loops through different energy types and computes the mean emissions
        """

        output_data = {}

        def default_series():
            return pd.Series(
                [0.0] * len(range(self.historic_start_year, self.end_year + 1)),
                index=range(self.historic_start_year, self.end_year + 1),
            )

        for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
            # Get the share of each pathway for this aircraft type
            pathways = self.pathways_manager.get(aircraft_type=aircraft_type)

            mean_emission_factor = default_series()
            mean_mfsp = default_series()
            mean_net_mfsp = default_series()
            mean_net_mfsp_without_carbon_tax = default_series()

            for pathway in pathways:
                share = input_data[f"{pathway.name}_share_{aircraft_type}"]
                mean_emission_factor += (
                    input_data[f"{pathway.name}_co2_emission_factor"] * share
                ).fillna(0) / 100

                mean_mfsp += (input_data[f"{pathway.name}_mfsp"] * share).fillna(0) / 100
                mean_net_mfsp += (input_data[f"{pathway.name}_net_mfsp"] * share).fillna(0) / 100
                mean_net_mfsp_without_carbon_tax += (
                    input_data[f"{pathway.name}_net_mfsp_without_carbon_tax"] * share
                ).fillna(0) / 100

            # store means in the inputs data
            output_data[f"{aircraft_type}_mean_co2_emission_factor"] = mean_emission_factor
            output_data[f"{aircraft_type}_mean_mfsp"] = mean_mfsp
            output_data[f"{aircraft_type}_mean_net_mfsp"] = mean_net_mfsp
            output_data[f"{aircraft_type}_mean_net_mfsp_without_carbon_tax"] = (
                mean_net_mfsp_without_carbon_tax
            )

        # get output data in the means
        self._store_outputs(output_data)

        return output_data
