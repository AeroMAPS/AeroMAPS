"""Multi-scenario comparison plots for costs."""

from aeromaps.plots.multi_scenario_plot import MultiScenarioPlot


class EnergyExpensesComparisonPlot(MultiScenarioPlot):
    """Compare total (non-discounted) energy expenses across scenarios."""

    required_outputs = ["non_discounted_energy_expenses"]
    column_name = "non_discounted_energy_expenses"
    years_source = "prospective_years"

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_title("Annual Energy Expenses Comparison")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Energy expenses [M€]")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)


class NetEnergyExpensesComparisonPlot(MultiScenarioPlot):
    """Compare net (non-discounted) energy expenses (incl. carbon tax) across scenarios."""

    required_outputs = ["non_discounted_net_energy_expenses"]
    column_name = "non_discounted_net_energy_expenses"
    years_source = "prospective_years"

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_title("Annual Net Energy Expenses Comparison (incl. carbon tax)")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Net energy expenses [M€]")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)


class DOCComparisonPlot(MultiScenarioPlot):
    """Compare fleet-average Direct Operating Cost (DOC) per ASK across scenarios."""

    required_outputs = ["doc_total_per_ask_mean"]
    column_name = "doc_total_per_ask_mean"
    years_source = "prospective_years"

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_title("Fleet-Average Direct Operating Cost (DOC) Comparison")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("DOC [€/ASK]")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)


class DOCEnergyComparisonPlot(MultiScenarioPlot):
    """Compare the energy component of DOC per ASK across scenarios."""

    required_outputs = ["doc_energy_per_ask_mean"]
    column_name = "doc_energy_per_ask_mean"
    years_source = "prospective_years"

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_title("Energy Component of DOC Comparison")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("DOC energy [€/ASK]")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)


class AirfareComparisonPlot(MultiScenarioPlot):
    """Compare total airfare per ASK across scenarios."""

    required_outputs = ["airfare_per_ask"]
    column_name = "airfare_per_ask"
    years_source = "prospective_years"

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_title("Total Airfare Comparison")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Airfare [€/ASK]")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)


class AllEnergyCostsPerRPKComparisonPlot(MultiScenarioPlot):
    """Compare total energy-related costs per RPK across scenarios.

    Plots ``doc_net_energy_per_rpk_mean`` (energy + carbon tax − subsidy +
    energy tax, expressed per Revenue Passenger Kilometer) so trajectories
    can be compared visually.
    """

    required_outputs = ["doc_net_energy_per_rpk_mean"]
    column_name = "doc_net_energy_per_rpk_mean"
    years_source = "prospective_years"

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_title("All Energy Costs per RPK – Scenario Comparison")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Energy costs [€/RPK]")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)
