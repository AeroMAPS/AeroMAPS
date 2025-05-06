import warnings

import numpy as np
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

        aircraft_types = ["dropin_fuel", "hydrogen", "electric"]

        for aircraft_type in aircraft_types:
            self.output_names.update(
                {
                    f"{aircraft_type}_mean_co2_emission_factor": pd.Series([0.0]),
                    f"{aircraft_type}_mean_mfsp": pd.Series([0.0]),
                    f"{aircraft_type}_mean_net_mfsp": pd.Series([0.0]),
                    f"{aircraft_type}_mean_net_mfsp_without_carbon_tax": pd.Series([0.0]),
                    f"{aircraft_type}_mean_carbon_tax_supplement": pd.Series([0.0]),
                }
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

        aircraft_types = ["dropin_fuel", "hydrogen", "electric"]

        for aircraft_type in aircraft_types:
            # Get the share of each pathway for this aircraft type
            pathways = self.pathways_manager.get(aircraft_type=aircraft_type)

            mean_emission_factor = default_series()
            mean_mfsp = default_series()
            mean_net_mfsp = default_series()
            mean_net_mfsp_without_carbon_tax = default_series()
            mean_carbon_tax_supplement = default_series()
            marginal_net_mfsp = default_series()
            cumulative_share = default_series()

            for pathway in pathways:
                share = input_data[f"{pathway.name}_share_{aircraft_type}"]
                cumulative_share = cumulative_share + share.fillna(0) / 100
                mean_emission_factor += (
                    input_data[f"{pathway.name}_co2_emission_factor"] * share
                ).fillna(0) / 100

                mean_mfsp += (input_data[f"{pathway.name}_mfsp"] * share).fillna(0) / 100
                mean_net_mfsp += (input_data[f"{pathway.name}_net_mfsp"] * share).fillna(0) / 100
                mean_net_mfsp_without_carbon_tax += (
                    input_data[f"{pathway.name}_net_mfsp_without_carbon_tax"] * share
                ).fillna(0) / 100
                mean_carbon_tax_supplement += (
                    (mean_net_mfsp - mean_net_mfsp_without_carbon_tax) * share
                ).fillna(0) / 100

                # compute the marginal net MFSP for each aircraft type: the most expensive pathways each year
                marginal_net_mfsp = marginal_net_mfsp.where(
                    marginal_net_mfsp > (input_data[f"{pathway.name}_net_mfsp"]).fillna(0),
                    (input_data[f"{pathway.name}_net_mfsp"]).fillna(0),
                )

            # if no energy consumption for any year, replace by nan. if all pathways not equal to 100%, triggers warning
            valid_years = cumulative_share.replace(0, np.nan)
            # check that there are only ones in the cumulative share

            faulty_years = valid_years[valid_years.notna() & (valid_years.round(3) != 1.000)].index
            if not faulty_years.empty:
                warnings.warn(
                    f"AeroMAPS internal error: sum of pathway shares for {aircraft_type} is not equal to 100% in the following years: {faulty_years.tolist()}"
                )

            # store means in the inputs data, and multiply by cumulative share to set nans when there s no energy consumption
            output_data[f"{aircraft_type}_mean_co2_emission_factor"] = (
                mean_emission_factor * valid_years
            )
            output_data[f"{aircraft_type}_mean_mfsp"] = mean_mfsp * valid_years
            output_data[f"{aircraft_type}_mean_net_mfsp"] = mean_net_mfsp * valid_years
            output_data[f"{aircraft_type}_mean_net_mfsp_without_carbon_tax"] = (
                mean_net_mfsp_without_carbon_tax * valid_years
            )
            output_data[f"{aircraft_type}_mean_carbon_tax_supplement"] = (
                mean_carbon_tax_supplement * valid_years
            )
            output_data[f"{aircraft_type}_marginal_net_mfsp"] = marginal_net_mfsp * valid_years

        # get output data in the means
        self._store_outputs(output_data)

        return output_data
