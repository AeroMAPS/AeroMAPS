"""Single-scenario plots for the generic operational concepts.

All plots discover operational concepts dynamically via ``operations_manager``
(populated when the generic operations module is activated through the
``models.operations`` key of the configuration file). They show how the aggregate
operational effects are built up from the per-concept contributions.
"""

from aeromaps.plots import colors
from aeromaps.plots.single_scenario_plot import SingleScenarioPlot, plot_3_x, plot_3_y


def _readable_label(raw_name):
    """Turn a snake_case name into a readable label."""
    return raw_name.replace("_", " ").title()


class _OperationsPlot(SingleScenarioPlot):
    """Base class for generic operations plots, exposing the operations manager."""

    required_outputs = []

    def __init__(self, process, figsize=None, **kwargs):
        self.operations_manager = getattr(process, "operations_manager", None)
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize, **kwargs)

    def _get_default_figsize(self):
        return (plot_3_x, plot_3_y)

    def _update_plot_elements(self):
        self.ax.clear()
        self.create_plot()

    def _stack_columns(self, columns_labels_colors):
        """Stacked area of the given (column, label, color) triplets over the prospective years."""
        stack_data, stack_labels, stack_colors = [], [], []
        for column, label, color in columns_labels_colors:
            if column in self.df.columns:
                values = self.df.loc[self.prospective_years, column].fillna(0)
                if (values != 0).any():
                    stack_data.append(values)
                    stack_labels.append(label)
                    stack_colors.append(color)
        if stack_data:
            self.ax.stackplot(
                self.prospective_years,
                *stack_data,
                labels=stack_labels,
                colors=stack_colors,
                alpha=0.85,
            )
            self.ax.legend(loc="upper left", fontsize=8)

    def _finalize(self, title, ylabel):
        self.ax.grid(True, alpha=0.3)
        self.ax.set_title(title)
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel(ylabel)
        self.ax.set_xlim(self.prospective_years[0], self.prospective_years[-1])


class OperationsGainByConceptPlot(_OperationsPlot):
    """
    Stacked area of the fuel-efficiency ``operations_gain`` decomposed per
    operational concept (percentage points, summing to the aggregate gain).
    """

    def create_plot(self):
        if self.operations_manager is None:
            return
        concepts = [c for c in self.operations_manager.get_all() if c.has_fuel_efficiency]
        concept_color = colors.categorical_colors([c.name for c in concepts])
        self._stack_columns(
            [
                (
                    f"{c.name}_operations_gain_contribution",
                    _readable_label(c.name),
                    concept_color[c.name],
                )
                for c in concepts
            ]
        )
        self._finalize("Fuel-efficiency operations gain by concept", "Energy-per-ASK reduction [%]")


class OperationsGainByCategoryPlot(_OperationsPlot):
    """
    Stacked area of the fuel-efficiency ``operations_gain`` decomposed per
    operational category.
    """

    def create_plot(self):
        if self.operations_manager is None:
            return
        # Only categories that carry a fuel-efficiency concept.
        categories = [
            cat
            for cat in self.operations_manager.get_all_types("category")
            if any(c.has_fuel_efficiency for c in self.operations_manager.get(category=cat))
        ]
        category_color = colors.categorical_colors(categories)
        self._stack_columns(
            [
                (
                    f"{cat}_operations_gain_contribution",
                    _readable_label(cat),
                    category_color[cat],
                )
                for cat in categories
            ]
        )
        self._finalize(
            "Fuel-efficiency operations gain by category", "Energy-per-ASK reduction [%]"
        )


class OperationsContrailsGainByConceptPlot(_OperationsPlot):
    """
    Stacked area of the contrail ``operations_contrails_gain`` (non-CO2 climate
    impact reduction) decomposed per operational concept.
    """

    def create_plot(self):
        if self.operations_manager is None:
            return
        concepts = [c for c in self.operations_manager.get_all() if c.has_contrails]
        concept_color = colors.categorical_colors([c.name for c in concepts])
        self._stack_columns(
            [
                (
                    f"{c.name}_operations_contrails_gain_contribution",
                    _readable_label(c.name),
                    concept_color[c.name],
                )
                for c in concepts
            ]
        )
        self._finalize(
            "Contrail-avoidance gain by concept", "Contrail climate-impact reduction [%]"
        )
