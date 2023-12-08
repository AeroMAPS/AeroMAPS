import pandas as pd
import numpy as np
from numpy import genfromtxt
from scipy.interpolate import interp1d
import warnings


class AeromapsModel(object):
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
        self.historic_start_year = self.parameters.historic_start_year
        self.prospection_start_year = self.parameters.prospection_start_year
        self.end_year = self.parameters.end_year
        self.df: pd.DataFrame = pd.DataFrame(
            index=range(self.historic_start_year, self.end_year + 1)
        )
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
            self.df.loc[k, "interpolation_function_values"] = reference_years_values
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
            self.df.loc[k, "leveling_function_values"] = reference_periods_values
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
    self, emissions_erf, gwpstar_variation_duration, alpha_coefficient
):

    # Reference: Smith et al. (2021), https://doi.org/10.1038/s41612-021-00169-8
    # Global
    climate_time_horizon = 100
    co2_agwp_h = AbsoluteGlobalWarmingPotentialCO2Function(climate_time_horizon)

    # g coefficient for GWP*
    if alpha_coefficient == 0:
        g_coefficient = 1
    else:
        g_coefficient = (
            1 - np.exp(-alpha_coefficient / (1 - alpha_coefficient))
        ) / alpha_coefficient

    # Main
    for k in range(self.prospection_start_year, self.end_year + 1):
        self.df.loc[k, "emissions_erf_variation"] = (
            emissions_erf.loc[k] - emissions_erf.loc[k - gwpstar_variation_duration]
        ) / gwpstar_variation_duration
    for k in range(self.prospection_start_year, self.end_year + 1):
        self.df.loc[k, "emissions_equivalent_emissions"] = (
            g_coefficient
            * (1 - alpha_coefficient)
            * climate_time_horizon
            / co2_agwp_h
            * self.df.loc[k, "emissions_erf_variation"]
        ) + g_coefficient * alpha_coefficient / co2_agwp_h * emissions_erf.loc[k]
    emissions_equivalent_emissions = self.df.loc[:, "emissions_equivalent_emissions"]

    # Delete intermediate df column
    self.df.pop("emissions_erf_variation")
    self.df.pop("emissions_equivalent_emissions")

    return emissions_equivalent_emissions


def GWPStarEquivalentEmissionsArrayFunction(
    self, emissions_erf, gwpstar_variation_duration, alpha_coefficient
):

    # Reference: Smith et al. (2021), https://doi.org/10.1038/s41612-021-00169-8
    # Global
    climate_time_horizon = 100
    co2_agwp_h = AbsoluteGlobalWarmingPotentialCO2Function(climate_time_horizon)

    # g coefficient for GWP*
    if alpha_coefficient == 0:
        g_coefficient = 1
    else:
        g_coefficient = (
            1 - np.exp(-alpha_coefficient / (1 - alpha_coefficient))
        ) / alpha_coefficient

    # Main
    emissions_erf_variation = np.zeros(len(emissions_erf))
    for k in range(0, len(emissions_erf)):
        if k >= gwpstar_variation_duration:
            emissions_erf_variation[k] = (
                emissions_erf[k] - emissions_erf[k - int(gwpstar_variation_duration)]
            ) / gwpstar_variation_duration
        else:
            emissions_erf_variation[k] = emissions_erf[k]
    emissions_equivalent_emissions = np.zeros(len(emissions_erf))
    for k in range(0, len(emissions_erf)):
        emissions_equivalent_emissions[k] = (
            g_coefficient
            * (1 - alpha_coefficient)
            * climate_time_horizon
            / co2_agwp_h
            * emissions_erf_variation[k]
        ) + g_coefficient * alpha_coefficient / co2_agwp_h * emissions_erf[k]

    return emissions_equivalent_emissions
