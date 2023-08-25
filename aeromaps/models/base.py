import pandas as pd
import numpy as np
from scipy.interpolate import interp1d

from aeromaps.models.constants import ModelType


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


class LogisticFunctionYearSeries(AeromapsModel):
    def __init__(self, maximum_value=None, growth_rate=None, midpoint_year=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maximum_value = maximum_value
        self.growth_rate = growth_rate
        self.midpoint_year = midpoint_year

    def _compute(self, maximum_value=None, growth_rate=None, midpoint_year=None):
        if not maximum_value:
            maximum_value = self.maximum_value
        if not growth_rate:
            growth_rate = self.growth_rate
        if not midpoint_year:
            midpoint_year = self.midpoint_year
        x = np.linspace(self.prospection_start_year, self.end_year, len(self.df.index))
        y = maximum_value / (1 + np.exp(-growth_rate * (x - midpoint_year)))
        self.df[self.name] = y
        return y


class ExponentialGrowthYearSeries(AeromapsModel):
    def __init__(
        self, initial_value=0.0, growth_rates={2030: 3.1, 2040: 3.0, 2050: 2.9}, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.initial_value = initial_value
        self.growth_rates = growth_rates

    def _compute(self, initial_value=None, growth_rates=None):
        if not initial_value:
            initial_value = self.initial_value
        if not growth_rates:
            growth_rates = self.growth_rates
        x = self.df.index
        y = np.ones(len(x))
        self.df[self.name] = y
        self.df.loc[self.start_year, self.name] = initial_value
        for year in x:
            if year != self.start_year:
                self.df.loc[year, self.name] = self.df.loc[year - 1, self.name] * (
                    1 + self._get_growth_rate(year, growth_rates=growth_rates) / 100
                )

        return y

    def _get_growth_rate(self, year, growth_rates=None):
        if not growth_rates:
            growth_rates = self.growth_rates
        for key, growth_rate in growth_rates.items():
            if year <= key:
                actual_growth_rate = growth_rate

        return actual_growth_rate


class InterpAeromapsModel(AeromapsModel):
    def __init__(
        self,
        year_values={2020: 100.0, 2030: 80.0, 2040: 50.0, 2050: 20.0},
        model_type=ModelType.LINEAR,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.year_values = year_values
        self.model_type = model_type

    def _compute(self):
        reference_years, reference_values = self.year_values.items()
        interpolation = interp1d(reference_years, reference_values, kind=self.model_type)

        values = interpolation(self.years)

        return values
