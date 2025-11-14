import warnings

import pandas as pd
from scipy.interpolate import interp1d


from aeromaps.models.base import AeroMAPSModel


class YAMLInterpolator(AeroMAPSModel):
    """
    Generic interpolation model called each time an AeroMapsCustomDataType is used in the YAML configuration file of generic energy models.
    """

    def __init__(
        self,
        name,
        custom_data_type,
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
        # Get the name of the resource
        self.value_name = name
        self.custom_data_type = custom_data_type

        self.input_names = {
            f"{self.value_name}_years": custom_data_type.years,
            f"{self.value_name}_values": custom_data_type.values,
        }

        self.output_names = {self.value_name: pd.Series([0.0])}

    def compute(self, input_data) -> dict:
        try:
            interpolated_value = self._yaml_interpolation_function(
                reference_years=input_data[f"{self.value_name}_years"],
                reference_years_values=input_data[f"{self.value_name}_values"],
                prospection_start_year=self.prospection_start_year,
                end_year=self.end_year,
                method=self.custom_data_type.method,
                positive_constraint=self.custom_data_type.positive_constraint,
                model_name=self.value_name,
            )
        except Exception as e:
            raise RuntimeError(
                f"[YAMLInterpolator] Error while interpolating '{self.value_name}' "
                f"with method '{self.custom_data_type.method}' "
                f"(years and values lengths may mismatch): {e}"
            ) from e

        output_data = {self.value_name: interpolated_value}
        self._store_outputs(output_data)

        return output_data

    @staticmethod
    def _yaml_interpolation_function(
        reference_years,
        reference_years_values,
        prospection_start_year,
        end_year,
        method="linear",
        positive_constraint=False,
        model_name="Not provided",
    ):
        interpolation_function_values = []

        # If no reference years are provided, use the first reference value for all years
        if len(reference_years) == 0:
            interpolation_function_values = [reference_years_values[0]] * (
                end_year - prospection_start_year + 1
            )
        else:
            # Create the interpolation function
            interpolation_function = interp1d(
                reference_years,
                reference_years_values,
                kind=method,
            )

            # If first reference year is lower than prospection start year, we start interpolating before
            # TODO @Planes ok for you?
            if reference_years[0] != prospection_start_year:
                warnings.warn(
                    f"\n[Interpolation Model: {model_name} Warning]\n"
                    f"The first reference year ({reference_years[0]}) differs from the prospection start year ({prospection_start_year}).\n"
                    f"Interpolation will begin at the first reference year."
                )
                prospection_start_year = reference_years[0]

                # If the last reference year matches the end year, interpolate for all years
            if reference_years[-1] == end_year:
                for k in range(prospection_start_year, reference_years[-1] + 1):
                    value = interpolation_function(k).item()
                    if positive_constraint and value <= 0.0:
                        interpolation_function_values.append(0.0)
                    else:
                        interpolation_function_values.append(value)

            # If the last reference year is greater than the end year, interpolate up to the end year
            elif reference_years[-1] > end_year:
                warnings.warn(
                    f"\n[Interpolation Model: {model_name} Warning]\n"
                    f"The last reference year ({reference_years[-1]}) is higher than the end year ({end_year}).\n"
                    f"The interpolation function will not be used in its entirety."
                )
                for k in range(prospection_start_year, end_year + 1):
                    value = interpolation_function(k).item()
                    if positive_constraint and value <= 0.0:
                        interpolation_function_values.append(0.0)
                    else:
                        interpolation_function_values.append(value)
            # If the last reference year is less than the end year, use the last value as a constant for the remaining years
            else:
                warnings.warn(
                    f"\n[Interpolation Model: {model_name} Warning]\n"
                    f"The last reference year ({reference_years[-1]}) is lower than the end year ({end_year}).\n"
                    f"The value associated with the last reference year will be used as a constant for the upper years."
                )
                for k in range(prospection_start_year, reference_years[-1] + 1):
                    value = interpolation_function(k).item()
                    if positive_constraint and value <= 0.0:
                        interpolation_function_values.append(0.0)
                    else:
                        interpolation_function_values.append(value)
                last_value = interpolation_function_values[-1]
                for k in range(reference_years[-1] + 1, end_year + 1):
                    interpolation_function_values.append(last_value)

        return pd.Series(
            interpolation_function_values, index=range(prospection_start_year, end_year + 1)
        )
