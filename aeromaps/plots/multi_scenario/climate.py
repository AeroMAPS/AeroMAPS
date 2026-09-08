"""Multi-scenario comparison plots for climate metrics."""

from aeromaps.plots.climate_mechanisms import (
    MECHANISM_COLORS,
    MECHANISM_GROUPS,
    TOTAL_COLOR,
    all_erf_columns,
    all_temperature_columns,
    group_erf,
    group_temperature,
)
from aeromaps.plots.multi_scenario_plot import MultiScenarioPlot
from aeromaps.plots.single_scenario_plot import plot_1_x


class TotalERFComparisonPlot(MultiScenarioPlot):
    """Compare total effective radiative forcing (ERF) across scenarios."""

    required_outputs = ["total_erf"]
    column_name = "total_erf"
    data_source = "df_climate"

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_title("Total Effective Radiative Forcing Comparison")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Total ERF [W/m²]")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)


class TemperatureIncreaseComparisonPlot(MultiScenarioPlot):
    """Compare temperature increase from aviation across scenarios."""

    required_outputs = ["temperature_increase_from_aviation"]
    column_name = "temperature_increase_from_aviation"
    data_source = "df_climate"
    y_scale = 1000  # convert from K to mK

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_title("Temperature Increase from Aviation Comparison")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Temperature increase [mK]")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)


class CO2ERFComparisonPlot(MultiScenarioPlot):
    """Compare CO2 effective radiative forcing across scenarios."""

    required_outputs = ["co2_erf"]
    column_name = "co2_erf"
    data_source = "df_climate"

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_title("CO₂ Effective Radiative Forcing Comparison")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("CO₂ ERF [W/m²]")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)


class NonCO2ERFComparisonPlot(MultiScenarioPlot):
    """Compare non-CO2 ERF across scenarios (total minus CO2)."""

    required_outputs = ["total_erf", "co2_erf"]

    def _scenario_xy(self, scenario_name, data):
        df = data["df_climate"]
        x = data["years"]
        return x, df.loc[x, "total_erf"] - df.loc[x, "co2_erf"]

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_title("Non-CO₂ Effective Radiative Forcing Comparison")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Non-CO₂ ERF [W/m²]")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)


class ContrailsTemperatureComparisonPlot(MultiScenarioPlot):
    """Compare contrail-induced temperature increase across scenarios.

    Contrails are typically the largest single non-CO2 warming term, and the
    one most sensitive to operational and combustor interventions, so they are
    worth comparing on their own rather than only inside the non-CO2 aggregate.
    """

    required_outputs = ["temperature_increase_from_contrails_from_aviation"]
    column_name = "temperature_increase_from_contrails_from_aviation"
    data_source = "df_climate"
    y_scale = 1000  # convert from K to mK

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_title("Contrail-Induced Temperature Increase Comparison")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Temperature increase [mK]")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)


class ContrailsERFComparisonPlot(MultiScenarioPlot):
    """Compare contrail effective radiative forcing across scenarios."""

    required_outputs = ["contrails_erf"]
    column_name = "contrails_erf"
    data_source = "df_climate"

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_title("Contrail Effective Radiative Forcing Comparison")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Contrail ERF [W/m²]")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)


# ---------------------------------------------------------------------------
# Per-mechanism decomposition (one subplot per scenario)
# ---------------------------------------------------------------------------


class _MechanismDecompositionComparisonPlot(MultiScenarioPlot):
    """Shared base for per-mechanism climate decompositions.

    Draws one subplot per scenario with a line per mechanism family plus the
    total. Lines rather than stacked bands because the net NOx and aerosol
    terms are negative: stacking them would misrepresent the balance the plot
    exists to show.

    Subclasses set ``series`` (callable returning one family's series),
    ``y_scale``, ``y_label`` and ``plot_title``.
    """

    required_outputs = []
    y_scale = 1.0
    y_label = ""
    plot_title = ""

    def _series(self, df_climate, years, group):
        raise NotImplementedError

    def _get_default_figsize(self):
        n = len(self.scenario_data)
        return (plot_1_x, max(4, 3 * n))

    def create_plot(self):
        scenario_items = list(self.scenario_data.items())
        n_scenarios = len(scenario_items)

        self.fig.clear()
        axes = self.fig.subplots(n_scenarios, 1, squeeze=False, sharex=True)

        for idx, (scenario_name, data) in enumerate(scenario_items):
            ax = axes[idx, 0]
            years = data["years"]
            df_climate = data["df_climate"]

            total = None
            for group, (label, _) in MECHANISM_GROUPS.items():
                values = self._series(df_climate, years, group) * self.y_scale
                total = values if total is None else total + values
                ax.plot(years, values, color=MECHANISM_COLORS[group], linewidth=2, label=label)

            ax.plot(years, total, color=TOTAL_COLOR, linewidth=2.4, label="Total", zorder=5)
            ax.axhline(0, color=TOTAL_COLOR, linewidth=0.8, alpha=0.4)

            ax.set_ylabel(self.y_label, fontsize=10)
            ax.set_title(scenario_name, fontsize=11, fontweight="bold")
            ax.grid(True, alpha=0.3)
            if idx == 0:
                ax.legend(loc="upper left", fontsize=9, ncol=2)
            if idx == n_scenarios - 1:
                ax.set_xlabel("Year", fontsize=12)

        self.fig.suptitle(self.plot_title, fontsize=14, y=0.995)
        self.axes = axes

    def _update_plot_elements(self):
        self.fig.clear()
        self.create_plot()


class TemperatureDecompositionComparisonPlot(_MechanismDecompositionComparisonPlot):
    """Compare the per-mechanism temperature decomposition across scenarios."""

    required_outputs = all_temperature_columns()
    y_scale = 1000  # convert from K to mK
    y_label = "Temperature increase [mK]"
    plot_title = "Temperature Decomposition by Mechanism"

    def _series(self, df_climate, years, group):
        return group_temperature(df_climate, years, group)


class ERFDecompositionComparisonPlot(_MechanismDecompositionComparisonPlot):
    """Compare the per-mechanism ERF decomposition across scenarios."""

    required_outputs = all_erf_columns()
    y_label = "Effective radiative forcing [W/m²]"
    plot_title = "Effective Radiative Forcing Decomposition by Mechanism"

    def _series(self, df_climate, years, group):
        return group_erf(df_climate, years, group)
