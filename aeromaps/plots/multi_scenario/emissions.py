"""Multi-scenario comparison plots for emissions."""

from aeromaps.plots.multi_scenario_plot import MultiScenarioPlot


class CO2EmissionsComparisonPlot(MultiScenarioPlot):
    """Compare CO2 emissions over time across scenarios."""

    required_outputs = ["co2_emissions"]
    column_name = "co2_emissions"
    data_source = "df_climate"

    def create_plot(self):
        self._plot_grouped_series()
        self.ax.set_xlabel("Year", fontsize=12)
        self.ax.set_ylabel("CO2 Emissions [Mt CO2]", fontsize=12)
        self.ax.set_title("CO2 Emissions Comparison Across Scenarios", fontsize=14)
        self.ax.legend(loc='best')
        self.ax.grid(True, alpha=0.3)


class CumulativeCO2EmissionsComparisonPlot(MultiScenarioPlot):
    """Compare cumulative CO2 emissions and per-scenario carbon budget."""

    required_outputs = ["cumulative_co2_emissions"]
    column_name = "cumulative_co2_emissions"

    def create_plot(self):
        # Carbon budget axhlines (one per unique value across all scenarios).
        # required_outputs already guarantees cumulative_co2_emissions; the
        # only conditional left is the optional `aviation_carbon_budget`
        # float output.
        scenario_items = (self.scenario_data.items()
                          if isinstance(self.scenario_data, dict)
                          else [(f"Scenario {i+1}", d) for i, d in enumerate(self.scenario_data)])
        budgets_by_scenario = [
            (name, (data["float_outputs"] or {}).get("aviation_carbon_budget"))
            for name, data in scenario_items
        ]
        plotted_budgets = {}  # budget_value -> [(scenario_name, line_handle_or_None)]
        for scenario_name, budget in budgets_by_scenario:
            if budget is None:
                pass  # no budget to draw for this scenario
            elif budget in plotted_budgets:
                plotted_budgets[budget].append((scenario_name, None))
            else:
                line = self.ax.axhline(
                    y=budget, color="k", linestyle='-',
                    linewidth=1, alpha=0.7, label="Budget",
                )
                plotted_budgets[budget] = [(scenario_name, line)]

        # Relabel budgets: single shared -> "Budget"; otherwise scenario-specific.
        num_unique = len(plotted_budgets)
        for _budget, info in plotted_budgets.items():
            names = [n for n, _ in info]
            line = info[0][1]
            if num_unique == 1:
                line.set_label("Budget")
            elif len(names) > 1:
                line.set_label("Budget - Rest")
            else:
                line.set_label(f"Budget - {names[0]}")

        # Emissions curves go through the group helper.
        self._plot_grouped_series()

        self.ax.set_xlabel("Year", fontsize=12)
        self.ax.set_ylabel("Cumulative CO2 Emissions [Gt CO2]", fontsize=12)
        self.ax.set_title("Cumulative CO2 vs Carbon Budget Comparison", fontsize=14)
        self.ax.legend(loc='best', fontsize=9)
        self.ax.grid(True, alpha=0.3)
