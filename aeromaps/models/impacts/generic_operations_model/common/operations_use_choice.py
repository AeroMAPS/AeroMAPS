"""
operations_use_choice

=====================
Central module composing the per-concept operational gains into the aggregate
operational effects consumed downstream (``operations_gain``,
``operations_contrails_gain``, ``operations_contrails_overconsumption``) and
decomposing each aggregate per operational concept and per category.

Composition is multiplicative: independent operational measures each act on the
consumption/impact remaining after the others, so a fuel-efficiency gain
``operations_gain = (1 - prod_i(1 - g_i/100)) * 100`` rather than a naive sum.
The per-concept contributions are obtained by a sequential (telescoping)
attribution that sums exactly to the aggregate.
"""

import pandas as pd

from aeromaps.models.base import AeroMAPSModel


class OperationsUseChoice(AeroMAPSModel):
    """
    Compose the per-concept operational gains into the aggregate operational
    effects and decompose them per concept and per category.

    Parameters
    ----------
    name : str
        Name of the model instance ('operations_use_choice' by default).
    configuration_data : dict
        Configuration data for the operations models.
    operations_manager : OperationalConceptManager
        Manager containing all operational concept metadata.

    Attributes
    ----------
    input_names : dict
        Input variable names populated at model initialisation before MDA chain creation.
    output_names : dict
        Output variable names populated at model initialisation before MDA chain creation.
    """

    def __init__(self, name, configuration_data, operations_manager, *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        # Metadata only (not a coupling variable); coupling variables go in input_names.
        self.operations_manager = operations_manager

        self.input_names = {}
        for concept in self.operations_manager.get_all():
            if concept.has_fuel_efficiency:
                self.input_names[f"{concept.name}_fuel_efficiency_gain"] = pd.Series([0.0])
            if concept.has_contrails:
                self.input_names[f"{concept.name}_contrails_gain"] = pd.Series([0.0])
                self.input_names[f"{concept.name}_contrails_overconsumption"] = pd.Series([0.0])

        # Aggregate operational effects consumed downstream (replace the simple
        # operations and contrails models).
        self.output_names = {
            "operations_gain": pd.Series([0.0]),
            "operations_contrails_gain": pd.Series([0.0]),
            "operations_contrails_overconsumption": pd.Series([0.0]),
        }
        # Per-concept contributions (percentage points of the aggregate).
        for concept in self.operations_manager.get_all():
            if concept.has_fuel_efficiency:
                self.output_names[f"{concept.name}_operations_gain_contribution"] = pd.Series([0.0])
            if concept.has_contrails:
                self.output_names[f"{concept.name}_operations_contrails_gain_contribution"] = (
                    pd.Series([0.0])
                )
                self.output_names[
                    f"{concept.name}_operations_contrails_overconsumption_contribution"
                ] = pd.Series([0.0])
        # Per-category aggregates.
        for category in self.operations_manager.get_all_types("category"):
            self.output_names[f"{category}_operations_gain_contribution"] = pd.Series([0.0])
            self.output_names[f"{category}_operations_contrails_gain_contribution"] = pd.Series(
                [0.0]
            )
            self.output_names[f"{category}_operations_contrails_overconsumption_contribution"] = (
                pd.Series([0.0])
            )

    def compute(self, input_data) -> dict:
        """
        Compose the per-concept gains and decompose the aggregates.

        Parameters
        ----------
        input_data
            Dictionary of input data, completed at instantiation with information
            from the yaml file and the outputs of other models.

        Returns
        -------
        output_data
            Dictionary of all output data (aggregates and per-concept/per-category
            contributions).
        """
        output_data = {}
        full_index = pd.RangeIndex(start=self.historic_start_year, stop=self.end_year + 1)
        # Operational gains only apply over the prospective window.
        prospective = full_index >= self.prospection_start_year

        def concept_series(name):
            return input_data[name].reindex(full_index).fillna(0).where(prospective, 0.0)

        # --- Fuel-efficiency gain: multiplicative reduction, sequential attribution ---
        remaining = pd.Series(1.0, index=full_index)
        for concept in self.operations_manager.get_all():
            if not concept.has_fuel_efficiency:
                continue
            gain = concept_series(f"{concept.name}_fuel_efficiency_gain") / 100
            contribution = remaining * gain
            remaining = remaining * (1 - gain)
            output_data[f"{concept.name}_operations_gain_contribution"] = contribution * 100
        output_data["operations_gain"] = (1 - remaining) * 100

        # --- Contrail gain (ERF reduction): multiplicative reduction, sequential attribution ---
        remaining = pd.Series(1.0, index=full_index)
        for concept in self.operations_manager.get_all():
            if not concept.has_contrails:
                continue
            gain = concept_series(f"{concept.name}_contrails_gain") / 100
            contribution = remaining * gain
            remaining = remaining * (1 - gain)
            output_data[f"{concept.name}_operations_contrails_gain_contribution"] = (
                contribution * 100
            )
        output_data["operations_contrails_gain"] = (1 - remaining) * 100

        # --- Contrail overconsumption (fuel penalty): multiplicative increase ---
        running = pd.Series(1.0, index=full_index)
        for concept in self.operations_manager.get_all():
            if not concept.has_contrails:
                continue
            overconsumption = concept_series(f"{concept.name}_contrails_overconsumption") / 100
            contribution = running * overconsumption
            running = running * (1 + overconsumption)
            output_data[f"{concept.name}_operations_contrails_overconsumption_contribution"] = (
                contribution * 100
            )
        output_data["operations_contrails_overconsumption"] = (running - 1) * 100

        # --- Per-category aggregates (sum of the concept contributions in the category) ---
        for category in self.operations_manager.get_all_types("category"):
            concepts = self.operations_manager.get(category=category)
            for channel in (
                "operations_gain_contribution",
                "operations_contrails_gain_contribution",
                "operations_contrails_overconsumption_contribution",
            ):
                columns = [
                    output_data[f"{concept.name}_{channel}"]
                    for concept in concepts
                    if f"{concept.name}_{channel}" in output_data
                ]
                total = sum(columns) if columns else pd.Series(0.0, index=full_index)
                output_data[f"{category}_{channel}"] = total

        self._store_outputs(output_data)
        return output_data
