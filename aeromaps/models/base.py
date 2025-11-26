"""
Utility base classes and climate-related helper functions used by AeroMAPS models.
"""

import xarray as xr
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
import warnings
from fair import FAIR
from fair.interface import fill, initialise


class AeroMapsCustomDataType:
    """
    Custom type class to handle yaml data input for AeroMAPS models.
    It contains reference years and values, and interpolation options.
    When an AeroMapsCustomDataType is found when reading the yaml it
    instantiates an interpolation model from yaml_interpolator.py

    Parameters
    ----------
    reference_data
        Dictionary containing interpolation attributes.

    Attributes
    ----------
    years
        List of reference years for the interpolation.
    values
        List of reference values for the interpolation.
    method
        Interpolation method, default is 'linear'.
    positive_constraint
        If True, ensures interpolated values are non-negative.
    """

    def __init__(self, reference_data: dict):
        self.years = reference_data["years"]
        self.values = reference_data["values"]
        if "method" in reference_data:
            self.method = reference_data["method"]
        else:
            self.method = "linear"
        if "positive_constraint" in reference_data:
            self.positive_constraint = reference_data["positive_constraint"]
        else:
            self.positive_constraint = False


class AeroMAPSModel(object):
    """
    Base class for AeroMAPS model components that provides shared state and utilities.

    Parameters
    ----------
    name
        Name of the model instance.
    parameters
        AeroMAPS process parameters object containing model inputs.
    model_type
        Type of the model, either 'auto' or 'custom'.

    Attributes
    ----------
    name
        Name of the model instance.
    parameters
        Reference to the parameters object passed at construction.
    float_outputs
        Dictionary storing scalar outputs produced by the model.
    model_type
        Configured model type, either 'auto' or 'custom'.
    input_names
        Dictionary of expected input names and types (only for 'custom' models).
    output_names
        Dictionary of output names and types (only for 'custom' models).
    default_input_data
        Default input data provided internally by the model (only for 'custom' models).
    _skip_data_type_validation
        Flag to skip input/output data type validation for custom models.
    climate_historic_start_year
        Start year for climate-related historical data.
    historic_start_year
        Start year for general historical data.
    prospection_start_year
        First year of the prospection/projection period.
    end_year
        Last year of the model time horizon.
    df
        pandas DataFrame indexed by model years for vector outputs.
    df_climate
        pandas DataFrame indexed by climate years for climate-specific outputs.
    xarray_lca
        xarray DataArray placeholder used by some LCA computations.
    years
        Numpy array of years spanning the model horizon.
    """

    def __init__(self, name, parameters=None, model_type="auto"):
        self.name = name
        self.parameters = parameters
        self.float_outputs = {}
        if self.parameters is not None:
            self._initialize_df()

        # Verify model type
        self.model_type = model_type
        if self.model_type == "custom":
            self.input_names = {}  # Dictionary to store input names and their types (or values)
            self.output_names = {}  # Dictionary to store output names and their types (or values)
            self.default_input_data = {}  # Dictionary to store default input data (i.e. provided internally by the model rather than parameters.json)
            self._skip_data_type_validation = False  # Whether to skip input/output data type validation. If True, input_names and output_names can be lists of names only.
        elif self.model_type != "auto":
            raise ValueError("model_type must be either 'auto' or 'custom'")

    def _initialize_df(self):
        self.climate_historic_start_year = self.parameters.climate_historic_start_year
        self.historic_start_year = self.parameters.historic_start_year
        self.prospection_start_year = self.parameters.prospection_start_year
        self.end_year = self.parameters.end_year
        self.df: pd.DataFrame = pd.DataFrame(
            index=range(self.historic_start_year, self.end_year + 1)
        )
        self.df_climate: pd.DataFrame = pd.DataFrame(
            index=range(self.climate_historic_start_year, self.end_year + 1)
        )
        self.xarray_lca: xr.DataArray = xr.DataArray()
        self.years = np.linspace(self.historic_start_year, self.end_year, len(self.df.index))

    def _store_outputs(self, output_data):
        """
        Store vector outputs in self.df and float outputs in self.float_outputs.
        Checks if the columns already exist in self.df to update them in place, otherwise joins new columns.

        Parameters
        ----------
        output_data
            Dictionary with output names as keys and output data as values.
        """
        # Separate series-like outputs and scalar outputs
        series_items = {k: v for k, v in output_data.items() if isinstance(v, pd.Series)}
        other_items = {k: v for k, v in output_data.items() if k not in series_items}

        # If there are Series outputs, update existing columns and join new ones
        if series_items:
            df_series = pd.DataFrame(series_items)

            # Columns that already exist in self.df -> update in place
            existing_cols = [c for c in df_series.columns if c in self.df.columns]
            for c in existing_cols:
                self.df.loc[:, c] = df_series[c]

            # New columns -> join to self.df
            new_cols = [c for c in df_series.columns if c not in self.df.columns]
            if new_cols:
                self.df = self.df.join(df_series[new_cols])

        # Handle non-series outputs (floats) and validate types
        for key, val in other_items.items():
            if isinstance(val, float) or isinstance(val, (int, np.floating, np.integer)):
                # store numeric scalars as float_outputs (coerce ints)
                self.float_outputs[key] = float(val)
            elif isinstance(val, pd.Series):
                # Shouldn't reach here, but handle defensively
                self.df.loc[:, key] = val
            else:
                raise ValueError(f"Output {key} is not a valid type.")


def aeromaps_interpolation_function(
    self,
    reference_years,
    reference_years_values,
    method="linear",
    positive_constraint=False,
    model_name="Not provided",
):
    """
    Interpolate values across the scenario horizon from reference years and values.

    Parameters
    ----------
    reference_years
        Sequence of reference years used for interpolation.
    reference_years_values
        Sequence of values corresponding to the reference years.
    method
        Interpolation method to use (e.g. 'linear').
    positive_constraint
        If True, negative interpolated values are clipped to zero.
    model_name
        Optional name used in warnings.

    Returns
    -------
    interpolation_function_values
        Series of interpolated values indexed by year taken from the model's DataFrame.
    """
    # Main
    if len(reference_years) == 0:
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "interpolation_function_values"] = reference_years_values[0]
    else:
        interpolation_function = interp1d(
            reference_years,
            reference_years_values,
            kind=method,
        )

        # If first reference year is lower than prospection start year, we start interpolating before
        if reference_years[0] != self.prospection_start_year:
            warnings.warn(
                f"\n[Interpolation Model: {model_name} Warning]\n"
                f"The first reference year ({reference_years[0]}) differs from the prospection start year ({self.prospection_start_year}).\n"
                f"Interpolation will begin at the first reference year."
            )
            prospection_start_year = reference_years[0]
        else:
            prospection_start_year = self.prospection_start_year

        if reference_years[-1] == self.end_year:
            for k in range(prospection_start_year, reference_years[-1] + 1):
                if positive_constraint and interpolation_function(k) <= 0.0:
                    self.df.loc[k, "interpolation_function_values"] = 0.0
                else:
                    self.df.loc[k, "interpolation_function_values"] = interpolation_function(k)
        elif reference_years[-1] > self.end_year:
            warnings.warn(
                "Warning Message - "
                + "Model name: "
                + model_name
                + " - Warning on aeromaps_interpolation_function:"
                + " The last reference year for the interpolation is higher than end_year, the interpolation function is therefore not used in its entirety.",
            )
            for k in range(prospection_start_year, self.end_year + 1):
                if positive_constraint and interpolation_function(k) <= 0.0:
                    self.df.loc[k, "interpolation_function_values"] = 0.0
                else:
                    self.df.loc[k, "interpolation_function_values"] = interpolation_function(k)
        else:
            warnings.warn(
                "Warning Message - "
                + "Model name: "
                + model_name
                + " - Warning on aeromaps_interpolation_function:"
                + " The last reference year for the interpolation is lower than end_year, the value associated to the last reference year is therefore used as a constant for the upper years.",
            )
            for k in range(prospection_start_year, reference_years[-1] + 1):
                if positive_constraint and interpolation_function(k) <= 0.0:
                    self.df.loc[k, "interpolation_function_values"] = 0.0
                else:
                    self.df.loc[k, "interpolation_function_values"] = interpolation_function(k)
            for k in range(reference_years[-1] + 1, self.end_year + 1):
                self.df.loc[k, "interpolation_function_values"] = self.df.loc[
                    k - 1, "interpolation_function_values"
                ]

    interpolation_function_values = self.df.loc[:, "interpolation_function_values"]

    # Delete intermediate df column
    self.df.pop("interpolation_function_values")

    return interpolation_function_values


def aeromaps_leveling_function(
    self, reference_periods, reference_periods_values, model_name="Not provided"
):
    """
    Build a stepwise series that holds values constant across defined reference periods.

    Parameters
    ----------
    reference_periods
        Sequence of period boundary years used to define steps.
    reference_periods_values
        Sequence of values corresponding to each reference period.
    model_name
        Optional name used in warnings.

    Returns
    -------
    leveling_function_values
        Series of leveled values indexed by year taken from the model's DataFrame.
    """
    # Main
    if len(reference_periods) == 0:
        for k in range(self.prospection_start_year, self.end_year + 1):
            self.df.loc[k, "leveling_function_values"] = reference_periods_values[0]
    else:
        if reference_periods[-1] == self.end_year:
            for i in range(0, len(reference_periods) - 1):
                for k in range(reference_periods[i], reference_periods[i + 1] + 1):
                    self.df.loc[k, "leveling_function_values"] = reference_periods_values[i]
        elif reference_periods[-1] > self.end_year:
            warnings.warn(
                "Warning Message - "
                + "Model name: "
                + model_name
                + " - Warning on aeromaps_leveling_function:"
                + " The last reference year for the leveling is higher than end_year, the leveling function is therefore not used in its entirety.",
            )
            for i in range(0, len(reference_periods) - 1):
                for k in range(reference_periods[i], reference_periods[i + 1] + 1):
                    if k <= self.end_year:
                        self.df.loc[k, "leveling_function_values"] = reference_periods_values[i]
                    else:
                        pass
        else:
            warnings.warn(
                "Warning Message - "
                + "Model name: "
                + model_name
                + " - Warning on aeromaps_leveling_function:"
                + " The last reference year for the leveling is lower than end_year, the value associated to the last reference period is therefore used as a constant for the upper period.",
            )
            for i in range(0, len(reference_periods) - 1):
                for k in range(reference_periods[i], reference_periods[i + 1] + 1):
                    self.df.loc[k, "leveling_function_values"] = reference_periods_values[i]
            for k in range(reference_periods[-1] + 1, self.end_year + 1):
                self.df.loc[k, "leveling_function_values"] = self.df.loc[
                    k - 1, "leveling_function_values"
                ]

    leveling_function_values = self.df.loc[:, "leveling_function_values"]

    # Delete intermediate df column
    self.df.pop("leveling_function_values")

    return leveling_function_values


def AbsoluteGlobalWarmingPotentialCO2Function(climate_time_horizon):
    """
    Compute the absolute global warming potential (AGWP) for CO2 for a given time horizon.
    TODO: is base.py the appropriate location for this function?

    Parameters
    ----------
    climate_time_horizon
        Time horizon over which to compute the AGWP.

    Returns
    -------
    co2_agwp_h
        Absolute global warming potential value computed for CO2.
    """
    # Reference: IPCC AR5 - https://www.ipcc.ch/site/assets/uploads/2018/07/WGI_AR5.Chap_.8_SM.pdf

    # Parameter: climate time horizon
    h = climate_time_horizon

    co2_molar_mass = 44.01 * 1e-3  # [kg/mol]
    air_molar_mass = 28.97e-3  # [kg/mol]
    atmosphere_total_mass = 5.1352e18  # [kg]

    radiative_efficiency = 1.37e-2 * 1e9  # radiative efficiency [mW/m^2]

    # RF per unit mass increase in atmospheric abundance of CO2 [W/m^2/kg]
    A_CO2 = radiative_efficiency * air_molar_mass / (co2_molar_mass * atmosphere_total_mass) * 1e-3

    # Coefficients for the model
    a = [0.2173, 0.2240, 0.2824, 0.2763]
    tau = [0, 394.4, 36.54, 4.304]  # CO2 lifetime [yrs]

    co2_agwp_h = A_CO2 * a[0] * h
    for i in [1, 2, 3]:
        co2_agwp_h += A_CO2 * a[i] * tau[i] * (1 - np.exp(-h / tau[i]))

    # From W/m^2/kg.yr to mW/m^2/Mt.yr
    co2_agwp_h = co2_agwp_h * 1e3 * 1e9

    return co2_agwp_h


def GWPStarEquivalentEmissionsFunction(
    self, emissions_erf, gwpstar_variation_duration, gwpstar_s_coefficient
):
    """
    Compute equivalent CO2 emissions according to the GWP* formulation.
    TODO: is base.py the appropriate location for this function?

    Parameters
    ----------
    emissions_erf
        Time series of emissions expressed as effective radiative forcing or equivalent values.
    gwpstar_variation_duration
        Duration over which emission rate changes are evaluated for GWP*.
    gwpstar_s_coefficient
        S coefficient used in the GWP* formulation to weight instantaneous forcing.

    Returns
    -------
    emissions_equivalent_emissions
        Series of GWP*-equivalent CO2 emissions indexed by climate years.
    """
    # Reference: Smith et al. (2021), https://doi.org/10.1038/s41612-021-00169-8
    # Global
    climate_time_horizon = 100
    co2_agwp_h = AbsoluteGlobalWarmingPotentialCO2Function(climate_time_horizon)

    # g coefficient for GWP*
    if gwpstar_s_coefficient == 0:
        g_coefficient = 1
    else:
        g_coefficient = (
            1 - np.exp(-gwpstar_s_coefficient / (1 - gwpstar_s_coefficient))
        ) / gwpstar_s_coefficient

    # Main
    for k in range(self.climate_historic_start_year, self.end_year + 1):
        if k - self.climate_historic_start_year >= gwpstar_variation_duration:
            self.df_climate.loc[k, "emissions_erf_variation"] = (
                emissions_erf.loc[k] - emissions_erf.loc[k - gwpstar_variation_duration]
            ) / gwpstar_variation_duration
        else:
            self.df_climate.loc[k, "emissions_erf_variation"] = (
                emissions_erf.loc[k] / gwpstar_variation_duration
            )

    for k in range(self.climate_historic_start_year, self.end_year + 1):
        self.df_climate.loc[k, "emissions_equivalent_emissions"] = (
            g_coefficient
            * (1 - gwpstar_s_coefficient)
            * climate_time_horizon
            / co2_agwp_h
            * self.df_climate.loc[k, "emissions_erf_variation"]
        ) + g_coefficient * gwpstar_s_coefficient / co2_agwp_h * emissions_erf.loc[k]
    emissions_equivalent_emissions = self.df_climate.loc[:, "emissions_equivalent_emissions"]

    # Delete intermediate df column
    self.df_climate.pop("emissions_erf_variation")
    self.df_climate.pop("emissions_equivalent_emissions")

    return emissions_equivalent_emissions


def RunFair(self, species_quantities, without="None"):
    """
    Configure and run the FaIR climate model using provided species inputs.
    TODO: is base.py the appropriate location for this function?

    Parameters
    ----------
    species_quantities
        List or sequence of species input arrays used to fill FaIR emissions and forcings.
    without
        Optional string controlling which aviation components are excluded from the run.

    Returns
    -------
    temperature, forcing_sum
        Temperature time series and total forcing time series produced by the FaIR run.
    """
    # Creation of FaIR instance
    f = FAIR()

    # Definition of time horizon, scenarios, configs
    start_time = 1765
    end_time = self.end_year
    f.define_time(start_time, end_time, 1)
    f.define_scenarios(["central"])
    f.define_configs(["central"])
    # f.define_configs(["high", "central", "low"])

    # Definition of species and properties
    species = [
        "CO2",  # Includes world emissions, aviation emissions, and equivalent emissions for NOx effects (except ST O3)
        "World CH4",
        "Aviation contrails",
        "Aviation NOx ST O3 increase",
        "Aviation H2O",
        "Aviation sulfur",
        "Aviation soot",
        "Aviation aerosols",
    ]
    properties = {
        "CO2": {
            "type": "co2",
            "input_mode": "emissions",
            "greenhouse_gas": True,
            "aerosol_chemistry_from_emissions": False,
            "aerosol_chemistry_from_concentration": False,
        },
        "World CH4": {
            "type": "ch4",
            "input_mode": "emissions",
            "greenhouse_gas": True,
            "aerosol_chemistry_from_emissions": False,
            "aerosol_chemistry_from_concentration": True,  # we treat methane as a reactive gas
        },
        "Aviation contrails": {
            "type": "contrails",
            "input_mode": "forcing",
            "greenhouse_gas": False,
            "aerosol_chemistry_from_emissions": False,
            "aerosol_chemistry_from_concentration": False,
        },
        "Aviation NOx ST O3 increase": {
            "type": "ozone",
            "input_mode": "forcing",
            "greenhouse_gas": False,
            "aerosol_chemistry_from_emissions": False,
            "aerosol_chemistry_from_concentration": False,
        },
        "Aviation H2O": {
            "type": "h2o stratospheric",
            "input_mode": "forcing",
            "greenhouse_gas": False,
            "aerosol_chemistry_from_emissions": False,
            "aerosol_chemistry_from_concentration": False,
        },
        "Aviation sulfur": {
            "type": "sulfur",
            "input_mode": "emissions",
            "greenhouse_gas": False,
            "aerosol_chemistry_from_emissions": True,
            "aerosol_chemistry_from_concentration": False,
        },
        "Aviation soot": {
            "type": "black carbon",
            "input_mode": "emissions",
            "greenhouse_gas": False,
            "aerosol_chemistry_from_emissions": True,
            "aerosol_chemistry_from_concentration": False,
        },
        # Dedicated specie for aerosols
        "Aviation aerosols": {
            "type": "ari",
            "input_mode": "calculated",
            "greenhouse_gas": False,
            "aerosol_chemistry_from_emissions": False,
            "aerosol_chemistry_from_concentration": False,
        },
    }
    f.define_species(species, properties)

    # Definition of run options
    f.ghg_method = "leach2021"
    f.aci_method = "myhre1998"

    # Creation of input and output data
    f.allocate()

    # Filling species quantities
    if without == "All aviation":
        fill(
            f.emissions,
            species_quantities[0][1 : self.end_year - 1765 + 1],
            specie="CO2",
            config=f.configs[0],
            scenario=f.scenarios[0],
        )
        fill(
            f.emissions,
            species_quantities[5][1 : self.end_year - 1765 + 1],
            specie="World CH4",
            config=f.configs[0],
            scenario=f.scenarios[0],
        )
        fill(
            f.forcing, 0, specie="Aviation contrails", config=f.configs[0], scenario=f.scenarios[0]
        )
        fill(
            f.forcing,
            0,
            specie="Aviation NOx ST O3 increase",
            config=f.configs[0],
            scenario=f.scenarios[0],
        )
        fill(f.forcing, 0, specie="Aviation H2O", config=f.configs[0], scenario=f.scenarios[0])
        fill(f.emissions, 0, specie="Aviation sulfur", config=f.configs[0], scenario=f.scenarios[0])
        fill(f.emissions, 0, specie="Aviation soot", config=f.configs[0], scenario=f.scenarios[0])
    else:
        if without == "Aviation CO2":
            total_CO2 = (
                species_quantities[0][1 : self.end_year - 1765 + 1]
                + species_quantities[2][1 : self.end_year - 1765 + 1]
                + species_quantities[3][1 : self.end_year - 1765 + 1]
                + species_quantities[4][1 : self.end_year - 1765 + 1]
            )
        elif without == "Aviation NOx LT O3 decrease":
            total_CO2 = (
                species_quantities[0][1 : self.end_year - 1765 + 1]
                + species_quantities[1][1 : self.end_year - 1765 + 1]
                + species_quantities[3][1 : self.end_year - 1765 + 1]
                + species_quantities[4][1 : self.end_year - 1765 + 1]
            )
        elif without == "Aviation NOx CH4 decrease":
            total_CO2 = (
                species_quantities[0][1 : self.end_year - 1765 + 1]
                + species_quantities[1][1 : self.end_year - 1765 + 1]
                + species_quantities[2][1 : self.end_year - 1765 + 1]
                + species_quantities[4][1 : self.end_year - 1765 + 1]
            )
        elif without == "Aviation NOx H2O decrease":
            total_CO2 = (
                species_quantities[0][1 : self.end_year - 1765 + 1]
                + species_quantities[1][1 : self.end_year - 1765 + 1]
                + species_quantities[2][1 : self.end_year - 1765 + 1]
                + species_quantities[3][1 : self.end_year - 1765 + 1]
            )
        else:
            total_CO2 = (
                species_quantities[0][1 : self.end_year - 1765 + 1]
                + species_quantities[1][1 : self.end_year - 1765 + 1]
                + species_quantities[2][1 : self.end_year - 1765 + 1]
                + species_quantities[3][1 : self.end_year - 1765 + 1]
                + species_quantities[4][1 : self.end_year - 1765 + 1]
            )
        fill(f.emissions, total_CO2, specie="CO2", config=f.configs[0], scenario=f.scenarios[0])
        fill(
            f.emissions,
            species_quantities[5][1 : self.end_year - 1765 + 1],
            specie="World CH4",
            config=f.configs[0],
            scenario=f.scenarios[0],
        )
        if without != "Aviation contrails":
            fill(
                f.forcing,
                species_quantities[6],
                specie="Aviation contrails",
                config=f.configs[0],
                scenario=f.scenarios[0],
            )
        else:
            fill(
                f.forcing,
                0,
                specie="Aviation contrails",
                config=f.configs[0],
                scenario=f.scenarios[0],
            )
        if without != "Aviation NOx ST O3 increase":
            fill(
                f.forcing,
                species_quantities[7],
                specie="Aviation NOx ST O3 increase",
                config=f.configs[0],
                scenario=f.scenarios[0],
            )
        else:
            fill(
                f.forcing,
                0,
                specie="Aviation NOx ST O3 increase",
                config=f.configs[0],
                scenario=f.scenarios[0],
            )
        if without != "Aviation H2O":
            fill(
                f.forcing,
                species_quantities[8],
                specie="Aviation H2O",
                config=f.configs[0],
                scenario=f.scenarios[0],
            )
        else:
            fill(f.forcing, 0, specie="Aviation H2O", config=f.configs[0], scenario=f.scenarios[0])
        if without != "Aviation sulfur":
            fill(
                f.emissions,
                species_quantities[9][1 : self.end_year - 1765 + 1],
                specie="Aviation sulfur",
                config=f.configs[0],
                scenario=f.scenarios[0],
            )
        else:
            fill(
                f.emissions,
                0,
                specie="Aviation sulfur",
                config=f.configs[0],
                scenario=f.scenarios[0],
            )
        if without != "Aviation soot":
            fill(
                f.emissions,
                species_quantities[10][1 : self.end_year - 1765 + 1],
                specie="Aviation soot",
                config=f.configs[0],
                scenario=f.scenarios[0],
            )
        else:
            fill(
                f.emissions, 0, specie="Aviation soot", config=f.configs[0], scenario=f.scenarios[0]
            )

    initialise(f.forcing, 0)
    initialise(f.temperature, 0)
    initialise(f.cumulative_emissions, 0)
    initialise(f.airborne_emissions, 0)

    # Filling climate configs
    # fill(f.climate_configs["ocean_heat_transfer"], [1.1, 1.6, 0.9], config="central")
    # fill(f.climate_configs["ocean_heat_capacity"], [8, 14, 100], config="central")
    # fill(f.climate_configs["deep_ocean_efficacy"], 1.1, config="central")
    # Corresponds to a "low" configuration on FaIR
    fill(f.climate_configs["ocean_heat_transfer"], [1.7, 2.0, 1.1], config="central")
    fill(f.climate_configs["ocean_heat_capacity"], [6, 11, 75], config="central")
    fill(f.climate_configs["deep_ocean_efficacy"], 0.8, config="central")

    # Filling species configs
    for specie in species:
        if specie == "CO2":
            fill(
                f.species_configs["partition_fraction"],
                [0.2173, 0.2240, 0.2824, 0.2763],
                specie="CO2",
            )
            fill(
                f.species_configs["unperturbed_lifetime"], [1e9, 394.4, 36.54, 4.304], specie="CO2"
            )
            fill(f.species_configs["baseline_concentration"], 278.3, specie="CO2")
            fill(f.species_configs["forcing_reference_concentration"], 278.3, specie="CO2")
            fill(f.species_configs["molecular_weight"], 44.009, specie="CO2")
            fill(
                f.species_configs["greenhouse_gas_radiative_efficiency"],
                1.3344985680386619e-05,
                specie="CO2",
            )
            f.calculate_iirf0()
            f.calculate_g()
            f.calculate_concentration_per_emission()
            fill(f.species_configs["iirf_0"], 29, specie="CO2")
            fill(f.species_configs["iirf_airborne"], [0.000819 * 2], specie="CO2")
            fill(f.species_configs["iirf_uptake"], [0.00846 * 2], specie="CO2")
            fill(f.species_configs["iirf_temperature"], [8], specie="CO2")
            fill(f.species_configs["aci_scale"], -2.09841432)

        if specie == "World CH4":
            fill(f.species_configs["partition_fraction"], [1, 0, 0, 0], specie=specie)
            fill(f.species_configs["unperturbed_lifetime"], 8.25, specie=specie)
            fill(f.species_configs["baseline_concentration"], 729, specie=specie)  # ppb
            fill(f.species_configs["forcing_reference_concentration"], 729, specie=specie)
            fill(f.species_configs["molecular_weight"], 16.043, specie=specie)
            fill(
                f.species_configs["greenhouse_gas_radiative_efficiency"],
                0.00038864402860869495,
                specie=specie,
            )
            f.calculate_iirf0()
            f.calculate_g()
            f.calculate_concentration_per_emission()
            fill(f.species_configs["iirf_airborne"], 0.00032, specie=specie)
            fill(f.species_configs["iirf_uptake"], 0, specie=specie)
            fill(f.species_configs["iirf_temperature"], -0.3, specie=specie)
            fill(
                f.species_configs["erfari_radiative_efficiency"],
                -0.002653 / 1023.2219696044921,
                specie=specie,
            )  # W m-2 ppb-1
            fill(f.species_configs["aci_scale"], -2.09841432)

        if specie == "Aviation sulfur":
            erf_aci_sulfur = 0.0
            fill(
                f.species_configs["erfari_radiative_efficiency"],
                -0.0199 + erf_aci_sulfur,
                specie=specie,
            )  # W m-2 MtSO2-1 yr
            fill(f.species_configs["aci_shape"], 0.0, specie=specie)

        if specie == "Aviation soot":
            erf_aci_BC = 0.0
            fill(
                f.species_configs["erfari_radiative_efficiency"], 0.1007 + erf_aci_BC, specie=specie
            )  # W m-2 MtC-1 yr
            fill(f.species_configs["aci_shape"], 0.0, specie=specie)

    # Run
    f.run()

    return (
        f.temperature.loc[dict(config=f.configs[0], layer=0)].data,
        f.forcing_sum.loc[dict(config=f.configs[0])].data,
    )
