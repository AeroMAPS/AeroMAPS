import pandas as pd
from typing import Tuple
from aeromaps.models.base import AeroMAPSModel


class HealthImpactsClimate(AeroMAPSModel):
    """
    Class to compute health impacts from climate change induced by aviation.

    This model estimates Disability-Adjusted Life Years (DALYs) resulting from
    temperature increases attributable to aviation emissions. Damages are computed
    using damage factors applied to the temperature increase relative to a baseline year.

    METHODOLOGICAL NOTE:
    This implementation follows a "retrospective" approach:
        - For a given year t, DALYs represent the health impacts associated with the
          temperature increase from aviation emissions up to year t.
        - Consequently, damages are driven by past emissions rather than emissions in year t.
    This approach differs from standard life cycle impact assessment (LCIA) methodologies
    (e.g. Impact World+), which estimate future damages over a fixed time horizon (e.g. 100 years)
    *following* an emission (future-oriented).
    The retrospective approach is chosen here to better reflect the actual damages estimated to occur each year.

    BASELINE PERIOD:
    Climate change impacts are defined as the excess DALYs relative to a baseline period.
    In this implementation, temperature anomalies are computed relative to the average climate state
    over the period [climate_historic_start_year; historic_start_year] (typically 1940-2000).

    SOURCES:
    Damage factors are obtained from the LCIA methodology Impact World+ v2.1, which is based on:
        - Heat/cold stresses: Rupcic et al. 2022; Bressler et al. 2021.
        - Dengue, diarrhea, undernutrition, coastal flood and malaria: WHO Report 2014.
    See: https://github.com/CIRAIG/IWP_Reborn/blob/master/Methodology/Climate%20change.md


    Parameters
    ----------
    name : str, optional
        Name of the model instance, by default "health_impacts_climate".
    """

    def __init__(self, name="health_impacts_climate", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
            self,
            temperature_increase_from_aviation: pd.Series,
            temperature_increase_from_co2_from_aviation: pd.Series,
            temperature_increase_from_contrails_from_aviation: pd.Series,
            temperature_increase_from_nox_from_aviation: pd.Series,
            temperature_increase_from_nox_short_term_o3_increase_from_aviation: pd.Series,
            temperature_increase_from_nox_long_term_o3_decrease_from_aviation: pd.Series,
            temperature_increase_from_nox_ch4_decrease_from_aviation: pd.Series,
            temperature_increase_from_nox_stratospheric_water_vapor_decrease_from_aviation: pd.Series,
            temperature_increase_from_h2o_from_aviation: pd.Series,
            temperature_increase_from_soot_from_aviation: pd.Series,
            temperature_increase_from_sulfur_from_aviation: pd.Series,
            damage_factor_climate_change_heat: float,
            damage_factor_climate_change_dengue: float,
            damage_factor_climate_change_diarrhea: float,
            damage_factor_climate_change_malaria: float,
            damage_factor_climate_change_undernutrition: float,
            damage_factor_climate_change_coastal: float

    ) -> Tuple[
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series
    ]:
        """
        Compute DALYs from temperature increase for each species and total.

        Parameters
        ----------
        temperature_increase_from_aviation : pd.Series
            Time series of temperature increase from total aviation emissions.
        temperature_increase_from_co2_from_aviation : pd.Series
            Time series of temperature increase from CO2 emissions from aviation.
        temperature_increase_from_contrails_from_aviation : pd.Series
            Time series of temperature increase from contrails from aviation.
        temperature_increase_from_nox_from_aviation : pd.Series
            Time series of temperature increase from NOx emissions from aviation (total effects).
        temperature_increase_from_nox_short_term_o3_increase_from_aviation : pd.Series
            Time series of temperature increase from NOx emissions from aviation (short term O3 effects).
        temperature_increase_from_nox_long_term_o3_decrease_from_aviation : pd.Series
            Time series of temperature increase from NOx emissions from aviation (long term O3 effects).
        temperature_increase_from_nox_ch4_decrease_from_aviation : pd.Series
            Time series of temperature increase from NOx emissions from aviation (CH4 decrease effects).
        temperature_increase_from_nox_stratospheric_water_vapor_decrease_from_aviation : pd.Series
            Time series of temperature increase from NOx emissions from aviation (stratospheric water vapor decrease effects).
        temperature_increase_from_h2o_from_aviation : pd.Series
            Time series of temperature increase from H2O emissions from aviation.
        temperature_increase_from_soot_from_aviation : pd.Series
            Time series of temperature increase from soot emissions from aviation.
        temperature_increase_from_sulfur_from_aviation : pd.Series
            Time series of temperature increase from sulfur emissions from aviation.
        damage_factor_climate_change_heat : float
            Conversion factor from temperature increase [°C] to [DALYs/year] for heat and cold stresses.
        damage_factor_climate_change_dengue : float
            Conversion factor from temperature increase [°C] to [DALYs/year] for dengue.
        damage_factor_climate_change_diarrhea : float
            Conversion factor from temperature increase [°C] to [DALYs/year] for diarrhea.
        damage_factor_climate_change_malaria : float
            Conversion factor from temperature increase [°C] to [DALYs/year] for malaria.
        damage_factor_climate_change_undernutrition : float
            Conversion factor from temperature increase [°C] to [DALYs/year] for undernutrition.
        damage_factor_climate_change_coastal : float
            Conversion factor from temperature increase [°C] to [DALYs/year] for coastal floods

        Returns
        -------
        Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]
            DALYs per year attributable to total aviation and each species (co2, contrails, nox, h2o, soot, sulfur).
        """
        # Temperature inputs
        input_data = {
            "temperature_increase_from_aviation": temperature_increase_from_aviation,
            "temperature_increase_from_co2": temperature_increase_from_co2_from_aviation,
            "temperature_increase_from_contrails": temperature_increase_from_contrails_from_aviation,
            "temperature_increase_from_nox": temperature_increase_from_nox_from_aviation,
            "temperature_increase_from_nox_short_term_o3_increase": temperature_increase_from_nox_short_term_o3_increase_from_aviation,
            "temperature_increase_from_nox_long_term_o3_decrease": temperature_increase_from_nox_long_term_o3_decrease_from_aviation,
            "temperature_increase_from_nox_ch4_decrease": temperature_increase_from_nox_ch4_decrease_from_aviation,
            "temperature_increase_from_nox_stratospheric_water_vapor_decrease": temperature_increase_from_nox_stratospheric_water_vapor_decrease_from_aviation,
            "temperature_increase_from_h2o": temperature_increase_from_h2o_from_aviation,
            "temperature_increase_from_soot": temperature_increase_from_soot_from_aviation,
            "temperature_increase_from_sulfur": temperature_increase_from_sulfur_from_aviation,
        }

        # Conversion factor from temperature increase [°C] to [DALY/year] .
        damage_factor = (
                    damage_factor_climate_change_heat
                    + damage_factor_climate_change_dengue
                    + damage_factor_climate_change_diarrhea
                    + damage_factor_climate_change_malaria
                    + damage_factor_climate_change_undernutrition
                    + damage_factor_climate_change_coastal
            )

        # Compute DALYs for each species and total aviation
        output_data = {}
        species = [
            "co2",
            "contrails",
            "nox",
            "nox_short_term_o3_increase",
            "nox_long_term_o3_decrease",
            "nox_ch4_decrease",
            "nox_stratospheric_water_vapor_decrease",
            "h2o",
            "soot",
            "sulfur",
            "aviation"
        ]
        years = range(self.historic_start_year, self.end_year + 1)
        for spec in species:
            temperature = input_data[f"temperature_increase_from_{spec}"]
            baseline_temperature = temperature.loc[
                self.climate_historic_start_year:self.historic_start_year
            ].mean()
            delta_temp = temperature.loc[years] - baseline_temperature
            dalys_spec = damage_factor * delta_temp
            output_data[f"dalys_climate_change_{spec}"] = dalys_spec
            if spec == "aviation":
                self.df.loc[years, "dalys_climate_change"] = dalys_spec
            else:
                self.df.loc[years, f"dalys_climate_change_{spec}"] = dalys_spec

        # Output data
        dalys_climate_change = output_data["dalys_climate_change_aviation"]
        dalys_climate_change_co2 = output_data["dalys_climate_change_co2"]
        dalys_climate_change_contrails = output_data["dalys_climate_change_contrails"]
        dalys_climate_change_nox = output_data["dalys_climate_change_nox"]
        dalys_climate_change_nox_short_term_o3 = output_data["dalys_climate_change_nox_short_term_o3_increase"]
        dalys_climate_change_nox_long_term_o3 = output_data["dalys_climate_change_nox_long_term_o3_decrease"]
        dalys_climate_change_nox_ch4 = output_data["dalys_climate_change_nox_ch4_decrease"]
        dalys_climate_change_nox_stratospheric_water_vapor = output_data["dalys_climate_change_nox_stratospheric_water_vapor_decrease"]
        dalys_climate_change_h2o = output_data["dalys_climate_change_h2o"]
        dalys_climate_change_soot = output_data["dalys_climate_change_soot"]
        dalys_climate_change_sulfur = output_data["dalys_climate_change_sulfur"]

        return (
            dalys_climate_change,
            dalys_climate_change_co2,
            dalys_climate_change_contrails,
            dalys_climate_change_nox,
            dalys_climate_change_nox_short_term_o3,
            dalys_climate_change_nox_long_term_o3,
            dalys_climate_change_nox_ch4,
            dalys_climate_change_nox_stratospheric_water_vapor,
            dalys_climate_change_h2o,
            dalys_climate_change_soot,
            dalys_climate_change_sulfur,
        )


class HealthImpactsSurfaceOzone(AeroMAPSModel):
    """
    Class to compute health impacts from surface ozone induced by aviation.

    This model calculates Disability-Adjusted Life Years (DALYs) from surface ozone based on
    total aviation fuel consumption, NOx emissions and characterisation factors from Pollet et al. 2026 (preprint).

    Parameters
    ----------
    name : str, optional
        Name of the model instance, by default "health_impacts_surface_ozone".
    """

    def __init__(self, name="health_impacts_surface_ozone", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
            self,
            dropin_fuel_mass_consumption: pd.Series,
            hydrogen_nox_emissions: pd.Series,
            nox_emissions: pd.Series,
            characterisation_factor_health_ozone_fuel: float,  # could be a pd.Series in the future if prospective CFs
            characterisation_factor_health_ozone_nox: float  # could be a pd.Series in the future if prospective CFs
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Compute DALYs from surface ozone based on fuel consumption and NOx emissions, respectively.

        Parameters
        ----------
        dropin_fuel_mass_consumption : pd.Series
            Time series of mass of drop-in fuel consumed (i.e., burned) by aviation [kg].
        hydrogen_nox_emissions : pd.Series
            Time series of NOx emissions from hydrogen fuel burn [kg NOx].
        nox_emissions : pd.Series
            Time series of NOx emissions from aviation [kg].
        characterisation_factor_health_ozone_fuel : float
            Characterisation factor for fuel burn to surface ozone DALYs [DALY/kg fuel].
        characterisation_factor_health_ozone_nox : float
            Characterisation factor for NOx emissions to surface ozone DALYs [DALY/kg NOx

        Returns
        -------
        dalys_ozone : pd.Series
            Total DALYs caused by aviation-induced surface ozone
        dalys_ozone_nox : pd.Series
            DALYs caused by NOx emissions alone (excluding other emissions)
        """
        # === Total impacts from fuel burn (incl. NOx emissions) ===
        # Apply CF for fuel burn to drop-in fuels (all emissions incl. NOx)
        dalys_ozone = dropin_fuel_mass_consumption * characterisation_factor_health_ozone_fuel

        # Add DALYs due to hydrogen NOx emissions (assuming only NOx contribution for H2 fuel burn)
        # (1e9: conversion from Tg to kg)
        dalys_ozone += (hydrogen_nox_emissions * 1e9) * characterisation_factor_health_ozone_nox

        # === DALYs from NOx emissions alone ===
        dalys_ozone_nox = (nox_emissions * 1e9) * characterisation_factor_health_ozone_nox

        # === Store outputs ===
        # Cut data before historic_start_year (out of scope)
        # Note that currently CFs are only valid for present-day, and may underestimate DALYs for future emissions.
        # Future improvements include the derivation of prospective CFs.
        dalys_ozone = dalys_ozone.loc[self.historic_start_year:self.end_year]
        dalys_ozone_nox = dalys_ozone_nox.loc[self.historic_start_year:self.end_year]
        self.df.loc[self.historic_start_year:self.end_year, "dalys_surface_ozone"] = dalys_ozone
        self.df.loc[self.historic_start_year:self.end_year, "dalys_surface_ozone_nox"] = dalys_ozone_nox

        return (
            dalys_ozone,
            dalys_ozone_nox
        )


class HealthImpactsParticulateMatter(AeroMAPSModel):
    """
    Class to compute health impacts from particulate matter induced by aviation.

    This model calculates Disability-Adjusted Life Years (DALYs) from fine particulate matter based on
    total aviation fuel consumption, NOx emissions and characterisation factors from Pollet et al. 2026 (preprint).

    Parameters
    ----------
    name : str, optional
        Name of the model instance, by default "health_impacts_particulate_matter".
    """

    def __init__(self, name="health_impacts_particulate_matter", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
            self,
            dropin_fuel_mass_consumption: pd.Series,
            hydrogen_nox_emissions: pd.Series,
            nox_emissions: pd.Series,
            characterisation_factor_health_particulate_matter_fuel: float,  # could be a pd.Series in the future if prospective CFs
            characterisation_factor_health_particulate_matter_nox: float  # could be a pd.Series in the future if prospective CFs
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Compute DALYs from particulate matter based on total fuel consumption and NOx emissions.

        Parameters
        ----------
        dropin_fuel_mass_consumption : pd.Series
            Time series of mass of drop-in fuel consumed (i.e., burned) by aviation [kg].
        hydrogen_nox_emissions : pd.Series
            Time series of NOx emissions from hydrogen fuel burn [kg NOx].
        nox_emissions : pd.Series
            Time series of NOx emissions from aviation [kg].
        characterisation_factor_health_particulate_matter_fuel : float
            Characterisation factor for fuel burn to particulate matter DALYs [DALY/kg fuel].
        characterisation_factor_health_particulate_matter_nox : float
            Characterisation factor for NOx emissions to particulate matter DALYs [DALY/kg NOx].

        Returns
        -------
        dalys_pm : pd.Series
            Total DALYs caused by aviation-induced particulate matter
        dalys_pm_nox : pd.Series
            DALYs caused by NOx emissions alone (excluding other emissions)
        """
        # === Total impacts from fuel burn (incl. NOx emissions) ===
        # Apply CF for fuel burn to drop-in fuels (all emissions incl. NOx)
        dalys_pm = dropin_fuel_mass_consumption * characterisation_factor_health_particulate_matter_fuel

        # Add DALYs due to hydrogen NOx emissions (assuming only NOx contribution for H2 fuel burn)
        # (1e9: conversion from Tg to kg)
        dalys_pm += hydrogen_nox_emissions * characterisation_factor_health_particulate_matter_nox

        # === DALYs from NOx emissions alone ===
        dalys_pm_nox = (nox_emissions * 1e9) * characterisation_factor_health_particulate_matter_nox

        # === Store outputs ===
        # Cut data before historic_start_year (out of scope)
        # Note that currently CFs are only valid for present-day, and may underestimate DALYs for future emissions.
        # Future improvements include the derivation of prospective CFs.
        dalys_pm = dalys_pm.loc[self.historic_start_year:self.end_year]
        dalys_pm_nox = dalys_pm_nox.loc[self.historic_start_year:self.end_year]
        self.df.loc[self.historic_start_year:self.end_year, "dalys_particulate_matter"] = dalys_pm
        self.df.loc[self.historic_start_year:self.end_year, "dalys_particulate_matter_nox"] = dalys_pm_nox

        return (
            dalys_pm,
            dalys_pm_nox
        )
