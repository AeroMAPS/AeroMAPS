"""Single-scenario plots for the generic offsetting schemes.

All plots discover offsetting schemes dynamically via ``offsets_manager`` (populated
when the generic offsets module is activated through the ``models.offsets`` key of
the configuration file). They show how the aggregate carbon offset and its expense
are built up from the per-scheme quantities and prices.
"""

from aeromaps.models.impacts.emissions.co2_emissions import (
    offset_category_column,
    offset_scheme_column,
)
from aeromaps.plots import colors
from aeromaps.plots.labels import readable_label
from aeromaps.plots.single_scenario_plot import SingleScenarioPlot, plot_3_x, plot_3_y


class _OffsetsPlot(SingleScenarioPlot):
    """Base class for generic offsets plots, exposing the offsets manager."""

    required_outputs = []

    def __init__(self, process, figsize=None, **kwargs):
        self.offsets_manager = getattr(process, "offsets_manager", None)
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


class CarbonOffsetBySchemePlot(_OffsetsPlot):
    """
    Stacked area of the ``carbon_offset`` decomposed per offsetting scheme
    (MtCO2, summing to the aggregate offset).
    """

    def create_plot(self):
        if self.offsets_manager is None:
            return
        schemes = self.offsets_manager.get_all()
        scheme_color = colors.categorical_colors([s.name for s in schemes])
        self._stack_columns(
            [
                (offset_scheme_column(s.name), readable_label(s.name), scheme_color[s.name])
                for s in schemes
            ]
        )
        self._finalize("Carbon offset by scheme", "Carbon offset [MtCO2]")


class CarbonOffsetByCategoryPlot(_OffsetsPlot):
    """
    Stacked area of the ``carbon_offset`` decomposed per category of offsetting
    schemes (MtCO2).
    """

    def create_plot(self):
        if self.offsets_manager is None:
            return
        categories = self.offsets_manager.get_all_types("category")
        category_color = colors.categorical_colors(categories)
        self._stack_columns(
            [(offset_category_column(c), readable_label(c), category_color[c]) for c in categories]
        )
        self._finalize("Carbon offset by category", "Carbon offset [MtCO2]")


class CarbonOffsetExpenseBySchemePlot(_OffsetsPlot):
    """
    Stacked area of the ``carbon_offset_expense`` decomposed per offsetting scheme
    (M€, each scheme at its own price).
    """

    def create_plot(self):
        if self.offsets_manager is None:
            return
        schemes = self.offsets_manager.get_all()
        scheme_color = colors.categorical_colors([s.name for s in schemes])
        self._stack_columns(
            [
                (f"{s.name}_carbon_offset_expense", readable_label(s.name), scheme_color[s.name])
                for s in schemes
            ]
        )
        self._finalize("Carbon offset expense by scheme", "Carbon offset expense [M€]")
