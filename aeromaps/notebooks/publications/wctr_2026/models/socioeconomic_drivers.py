from typing import Tuple
import pandas as pd
from aeromaps.models.base import (
    AeroMAPSModel,
    aeromaps_interpolation_function,
)


class SocioeconomicDrivers(AeroMAPSModel):
    """Simple model for interpolating socioeconomic drivers data.

    Parameters
    ----------
    name
        Name of the model instance ('socioeconomic_drivers' by default).
    """

    def __init__(self, name="socioeconomic_drivers", *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)

    def compute(
        self,
        population_reference_years: list,
        population_reference_years_values: list,
        gdp_per_capita_reference_years: list,
        gdp_per_capita_reference_years_values: list,
        short_range_covid_end_year: int,
        medium_range_covid_end_year: int,
        long_range_covid_end_year: int,
    ) -> Tuple[pd.Series, pd.Series, float]:
        """Socioeconomic drivers calculation.

        Parameters
        ----------
        population_reference_years
            Reference years for the world population [yr].
        population_reference_years_values
            World population for the reference years [inhabitants].
        gdp_per_capita_reference_years
            Reference years for the GDP per capita [yr].
        gdp_per_capita_reference_years_values
            GDP per capita for the reference years [USD/capita].
        short_range_covid_end_year
            Year marking the end of the short-range COVID-19 impact [yr].
        medium_range_covid_end_year
            Year marking the end of the medium-range COVID-19 impact [yr].
        long_range_covid_end_year
            Year marking the end of the long-range COVID-19 impact [yr].

        Returns
        -------
        population
            World population [inhabitants].
        gdp_per_capita
            GDP per capita [USD/capita].
        gdp_per_capita_covid_end
            GDP per capita at the end of the COVID-19 period [USD/capita].
        """

        # Interpolation of world population
        population = aeromaps_interpolation_function(
            self,
            population_reference_years,
            population_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "population"] = population

        # Interpolation of GDP per capita
        gdp_per_capita = aeromaps_interpolation_function(
            self,
            gdp_per_capita_reference_years,
            gdp_per_capita_reference_years_values,
            model_name=self.name,
        )
        self.df.loc[:, "gdp_per_capita"] = gdp_per_capita

        covid_end_year_passenger = max(
            short_range_covid_end_year, medium_range_covid_end_year, long_range_covid_end_year
        )
        # GDP per capita at COVID end year
        gdp_per_capita_covid_end = self.df.loc[covid_end_year_passenger, "gdp_per_capita"]
        self.float_outputs["gdp_per_capita_covid_end"] = gdp_per_capita_covid_end

        return (population, gdp_per_capita, gdp_per_capita_covid_end)
