"""
production_capacity

=======================
Computes annual capacity additions required to follow an energy consumption trajectory.
"""

import jax
import jax.numpy as jnp
import numpy as np
import pandas as pd
import warnings
from aeromaps.models.base import AeroMAPSModel
from aeromaps.models.jax_helpers import jax_scalar_value, year_pos, years_index
from aeromaps.utils.functions import _get_value_for_year


def _jax_commissioning_scan(energy_required, plant_load_factor, plant_lifespan: int):
    """Replay the greedy plant-commissioning loop with :func:`jax.lax.scan`.

    Each year commissions just enough capacity to cover the production its
    already-running plants cannot supply; that capacity then produces for
    ``plant_lifespan`` years. The scan carries the rolling window of production
    and capacity already committed to the next ``plant_lifespan`` years, which
    is what the pandas ``.loc[year : year + lifespan - 1] +=`` slices build.
    """
    window = jnp.zeros((2, plant_lifespan))

    def step(carry, inputs):
        required, load_factor = inputs
        missing = required - carry[0, 0]
        commissioning = missing > 0.0
        commissioned = jnp.where(commissioning, missing, 0.0)
        unused = jnp.where(commissioning, 0.0, missing)
        required_capacity = jnp.where(commissioning, missing / load_factor, 0.0)

        updated = carry + jnp.stack(
            [
                jnp.full(plant_lifespan, commissioned),
                jnp.full(plant_lifespan, required_capacity),
            ]
        )
        # Slide the window one year forward.
        next_carry = jnp.concatenate([updated[:, 1:], jnp.zeros((2, 1))], axis=1)
        return next_carry, (required_capacity, commissioned, updated[1, 0], unused)

    _, outputs = jax.lax.scan(step, window, (energy_required, plant_load_factor))
    return outputs


class BottomUpCapacity(AeroMAPSModel):
    """
    Computes annual capacity additions required to follow an energy consumption trajectory.

    Parameters
    ------------
    name : str
        Name of the model instance ('f"{pathway_name}_production_capacity"' by default).
    configuration_data : dict
        Configuration data for the energy pathway from the config file.
    processes_data : dict
        Configuration data for all processes from the config file.

    Attributes
    ------------
    input_names : dict
        Dictionary of input variable names populated at model initialisation before MDA chain creation.
    output_names : dict
        Dictionary of output variable names populated at model initialisation before MDA chain creation.
    """

    MODEL_APPROACH = "bottom_up"

    def __init__(self, name, configuration_data, processes_data, *args, **kwargs):
        super().__init__(
            name=name,
            model_type="custom",
            *args,
            **kwargs,
        )
        self.pathway_name = configuration_data["name"]
        # Inputs
        self.input_names = {
            f"{self.pathway_name}_energy_consumption": pd.Series([0.0]),
        }

        for key, val in configuration_data.get("inputs").get("technical", {}).items():
            # TODO initialize with zeros instead of actual val? How to better get rid of unnecessary variables
            if (
                key == f"{self.pathway_name}_resource_names"
                or key == f"{self.pathway_name}_processes_names"
            ):
                pass  # avoid having strings as variable in gemseo, not needed as variables
            else:
                self.input_names[key] = val

        # Outputs
        self.output_names = {
            f"{self.pathway_name}_plant_building_scenario": pd.Series([0.0]),
            f"{self.pathway_name}_energy_production_commissioned": pd.Series([0.0]),
            f"{self.pathway_name}_plant_operating_capacity": pd.Series([0.0]),
            f"{self.pathway_name}_energy_unused": pd.Series([0.0]),
        }

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

        self.process_resource_keys = {}
        for process_key in self.process_keys:
            for key, val in processes_data[process_key].get("inputs").get("technical", {}).items():
                if key == f"{process_key}_resource_names":
                    resources = (
                        processes_data[process_key]
                        .get("inputs")
                        .get("technical", {})
                        .get(f"{process_key}_resource_names", [])
                    ).copy()
                    self.process_resource_keys[process_key] = resources
                elif key == f"{process_key}_load_factor":
                    self.input_names[key] = val
            self.output_names[f"{self.pathway_name}_{process_key}_plant_building_scenario"] = (
                pd.Series([0.0])
            )

    def compute(self, input_data) -> dict:
        """
        Compute the annual capacity additions required to follow the energy consumption trajectory.

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

        # Get the energy consumption trajectory and capacity factor
        energy_required = input_data.get(f"{self.pathway_name}_energy_consumption")

        technology_introduction = input_data.get(
            f"{self.pathway_name}_technology_introduction_year"
        )
        technology_introduction_volume = input_data.get(
            f"{self.pathway_name}_technology_introduction_volume"
        )

        # The hard part in this model is to be able to reconstruct the commissioning history of plants
        # however, we do not have access to the energy consumption before the scenarios,
        # which influences the availability of plants, and thus the need to build new ones.
        # The idea of the code is therefore to construct a virtual energy demand since the technology introduction year,
        # if needed, and to concatenate it with the real energy demand from the historic start year.
        # NB: that is transparent for alternative pathways that start after the historic start year.
        if energy_required.loc[self.historic_start_year] > 1e-9:
            if not technology_introduction or not technology_introduction_volume:
                raise ValueError(
                    f"Technology introduction year and volume for {self.pathway_name} must be specified if there is energy consumption before the historic start year."
                )
            else:
                first_plant_year = technology_introduction
                first_plant_volume = technology_introduction_volume
                virtual_cagr = (
                    energy_required.loc[self.historic_start_year] / first_plant_volume
                ) ** (1 / (self.historic_start_year - first_plant_year)) - 1
                # populate the energy_required Series with virtual years
                for virtual_year in range(first_plant_year, self.historic_start_year):
                    virtual_demand = first_plant_volume * (1 + virtual_cagr) ** (
                        virtual_year - first_plant_year
                    )
                    energy_required.loc[virtual_year] = virtual_demand
                energy_required.sort_index(inplace=True)

        years = energy_required.index

        plant_building_scenario = pd.Series(np.zeros(len(years)), years)
        plant_available_scenario = pd.Series(np.zeros(len(years)), years)
        energy_produced = pd.Series(np.zeros(len(years)), years)
        energy_production_commissioned = pd.Series(np.zeros(len(years)), years)
        energy_unused = pd.Series(np.zeros(len(years)), years)

        for year in years:
            # getting entry into service (eis) plant charcteristics
            plant_load_factor = _get_value_for_year(
                input_data.get(f"{self.pathway_name}_eis_plant_load_factor"), year, 1
            )
            plant_lifespan = _get_value_for_year(
                input_data.get(f"{self.pathway_name}_eis_plant_lifespan"), year, 25
            )

            missing_production = energy_required.fillna(0)[year] - energy_produced.fillna(0)[year]
            if missing_production <= 0.0:
                energy_unused[year] = missing_production
            else:
                # Calculate the required capacity to meet the energy demand
                for key in self.resource_keys:
                    if f"{key}_load_factor" in input_data:
                        resource_load_factor = _get_value_for_year(
                            input_data.get(f"{key}_load_factor"), year
                        )
                        if resource_load_factor is not None:
                            plant_load_factor = min(plant_load_factor, resource_load_factor)

                energy_production_commissioned[year] = missing_production

                required_capacity = (
                    missing_production / plant_load_factor
                )  # Absolute output in MJ per year
                plant_building_scenario[year] += required_capacity
                # Update the available capacity and production for plant lifespan
                plant_available_scenario.loc[year : year + plant_lifespan - 1] += required_capacity
                energy_produced.loc[year : year + plant_lifespan - 1] += missing_production

        # Warning for years where there is an excess of energy production
        if (energy_unused < 0).any():
            years_excess = energy_unused.index[energy_unused < 0].tolist()
            warnings.warn(
                f"\n⚠️ Excess {self.pathway_name} production in years: {years_excess}. Scaling down."
            )

        # computing additions for processes
        for process_key in self.process_keys:
            process_building_scenario = pd.Series(np.zeros(len(years)), years)
            for year in years:
                process_load_factor = _get_value_for_year(
                    input_data.get(f"{process_key}_load_factor", 1), year
                )
                for resource in self.process_resource_keys[process_key]:
                    if f"{resource}_load_factor" in input_data:
                        resource_load_factor = _get_value_for_year(
                            input_data.get(f"{resource}_load_factor"), year
                        )
                        if resource_load_factor is not None:
                            process_load_factor = min(process_load_factor, resource_load_factor)
                process_building_scenario[year] = (
                    energy_production_commissioned[year] / process_load_factor
                )
            process_building_scenario = process_building_scenario.loc[
                self.prospection_start_year : self.end_year
            ]
            output_data.update(
                {
                    f"{self.pathway_name}_{process_key}_plant_building_scenario": process_building_scenario
                }
            )

        # restrict the outputs to prospective years
        plant_building_scenario = plant_building_scenario.loc[
            self.prospection_start_year : self.end_year
        ]
        plant_available_scenario = plant_available_scenario.loc[
            self.prospection_start_year : self.end_year
        ]
        energy_unused = energy_unused.loc[self.prospection_start_year : self.end_year]
        energy_production_commissioned = energy_production_commissioned.loc[
            self.prospection_start_year : self.end_year
        ]

        output_data.update(
            {
                f"{self.pathway_name}_plant_building_scenario": plant_building_scenario,
                f"{self.pathway_name}_energy_production_commissioned": energy_production_commissioned,
                f"{self.pathway_name}_plant_operating_capacity": plant_available_scenario,
                f"{self.pathway_name}_energy_unused": -energy_unused,
            }
        )

        self._store_outputs(output_data)

        return output_data

    # Loop bounds and window lengths: static, not differentiable.
    jax_static_input_names = ()

    @property
    def jax_output_indexes(self):
        # Every output is restricted to the prospective years.
        prospective_index = pd.RangeIndex(self.prospection_start_year, self.end_year + 1)
        return {name: prospective_index for name in self.output_names}

    def _jax_year_values(self, value, n_virtual: int, default: float):
        """Per-year array of a technical input over the virtual + model years.

        Mirrors :func:`_get_value_for_year`: a scalar applies to every year, and
        a Series falls back to ``default`` on the years it does not cover (which
        the JAX wrapper marks with NaN when it pads a partial series).
        """
        n_years = len(years_index(self))
        if value is None:
            return jnp.full(n_virtual + n_years, default)
        scalar = jax_scalar_value(value)
        if scalar is not None:
            return jnp.full(n_virtual + n_years, scalar)
        value = jnp.asarray(value)
        return jnp.concatenate(
            [jnp.full(n_virtual, default), jnp.where(jnp.isnan(value), default, value)]
        )

    def jax_compute(self, input_data) -> dict:
        """JAX version of :meth:`compute` (same contract, pure jax.numpy).

        Unlike the pandas version this does not raise when a pathway has energy
        consumption before ``historic_start_year`` without technology
        introduction data: the check is on a coupling value, unavailable at
        trace time. Such a pathway silently gets no virtual history, exactly as
        if its historic consumption were zero.
        """
        output_data = {}
        n_years = len(years_index(self))
        energy_required = jnp.nan_to_num(
            jnp.asarray(input_data[f"{self.pathway_name}_energy_consumption"])
        )

        # Reconstruct the pre-scenario commissioning history, when the pathway
        # declares when and at which volume the technology was introduced.
        technology_introduction = input_data.get(
            f"{self.pathway_name}_technology_introduction_year"
        )
        technology_introduction_volume = input_data.get(
            f"{self.pathway_name}_technology_introduction_volume"
        )
        n_virtual = 0
        if technology_introduction and technology_introduction_volume is not None:
            first_plant_year = int(technology_introduction)
            # A technology introduced at or after historic_start_year needs no
            # reconstructed history.
            n_virtual = max(self.historic_start_year - first_plant_year, 0)
        if n_virtual > 0:
            historic_demand = energy_required[0]
            # Guarded so a pathway without historic consumption gets a flat zero
            # virtual history (no plant is commissioned), as in the pandas branch.
            has_history = historic_demand > 1e-9
            safe_demand = jnp.where(has_history, historic_demand, 1.0)
            virtual_cagr = (safe_demand / technology_introduction_volume) ** (1.0 / n_virtual) - 1.0
            virtual_years = jnp.arange(n_virtual)
            virtual_demand = jnp.where(
                has_history,
                technology_introduction_volume * (1.0 + virtual_cagr) ** virtual_years,
                0.0,
            )
            energy_required = jnp.concatenate([virtual_demand, energy_required])

        plant_load_factor = self._jax_year_values(
            input_data.get(f"{self.pathway_name}_eis_plant_load_factor"), n_virtual, 1.0
        )
        for key in self.resource_keys:
            if f"{key}_load_factor" in input_data:
                plant_load_factor = jnp.minimum(
                    plant_load_factor,
                    self._jax_year_values(input_data[f"{key}_load_factor"], n_virtual, 1.0),
                )

        plant_lifespan = int(
            _get_value_for_year(
                input_data.get(f"{self.pathway_name}_eis_plant_lifespan"),
                self.historic_start_year,
                25,
            )
        )

        (
            plant_building_scenario,
            energy_production_commissioned,
            plant_available_scenario,
            energy_unused,
        ) = _jax_commissioning_scan(energy_required, plant_load_factor, plant_lifespan)

        # Restrict the outputs to the prospective years.
        start = n_virtual + year_pos(self, self.prospection_start_year)
        stop = n_virtual + n_years

        for process_key in self.process_keys:
            process_load_factor = self._jax_year_values(
                input_data.get(f"{process_key}_load_factor"), n_virtual, 1.0
            )
            for resource in self.process_resource_keys[process_key]:
                if f"{resource}_load_factor" in input_data:
                    process_load_factor = jnp.minimum(
                        process_load_factor,
                        self._jax_year_values(
                            input_data[f"{resource}_load_factor"], n_virtual, 1.0
                        ),
                    )
            output_data[f"{self.pathway_name}_{process_key}_plant_building_scenario"] = (
                energy_production_commissioned / process_load_factor
            )[start:stop]

        output_data.update(
            {
                f"{self.pathway_name}_plant_building_scenario": plant_building_scenario[start:stop],
                f"{self.pathway_name}_energy_production_commissioned": energy_production_commissioned[
                    start:stop
                ],
                f"{self.pathway_name}_plant_operating_capacity": plant_available_scenario[
                    start:stop
                ],
                f"{self.pathway_name}_energy_unused": -energy_unused[start:stop],
            }
        )
        return output_data
