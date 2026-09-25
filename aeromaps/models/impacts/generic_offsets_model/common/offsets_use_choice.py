"""
offsets_use_choice

==================
Central module computing the offset quantity and expense of each offsetting scheme
declared in the generic offsets module, and summing them into the aggregates consumed
downstream (``carbon_offset``, ``carbon_offset_price``, ``noc_carbon_offset_per_ask``).

The aggregate carbon offset is the plain sum of the scheme quantities, so the
per-scheme quantities are themselves the sub-levers of the offsetting lever of the
CO2 cascade (``co2_emissions_lever_offset_scheme_<name>``): the decomposition is exact
by construction and carries no residual. The aggregate price is the quantity-weighted
mean of the scheme prices, so the existing single-price cost chain is reproduced
exactly: ``carbon_offset * carbon_offset_price`` is the sum of the scheme expenses.
"""

import logging

import pandas as pd

from aeromaps.models.base import AeroMAPSModel
from aeromaps.models.impacts.emissions.co2_emissions import (
    offset_category_column,
    offset_scheme_column,
)


class OffsetsUseChoice(AeroMAPSModel):
    """
    Compute the offset quantity and expense of each offsetting scheme and sum them
    into the aggregate carbon offset, its mean price and its cost per ASK.

    Three quantity rules are available, one per scheme, chosen by the scheme's
    ``quantity_mode``:

    * ``level``: the emissions above a baseline set at a share of the emissions of a
      reference year, times the share of emissions in the scheme's scope (the CORSIA
      rule of the simple ``LevelCarbonOffset`` model);
    * ``share_of_residual``: a share of the emissions left once the level-based
      schemes are applied (the rule of the simple ``ResidualCarbonOffset`` model);
    * ``quantity``: a prescribed annual quantity (the rule of ``ManualCarbonOffset``).

    Parameters
    ----------
    name : str
        Name of the model instance ('offsets_use_choice' by default).
    configuration_data : dict
        Configuration data for the offsets models.
    offsets_manager : OffsetSchemeManager
        Manager containing all offsetting scheme metadata.

    Attributes
    ----------
    input_names : dict
        Input variable names populated at model initialisation before MDA chain creation.
    output_names : dict
        Output variable names populated at model initialisation before MDA chain creation.
    """

    def __init__(self, name, configuration_data, offsets_manager, *args, **kwargs):
        super().__init__(name=name, model_type="custom", *args, **kwargs)
        # Metadata only (not a coupling variable); coupling variables go in input_names.
        self.offsets_manager = offsets_manager
        # Consistency warnings already issued, so that MDA iterations do not repeat them.
        self._warned = set()

        self.input_names = {
            "co2_emissions": pd.Series([0.0]),
            "ask": pd.Series([0.0]),
        }
        for scheme in self.offsets_manager.get_all():
            if scheme.quantity_mode == "share_of_residual":
                self.input_names[f"{scheme.name}_quantity_share"] = pd.Series([0.0])
            elif scheme.quantity_mode == "level":
                self.input_names[f"{scheme.name}_quantity_baseline_level_vs_reference_year"] = (
                    pd.Series([0.0])
                )
                self.input_names[f"{scheme.name}_quantity_coverage"] = pd.Series([0.0])
                self.input_names[f"{scheme.name}_quantity_reference_year"] = 0.0
            else:
                self.input_names[f"{scheme.name}_quantity_amount"] = pd.Series([0.0])
            self.input_names[f"{scheme.name}_economics_price"] = pd.Series([0.0])

        # Aggregates consumed downstream (replace the simple offset models and the
        # single-price carbon offset cost model).
        self.output_names = {
            "carbon_offset": pd.Series([0.0]),
            "carbon_offset_price": pd.Series([0.0]),
            "carbon_offset_expense": pd.Series([0.0]),
            "noc_carbon_offset_per_ask": pd.Series([0.0]),
        }
        # Per-scheme quantity (the sub-lever), price and expense.
        for scheme in self.offsets_manager.get_all():
            self.output_names[offset_scheme_column(scheme.name)] = pd.Series([0.0])
            self.output_names[f"{scheme.name}_carbon_offset_price"] = pd.Series([0.0])
            self.output_names[f"{scheme.name}_carbon_offset_expense"] = pd.Series([0.0])
        # Per-category aggregates.
        for category in self.offsets_manager.get_all_types("category"):
            self.output_names[offset_category_column(category)] = pd.Series([0.0])
            self.output_names[f"{category}_carbon_offset_expense"] = pd.Series([0.0])

    def compute(self, input_data) -> dict:
        """
        Compute the per-scheme quantities and expenses and their aggregates.

        Parameters
        ----------
        input_data
            Dictionary of input data, completed at instantiation with information
            from the yaml file and the outputs of other models.

        Returns
        -------
        output_data
            Dictionary of all output data (aggregates and per-scheme/per-category
            quantities and expenses).
        """
        output_data = {}
        full_index = pd.RangeIndex(start=self.historic_start_year, stop=self.end_year + 1)
        # Offsetting only applies over the prospective window.
        prospective = full_index >= self.prospection_start_year

        co2_emissions = input_data["co2_emissions"].reindex(full_index)
        ask = input_data["ask"].reindex(full_index)

        def scheme_series(name, fill):
            """A scheme input on the full index, held at its nearest value outside its range
            (``fill="nearest"``) or zero there (``fill=0``), and zero before the prospection."""
            series = input_data[name].reindex(full_index)
            series = series.ffill().bfill() if fill == "nearest" else series.fillna(0)
            return series.where(prospective, 0.0)

        schemes = self.offsets_manager.get_all()
        quantities = {}

        # Level-based schemes first: the residual the share-based ones apply to is net of them.
        for scheme in (s for s in schemes if s.quantity_mode == "level"):
            reference_year = int(input_data[f"{scheme.name}_quantity_reference_year"])
            level = scheme_series(f"{scheme.name}_quantity_baseline_level_vs_reference_year", 0)
            coverage = scheme_series(f"{scheme.name}_quantity_coverage", 0)
            baseline = co2_emissions.loc[reference_year] * level / 100
            quantities[scheme.name] = (
                (co2_emissions - baseline).clip(lower=0.0) * coverage / 100
            ).where(prospective, 0.0)

        residual = co2_emissions.where(prospective, 0.0) - sum(quantities.values())
        total_share = pd.Series(0.0, index=full_index)
        for scheme in (s for s in schemes if s.quantity_mode == "share_of_residual"):
            share = scheme_series(f"{scheme.name}_quantity_share", 0)
            quantities[scheme.name] = residual * share / 100
            total_share = total_share + share
        if (total_share > 100 + 1e-9).any():
            self._warn_once(
                "share",
                "The shares of residual emissions of the offsetting schemes exceed 100 %% "
                "in %s: more than the residual emissions are offset.",
                list(total_share.index[total_share > 100 + 1e-9]),
            )

        for scheme in (s for s in schemes if s.quantity_mode == "quantity"):
            quantities[scheme.name] = scheme_series(f"{scheme.name}_quantity_amount", 0)

        total = pd.Series(0.0, index=full_index)
        expense = pd.Series(0.0, index=full_index)
        per_category_q = {
            c: pd.Series(0.0, index=full_index)
            for c in self.offsets_manager.get_all_types("category")
        }
        per_category_e = {c: pd.Series(0.0, index=full_index) for c in per_category_q}
        for scheme in schemes:
            quantity = quantities[scheme.name].fillna(0.0)
            price = scheme_series(f"{scheme.name}_economics_price", "nearest")
            scheme_expense = quantity * price  # [MtCO2] x [EUR/tCO2] = [MEUR]
            output_data[offset_scheme_column(scheme.name)] = quantity
            output_data[f"{scheme.name}_carbon_offset_price"] = price
            output_data[f"{scheme.name}_carbon_offset_expense"] = scheme_expense
            total = total + quantity
            expense = expense + scheme_expense
            if scheme.category in per_category_q:
                per_category_q[scheme.category] += quantity
                per_category_e[scheme.category] += scheme_expense

        for category in per_category_q:
            output_data[offset_category_column(category)] = per_category_q[category]
            output_data[f"{category}_carbon_offset_expense"] = per_category_e[category]

        excess = total - co2_emissions.where(prospective, 0.0).fillna(0.0)
        if (excess > 1e-6).any():
            self._warn_once(
                "excess",
                "The carbon offset exceeds the CO2 emissions in %s (by up to %.1f MtCO2): "
                "check the schemes with a prescribed quantity, which are not deducted from "
                "the residual that the share-based schemes apply to.",
                list(excess.index[excess > 1e-6]),
                excess.max(),
            )

        output_data["carbon_offset"] = total
        output_data["carbon_offset_expense"] = expense
        output_data["carbon_offset_price"] = (expense / total).where(total != 0, 0.0)
        output_data["noc_carbon_offset_per_ask"] = (expense * 10**6 / ask).fillna(0.0)

        self._store_outputs(output_data)
        return output_data

    def _warn_once(self, key, message, *args):
        if key not in self._warned:
            self._warned.add(key)
            logging.warning(message, *args)
