import xarray as xr
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
import warnings
from fair import FAIR
from fair.interface import fill, initialise


class AeroMAPSModel(object):
    def __init__(
        self,
        name,
        parameters=None,
    ):
        self.name = name
        self.parameters = parameters
        self.float_outputs = {}
        if self.parameters is not None:
            self._initialize_df()

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


def AeromapsInterpolationFunction(
    self,
    reference_years,
    reference_years_values,
    method="linear",
    positive_constraint=False,
    model_name="Not provided",
):
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
        if reference_years[-1] == self.end_year:
            for k in range(self.prospection_start_year, reference_years[-1] + 1):
                if positive_constraint and interpolation_function(k) <= 0.0:
                    self.df.loc[k, "interpolation_function_values"] = 0.0
                else:
                    self.df.loc[k, "interpolation_function_values"] = interpolation_function(k)
        elif reference_years[-1] > self.end_year:
            warnings.warn(
                "Warning Message - "
                + "Model name: "
                + model_name
                + " - Warning on AeromapsInterpolationFunction:"
                + " The last reference year for the interpolation is higher than end_year, the interpolation function is therefore not used in its entirety.",
            )
            for k in range(self.prospection_start_year, self.end_year + 1):
                if positive_constraint and interpolation_function(k) <= 0.0:
                    self.df.loc[k, "interpolation_function_values"] = 0.0
                else:
                    self.df.loc[k, "interpolation_function_values"] = interpolation_function(k)
        else:
            warnings.warn(
                "Warning Message - "
                + "Model name: "
                + model_name
                + " - Warning on AeromapsInterpolationFunction:"
                + " The last reference year for the interpolation is lower than end_year, the value associated to the last reference year is therefore used as a constant for the upper years.",
            )
            for k in range(self.prospection_start_year, reference_years[-1] + 1):
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


def AeromapsLevelingFunction(
    self, reference_periods, reference_periods_values, model_name="Not provided"
):
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
                + " - Warning on AeromapsLevelingFunction:"
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
                + " - Warning on AeromapsLevelingFunction:"
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
