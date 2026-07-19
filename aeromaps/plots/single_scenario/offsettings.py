"""Single-scenario plots for carbon offsetting mechanisms.

All plots discover offsetting mechanisms dynamically via ``offsettings_manager``
(populated when the generic offsettings module is activated through the
``models.offsettings`` key of the configuration file).
"""

from aeromaps.plots.single_scenario_plot import SingleScenarioPlot, plot_3_x, plot_3_y

# Colors for the offsetting categories
OFFSETTING_CATEGORY_COLORS = {
    "carbon_dioxide_removal": "#1f77b4",  # blue
    "emissions_avoidance": "#2ca02c",  # green
}

# Fallback colors when the category or mechanism is not in the map above
OFFSETTING_FALLBACK_COLORS = [
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf",
]


def _get_category_color(category, fallback_index=0):
    """Return a colour for an offsetting category, falling back to a rotating palette."""
    if category in OFFSETTING_CATEGORY_COLORS:
        return OFFSETTING_CATEGORY_COLORS[category]
    return OFFSETTING_FALLBACK_COLORS[fallback_index % len(OFFSETTING_FALLBACK_COLORS)]


def _readable_label(raw_name):
    """Turn a snake_case name into a readable label."""
    return raw_name.replace("_", " ").title()


class _OffsettingsPlot(SingleScenarioPlot):
    """Base class for offsettings plots, exposing the offsettings manager."""

    required_outputs = []

    def __init__(self, process, figsize=None, **kwargs):
        self.offsettings_manager = getattr(process, "offsettings_manager", None)
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize, **kwargs)

    def _get_default_figsize(self):
        return (plot_3_x, plot_3_y)

    def _update_plot_elements(self):
        self.ax.clear()
        self.create_plot()

    def _stack_columns(self, columns_labels_colors, scale=1.0):
        """Stacked area of the given (column, label, color) triplets over the prospective years."""
        stack_data, stack_labels, stack_colors = [], [], []
        for column, label, color in columns_labels_colors:
            if column in self.df.columns:
                values = self.df.loc[self.prospective_years, column].fillna(0) * scale
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
                alpha=0.8,
            )
            self.ax.legend(loc="upper left", fontsize=9)


# ---------------------------------------------------------------------------
# Carbon offset by category (stacked area)
# ---------------------------------------------------------------------------


class CarbonOffsetMixPlot(_OffsettingsPlot):
    """
    Stacked area of the carbon offset by offsetting category.

    Categories (carbon dioxide removal, emissions avoidance, …) are discovered
    from ``offsettings_manager``.
    """

    def create_plot(self):
        if self.offsettings_manager is None:
            return

        categories = self.offsettings_manager.get_all_types("category")
        self._stack_columns(
            [
                (
                    f"{category}_carbon_offset",
                    _readable_label(category),
                    _get_category_color(category, fallback_index),
                )
                for fallback_index, category in enumerate(categories)
            ]
        )

        self.ax.grid(True, alpha=0.3)
        self.ax.set_title("Carbon offset by offsetting category")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Carbon offset [MtCO2]")
        self.ax.set_xlim(self.prospective_years[0], self.prospective_years[-1])


# ---------------------------------------------------------------------------
# Carbon offset by mechanism (stacked area)
# ---------------------------------------------------------------------------


class CarbonOffsetMechanismsBreakdownPlot(_OffsettingsPlot):
    """
    Stacked area of the carbon offset by offsetting mechanism.

    Mechanisms are discovered from ``offsettings_manager``.
    """

    def create_plot(self):
        if self.offsettings_manager is None:
            return

        mechanisms = self.offsettings_manager.get_all()
        self._stack_columns(
            [
                (
                    f"{mechanism.name}_carbon_offset",
                    _readable_label(mechanism.name),
                    OFFSETTING_FALLBACK_COLORS[fallback_index % len(OFFSETTING_FALLBACK_COLORS)],
                )
                for fallback_index, mechanism in enumerate(mechanisms)
            ]
        )

        self.ax.grid(True, alpha=0.3)
        self.ax.set_title("Carbon offset by offsetting mechanism")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Carbon offset [MtCO2]")
        self.ax.set_xlim(self.prospective_years[0], self.prospective_years[-1])


# ---------------------------------------------------------------------------
# Carbon offsetting costs by mechanism (stacked area)
# ---------------------------------------------------------------------------


class CarbonOffsetCostBreakdownPlot(_OffsettingsPlot):
    """
    Stacked area of the carbon offsetting costs by offsetting mechanism.

    Mechanisms are discovered from ``offsettings_manager``.
    """

    def create_plot(self):
        if self.offsettings_manager is None:
            return

        mechanisms = self.offsettings_manager.get_all()
        self._stack_columns(
            [
                (
                    f"{mechanism.name}_carbon_offset_cost",
                    _readable_label(mechanism.name),
                    OFFSETTING_FALLBACK_COLORS[fallback_index % len(OFFSETTING_FALLBACK_COLORS)],
                )
                for fallback_index, mechanism in enumerate(mechanisms)
            ]
        )

        self.ax.grid(True, alpha=0.3)
        self.ax.set_title("Carbon offsetting costs by mechanism")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Carbon offsetting costs [M€]")
        self.ax.set_xlim(self.prospective_years[0], self.prospective_years[-1])


# ---------------------------------------------------------------------------
# Carbon offset prices (lines)
# ---------------------------------------------------------------------------


class CarbonOffsetPricesPlot(_OffsettingsPlot):
    """
    Mean carbon offset price and net unit cost of each offsetting mechanism.

    Mechanisms are discovered from ``offsettings_manager``.
    """

    def create_plot(self):
        if self.offsettings_manager is None:
            return

        for fallback_index, mechanism in enumerate(self.offsettings_manager.get_all()):
            column = f"{mechanism.name}_net_unit_cost"
            if column in self.df.columns:
                self.ax.plot(
                    self.prospective_years,
                    self.df.loc[self.prospective_years, column],
                    label=_readable_label(mechanism.name),
                    linestyle="--",
                    color=OFFSETTING_FALLBACK_COLORS[
                        fallback_index % len(OFFSETTING_FALLBACK_COLORS)
                    ],
                )

        if "carbon_offset_mean_price" in self.df.columns:
            self.ax.plot(
                self.prospective_years,
                self.df.loc[self.prospective_years, "carbon_offset_mean_price"],
                label="Mean carbon offset price",
                color="black",
                linewidth=2,
            )

        self.ax.legend(loc="upper left", fontsize=9)
        self.ax.grid(True, alpha=0.3)
        self.ax.set_title("Carbon offset prices")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Price [€/tCO2]")
        self.ax.set_xlim(self.prospective_years[0], self.prospective_years[-1])
