"""
environmental

======
Module to compute pathway emissions based on bottom-up plant descriptions (EIS and capacity).
"""

import warnings

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel
from aeromaps.utils.functions import _get_value_for_year, _custom_series_addition


class BottomUpEnvironmental(AeroMAPSModel):
    """
    Generic environmental model for aviation energy carriers, relying on user's description of the carriers in the configuration file.

    Parameters
    ----------
    name : str
        Name of the model instance ('f"{pathway_name}_bottom_up_unit_environmental"' by default).
    configuration_data : dict
        Configuration data for the energy pathway from the configuration file.
    resources_data : dict
        Configuration data for the resources from the configuration file.
    processes_data : dict
        Configuration data for the processes from the configuration file.

    Attributes
    ----------
    input_names : dict
        Dictionary of input variable names populated at model initialisation before MDA chain creation.
    output_names : dict
        Dictionary of output variable names populated at model initialisation before MDA chain creation.

    Warning
    -------
    Description of i/o variables is very limited for models with dynamic i/o names. They are defined in .yaml configuration files.

    """

    def __init__(
        self,
        name,
        configuration_data,
        resources_data,
        processes_data,
        *args,
        **kwargs,
    ):
        super().__init__(
            name=name,
            model_type="custom",
            # inputs/outputs are defined in __init__ rather than auto generated from compute() signature
            *args,
            **kwargs,
        )
        # Get the name of the pathway
        self.pathway_name = configuration_data["name"]

        # Get the inputs from the configuration file: two options
        # 1. All inputs of a certain category in the yaml file
        for key, val in configuration_data.get("inputs").get("environmental", {}).items():
            # TODO initialize with zeros instead of actual val?
            self.input_names[key] = val
        for key, val in configuration_data.get("inputs").get("technical", {}).items():
            # TODO initialize with zeros instead of actual val? How to better get rid of unnecessary variables
            if (
                key == f"{self.pathway_name}_resource_names"
                or key == f"{self.pathway_name}_processes_names"
            ):
                pass  # avoid having strings as variable in gemseo, not needed as variables
            else:
                self.input_names[key] = val

        # 2. Set individual inputs, coming either from other models or from the yaml as well
        self.input_names.update(
            {
                f"{self.pathway_name}_energy_production_commissioned": pd.Series([0.0]),
                f"{self.pathway_name}_energy_consumption": pd.Series([0.0]),
                f"{self.pathway_name}_energy_unused": pd.Series([0.0]),
            }
        )

        # TODO find a better way to get the resource inputs ? Now better with the list(str) argument of each pathway .yaml
        # 3. Getting resources is a bit more complex as we need to get necessary resources for the pathway
        self.resource_keys = (
            configuration_data.get("inputs")
            .get("technical", {})
            .get(f"{self.pathway_name}_resource_names", [])
        ).copy()

        self.process_keys = (
            configuration_data.get("inputs")
            .get("technical", {})
            .get(f"{self.pathway_name}_processes_names", [])
        ).copy()

        # Adding resources-linked inputs and outputs
        for key in self.resource_keys:
            self.output_names[
                f"{self.pathway_name}_excluding_processes_{key}_mean_co2_emission_factor"
            ] = pd.Series([0.0])
            self.output_names[
                f"{self.pathway_name}_excluding_processes_{key}_total_consumption"
            ] = pd.Series([0.0])
            self.output_names[
                f"{self.pathway_name}_excluding_processes_{key}_total_mobilised_with_selectivity"
            ] = pd.Series([0.0])

            self.output_names[f"{self.pathway_name}_{key}_total_consumption"] = pd.Series([0.0])
            self.output_names[f"{self.pathway_name}_{key}_total_mobilised_with_selectivity"] = (
                pd.Series([0.0])
            )

        for process_key in self.process_keys:
            for key, val in processes_data[process_key].get("inputs").get("technical", {}).items():
                if key == f"{process_key}_resource_names":
                    resources = (
                        processes_data[process_key]
                        .get("inputs")
                        .get("technical", {})
                        .get(f"{process_key}_resource_names", [])
                    ).copy()
                    self.resource_keys.extend(resources)
                    for resource in resources:
                        self.output_names[
                            f"{self.pathway_name}_{process_key}_{resource}_mean_co2_emission_factor"
                        ] = pd.Series([0.0])
                        self.output_names[
                            f"{self.pathway_name}_{process_key}_{resource}_total_consumption"
                        ] = pd.Series([0.0])
                        self.output_names[
                            f"{self.pathway_name}_{process_key}_{resource}_total_mobilised_with_selectivity"
                        ] = pd.Series([0.0])
                else:
                    # TODO initialize with zeros instead of actual val?
                    self.input_names[key] = val

            for key, val in processes_data[process_key].get("inputs").get("economics", {}).items():
                # TODO initialize with zeros instead of actual val?
                self.input_names[key] = val
            self.output_names[
                f"{self.pathway_name}_{process_key}_without_resources_mean_co2_emission_factor"
            ] = pd.Series([0.0])

        # Getting unique resources
        self.resource_keys = list(set(self.resource_keys))

        for key in self.resource_keys:
            if f"{key}_co2_emission_factor" in resources_data[key]["specifications"]:
                self.input_names[f"{key}_co2_emission_factor"] = pd.Series([0.0])

            self.output_names[f"{self.pathway_name}_{key}_total_consumption"] = pd.Series([0.0])
            self.output_names[f"{self.pathway_name}_{key}_total_mobilised_with_selectivity"] = (
                pd.Series([0.0])
            )

        if configuration_data.get("compute_all_years"):
            self.compute_all_years = True
        else:
            self.compute_all_years = False
        # Checking if we need to compute the CAC
        if configuration_data.get("abatement_cost"):
            self.compute_abatement_cost = True
            self.input_names["exogenous_carbon_price_trajectory"] = pd.Series([0.0])
            self.input_names["social_discount_rate"] = 0.0
            self.output_names[f"{self.pathway_name}_lifespan_unitary_emissions"] = pd.Series([0.0])
            self.output_names[f"{self.pathway_name}_lifespan_discounted_unitary_emissions"] = (
                pd.Series([0.0])
            )
        else:
            self.compute_abatement_cost = False

        # Fill in the other expected outputs with names from the compute method
        self.output_names.update(
            {
                f"{self.pathway_name}_mean_co2_emission_factor": pd.Series([0.0]),
                f"{self.pathway_name}_vintage_eis_co2_emission_factor": pd.Series([0.0]),
                f"{self.pathway_name}_total_co2_emissions": pd.Series([0.0]),
                f"{self.pathway_name}_mean_co2_emission_factor_without_resource": pd.Series([0.0]),
            }
        )

    def compute(self, input_data) -> dict:
        """
        Compute the environmental impact of the energy carrier pathway.
        Each plant (vintage) is commissioned with the characteristics of its commissioning year,
        and its emissions are distributed over its lifespan, weighted by its share in annual production.

        Parameters
        ----------
        input_data
            Dictionary containing all input data required for the computation, completed at model instantiation with information from yaml files and outputs of other models.

        Returns
        -------
        output_data
            Dictionary containing all output data resulting from the computation. Contains outputs defined during model instantiation.
        """

        optional_nan_series = pd.Series(
            np.nan, index=range(self.historic_start_year, self.end_year + 1)
        )
        energy_production_commissioned = input_data[
            f"{self.pathway_name}_energy_production_commissioned"
        ]
        energy_consumption = input_data[f"{self.pathway_name}_energy_consumption"]
        energy_unused = input_data[f"{self.pathway_name}_energy_unused"]

        # Prepare outputs
        output_data = {k: optional_nan_series.copy() for k in self.output_names}

        co2_emission_factor = optional_nan_series.copy()

        # For each vintage, compute its emission factor and contribution
        for year, needed_capacity in energy_production_commissioned.items():
            lifespan = _get_value_for_year(
                input_data.get(f"{self.pathway_name}_eis_plant_lifespan"), year, 25
            )
            # The plant will operate from year to year+lifespan (or until end_year)
            vintage_indexes = range(year, year + lifespan)
            vintage_emission_factor = pd.Series(np.nan, index=vintage_indexes)
            if (
                energy_consumption[year] > 0
                and needed_capacity <= 0
                and self.compute_abatement_cost
                and not self.compute_all_years
            ):
                warnings.warn(
                    f"\n⚠️ For {self.pathway_name}, no plants commissioned in {year}. Unable to compute "
                    f"CAC: compute_all_years = False. Set it true to avoid NaN values in the MACC for this year."
                )
            if needed_capacity > 0 or self.compute_all_years:
                if needed_capacity < 0:
                    warnings.warn(
                        f"Negative needed capacity for {self.pathway_name} in year {year}. "
                        "This is not expected despite the compute_all_years option being set to True."
                    )
                # relative contibution of the vintage
                relative_share = needed_capacity / (energy_consumption + energy_unused)
                relative_share = relative_share.loc[year : year + lifespan - 1]

                # I -- First lets compute the core MFSP (no resources, no processes)
                # Get the inputs for the year
                core_emission_factor = _get_value_for_year(
                    input_data.get(f"{self.pathway_name}_eis_co2_emission_factor_without_resource"),
                    year,
                    0.0,
                )
                kerosene_selectivity = _get_value_for_year(
                    input_data.get(f"{self.pathway_name}_eis_kerosene_selectivity"), year, 1.0
                )

                vintage_emission_factor = _custom_series_addition(
                    vintage_emission_factor, core_emission_factor
                )
                output_data[f"{self.pathway_name}_mean_co2_emission_factor_without_resource"].loc[
                    year : year + lifespan - 1
                ] = _custom_series_addition(
                    output_data[
                        f"{self.pathway_name}_mean_co2_emission_factor_without_resource"
                    ].loc[year : year + lifespan - 1],
                    core_emission_factor * relative_share,
                )

                # II) Now let's compute the emissions from resources that are linked to the pathway itself
                for key in self.resource_keys:
                    specific_consumption = _get_value_for_year(
                        input_data.get(
                            f"{self.pathway_name}_eis_resource_specific_consumption_{key}"
                        ),
                        year,
                        None,
                    )

                    total_ressource_consumption = optional_nan_series.copy()
                    total_ressource_mobilised_with_selectivity = optional_nan_series.copy()

                    if specific_consumption is not None:
                        resources_consumption = (
                            energy_production_commissioned[year] * specific_consumption
                        )
                        resources_consumption_with_selectivity = (
                            resources_consumption * kerosene_selectivity
                        )

                        total_ressource_consumption.loc[year : year + lifespan - 1] = (
                            resources_consumption
                        )
                        total_ressource_mobilised_with_selectivity.loc[
                            year : year + lifespan - 1
                        ] = resources_consumption_with_selectivity

                        output_data[
                            f"{self.pathway_name}_excluding_processes_{key}_total_consumption"
                        ].loc[year : year + lifespan - 1] += resources_consumption
                        output_data[
                            f"{self.pathway_name}_excluding_processes_{key}_total_mobilised_with_selectivity"
                        ].loc[year : year + lifespan - 1] += resources_consumption_with_selectivity

                        # Get the CO2 emission factor for the resource
                        unit_emissions = input_data.get(
                            f"{key}_co2_emission_factor", optional_nan_series
                        )
                        # beyond sceanrio end year, we stick to last known value
                        unit_emissions = unit_emissions.reindex(
                            range(year, year + lifespan), method="ffill"
                        )

                        # get resource emission per unit of energy
                        co2_emission_factor_ressource = specific_consumption * unit_emissions
                        vintage_emission_factor = _custom_series_addition(
                            vintage_emission_factor, co2_emission_factor_ressource
                        )
                        output_data[
                            f"{self.pathway_name}_excluding_processes_{key}_mean_co2_emission_factor"
                        ].loc[year : year + lifespan - 1] = _custom_series_addition(
                            output_data[
                                f"{self.pathway_name}_excluding_processes_{key}_mean_co2_emission_factor"
                            ].loc[year : year + lifespan - 1],
                            co2_emission_factor_ressource * relative_share,
                        )
                    # III) Now let's compute the emissions from processes that gets a ressource
                    for process_key in self.process_keys:
                        specific_consumption = _get_value_for_year(
                            input_data.get(
                                f"{process_key}_eis_resource_specific_consumption_{key}"
                            ),
                            year,
                            None,
                        )
                        if specific_consumption is not None:
                            resources_consumption = (
                                energy_production_commissioned[year] * specific_consumption
                            )
                            resources_consumption_with_selectivity = (
                                resources_consumption * kerosene_selectivity
                            )

                            total_ressource_consumption.loc[year : year + lifespan - 1] = (
                                resources_consumption
                            )
                            total_ressource_mobilised_with_selectivity.loc[
                                year : year + lifespan - 1
                            ] = resources_consumption_with_selectivity

                            output_data[
                                f"{self.pathway_name}_{process_key}_{key}_total_consumption"
                            ].loc[year : year + lifespan - 1] += resources_consumption
                            output_data[
                                f"{self.pathway_name}_{process_key}_{key}_total_mobilised_with_selectivity"
                            ].loc[
                                year : year + lifespan - 1
                            ] += resources_consumption_with_selectivity

                            # Get the CO2 emission factor for the resource
                            unit_emissions = input_data.get(
                                f"{key}_co2_emission_factor", optional_nan_series
                            )
                            # beyond sceanrio end year, we stick to last known value
                            unit_emissions = unit_emissions.reindex(
                                range(year, year + lifespan), method="ffill"
                            )
                            # get resource emission per unit of energy
                            co2_emission_factor_ressource = specific_consumption * unit_emissions
                            vintage_emission_factor = _custom_series_addition(
                                vintage_emission_factor, co2_emission_factor_ressource
                            )
                            output_data[
                                f"{self.pathway_name}_{process_key}_{key}_mean_co2_emission_factor"
                            ].loc[year : year + lifespan - 1] = _custom_series_addition(
                                output_data[
                                    f"{self.pathway_name}_{process_key}_{key}_mean_co2_emission_factor"
                                ].loc[year : year + lifespan - 1],
                                co2_emission_factor_ressource * relative_share,
                            )
                    # store the total consumption of the resource
                    output_data[f"{self.pathway_name}_{key}_total_consumption"].loc[
                        year : year + lifespan - 1
                    ] = _custom_series_addition(
                        output_data[f"{self.pathway_name}_{key}_total_consumption"].loc[
                            year : year + lifespan - 1
                        ],
                        total_ressource_consumption.loc[year : year + lifespan - 1],
                    )
                    output_data[f"{self.pathway_name}_{key}_total_mobilised_with_selectivity"].loc[
                        year : year + lifespan - 1
                    ] = _custom_series_addition(
                        output_data[
                            f"{self.pathway_name}_{key}_total_mobilised_with_selectivity"
                        ].loc[year : year + lifespan - 1],
                        total_ressource_mobilised_with_selectivity.loc[year : year + lifespan - 1],
                    )

                # IV) Now let's compute the emissions from processes themselves
                for process_key in self.process_keys:
                    # Get the inputs for the year
                    process_emission_factor = _get_value_for_year(
                        input_data.get(f"{process_key}_eis_co2_emission_factor_without_resources"),
                        year,
                        0.0,
                    )
                    vintage_emission_factor = _custom_series_addition(
                        vintage_emission_factor, process_emission_factor
                    )
                    output_data[
                        f"{self.pathway_name}_{process_key}_without_resources_mean_co2_emission_factor"
                    ].loc[year : year + lifespan - 1] = _custom_series_addition(
                        output_data[
                            f"{self.pathway_name}_{process_key}_without_resources_mean_co2_emission_factor"
                        ].loc[year : year + lifespan - 1],
                        process_emission_factor * relative_share,
                    )

                # Compute the average emission factor from the vintage
                co2_emission_factor.loc[year : year + lifespan - 1] = _custom_series_addition(
                    co2_emission_factor.loc[year : year + lifespan - 1],
                    vintage_emission_factor * relative_share,
                )

                # Store the emission factor for the vintage
                output_data[f"{self.pathway_name}_vintage_eis_co2_emission_factor"].loc[year] = (
                    vintage_emission_factor.loc[year]
                )

                # compute the cumulative and discounted emissions for the vintage
                if self.compute_abatement_cost:
                    if vintage_emission_factor.notna().any():
                        # Get the exogenous carbon price trajectory and social discount rate
                        exogenous_carbon_price_trajectory = input_data.get(
                            "exogenous_carbon_price_trajectory", optional_nan_series
                        )
                        social_discount_rate = input_data.get("social_discount_rate", 0.0)

                        # Compute cumulative and discounted emissions for the vintage
                        cumul_em, generic_discounted_cumul_em = (
                            self._unitary_cumul_emissions_vintage(
                                vintage_emission_factor,
                                exogenous_carbon_price_trajectory,
                                social_discount_rate,
                            )
                        )
                    else:
                        cumul_em = np.NaN
                        generic_discounted_cumul_em = np.NaN

                    # Store the cumulative emissions for the vintage
                    output_data[f"{self.pathway_name}_lifespan_unitary_emissions"].loc[year] = (
                        cumul_em
                    )
                    output_data[f"{self.pathway_name}_lifespan_discounted_unitary_emissions"].loc[
                        year
                    ] = generic_discounted_cumul_em

        # Store the emission factor
        output_data[f"{self.pathway_name}_mean_co2_emission_factor"] = co2_emission_factor
        # Compute the total emissions from the vintage
        total_co2_emissions = energy_consumption * co2_emission_factor
        output_data[f"{self.pathway_name}_total_co2_emissions"] = total_co2_emissions

        self._store_outputs(output_data)
        return output_data

    def _unitary_cumul_emissions_vintage(
        self,
        vintage_emission_factor: pd.Series,
        exogenous_carbon_price_trajectory: pd.Series,
        social_discount_rate: float,
    ):
        """
        Compute cumulative and discounted emissions for each vintage,
        using the vintage ef
        """
        indexes = vintage_emission_factor.index
        cumul_em = 0
        generic_discounted_cumul_em = 0
        for i in indexes:
            # Use the emission factor of the commissioning year (vintage)
            if i <= self.end_year:
                cumul_em += vintage_emission_factor[i]
                generic_discounted_cumul_em += (
                    vintage_emission_factor[i]
                    * exogenous_carbon_price_trajectory[i]
                    / exogenous_carbon_price_trajectory[indexes[0]]
                    / (1 + social_discount_rate) ** (i - indexes[0])
                )
            else:
                # After scenario end, keep last known values and extrapolate SCC growth
                ef_end = vintage_emission_factor[self.end_year]
                future_scc_growth = (
                    exogenous_carbon_price_trajectory[self.end_year]
                    / exogenous_carbon_price_trajectory[self.end_year - 1]
                )
                cumul_em += ef_end
                generic_discounted_cumul_em += (
                    ef_end
                    * (
                        exogenous_carbon_price_trajectory[self.end_year]
                        / exogenous_carbon_price_trajectory[indexes[0]]
                        * (future_scc_growth) ** (i - self.end_year)
                    )
                    / (1 + social_discount_rate) ** (i - indexes[0])
                )

        return cumul_em, generic_discounted_cumul_em
