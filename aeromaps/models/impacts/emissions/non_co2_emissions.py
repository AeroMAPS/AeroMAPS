"""
non_co2_emissions

=========================
Module to compute non-CO2 emissions from various aircraft types and energy origins.
"""

import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel
from aeromaps.utils.defaults import get_default_series


class NOxEmissionIndex(AeroMAPSModel):
    """
    Class to compute NOx emission index.

    Parameters
    --------------
    name : str
        Name of the model instance ('nox_emission_index' by default).

    Attributes
    --------------
    pathways_manager : EnergyCarrierManager
        EnergyCarrierManager instance to manage generic energy pathways and their data.
    input_names : dict
        Dictionary of input variable names populated at model initialisation before MDA chain creation.
    output_names : dict
        Dictionary of output variable names populated at model initialisation before MDA chain creation.

    Warnings
    --------------
    - Detailed i/o documentation is not yet provided for models defined wityh generic .yaml files?
    """

    def __init__(self, name="nox_emission_index", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.pathways_manager = None
        # TODO Provide detailed i/o documentation.

    def custom_setup(self):
        """
        Dynamically add all pathways variables to input_names and function outputs to output_names.
        Specific function for custom AeroMAPSModel instances.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        # TODO caution aircraft types not generic there
        self.input_names = {
            "emission_index_nox_dropin_fuel_evolution": 0.0,
            "emission_index_nox_hydrogen_evolution": 0.0,
        }
        self.output_names = {}

        for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
            for energy_origin in self.pathways_manager.get_all_types("energy_origin"):
                if self.pathways_manager.get(
                    aircraft_type=aircraft_type, energy_origin=energy_origin
                ):
                    self.output_names.update(
                        {
                            f"{aircraft_type}_{energy_origin}_mean_emission_index_nox": pd.Series(
                                [0.0]
                            ),
                        }
                    )

            for pathway in self.pathways_manager.get(aircraft_type=aircraft_type):
                self.input_names.update(
                    {
                        f"{pathway.name}_emission_index_nox": 0.0,
                        f"{pathway.name}_massic_share_{aircraft_type}_{pathway.energy_origin}": pd.Series(
                            [0.0]
                        ),
                    }
                )

    def compute(self, input_data) -> dict:
        """
        NOx emission index calculation using simple method.

        Parameters
        ----------
        input_data
            Dictionary containing all input data required for the computation, completed at model instantiation with information from yaml files and outputs of other models.

        Returns
        -------
        output_data
            Dictionary containing all output data resulting from the computation. Contains outputs defined during model instantiation.

        """

        output_data = {}

        for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
            cagr_aircraft = input_data.get(f"emission_index_nox_{aircraft_type}_evolution", 0.0)
            growth_series = pd.Series(
                np.concatenate(
                    (
                        np.ones(self.prospection_start_year - self.historic_start_year),
                        (1 + cagr_aircraft)
                        ** np.arange(0, self.end_year - self.prospection_start_year + 1),
                    )
                ),
                index=range(self.historic_start_year, self.end_year + 1),
            )

            # intialize the mean values for the aircraft type
            for energy_origin in self.pathways_manager.get_all_types("energy_origin"):
                # Get the pathways for this aircraft type and energy origin
                pathways = self.pathways_manager.get(
                    aircraft_type=aircraft_type, energy_origin=energy_origin
                )
                if pathways:
                    origin_mean_emission_index_nox = get_default_series(
                        self.historic_start_year, self.end_year
                    )
                    origin_cumulative_share = get_default_series(
                        self.historic_start_year, self.end_year
                    )
                    for pathway in pathways:
                        origin_share = input_data[
                            f"{pathway.name}_massic_share_{aircraft_type}_{energy_origin}"
                        ]
                        origin_cumulative_share = (
                            origin_cumulative_share + origin_share.fillna(0) / 100
                        )
                        pathway_emission_index_nox = input_data[
                            f"{pathway.name}_emission_index_nox"
                        ]

                        origin_mean_emission_index_nox += (
                            pathway_emission_index_nox * origin_share
                        ).fillna(0) / 100

                    origin_valid_years = origin_cumulative_share.replace(0, np.nan)

                    output_data[f"{aircraft_type}_{energy_origin}_mean_emission_index_nox"] = (
                        origin_mean_emission_index_nox * origin_valid_years * growth_series
                    )

        self._store_outputs(output_data)

        return output_data


class NOxEmissionIndexComplex(AeroMAPSModel):
    """
    Class to compute NOx emission index using fleet renewal models.

    Parameters
    --------------
    name : str
        Name of the model instance ('nox_emission_index_complex' by default).

    Attributes
    --------------
    fleet_model : FleetModel(AeroMAPSModel)
        AeroMAPSModel instance to provide fleet renewal data for NOx emission index calculation.
    pathways_manager : EnergyCarrierManager
        EnergyCarrierManager instance to manage generic energy pathways and their data.
    input_names : dict
        Dictionary of input variable names populated at model initialisation before MDA chain creation.
    output_names : dict
        Dictionary of output variable names populated at model initialisation before MDA chain creation.

    Warnings
    --------------
    - Detailed i/o documentation is not yet provided for models defined wityh generic .yaml files?
    """

    def __init__(self, name="nox_emission_index_complex", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.fleet_model = None
        self.pathways_manager = None

    def custom_setup(self):
        """
        Dynamically add all pathways variables to input_names and function outputs to output_names.
        Specific function for custom AeroMAPSModel instances.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        # TODO caution aircraft types not generic there
        self.input_names = {
            "ask_long_range_dropin_fuel": pd.Series([0.0]),
            "ask_medium_range_dropin_fuel": pd.Series([0.0]),
            "ask_short_range_dropin_fuel": pd.Series([0.0]),
            "ask_long_range_hydrogen": pd.Series([0.0]),
            "ask_medium_range_hydrogen": pd.Series([0.0]),
            "ask_short_range_hydrogen": pd.Series([0.0]),
            "ask_long_range_electric": pd.Series([0.0]),
            "ask_medium_range_electric": pd.Series([0.0]),
            "ask_short_range_electric": pd.Series([0.0]),
        }

        self.output_names = {}

        aircraft_types = ["dropin_fuel", "hydrogen", "electric"]

        for aircraft_type in aircraft_types:
            for energy_origin in self.pathways_manager.get_all_types("energy_origin"):
                if self.pathways_manager.get(
                    aircraft_type=aircraft_type, energy_origin=energy_origin
                ):
                    self.output_names.update(
                        {
                            f"{aircraft_type}_{energy_origin}_mean_emission_index_nox": pd.Series(
                                [0.0]
                            ),
                        }
                    )

            for pathway in self.pathways_manager.get(aircraft_type=aircraft_type):
                self.input_names.update(
                    {
                        f"{pathway.name}_emission_index_nox": 0.0,
                        f"{pathway.name}_massic_share_{aircraft_type}_{pathway.energy_origin}": pd.Series(
                            [0.0]
                        ),
                    }
                )

    def compute(
        self,
        input_data,
    ) -> dict:
        """
        NOx emission index calculation using fleet renewal models.

        Parameters
        ----------
        input_data
            Dictionary containing all input data required for the computation, completed at model instantiation with information from yaml files and outputs of other models.

        Returns
        -------
        output_data
            Dictionary containing all output data resulting from the computation. Contains outputs defined during model instantiation.
        """
        output_data = {}
        # Getting fleet model data

        aircraft_types = ["dropin_fuel", "hydrogen", "electric"]

        for aircraft_type in aircraft_types:
            emission_index_nox_short_range = self.fleet_model.df[
                f"Short Range:emission_index_nox:{aircraft_type}"
            ]
            emission_index_nox_medium_range = self.fleet_model.df[
                f"Medium Range:emission_index_nox:{aircraft_type}"
            ]
            emission_index_nox_long_range = self.fleet_model.df[
                f"Long Range:emission_index_nox:{aircraft_type}"
            ]

            ask_short_range = input_data.get(
                f"ask_short_range_{aircraft_type}",
                get_default_series(self.historic_start_year, self.end_year),
            )
            ask_medium_range = input_data.get(
                f"ask_medium_range_{aircraft_type}",
                get_default_series(self.historic_start_year, self.end_year),
            )
            ask_long_range = input_data.get(
                f"ask_long_range_{aircraft_type}",
                get_default_series(self.historic_start_year, self.end_year),
            )

            emission_index_aircraft_type = (
                (
                    emission_index_nox_short_range.loc[self.historic_start_year : self.end_year]
                    * ask_short_range.loc[self.historic_start_year : self.end_year].fillna(0)
                )
                + (
                    emission_index_nox_medium_range.loc[self.historic_start_year : self.end_year]
                    * ask_medium_range.loc[self.historic_start_year : self.end_year].fillna(0)
                )
                + (
                    emission_index_nox_long_range.loc[self.historic_start_year : self.end_year]
                    * ask_long_range.loc[self.historic_start_year : self.end_year].fillna(0)
                )
            ) / (
                ask_short_range.loc[self.historic_start_year : self.end_year].fillna(0)
                + ask_medium_range.loc[self.historic_start_year : self.end_year].fillna(0)
                + ask_long_range.loc[self.historic_start_year : self.end_year].fillna(0)
            )

            relative_emission_index_aircraft_type = (
                emission_index_aircraft_type
                / emission_index_aircraft_type.loc[self.prospection_start_year - 1]
            )

            # intialize the mean values for the aircraft type
            for energy_origin in self.pathways_manager.get_all_types("energy_origin"):
                # Get the pathways for this aircraft type and energy origin
                pathways = self.pathways_manager.get(
                    aircraft_type=aircraft_type, energy_origin=energy_origin
                )
                if pathways:
                    origin_mean_emission_index_nox = get_default_series(
                        self.historic_start_year, self.end_year
                    )
                    origin_cumulative_share = get_default_series(
                        self.historic_start_year, self.end_year
                    )
                    for pathway in pathways:
                        origin_share = input_data[
                            f"{pathway.name}_massic_share_{aircraft_type}_{energy_origin}"
                        ]
                        origin_cumulative_share = (
                            origin_cumulative_share + origin_share.fillna(0) / 100
                        )
                        pathway_emission_index_nox = input_data[
                            f"{pathway.name}_emission_index_nox"
                        ]

                        origin_mean_emission_index_nox += (
                            pathway_emission_index_nox * origin_share
                        ).fillna(0) / 100

                    origin_valid_years = origin_cumulative_share.replace(0, np.nan)

                    output_data[f"{aircraft_type}_{energy_origin}_mean_emission_index_nox"] = (
                        origin_mean_emission_index_nox
                        * origin_valid_years
                        * relative_emission_index_aircraft_type
                    )

        # print(output_data)
        self._store_outputs(output_data)

        return output_data


class SootEmissionIndex(AeroMAPSModel):
    """
    Class to compute Soot emission index.

    Parameters
    --------------
    name : str
        Name of the model instance ('soot_emission_index' by default).

    Attributes
    --------------
    pathways_manager : EnergyCarrierManager
        EnergyCarrierManager instance to manage generic energy pathways and their data.
    input_names : dict
        Dictionary of input variable names populated at model initialisation before MDA chain creation.
    output_names : dict
        Dictionary of output variable names populated at model initialisation before MDA chain creation.

    Warnings
    --------------
    - Detailed i/o documentation is not yet provided for models defined wityh generic .yaml files?
    """

    def __init__(self, name="soot_emission_index", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.pathways_manager = None

    def custom_setup(self):
        """
        Dynamically add all pathways variables to input_names and function outputs to output_names.
        Specific function for custom AeroMAPSModel instances.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        # TODO caution aircraft types not generic there
        self.input_names = {"emission_index_soot_dropin_fuel_evolution": 0.0}

        self.output_names = {}

        for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
            for energy_origin in self.pathways_manager.get_all_types("energy_origin"):
                if self.pathways_manager.get(
                    aircraft_type=aircraft_type, energy_origin=energy_origin
                ):
                    self.output_names.update(
                        {
                            f"{aircraft_type}_{energy_origin}_mean_emission_index_soot": pd.Series(
                                [0.0]
                            ),
                        }
                    )

            for pathway in self.pathways_manager.get(aircraft_type=aircraft_type):
                self.input_names.update(
                    {
                        f"{pathway.name}_emission_index_soot": 0.0,
                        f"{pathway.name}_massic_share_{aircraft_type}_{pathway.energy_origin}": pd.Series(
                            [0.0]
                        ),
                    }
                )

    def compute(self, input_data) -> dict:
        """
        Execute Soot emission index calculation using simple method.

        Parameters
        ----------
        input_data
            Dictionary containing all input data required for the computation, completed at model instantiation with information from yaml files and outputs of other models.

        Returns
        -------
        output_data
            Dictionary containing all output data resulting from the computation. Contains outputs defined during model instantiation.

        """

        output_data = {}

        for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
            cagr_aircraft = input_data.get(f"emission_index_soot_{aircraft_type}_evolution", 0.0)
            growth_series = pd.Series(
                np.concatenate(
                    (
                        np.ones(self.prospection_start_year - self.historic_start_year),
                        (1 + cagr_aircraft)
                        ** np.arange(0, self.end_year - self.prospection_start_year + 1),
                    )
                ),
                index=range(self.historic_start_year, self.end_year + 1),
            )

            # initialise the mean values for the aircraft type
            for energy_origin in self.pathways_manager.get_all_types("energy_origin"):
                # Get the pathways for this aircraft type and energy origin
                pathways = self.pathways_manager.get(
                    aircraft_type=aircraft_type, energy_origin=energy_origin
                )
                if pathways:
                    origin_mean_emission_index_soot = get_default_series(
                        self.historic_start_year, self.end_year
                    )
                    origin_cumulative_share = get_default_series(
                        self.historic_start_year, self.end_year
                    )
                    for pathway in pathways:
                        origin_share = input_data[
                            f"{pathway.name}_massic_share_{aircraft_type}_{energy_origin}"
                        ]
                        origin_cumulative_share = (
                            origin_cumulative_share + origin_share.fillna(0) / 100
                        )
                        pathway_emission_index_soot = input_data[
                            f"{pathway.name}_emission_index_soot"
                        ]

                        origin_mean_emission_index_soot += (
                            pathway_emission_index_soot * origin_share
                        ).fillna(0) / 100

                    origin_valid_years = origin_cumulative_share.replace(0, np.nan)

                    output_data[f"{aircraft_type}_{energy_origin}_mean_emission_index_soot"] = (
                        origin_mean_emission_index_soot * origin_valid_years * growth_series
                    )

        self._store_outputs(output_data)

        return output_data


class SootEmissionIndexComplex(AeroMAPSModel):
    """
    Class to compute Soot emission index using fleet renewal models.

    Parameters
    --------------
    name : str
        Name of the model instance ('soot_emission_index_complex' by default).

    Attributes
    --------------
    fleet_model : FleetModel(AeroMAPSModel)
        AeroMAPSModel instance to provide fleet renewal data for Soot emission index calculation.
    pathways_manager : EnergyCarrierManager
        EnergyCarrierManager instance to manage generic energy pathways and their data.
    input_names : dict
        Dictionary of input variable names populated at model initialisation before MDA chain creation.
    output_names : dict
        Dictionary of output variable names populated at model initialisation before MDA chain creation.

    Warnings
    --------------
    - Detailed i/o documentation is not yet provided for models defined wityh generic .yaml files?
    """

    def __init__(self, name="soot_emission_index_complex", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.fleet_model = None
        self.pathways_manager = None

    def custom_setup(self):
        """
        Dynamically add all pathways variables to input_names and function outputs to output_names.
        Specific function for custom AeroMAPSModel instances.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        # TODO caution aircraft types not generic there
        self.input_names = {
            "ask_long_range_dropin_fuel": pd.Series([0.0]),
            "ask_medium_range_dropin_fuel": pd.Series([0.0]),
            "ask_short_range_dropin_fuel": pd.Series([0.0]),
            "ask_long_range_hydrogen": pd.Series([0.0]),
            "ask_medium_range_hydrogen": pd.Series([0.0]),
            "ask_short_range_hydrogen": pd.Series([0.0]),
            "ask_long_range_electric": pd.Series([0.0]),
            "ask_medium_range_electric": pd.Series([0.0]),
            "ask_short_range_electric": pd.Series([0.0]),
        }

        self.output_names = {}

        aircraft_types = ["dropin_fuel", "hydrogen", "electric"]
        for aircraft_type in aircraft_types:
            for energy_origin in self.pathways_manager.get_all_types("energy_origin"):
                if self.pathways_manager.get(
                    aircraft_type=aircraft_type, energy_origin=energy_origin
                ):
                    self.output_names.update(
                        {
                            f"{aircraft_type}_{energy_origin}_mean_emission_index_soot": pd.Series(
                                [0.0]
                            ),
                        }
                    )

            for pathway in self.pathways_manager.get(aircraft_type=aircraft_type):
                self.input_names.update(
                    {
                        f"{pathway.name}_emission_index_soot": 0.0,
                        f"{pathway.name}_massic_share_{aircraft_type}_{pathway.energy_origin}": pd.Series(
                            [0.0]
                        ),
                    }
                )

    def compute(
        self,
        input_data,
    ) -> dict:
        """Soot emission index calculation using fleet renewal models.

        Parameters
        ----------
        input_data
            Dictionary containing all input data required for the computation, completed at model instantiation with information from yaml files and outputs of other models.

        Returns
        -------
        output_data
            Dictionary containing all output data resulting from the computation. Contains outputs defined during model instantiation.

        """
        output_data = {}
        # Getting fleet model data

        aircraft_types = ["dropin_fuel", "hydrogen", "electric"]

        for aircraft_type in aircraft_types:
            emission_index_soot_short_range = self.fleet_model.df[
                f"Short Range:emission_index_soot:{aircraft_type}"
            ]
            emission_index_soot_medium_range = self.fleet_model.df[
                f"Medium Range:emission_index_soot:{aircraft_type}"
            ]
            emission_index_soot_long_range = self.fleet_model.df[
                f"Long Range:emission_index_soot:{aircraft_type}"
            ]

            ask_short_range = input_data[f"ask_short_range_{aircraft_type}"]
            ask_medium_range = input_data[f"ask_medium_range_{aircraft_type}"]
            ask_long_range = input_data[f"ask_long_range_{aircraft_type}"]

            emission_index_aircraft_type = (
                (
                    emission_index_soot_short_range.loc[self.historic_start_year : self.end_year]
                    * ask_short_range.loc[self.historic_start_year : self.end_year].fillna(0)
                )
                + (
                    emission_index_soot_medium_range.loc[self.historic_start_year : self.end_year]
                    * ask_medium_range.loc[self.historic_start_year : self.end_year].fillna(0)
                )
                + (
                    emission_index_soot_long_range.loc[self.historic_start_year : self.end_year]
                    * ask_long_range.loc[self.historic_start_year : self.end_year].fillna(0)
                )
            ) / (
                ask_short_range.loc[self.historic_start_year : self.end_year].fillna(0)
                + ask_medium_range.loc[self.historic_start_year : self.end_year].fillna(0)
                + ask_long_range.loc[self.historic_start_year : self.end_year].fillna(0)
            )

            relative_emission_index_aircraft_type = (
                emission_index_aircraft_type
                / emission_index_aircraft_type.loc[self.prospection_start_year - 1]
            )

            # intialize the mean values for the aircraft type
            for energy_origin in self.pathways_manager.get_all_types("energy_origin"):
                # Get the pathways for this aircraft type and energy origin
                pathways = self.pathways_manager.get(
                    aircraft_type=aircraft_type, energy_origin=energy_origin
                )
                if pathways:
                    origin_mean_emission_index_soot = get_default_series(
                        self.historic_start_year, self.end_year
                    )
                    origin_cumulative_share = get_default_series(
                        self.historic_start_year, self.end_year
                    )
                    for pathway in pathways:
                        origin_share = input_data[
                            f"{pathway.name}_massic_share_{aircraft_type}_{energy_origin}"
                        ]
                        origin_cumulative_share = (
                            origin_cumulative_share + origin_share.fillna(0) / 100
                        )
                        pathway_emission_index_soot = input_data[
                            f"{pathway.name}_emission_index_soot"
                        ]

                        origin_mean_emission_index_soot += (
                            pathway_emission_index_soot * origin_share
                        ).fillna(0) / 100

                    origin_valid_years = origin_cumulative_share.replace(0, np.nan)

                    output_data[f"{aircraft_type}_{energy_origin}_mean_emission_index_soot"] = (
                        origin_mean_emission_index_soot
                        * origin_valid_years
                        * relative_emission_index_aircraft_type
                    )
        self._store_outputs(output_data)

        return output_data


class H2OEmissionIndex(AeroMAPSModel):
    """
    Class to compute H2O emission index.

    Parameters
    --------------
    name : str
        Name of the model instance ('h2o_emission_index' by default).

    Attributes
    --------------
    pathways_manager : EnergyCarrierManager
        EnergyCarrierManager instance to manage generic energy pathways and their data.
    input_names : dict
        Dictionary of input variable names populated at model initialisation before MDA chain creation.
    output_names : dict
        Dictionary of output variable names populated at model initialisation before MDA chain creation.

    Warnings
    --------------
    - Detailed i/o documentation is not yet provided for models defined wityh generic .yaml files?
    """

    def __init__(self, name="h2o_emission_index", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.pathways_manager = None

    def custom_setup(self):
        """
        Dynamically add all pathways variables to input_names and function outputs to output_names.
        Specific function for custom AeroMAPSModel instances.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.input_names = {}
        self.output_names = {}

        for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
            for energy_origin in self.pathways_manager.get_all_types("energy_origin"):
                if self.pathways_manager.get(
                    aircraft_type=aircraft_type, energy_origin=energy_origin
                ):
                    self.output_names.update(
                        {
                            f"{aircraft_type}_{energy_origin}_mean_emission_index_h2o": pd.Series(
                                [0.0]
                            ),
                        }
                    )

            for pathway in self.pathways_manager.get(aircraft_type=aircraft_type):
                self.input_names.update(
                    {
                        f"{pathway.name}_emission_index_h2o": 0.0,
                        f"{pathway.name}_massic_share_{aircraft_type}_{pathway.energy_origin}": pd.Series(
                            [0.0]
                        ),
                    }
                )

    def compute(self, input_data) -> dict:
        """Average H20 emission index calculation

        Parameters
        ----------
        input_data
            Dictionary containing all input data required for the computation, completed at model instantiation with information from yaml files and outputs of other models.

        Returns
        -------
        output_data
            Dictionary containing all output data resulting from the computation. Contains outputs defined during model instantiation.

        """

        output_data = {}

        for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
            # initialise the mean values for the aircraft type
            for energy_origin in self.pathways_manager.get_all_types("energy_origin"):
                # Get the pathways for this aircraft type and energy origin
                pathways = self.pathways_manager.get(
                    aircraft_type=aircraft_type, energy_origin=energy_origin
                )
                if pathways:
                    origin_mean_emission_index_h2o = get_default_series(
                        self.historic_start_year, self.end_year
                    )
                    origin_cumulative_share = get_default_series(
                        self.historic_start_year, self.end_year
                    )
                    for pathway in pathways:
                        origin_share = input_data[
                            f"{pathway.name}_massic_share_{aircraft_type}_{energy_origin}"
                        ]
                        origin_cumulative_share = (
                            origin_cumulative_share + origin_share.fillna(0) / 100
                        )
                        pathway_emission_index_h2o = input_data[
                            f"{pathway.name}_emission_index_h2o"
                        ]

                        origin_mean_emission_index_h2o += (
                            pathway_emission_index_h2o * origin_share
                        ).fillna(0) / 100

                    origin_valid_years = origin_cumulative_share.replace(0, np.nan)

                    output_data[f"{aircraft_type}_{energy_origin}_mean_emission_index_h2o"] = (
                        origin_mean_emission_index_h2o * origin_valid_years
                    )

        self._store_outputs(output_data)

        return output_data


class SulfurEmissionIndex(AeroMAPSModel):
    """
    Class to compute Sulfur emission index.

    Parameters
    --------------
    name : str
        Name of the model instance ('sulfur_emission_index' by default).

    Attributes
    --------------
    pathways_manager : EnergyCarrierManager
        EnergyCarrierManager instance to manage generic energy pathways and their data.
    input_names : dict
        Dictionary of input variable names populated at model initialisation before MDA chain creation.
    output_names : dict
        Dictionary of output variable names populated at model initialisation before MDA chain creation.

    Warnings
    --------------
    - Detailed i/o documentation is not yet provided for models defined wityh generic .yaml files?
    """

    def __init__(self, name="sulfur_emission_index", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.pathways_manager = None

    def custom_setup(self):
        """
        Dynamically add all pathways variables to input_names and function outputs to output_names.
        Specific function for custom AeroMAPSModel instances.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.input_names = {}
        self.output_names = {}

        for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
            for energy_origin in self.pathways_manager.get_all_types("energy_origin"):
                if self.pathways_manager.get(
                    aircraft_type=aircraft_type, energy_origin=energy_origin
                ):
                    self.output_names.update(
                        {
                            f"{aircraft_type}_{energy_origin}_mean_emission_index_sulfur": pd.Series(
                                [0.0]
                            ),
                        }
                    )

            for pathway in self.pathways_manager.get(aircraft_type=aircraft_type):
                self.input_names.update(
                    {
                        f"{pathway.name}_emission_index_sulfur": 0.0,
                        f"{pathway.name}_massic_share_{aircraft_type}_{pathway.energy_origin}": pd.Series(
                            [0.0]
                        ),
                    }
                )

    def compute(self, input_data) -> dict:
        """Average H20 emission index calculation

        Parameters
        ----------
        input_data
            Dictionary containing all input data required for the computation, completed at model instantiation with information from yaml files and outputs of other models.

        Returns
        -------
        output_data
            Dictionary containing all output data resulting from the computation. Contains outputs defined during model instantiation.

        """

        output_data = {}

        for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
            # initialise the mean values for the aircraft type
            for energy_origin in self.pathways_manager.get_all_types("energy_origin"):
                # Get the pathways for this aircraft type and energy origin
                pathways = self.pathways_manager.get(
                    aircraft_type=aircraft_type, energy_origin=energy_origin
                )
                if pathways:
                    origin_mean_emission_index_sulfur = get_default_series(
                        self.historic_start_year, self.end_year
                    )
                    origin_cumulative_share = get_default_series(
                        self.historic_start_year, self.end_year
                    )
                    for pathway in pathways:
                        origin_share = input_data[
                            f"{pathway.name}_massic_share_{aircraft_type}_{energy_origin}"
                        ]
                        origin_cumulative_share = (
                            origin_cumulative_share + origin_share.fillna(0) / 100
                        )
                        pathway_emission_index_sulfur = input_data[
                            f"{pathway.name}_emission_index_sulfur"
                        ]

                        origin_mean_emission_index_sulfur += (
                            pathway_emission_index_sulfur * origin_share
                        ).fillna(0) / 100

                    origin_valid_years = origin_cumulative_share.replace(0, np.nan)

                    output_data[f"{aircraft_type}_{energy_origin}_mean_emission_index_sulfur"] = (
                        origin_mean_emission_index_sulfur * origin_valid_years
                    )

        self._store_outputs(output_data)

        return output_data


class NonCO2Emissions(AeroMAPSModel):
    """
    Class to compute non-CO2 emissions.

    Parameters
    --------------
    name : str
        Name of the model instance ('non_co2_emissions' by default).

    Attributes
    --------------
    pathways_manager : EnergyCarrierManager
        EnergyCarrierManager instance to manage generic energy pathways and their data.
    input_names : dict
        Dictionary of input variable names populated at model initialisation before MDA chain creation.
    output_names : dict
        Dictionary of output variable names populated at model initialisation before MDA chain creation.

    Warnings
    --------------
    - Detailed i/o documentation is not yet provided for models defined wityh generic .yaml files?
    """

    def __init__(self, name="non_co2_emissions", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.climate_historical_data = None
        self.pathways_manager = None

    def custom_setup(self):
        """
        Dynamically add all pathways variables to input_names and function outputs to output_names.
        Specific function for custom AeroMAPSModel instances.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        aircraft_type = ["dropin_fuel", "hydrogen"]

        for aircraft_type in aircraft_type:
            for energy_origin in self.pathways_manager.get_all_types("energy_origin"):
                if self.pathways_manager.get(
                    aircraft_type=aircraft_type, energy_origin=energy_origin
                ):
                    self.input_names.update(
                        {
                            f"{aircraft_type}_{energy_origin}_mean_emission_index_nox": pd.Series(
                                [0.0]
                            ),
                            f"{aircraft_type}_{energy_origin}_mean_emission_index_soot": pd.Series(
                                [0.0]
                            ),
                            f"{aircraft_type}_{energy_origin}_mean_emission_index_h2o": pd.Series(
                                [0.0]
                            ),
                            f"{aircraft_type}_{energy_origin}_mean_emission_index_sulfur": pd.Series(
                                [0.0]
                            ),
                            f"{aircraft_type}_{energy_origin}_mean_lhv": pd.Series([0.0]),
                            f"{aircraft_type}_{energy_origin}_energy_consumption": pd.Series([0.0]),
                        }
                    )

        self.output_names.update(
            {
                "soot_emissions": pd.Series([0.0]),
                "h2o_emissions": pd.Series([0.0]),
                "nox_emissions": pd.Series([0.0]),
                "sulfur_emissions": pd.Series([0.0]),
            }
        )

    def compute(self, input_data) -> dict:
        """Non-CO2 emissions calculation.

        Parameters
        ----------
        input_data
            Dictionary containing all input data required for the computation, completed at model instantiation with information from yaml files and outputs of other models.

        Returns
        -------
        output_data
            Dictionary containing all output data resulting from the computation. Contains outputs defined during model instantiation.
        """

        soot_emissions = get_default_series(self.climate_historic_start_year, self.end_year)
        h2o_emissions = get_default_series(self.climate_historic_start_year, self.end_year)
        nox_emissions = get_default_series(self.climate_historic_start_year, self.end_year)
        sulfur_emissions = get_default_series(self.climate_historic_start_year, self.end_year)

        ## Initialization
        historical_nox_emissions_for_temperature = self.climate_historical_data[:, 2]
        historical_h2o_emissions_for_temperature = self.climate_historical_data[:, 3]
        historical_soot_emissions_for_temperature = self.climate_historical_data[:, 4]
        historical_sulfur_emissions_for_temperature = self.climate_historical_data[:, 5]

        soot_emissions.loc[self.climate_historic_start_year : self.historic_start_year] = (
            historical_soot_emissions_for_temperature
        )
        h2o_emissions.loc[self.climate_historic_start_year : self.historic_start_year] = (
            historical_h2o_emissions_for_temperature
        )
        nox_emissions.loc[self.climate_historic_start_year : self.historic_start_year] = (
            historical_nox_emissions_for_temperature
        )
        sulfur_emissions.loc[self.climate_historic_start_year : self.historic_start_year] = (
            historical_sulfur_emissions_for_temperature
        )

        for aircraft_type in ["dropin_fuel", "hydrogen"]:
            for energy_origin in self.pathways_manager.get_all_types("energy_origin"):
                if self.pathways_manager.get(
                    aircraft_type=aircraft_type, energy_origin=energy_origin
                ):
                    mass_consumption = (
                        input_data[f"{aircraft_type}_{energy_origin}_energy_consumption"]
                        / input_data[f"{aircraft_type}_{energy_origin}_mean_lhv"]
                        / 10**9  # convert MJ to Mt
                    )
                    soot_emissions.loc[self.historic_start_year + 1 : self.end_year] += (
                        input_data[f"{aircraft_type}_{energy_origin}_mean_emission_index_soot"]
                        * mass_consumption
                    ).fillna(0.0)
                    h2o_emissions.loc[self.historic_start_year + 1 : self.end_year] += (
                        input_data[f"{aircraft_type}_{energy_origin}_mean_emission_index_h2o"]
                        * mass_consumption
                    ).fillna(0.0)
                    nox_emissions.loc[self.historic_start_year + 1 : self.end_year] += (
                        input_data[f"{aircraft_type}_{energy_origin}_mean_emission_index_nox"]
                        * mass_consumption
                    ).fillna(0.0)
                    sulfur_emissions.loc[self.historic_start_year + 1 : self.end_year] += (
                        input_data[f"{aircraft_type}_{energy_origin}_mean_emission_index_sulfur"]
                        * mass_consumption
                    ).fillna(0.0)

        output_data = {
            "soot_emissions": soot_emissions,
            "h2o_emissions": h2o_emissions,
            "nox_emissions": nox_emissions,
            "sulfur_emissions": sulfur_emissions,
        }

        self.df_climate.loc[:, "soot_emissions"] = soot_emissions
        self.df_climate.loc[:, "h2o_emissions"] = h2o_emissions
        self.df_climate.loc[:, "nox_emissions"] = nox_emissions
        self.df_climate.loc[:, "sulfur_emissions"] = sulfur_emissions

        return output_data
