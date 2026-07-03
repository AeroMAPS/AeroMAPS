"""Single-scenario plots for energy mix and fuel supply breakdowns.

All plots discover energy carriers dynamically via ``pathways_manager``.
"""

from aeromaps.plots.single_scenario_plot import SingleScenarioPlot, plot_3_x, plot_3_y
from aeromaps.plots.multi_scenario_plot import ENERGY_ORIGIN_COLORS, ENERGY_ORIGIN_FALLBACK_COLORS


def _get_origin_color(energy_origin, fallback_index=0):
    """Return a colour for an energy origin, falling back to a rotating palette."""
    if energy_origin in ENERGY_ORIGIN_COLORS:
        return ENERGY_ORIGIN_COLORS[energy_origin]
    return ENERGY_ORIGIN_FALLBACK_COLORS[fallback_index % len(ENERGY_ORIGIN_FALLBACK_COLORS)]


def _readable_label(raw_name):
    """Turn a snake_case name into a readable label."""
    return raw_name.replace("_", " ").title()


def _aggregate_pathways_energy(df, years, pathways):
    """Sum ``{pathway.name}_energy_consumption`` for a list of pathways."""
    total = None
    for pathway in pathways:
        col = f"{pathway.name}_energy_consumption"
        if col in df.columns:
            values = df.loc[years, col].fillna(0)
            total = values if total is None else total + values
    return total


# ---------------------------------------------------------------------------
# Energy mix by origin (stacked area)
# ---------------------------------------------------------------------------


class EnergyMixPlot(SingleScenarioPlot):
    """
    Stacked area of total energy consumption by energy origin.

    Origins (fossil, biomass, electricity, …) are discovered from
    ``pathways_manager``.
    """

    required_outputs = []

    def __init__(self, process, figsize=None, **kwargs):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize, **kwargs)

    def _get_default_figsize(self):
        return (plot_3_x, plot_3_y)

    def create_plot(self):
        if self.pathways_manager is None:
            return

        energy_origins = self.pathways_manager.get_all_types("energy_origin")
        years = self.years

        stack_data, stack_labels, stack_colors = [], [], []
        fallback_idx = 0

        for origin in energy_origins:
            pathways = self.pathways_manager.get(energy_origin=origin)
            origin_energy = _aggregate_pathways_energy(self.df, years, pathways)
            if origin_energy is not None and origin_energy.sum() > 0:
                stack_data.append(origin_energy * 1e-12)
                stack_labels.append(_readable_label(origin))
                stack_colors.append(_get_origin_color(origin, fallback_idx))
                fallback_idx += 1

        if stack_data:
            self.ax.stackplot(
                years,
                *stack_data,
                labels=stack_labels,
                colors=stack_colors,
                alpha=0.8,
            )
            self.ax.legend(loc="upper left", fontsize=9)

        self.ax.grid(True, alpha=0.3)
        self.ax.set_title("Energy mix by origin")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Energy consumption [EJ]")
        self.ax.set_xlim(self.years[0], self.years[-1])

    def _update_plot_elements(self):
        self.ax.clear()
        self.create_plot()


# ---------------------------------------------------------------------------
# Drop-in fuel supply breakdown by origin (stacked area)
# ---------------------------------------------------------------------------


class DropInSupplyBreakdownPlot(SingleScenarioPlot):
    """
    Stacked area of drop-in fuel consumption by energy origin.

    Only pathways with ``aircraft_type='dropin_fuel'`` are included.
    """

    required_outputs = []

    def __init__(self, process, figsize=None, **kwargs):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize, **kwargs)

    def _get_default_figsize(self):
        return (plot_3_x, plot_3_y)

    def create_plot(self):
        if self.pathways_manager is None:
            return

        energy_origins = self.pathways_manager.get_all_types("energy_origin")
        years = self.years

        stack_data, stack_labels, stack_colors = [], [], []
        fallback_idx = 0

        for origin in energy_origins:
            pathways = self.pathways_manager.get(
                aircraft_type="dropin_fuel",
                energy_origin=origin,
            )
            origin_energy = _aggregate_pathways_energy(self.df, years, pathways)
            if origin_energy is not None and origin_energy.sum() > 0:
                stack_data.append(origin_energy * 1e-12)
                stack_labels.append(_readable_label(origin))
                stack_colors.append(_get_origin_color(origin, fallback_idx))
                fallback_idx += 1

        if stack_data:
            self.ax.stackplot(
                years,
                *stack_data,
                labels=stack_labels,
                colors=stack_colors,
                alpha=0.8,
            )
            self.ax.legend(loc="upper left", fontsize=9)

        self.ax.grid(True, alpha=0.3)
        self.ax.set_title("Drop-in fuel supply breakdown")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Energy [EJ]")
        self.ax.set_xlim(self.years[0], self.years[-1])

    def _update_plot_elements(self):
        self.ax.clear()
        self.create_plot()


# ---------------------------------------------------------------------------
# Biofuel mix — per-pathway breakdown (stacked area)
# ---------------------------------------------------------------------------

_PATHWAY_COLORS = [
    "#2ca02c",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf",
    "#9467bd",
    "#d62728",
    "#ff7f0e",
    "#1f77b4",
]


# ---------------------------------------------------------------------------
# Blending mandates — relative share of drop-in fuel by energy origin (%)
# ---------------------------------------------------------------------------


class DropInSharesBreakdownPlot(SingleScenarioPlot):
    """
    Stacked area (0–100 %) showing the share of each energy origin in the
    drop-in fuel blend.

    Uses ``{pathway.name}_share_dropin_fuel`` columns, aggregated by origin,
    so the areas always sum to 100 % for each prospective year.
    Historic years are included if the data covers them.
    """

    required_outputs = []

    def __init__(self, process, figsize=None, **kwargs):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize, **kwargs)

    def _get_default_figsize(self):
        return (plot_3_x, plot_3_y)

    def create_plot(self):
        if self.pathways_manager is None:
            return

        energy_origins = self.pathways_manager.get_all_types("energy_origin")
        years = self.years

        stack_data, stack_labels, stack_colors = [], [], []
        fallback_idx = 0

        for origin in energy_origins:
            pathways = self.pathways_manager.get(
                aircraft_type="dropin_fuel",
                energy_origin=origin,
            )
            # Sum individual pathway shares for this origin
            total_share = None
            for pathway in pathways:
                col = f"{pathway.name}_share_dropin_fuel"
                if col in self.df.columns:
                    values = self.df.loc[years, col].fillna(0)
                    total_share = values if total_share is None else total_share + values

            if total_share is not None and total_share.sum() > 0:
                stack_data.append(total_share)
                stack_labels.append(_readable_label(origin))
                stack_colors.append(_get_origin_color(origin, fallback_idx))
                fallback_idx += 1

        if stack_data:
            self.ax.stackplot(
                years,
                *stack_data,
                labels=stack_labels,
                colors=stack_colors,
                alpha=0.8,
            )
            self.ax.legend(loc="upper left", fontsize=9)
            self.ax.set_ylim(0, 100)

        self.ax.grid(True, alpha=0.3)
        self.ax.set_title("Drop-in fuel shares breakdown (by origin)")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Share of drop-in fuel blend [%]")
        self.ax.set_xlim(years[0], years[-1])

    def _update_plot_elements(self):
        self.ax.clear()
        self.create_plot()


class BiofuelMixPlot(SingleScenarioPlot):
    """
    Stacked area of individual biomass-origin drop-in pathways.
    """

    required_outputs = []

    def __init__(self, process, figsize=None, **kwargs):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize, **kwargs)

    def _get_default_figsize(self):
        return (plot_3_x, plot_3_y)

    def create_plot(self):
        if self.pathways_manager is None:
            return

        bio_pathways = self.pathways_manager.get(
            aircraft_type="dropin_fuel",
            energy_origin="biomass",
        )
        years = self.years

        stack_data, stack_labels, stack_colors = [], [], []

        for p_idx, pathway in enumerate(bio_pathways):
            col = f"{pathway.name}_energy_consumption"
            if col in self.df.columns:
                values = self.df.loc[years, col].fillna(0) * 1e-12
                if values.sum() > 0:
                    stack_data.append(values)
                    stack_labels.append(_readable_label(pathway.name))
                    stack_colors.append(_PATHWAY_COLORS[p_idx % len(_PATHWAY_COLORS)])

        if stack_data:
            self.ax.stackplot(
                years,
                *stack_data,
                labels=stack_labels,
                colors=stack_colors,
                alpha=0.8,
            )
            self.ax.legend(loc="upper left", fontsize=9, ncol=2)

        self.ax.grid(True, alpha=0.3)
        self.ax.set_title("Biofuel mix by pathway")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Biofuel production [EJ]")
        self.ax.set_xlim(self.years[0], self.years[-1])

    def _update_plot_elements(self):
        self.ax.clear()
        self.create_plot()
