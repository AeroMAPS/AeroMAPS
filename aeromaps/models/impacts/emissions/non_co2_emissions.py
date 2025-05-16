import numpy as np
import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class NOxEmissionIndex(AeroMAPSModel):
    def __init__(self, name="nox_emission_index", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.pathways_manager = None

    def custom_setup(self):
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
                        f"{pathway.name}_share_{aircraft_type}_{pathway.energy_origin}": pd.Series(
                            [0.0]
                        ),
                    }
                )

    def compute(self, input_data) -> dict:
        """NOx emission index calculation using simple method."""

        output_data = {}

        def default_series():
            return pd.Series(
                [0.0] * len(range(self.historic_start_year, self.end_year + 1)),
                index=range(self.historic_start_year, self.end_year + 1),
            )

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
                    origin_mean_emission_index_nox = default_series()
                    origin_cumulative_share = default_series()
                    for pathway in pathways:
                        origin_share = input_data[
                            f"{pathway.name}_share_{aircraft_type}_{energy_origin}"
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
    def __init__(self, name="nox_emission_index_complex", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        self.fleet_model = None
        self.pathways_manager = None

    def custom_setup(self):
        # TODO caution aircraft types not generic there
        # TODO CAUTION MODEL NOT TESTED => NEED TO CONVERT NOTEBOOK
        self.input_names = {
            "ask_long_range_dropin_fuel": pd.Series([0.0]),
            "ask_medium_range_dropin_fuel": pd.Series([0.0]),
            "ask_short_range_dropin_fuel": pd.Series([0.0]),
            "ask_long_range_hydrogen": pd.Series([0.0]),
            "ask_medium_range_hydrogen": pd.Series([0.0]),
            "ask_short_range_hydrogen": pd.Series([0.0]),
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
                        f"{pathway.name}_share_{aircraft_type}_{pathway.energy_origin}": pd.Series(
                            [0.0]
                        ),
                    }
                )

    def compute(
        self,
        input_data,
    ) -> dict:
        """NOx emission index calculation using fleet renewal models."""
        output_data = {}
        # Getting fleet model data

        def default_series():
            return pd.Series(
                [0.0] * len(range(self.historic_start_year, self.end_year + 1)),
                index=range(self.historic_start_year, self.end_year + 1),
            )

        for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
            emission_index_nox_short_range = self.fleet_model.df[
                f"Short Range:emission_index_nox:{aircraft_type}"
            ]
            emission_index_nox_medium_range = self.fleet_model.df[
                f"Medium Range:emission_index_nox:{aircraft_type}"
            ]
            emission_index_nox_long_range = self.fleet_model.df[
                f"Long Range:emission_index_nox:{aircraft_type}"
            ]

            ask_short_range = input_data[f"ask_short_range_{aircraft_type}"]
            ask_medium_range = input_data[f"ask_medium_range_{aircraft_type}"]
            ask_long_range = input_data[f"ask_long_range_{aircraft_type}"]

            emission_index_aircraft_type = (
                (
                    emission_index_nox_short_range.loc[
                        self.historic_start_year, self.prospection_start_year
                    ]
                    * ask_short_range.loc[
                        self.historic_start_year, self.prospection_start_year
                    ].fillna(0)
                )
                + (
                    emission_index_nox_medium_range.loc[
                        self.historic_start_year, self.prospection_start_year
                    ]
                    * ask_medium_range.loc[
                        self.historic_start_year, self.prospection_start_year
                    ].fillna(0)
                )
                + (
                    emission_index_nox_long_range.loc[
                        self.historic_start_year, self.prospection_start_year
                    ]
                    * ask_long_range.loc[
                        self.historic_start_year, self.prospection_start_year
                    ].fillna(0)
                )
            ) / (
                ask_short_range.loc[self.historic_start_year, self.prospection_start_year].fillna(0)
                + ask_medium_range.loc[
                    self.historic_start_year, self.prospection_start_year
                ].fillna(0)
                + ask_long_range.loc[self.historic_start_year, self.prospection_start_year].fillna(
                    0
                )
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
                    origin_mean_emission_index_nox = default_series()
                    origin_cumulative_share = default_series()
                    for pathway in pathways:
                        origin_share = input_data[
                            f"{pathway.name}_share_{aircraft_type}_{energy_origin}"
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
        self._store_outputs(output_data)

        return output_data


class SootEmissionIndex(AeroMAPSModel):
    def __init__(self, name="soot_emission_index", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.pathways_manager = None

    def custom_setup(self):
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
                        f"{pathway.name}_share_{aircraft_type}_{pathway.energy_origin}": pd.Series(
                            [0.0]
                        ),
                    }
                )

    def compute(self, input_data) -> dict:
        """Soot emission index calculation using simple method."""

        output_data = {}

        def default_series():
            return pd.Series(
                [0.0] * len(range(self.historic_start_year, self.end_year + 1)),
                index=range(self.historic_start_year, self.end_year + 1),
            )

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
                    origin_mean_emission_index_soot = default_series()
                    origin_cumulative_share = default_series()
                    for pathway in pathways:
                        origin_share = input_data[
                            f"{pathway.name}_share_{aircraft_type}_{energy_origin}"
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
    def __init__(self, name="soot_emission_index_complex", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        self.fleet_model = None
        self.pathways_manager = None

    def custom_setup(self):
        # TODO caution aircraft types not generic there
        # TODO CAUTION MODEL NOT TESTED => NEED TO CONVERT NOTEBOOK
        self.input_names = {
            "ask_long_range_dropin_fuel": pd.Series([0.0]),
            "ask_medium_range_dropin_fuel": pd.Series([0.0]),
            "ask_short_range_dropin_fuel": pd.Series([0.0]),
            "ask_long_range_hydrogen": pd.Series([0.0]),
            "ask_medium_range_hydrogen": pd.Series([0.0]),
            "ask_short_range_hydrogen": pd.Series([0.0]),
        }

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
                        f"{pathway.name}_share_{aircraft_type}_{pathway.energy_origin}": pd.Series(
                            [0.0]
                        ),
                    }
                )

    def compute(
        self,
        input_data,
    ) -> dict:
        """NOx emission index calculation using fleet renewal models."""
        output_data = {}
        # Getting fleet model data

        def default_series():
            return pd.Series(
                [0.0] * len(range(self.historic_start_year, self.end_year + 1)),
                index=range(self.historic_start_year, self.end_year + 1),
            )

        for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
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
                    emission_index_soot_short_range.loc[
                        self.historic_start_year, self.prospection_start_year
                    ]
                    * ask_short_range.loc[
                        self.historic_start_year, self.prospection_start_year
                    ].fillna(0)
                )
                + (
                    emission_index_soot_medium_range.loc[
                        self.historic_start_year, self.prospection_start_year
                    ]
                    * ask_medium_range.loc[
                        self.historic_start_year, self.prospection_start_year
                    ].fillna(0)
                )
                + (
                    emission_index_soot_long_range.loc[
                        self.historic_start_year, self.prospection_start_year
                    ]
                    * ask_long_range.loc[
                        self.historic_start_year, self.prospection_start_year
                    ].fillna(0)
                )
            ) / (
                ask_short_range.loc[self.historic_start_year, self.prospection_start_year].fillna(0)
                + ask_medium_range.loc[
                    self.historic_start_year, self.prospection_start_year
                ].fillna(0)
                + ask_long_range.loc[self.historic_start_year, self.prospection_start_year].fillna(
                    0
                )
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
                    origin_mean_emission_index_soot = default_series()
                    origin_cumulative_share = default_series()
                    for pathway in pathways:
                        origin_share = input_data[
                            f"{pathway.name}_share_{aircraft_type}_{energy_origin}"
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
    def __init__(self, name="h2o_emission_index", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.pathways_manager = None

    def custom_setup(self):
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
                        f"{pathway.name}_share_{aircraft_type}_{pathway.energy_origin}": pd.Series(
                            [0.0]
                        ),
                    }
                )

    def compute(self, input_data) -> dict:
        """Average H20 emission index calculation"""

        output_data = {}

        def default_series():
            return pd.Series(
                [0.0] * len(range(self.historic_start_year, self.end_year + 1)),
                index=range(self.historic_start_year, self.end_year + 1),
            )

        for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
            # initialise the mean values for the aircraft type
            for energy_origin in self.pathways_manager.get_all_types("energy_origin"):
                # Get the pathways for this aircraft type and energy origin
                pathways = self.pathways_manager.get(
                    aircraft_type=aircraft_type, energy_origin=energy_origin
                )
                if pathways:
                    origin_mean_emission_index_h2o = default_series()
                    origin_cumulative_share = default_series()
                    for pathway in pathways:
                        origin_share = input_data[
                            f"{pathway.name}_share_{aircraft_type}_{energy_origin}"
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
    def __init__(self, name="sulfur_emission_index", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.pathways_manager = None

    def custom_setup(self):
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
                        f"{pathway.name}_share_{aircraft_type}_{pathway.energy_origin}": pd.Series(
                            [0.0]
                        ),
                    }
                )

    def compute(self, input_data) -> dict:
        """Average H20 emission index calculation"""

        output_data = {}

        def default_series():
            return pd.Series(
                [0.0] * len(range(self.historic_start_year, self.end_year + 1)),
                index=range(self.historic_start_year, self.end_year + 1),
            )

        for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
            # initialise the mean values for the aircraft type
            for energy_origin in self.pathways_manager.get_all_types("energy_origin"):
                # Get the pathways for this aircraft type and energy origin
                pathways = self.pathways_manager.get(
                    aircraft_type=aircraft_type, energy_origin=energy_origin
                )
                if pathways:
                    origin_mean_emission_index_sulfur = default_series()
                    origin_cumulative_share = default_series()
                    for pathway in pathways:
                        origin_share = input_data[
                            f"{pathway.name}_share_{aircraft_type}_{energy_origin}"
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
    def __init__(self, name="non_co2_emissions", *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        self.climate_historical_data = None
        self.pathways_manager = None

    def custom_setup(self):
        for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
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
        """Non-CO2 emissions calculation."""

        def default_series():
            return pd.Series(
                [0.0] * len(range(self.climate_historic_start_year, self.end_year + 1)),
                index=range(self.climate_historic_start_year, self.end_year + 1),
            )

        soot_emissions = default_series()
        h2o_emissions = default_series()
        nox_emissions = default_series()
        sulfur_emissions = default_series()

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

        for aircraft_type in self.pathways_manager.get_all_types("aircraft_type"):
            for energy_origin in self.pathways_manager.get_all_types("energy_origin"):
                if self.pathways_manager.get(
                    aircraft_type=aircraft_type, energy_origin=energy_origin
                ):
                    mass_consumption = (
                        input_data[f"{aircraft_type}_{energy_origin}_energy_consumption"]
                        / input_data[f"{aircraft_type}_{energy_origin}_mean_lhv"]
                        / 10**9  # convert MJ to Mt
                    )
                    soot_emissions.loc[self.historic_start_year : self.end_year] += (
                        input_data[f"{aircraft_type}_{energy_origin}_mean_emission_index_soot"]
                        * mass_consumption
                    ).fillna(0.0)
                    h2o_emissions.loc[self.historic_start_year : self.end_year] += (
                        input_data[f"{aircraft_type}_{energy_origin}_mean_emission_index_h2o"]
                        * mass_consumption
                    ).fillna(0.0)
                    nox_emissions.loc[self.historic_start_year : self.end_year] += (
                        input_data[f"{aircraft_type}_{energy_origin}_mean_emission_index_nox"]
                        * mass_consumption
                    ).fillna(0.0)
                    sulfur_emissions.loc[self.historic_start_year : self.end_year] += (
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
