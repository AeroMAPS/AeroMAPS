"""Multi-scenario comparison plots for costs."""

from aeromaps.plots.multi_scenario_plot import MultiScenarioPlot


class EnergyExpensesComparisonPlot(MultiScenarioPlot):
    """Compare total (non-discounted) energy expenses across scenarios."""

    required_outputs = ["non_discounted_energy_expenses"]


    def create_plot(self):
        for scenario_name, data in self.scenario_data.items():
            style = self.get_scenario_style(scenario_name)
            years = data["prospective_years"]
            self.ax.plot(
                years,
                data["df"].loc[years, "non_discounted_energy_expenses"],
                label=scenario_name,
                color=style["color"],
                linestyle=style["linestyle"],
                linewidth=2,
            )

        self.ax.set_title("Annual Energy Expenses Comparison")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Energy expenses [M€]")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)

    def _update_plot_elements(self):
        self.ax.clear()
        self.create_plot()


class NetEnergyExpensesComparisonPlot(MultiScenarioPlot):
    """Compare net (non-discounted) energy expenses (incl. carbon tax) across scenarios."""

    required_outputs = ["non_discounted_net_energy_expenses"]


    def create_plot(self):
        for scenario_name, data in self.scenario_data.items():
            style = self.get_scenario_style(scenario_name)
            years = data["prospective_years"]
            self.ax.plot(
                years,
                data["df"].loc[years, "non_discounted_net_energy_expenses"],
                label=scenario_name,
                color=style["color"],
                linestyle=style["linestyle"],
                linewidth=2,
            )

        self.ax.set_title("Annual Net Energy Expenses Comparison (incl. carbon tax)")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Net energy expenses [M€]")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)

    def _update_plot_elements(self):
        self.ax.clear()
        self.create_plot()


class DOCComparisonPlot(MultiScenarioPlot):
    """Compare fleet-average Direct Operating Cost (DOC) per ASK across scenarios."""

    required_outputs = ["doc_total_per_ask_mean"]


    def create_plot(self):
        for scenario_name, data in self.scenario_data.items():
            style = self.get_scenario_style(scenario_name)
            years = data["prospective_years"]
            self.ax.plot(
                years,
                data["df"].loc[years, "doc_total_per_ask_mean"],
                label=scenario_name,
                color=style["color"],
                linestyle=style["linestyle"],
                linewidth=2,
            )

        self.ax.set_title("Fleet-Average Direct Operating Cost (DOC) Comparison")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("DOC [€/ASK]")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)

    def _update_plot_elements(self):
        self.ax.clear()
        self.create_plot()


class DOCEnergyComparisonPlot(MultiScenarioPlot):
    """Compare the energy component of DOC per ASK across scenarios."""

    required_outputs = ["doc_energy_per_ask_mean"]


    def create_plot(self):
        for scenario_name, data in self.scenario_data.items():
            style = self.get_scenario_style(scenario_name)
            years = data["prospective_years"]
            self.ax.plot(
                years,
                data["df"].loc[years, "doc_energy_per_ask_mean"],
                label=scenario_name,
                color=style["color"],
                linestyle=style["linestyle"],
                linewidth=2,
            )

        self.ax.set_title("Energy Component of DOC Comparison")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("DOC energy [€/ASK]")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)

    def _update_plot_elements(self):
        self.ax.clear()
        self.create_plot()


class AirfareComparisonPlot(MultiScenarioPlot):
    """Compare total airfare per ASK across scenarios."""

    required_outputs = ["airfare_per_ask"]


    def create_plot(self):
        for scenario_name, data in self.scenario_data.items():
            style = self.get_scenario_style(scenario_name)
            years = data["prospective_years"]
            self.ax.plot(
                years,
                data["df"].loc[years, "airfare_per_ask"],
                label=scenario_name,
                color=style["color"],
                linestyle=style["linestyle"],
                linewidth=2,
            )

        self.ax.set_title("Total Airfare Comparison")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Airfare [€/ASK]")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)

    def _update_plot_elements(self):
        self.ax.clear()
        self.create_plot()


class AllEnergyCostsPerRPKComparisonPlot(MultiScenarioPlot):
    """Compare total energy-related costs per RPK across scenarios.

    Plots ``doc_all_energy_costs_per_rpk`` (energy + carbon tax − subsidy +
    energy tax, expressed per Revenue Passenger Kilometer) as one line per
    scenario so that trajectories can be compared visually.
    """

    required_outputs = ["doc_all_energy_costs_per_rpk"]


    def create_plot(self):
        for scenario_name, data in self.scenario_data.items():
            style = self.get_scenario_style(scenario_name)
            years = data["prospective_years"]
            self.ax.plot(
                years,
                data["df"].loc[years, "doc_all_energy_costs_per_rpk"],
                label=scenario_name,
                color=style["color"],
                linestyle=style["linestyle"],
                linewidth=2,
            )

        self.ax.set_title("All Energy Costs per RPK – Scenario Comparison")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Energy costs [€/RPK]")
        self.ax.legend(loc="best")
        self.ax.grid(True, alpha=0.3)

    def _update_plot_elements(self):
        self.ax.clear()
        self.create_plot()

