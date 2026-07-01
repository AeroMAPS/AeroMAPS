"""Single-scenario plots for the delivery-driven ("push") fleet model.

These replace the bespoke matplotlib in
``fleet_model_push_visualisations.py`` (``visu_fleet_array``,
``visu_retirements_array``, ``visu_retirement_age``, ``visu_energy_intensity``):
they read the Phase-5 process outputs emitted by
:class:`PassengerAircraftEfficiencyFleetPush` instead of calling the engine.

Output naming consumed here (per passenger market ``mid`` / display ``name``)
    - ``"<name>: Aircraft In Fleet"``           per-segment total fleet count
    - ``<mid>:<aircraft_type>:aircraft_in_fleet``  per-type fleet count
    - ``<mid>:<aircraft_type>:aircraft_deliveries`` per-type deliveries
    - ``energy_per_ask_without_operations_<mid>_dropin_fuel`` MJ/ASK

Because the markets (and the per-type column set) are scenario-defined, these
plots discover the available columns from ``process.data["vector_outputs"]``
rather than declaring a fixed ``required_outputs`` list.
"""

import re

from aeromaps.plots.single_scenario_plot import SingleScenarioPlot
from aeromaps.plots.single_scenario_plot import plot_1_x
from aeromaps.plots.single_scenario_plot import plot_1_y

# Engine segment ids (markets_push.yaml) in display order, with a stable colour.
_PUSH_SEGMENTS = [
    ("turboprop", "Turboprop", "#4DAF4A"),
    ("regional_jet", "Regional Jet", "#377EB8"),
    ("narrow_body", "Narrow Body", "#E41A1C"),
    ("wide_body", "Wide Body", "#984EA3"),
]

# Stacked-area palette for the per-type deliveries plot.
_TYPE_COLORS = [
    "#E41A1C",
    "#377EB8",
    "#4DAF4A",
    "#984EA3",
    "#FF7F00",
    "#A65628",
    "#00FFFF",
    "#FF00FF",
    "#008080",
    "#3F51B5",
    "#B2FF00",
    "#0A2A4F",
    "#FF6F61",
    "#808000",
    "#87CEEB",
    "#B22222",
    "#CFA0E9",
    "#FFD700",
    "#228B22",
    "#003F5C",
    "#D100D1",
    "#000000",
]


def _present_segments(df):
    """Segments whose per-segment total column is present in ``df``."""
    return [
        (mid, name, color)
        for (mid, name, color) in _PUSH_SEGMENTS
        if f"{name}: Aircraft In Fleet" in df.columns
    ]


class FleetCountBySegmentPlot(SingleScenarioPlot):
    """Per-segment total aircraft-in-fleet evolution (push model)."""

    def __init__(self, process, figsize=None, **kwargs):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize, **kwargs)

    def _get_default_figsize(self):
        return (plot_1_x, plot_1_y)

    def create_plot(self):
        segments = _present_segments(self.df)
        for mid, name, color in segments:
            series = self.df[f"{name}: Aircraft In Fleet"].dropna()
            self.ax.plot(
                series.index,
                series.values,
                color=color,
                linestyle="-",
                linewidth=2,
                label=name,
            )

        self.ax.grid()
        self.ax.set_title("Push fleet model — aircraft in fleet by segment")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Aircraft in fleet [count]")
        self.ax.set_ylim(bottom=0)
        self.ax.legend()
        self._set_x_limits()


class FleetDeliveriesByTypePlot(SingleScenarioPlot):
    """Per-type new deliveries per year, stacked, for one segment (push model).

    Parameters
    ----------
    segment : str, optional
        Engine segment id (``turboprop``/``regional_jet``/``narrow_body``/
        ``wide_body``). Defaults to ``narrow_body``.
    max_types : int, optional
        Cap on the number of individually coloured types (largest by total
        deliveries); the rest are aggregated into "Others". Default 12.
    """

    def __init__(self, process, segment="narrow_body", max_types=12, figsize=None, **kwargs):
        self._segment = segment
        self._max_types = max_types
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize, **kwargs)

    def _get_default_figsize(self):
        return (plot_1_x, plot_1_y)

    def _segment_name(self):
        for mid, name, _ in _PUSH_SEGMENTS:
            if mid == self._segment:
                return name
        return self._segment

    def _delivery_columns(self):
        pat = re.compile(rf"^{re.escape(self._segment)}:(.+):aircraft_deliveries$")
        cols = {}
        for col in self.df.columns:
            m = pat.match(col)
            if m:
                cols[m.group(1)] = col
        return cols

    def create_plot(self):
        cols = self._delivery_columns()
        name = self._segment_name()
        if not cols:
            self.ax.set_title(f"No delivery data for segment '{self._segment}'")
            return

        # Rank types by total deliveries; keep the top max_types, aggregate the rest.
        totals = {ac: self.df[col].fillna(0).sum() for ac, col in cols.items()}
        ranked = sorted(totals, key=lambda ac: -totals[ac])
        keep = [ac for ac in ranked if totals[ac] > 0][: self._max_types]
        others = [ac for ac in ranked if ac not in keep and totals[ac] > 0]

        years = self.prospective_years
        stack = []
        labels = []
        colors = []
        for i, ac in enumerate(keep):
            stack.append(self.df.loc[years, cols[ac]].fillna(0).values)
            labels.append(ac)
            colors.append(_TYPE_COLORS[i % len(_TYPE_COLORS)])
        if others:
            agg = None
            for ac in others:
                vals = self.df.loc[years, cols[ac]].fillna(0).values
                agg = vals if agg is None else agg + vals
            stack.append(agg)
            labels.append("Others")
            colors.append("grey")

        self.ax.stackplot(years, stack, labels=labels, colors=colors)

        self.ax.grid(axis="y")
        self.ax.set_title(f"Push fleet model — deliveries by type ({name})")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Aircraft delivered per year [count]")
        self.ax.set_ylim(bottom=0)
        self.ax.legend(loc="upper left", ncol=2, fontsize=8)
        self._set_x_limits()


class EnergyIntensityBySegmentPlot(SingleScenarioPlot):
    """Per-segment drop-in energy intensity (MJ/ASK) evolution (push model)."""

    def __init__(self, process, figsize=None, **kwargs):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize, **kwargs)

    def _get_default_figsize(self):
        return (plot_1_x, plot_1_y)

    def create_plot(self):
        for mid, name, color in _PUSH_SEGMENTS:
            col = f"energy_per_ask_without_operations_{mid}_dropin_fuel"
            if col not in self.df.columns:
                continue
            series = self.df[col].dropna()
            self.ax.plot(
                series.index,
                series.values,
                color=color,
                linestyle="-",
                linewidth=2,
                label=name,
            )

        if self.last_pivot_year() is not None:
            self.ax.axvline(self.last_pivot_year(), ls="--", lw=1, color="grey")

        self.ax.grid()
        self.ax.set_title("Push fleet model — drop-in energy intensity by segment")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Energy per ASK [MJ/ASK]")
        self.ax.set_ylim(bottom=0)
        self.ax.legend()
        self._set_x_limits()

    def last_pivot_year(self):
        """First prospective year minus one (the engine pivot), or None."""
        if self.prospective_years is not None and len(self.prospective_years) > 0:
            return self.prospective_years[0] - 1
        return None
