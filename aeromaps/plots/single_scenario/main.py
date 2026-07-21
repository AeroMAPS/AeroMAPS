import matplotlib.pyplot as plt
import numpy as np

from aeromaps.models.impacts.emissions.co2_emissions import (
    MARKET_CROSS_MIX,
    aircraft_efficiency_lever_names,
    market_lever_column,
    market_lever_names,
)
from aeromaps.plots import colors
from aeromaps.plots.single_scenario_plot import SingleScenarioPlot
from aeromaps.plots.single_scenario_plot import plot_1_x
from aeromaps.plots.single_scenario_plot import plot_1_y


class AirTransportCO2EmissionsPlot(SingleScenarioPlot):
    required_outputs = [
        "co2_emissions_last_historical_year_technology",
        "co2_emissions_including_aircraft_efficiency",
        "co2_emissions_including_load_factor",
        "co2_emissions_including_energy",
        "co2_emissions_last_historical_year_technology_baseline3",
        "carbon_offset",
        "co2_emissions",
    ]

    def __init__(self, process, figsize=None, **kwargs):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize, **kwargs)

    def _get_default_figsize(self):
        return (plot_1_x, plot_1_y)

    def create_plot(self):
        (self.line_co2_emissions_including_sobriety,) = self.ax.plot(
            self.years,
            self.df["co2_emissions_last_historical_year_technology"],
            color="black",
            linestyle="--",
            linewidth=1,
        )

        (self.line_co2_emissions_including_technology,) = self.ax.plot(
            self.years,
            self.df["co2_emissions_including_aircraft_efficiency"],
            color="black",
            linestyle="--",
            linewidth=1,
        )

        (self.line_co2_emissions_including_load_factor,) = self.ax.plot(
            self.years,
            self.df["co2_emissions_including_load_factor"],
            color="black",
            linestyle="--",
            linewidth=1,
        )

        (self.line_co2_emissions_including_energy,) = self.ax.plot(
            self.years,
            self.df["co2_emissions_including_energy"],
            color="black",
            linestyle="--",
            linewidth=1,
        )

        self.ax.plot(
            self.historic_years,
            self.df_climate.loc[self.historic_years, "co2_emissions"],
            color="black",
            linestyle="-",
            label="Historical emissions",
            linewidth=3,
            zorder=4,
        )

        (self.line_co2_emissions_no_action,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[
                self.prospective_years, "co2_emissions_last_historical_year_technology_baseline3"
            ],
            color="red",
            linestyle="-",
            label="Emissions at 2019 technological level with trend air traffic growth",
            linewidth=3,
            zorder=3,
        )

        (self.line_co2_emissions,) = self.ax.plot(
            self.prospective_years,
            self.df_climate.loc[self.prospective_years, "co2_emissions"],
            color="green",
            linestyle="-",
            label="Projected emissions including all levers of action",
            linewidth=3,
            zorder=3,
        )

        (self.line_co2_emissions_offset,) = self.ax.plot(
            self.prospective_years,
            self.df_climate.loc[self.prospective_years, "co2_emissions"]
            - self.df.loc[self.prospective_years, "carbon_offset"],
            color="grey",
            linestyle="--",
            label="Projected emissions including all levers of action and offsetting",
            linewidth=2,
            zorder=3,
        )

        # Fill between

        self.ax.fill_between(
            self.years,
            self.df["co2_emissions_last_historical_year_technology_baseline3"],
            self.df["co2_emissions_last_historical_year_technology"],
            color=colors.LEVER_COLORS["demand"],
            label="Demand/supply side management",
        )

        self.ax.fill_between(
            self.years,
            self.df["co2_emissions_last_historical_year_technology"],
            self.df["co2_emissions_including_aircraft_efficiency"],
            color=colors.LEVER_COLORS["efficiency"],
            label="Aircraft efficiency",
        )

        self.ax.fill_between(
            self.years,
            self.df["co2_emissions_including_aircraft_efficiency"],
            self.df["co2_emissions_including_load_factor"],
            color=colors.LEVER_OPERATIONS_LOADFACTOR,
            label="Fleet operations and load factor",
        )

        self.ax.fill_between(
            self.years,
            self.df["co2_emissions_including_load_factor"],
            self.df_climate.loc[self.years, "co2_emissions"],
            color=colors.LEVER_COLORS["energy"],
            label="Aircraft energy",
        )

        plt.rc("hatch", linewidth=4)
        self.ax.fill_between(
            self.years,
            self.df_climate.loc[self.years, "co2_emissions"],
            self.df_climate.loc[self.years, "co2_emissions"] - self.df["carbon_offset"],
            color="white",
            facecolor=colors.LEVER_COLORS["offset"],
            hatch="//",
            label="Carbon offset",
        )

        self.ax.grid()
        self.ax.set_title("Evolution of annual CO₂ emissions from air transport")
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Annual CO₂ emissions [MtCO₂]")
        self.ax.legend(loc=2)
        self.ax.set_xlim(self.years[0], self.years[-1])

    def _update_plot_elements(self):
        self.line_co2_emissions_including_sobriety.set_ydata(
            self.df["co2_emissions_last_historical_year_technology"]
        )

        self.line_co2_emissions_including_technology.set_ydata(
            self.df["co2_emissions_including_aircraft_efficiency"]
        )

        self.line_co2_emissions_including_load_factor.set_ydata(
            self.df["co2_emissions_including_load_factor"]
        )

        self.line_co2_emissions_including_energy.set_ydata(
            self.df["co2_emissions_including_energy"]
        )

        self.line_co2_emissions.set_ydata(
            self.df_climate.loc[self.prospective_years, "co2_emissions"]
        )

        self.line_co2_emissions_offset.set_ydata(
            self.df_climate.loc[self.prospective_years, "co2_emissions"]
            - self.df.loc[self.prospective_years, "carbon_offset"]
        )

        for collection in self.ax.collections:
            collection.remove()

        # Fill between
        self.ax.fill_between(
            self.years,
            self.df["co2_emissions_last_historical_year_technology_baseline3"],
            self.df["co2_emissions_last_historical_year_technology"],
            color=colors.LEVER_COLORS["demand"],
            label="Demand/supply side management",
        )

        self.ax.fill_between(
            self.years,
            self.df["co2_emissions_last_historical_year_technology"],
            self.df["co2_emissions_including_aircraft_efficiency"],
            color=colors.LEVER_COLORS["efficiency"],
            label="Aircraft efficiency",
        )

        self.ax.fill_between(
            self.years,
            self.df["co2_emissions_including_aircraft_efficiency"],
            self.df["co2_emissions_including_load_factor"],
            color=colors.LEVER_OPERATIONS_LOADFACTOR,
            label="Fleet operations and load factor",
        )

        self.ax.fill_between(
            self.years,
            self.df["co2_emissions_including_load_factor"],
            self.df_climate.loc[self.years, "co2_emissions"],
            color=colors.LEVER_COLORS["energy"],
            label="Aircraft energy",
        )

        plt.rc("hatch", linewidth=4)
        self.ax.fill_between(
            self.years,
            self.df_climate.loc[self.years, "co2_emissions"],
            self.df_climate.loc[self.years, "co2_emissions"] - self.df["carbon_offset"],
            color="white",
            facecolor=colors.LEVER_COLORS["offset"],
            hatch="//",
            label="Carbon offset",
        )
        self.fig.canvas.draw()


class AirTransportCO2EmissionsDetailedPlot(SingleScenarioPlot):
    """
    Variant of AirTransportCO2EmissionsPlot where the "Aircraft efficiency" and/or
    "Aircraft energy" levers of action are decomposed into sub-levers: fleet
    renewal and each new aircraft of the fleet for the efficiency lever, and each
    energy pathway for the energy lever.

    Each decomposition is independent and optional: the efficiency lever is only
    decomposed when the bottom-up fleet model and DetailedCo2EmissionsPerAircraft
    are used, and the energy lever only when the generic energy models and
    DetailedCo2EmissionsPerPathway are used. Any lever whose sub-levers are not
    available (e.g. a top-down fleet model, or non-generic energy models) simply
    falls back to a single aggregated band, exactly like AirTransportCO2EmissionsPlot.
    """

    required_outputs = [
        "co2_emissions_last_historical_year_technology",
        "co2_emissions_including_aircraft_efficiency",
        "co2_emissions_including_load_factor",
        "co2_emissions_including_energy",
        "co2_emissions_last_historical_year_technology_baseline3",
        "carbon_offset",
        "co2_emissions",
    ]

    # Colormap used per energy origin for the energy pathway sub-levers
    # (fuel-origin convention, shared with the colour module).
    ENERGY_ORIGIN_COLORMAPS = colors.ENERGY_ORIGIN_COLORMAPS
    ENERGY_ORIGIN_FALLBACK_COLORMAP = colors.ENERGY_ORIGIN_FALLBACK_COLORMAP

    # Bands whose absolute contribution never exceeds this value [MtCO2] are not
    # drawn nor referenced in the legend (their thickness would not be visible)
    NEGLIGIBLE_BAND_THRESHOLD = 1e-3

    EFFICIENCY_GRANULARITIES = ("aircraft", "category")
    ENERGY_GRANULARITIES = ("pathway", "origin")

    def __init__(
        self,
        process,
        figsize=None,
        efficiency_granularity="aircraft",
        energy_granularity="pathway",
        **kwargs,
    ):
        """
        Parameters
        ----------
        efficiency_granularity : {"aircraft", "category"}
            Granularity of the aircraft-efficiency decomposition: one band per
            individual aircraft (default) or one band per fleet category (the
            per-aircraft contributions summed within each category).
        energy_granularity : {"pathway", "origin"}
            Granularity of the aircraft-energy decomposition: one band per energy
            pathway (default) or one band per fuel origin family (biofuels /
            electrofuels & e-hydrogen / fossil-derived).
        """
        if efficiency_granularity not in self.EFFICIENCY_GRANULARITIES:
            raise ValueError(
                f"efficiency_granularity must be one of {self.EFFICIENCY_GRANULARITIES}, "
                f"got {efficiency_granularity!r}"
            )
        if energy_granularity not in self.ENERGY_GRANULARITIES:
            raise ValueError(
                f"energy_granularity must be one of {self.ENERGY_GRANULARITIES}, "
                f"got {energy_granularity!r}"
            )
        self._efficiency_granularity = efficiency_granularity
        self._energy_granularity = energy_granularity
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize, **kwargs)

    def _get_default_figsize(self):
        return (plot_1_x, plot_1_y)

    def _col(self, column):
        """Sub-lever column over the plot years, NaNs treated as zero."""
        return self.df.loc[self.years, column].fillna(0)

    def _sum_cols(self, columns):
        """Sum of several sub-lever columns over the plot years (for grouping)."""
        return self.df.loc[self.years, list(columns)].fillna(0).sum(axis=1)

    def _efficiency_bands(self):
        """Return the (label, values, color) list of the aircraft efficiency sub-levers.

        Sub-levers are shown per individual aircraft or, when
        ``efficiency_granularity="category"``, aggregated per fleet category.
        Returns None when the decomposition is not available (e.g. a top-down
        fleet model is used instead of the bottom-up one), so that the caller
        falls back to a single aggregated band.
        """
        fleet_model = getattr(self.process, "fleet_model", None)
        if fleet_model is None or "co2_emissions_lever_efficiency_fleet_renewal" not in (
            self.df.columns
        ):
            return None

        lever_names = aircraft_efficiency_lever_names(fleet_model.fleet)
        # (category, aircraft, column) for every aircraft with a contribution.
        aircraft = [
            (category_name, aircraft_name, column)
            for (category_name, _, aircraft_name), column in lever_names.items()
            if column in self.df.columns
        ]

        # Ordinal sub-levers read as steps of the efficiency lever's own hue (blue).
        efficiency_cmap = colors.LEVER_SEQUENTIAL_CMAP["efficiency"]

        bands = [
            (
                "Fleet renewal",
                self._col("co2_emissions_lever_efficiency_fleet_renewal"),
                efficiency_cmap(0.35),
            )
        ]

        if self._efficiency_granularity == "category":
            categories = list(dict.fromkeys(category for category, _, _ in aircraft))
            ramp = efficiency_cmap(np.linspace(0.45, 0.85, max(len(categories), 1)))
            for category_name, color in zip(categories, ramp):
                columns = [col for cat, _, col in aircraft if cat == category_name]
                bands.append((f"{category_name} fleet", self._sum_cols(columns), color))
        else:
            ramp = efficiency_cmap(np.linspace(0.45, 0.85, max(len(aircraft), 1)))
            for (category_name, aircraft_name, column), color in zip(aircraft, ramp):
                bands.append((f"{aircraft_name} ({category_name})", self._col(column), color))

        bands.append(
            (
                "Freight fleet",
                self._col("co2_emissions_lever_efficiency_freight"),
                efficiency_cmap(0.25),
            )
        )
        # Residual (traffic mix) is not an identity band -> neutral grey.
        bands.append(
            (
                "Traffic mix and others",
                self._col("co2_emissions_lever_efficiency_other"),
                colors.NEUTRAL,
            )
        )
        return bands

    def _energy_bands(self):
        """Return the (label, values, color) list of the energy pathway sub-levers.

        Sub-levers are shown per pathway or, when ``energy_granularity="origin"``,
        aggregated per fuel origin family (biofuels / electrofuels / fossil).
        Returns None when the decomposition is not available (e.g. non-generic,
        top-down energy models are used), so that the caller falls back to a
        single aggregated band.
        """
        if self.pathways_manager is None or "co2_emissions_lever_energy_other" not in (
            self.df.columns
        ):
            return None

        pathways_by_origin = {}
        for pathway in self.pathways_manager.get_all():
            column = f"co2_emissions_lever_energy_{pathway.name}"
            if column in self.df.columns:
                pathways_by_origin.setdefault(pathway.energy_origin, []).append(
                    (pathway.name, column)
                )

        bands = []
        for energy_origin, pathways in pathways_by_origin.items():
            colormap = self.ENERGY_ORIGIN_COLORMAPS.get(
                energy_origin, self.ENERGY_ORIGIN_FALLBACK_COLORMAP
            )
            if self._energy_granularity == "origin":
                # One solid band per fuel family (biofuels / electrofuels / fossil).
                label = colors.ENERGY_ORIGIN_LABELS.get(
                    energy_origin, energy_origin.replace("_", " ").title()
                )
                columns = [column for _, column in pathways]
                bands.append((label, self._sum_cols(columns), colormap(0.7)))
            else:
                pathway_colors = colormap(np.linspace(0.4, 0.8, len(pathways)))
                for (pathway_name, column), color in zip(pathways, pathway_colors):
                    bands.append((pathway_name.replace("_", " ").title(), self._col(column), color))
        # Residual energy effects are not an identity band -> neutral grey.
        bands.append(
            ("Other energy effects", self._col("co2_emissions_lever_energy_other"), colors.NEUTRAL)
        )
        return bands

    def _plot_sub_lever_bands(self, upper, bands):
        """Stack sub-lever bands downwards from the given upper curve.

        Negligible bands are subtracted but not drawn, so that the legend only
        references visible bands.
        """
        for label, values, color in bands:
            lower = upper - values
            if values.abs().max() > self.NEGLIGIBLE_BAND_THRESHOLD:
                self.ax.fill_between(self.years, upper, lower, color=color, label=label)
            upper = lower
        return upper

    def create_plot(self):
        self.ax.plot(
            self.historic_years,
            self.df_climate.loc[self.historic_years, "co2_emissions"],
            color="black",
            linestyle="-",
            label="Historical emissions",
            linewidth=3,
            zorder=4,
        )

        (self.line_co2_emissions_no_action,) = self.ax.plot(
            self.prospective_years,
            self.df.loc[
                self.prospective_years, "co2_emissions_last_historical_year_technology_baseline3"
            ],
            color="red",
            linestyle="-",
            label="Emissions at 2019 technological level with trend air traffic growth",
            linewidth=3,
            zorder=3,
        )

        (self.line_co2_emissions,) = self.ax.plot(
            self.prospective_years,
            self.df_climate.loc[self.prospective_years, "co2_emissions"],
            color="green",
            linestyle="-",
            label="Projected emissions including all levers of action",
            linewidth=3,
            zorder=3,
        )

        (self.line_co2_emissions_offset,) = self.ax.plot(
            self.prospective_years,
            self.df_climate.loc[self.prospective_years, "co2_emissions"]
            - self.df.loc[self.prospective_years, "carbon_offset"],
            color="grey",
            linestyle="--",
            label="Projected emissions including all levers of action and offsetting",
            linewidth=2,
            zorder=3,
        )

        self._draw_fills()

        self.ax.grid()
        self.ax.set_title(
            "Evolution of annual CO₂ emissions from air transport - Detailed levers of action"
        )
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Annual CO₂ emissions [MtCO₂]")
        self.ax.legend(loc=2, fontsize=6, ncols=2)
        self.ax.set_xlim(self.years[0], self.years[-1])

    def _draw_fills(self):
        # Demand/supply side management
        self.ax.fill_between(
            self.years,
            self.df["co2_emissions_last_historical_year_technology_baseline3"],
            self.df["co2_emissions_last_historical_year_technology"],
            color=colors.LEVER_COLORS["demand"],
            label="Demand/supply side management",
        )

        # Aircraft efficiency: decomposed into sub-levers when available, otherwise
        # a single aggregated band (same as AirTransportCO2EmissionsPlot)
        efficiency_bands = self._efficiency_bands()
        if efficiency_bands is not None:
            upper = self.df.loc[self.years, "co2_emissions_last_historical_year_technology"]
            self._plot_sub_lever_bands(upper, efficiency_bands)
        else:
            self.ax.fill_between(
                self.years,
                self.df["co2_emissions_last_historical_year_technology"],
                self.df["co2_emissions_including_aircraft_efficiency"],
                color="gold",
                label="Aircraft efficiency",
            )

        # Fleet operations and load factor
        self.ax.fill_between(
            self.years,
            self.df["co2_emissions_including_aircraft_efficiency"],
            self.df["co2_emissions_including_load_factor"],
            color=colors.LEVER_OPERATIONS_LOADFACTOR,
            label="Fleet operations and load factor",
        )

        # Aircraft energy: decomposed into sub-levers when available, otherwise
        # a single aggregated band (same as AirTransportCO2EmissionsPlot)
        energy_bands = self._energy_bands()
        if energy_bands is not None:
            upper = self.df.loc[self.years, "co2_emissions_including_load_factor"]
            self._plot_sub_lever_bands(upper, energy_bands)
        else:
            self.ax.fill_between(
                self.years,
                self.df["co2_emissions_including_load_factor"],
                self.df_climate.loc[self.years, "co2_emissions"],
                color="yellowgreen",
                label="Aircraft energy",
            )

        # Carbon offset
        plt.rc("hatch", linewidth=4)
        self.ax.fill_between(
            self.years,
            self.df_climate.loc[self.years, "co2_emissions"],
            self.df_climate.loc[self.years, "co2_emissions"] - self.df["carbon_offset"],
            color="white",
            facecolor=colors.LEVER_COLORS["offset"],
            hatch="//",
            label="Carbon offset",
        )

    def _update_plot_elements(self):
        self.line_co2_emissions_no_action.set_ydata(
            self.df.loc[
                self.prospective_years, "co2_emissions_last_historical_year_technology_baseline3"
            ]
        )

        self.line_co2_emissions.set_ydata(
            self.df_climate.loc[self.prospective_years, "co2_emissions"]
        )

        self.line_co2_emissions_offset.set_ydata(
            self.df_climate.loc[self.prospective_years, "co2_emissions"]
            - self.df.loc[self.prospective_years, "carbon_offset"]
        )

        for collection in self.ax.collections:
            collection.remove()

        self._draw_fills()
        self.fig.canvas.draw()


class AirTransportCO2EmissionsGroupedPlot(AirTransportCO2EmissionsDetailedPlot):
    """
    Coarse-granularity variant of AirTransportCO2EmissionsDetailedPlot: the
    aircraft-efficiency lever is decomposed per fleet category (rather than per
    individual aircraft) and the aircraft-energy lever per fuel origin family
    (biofuels / electrofuels & e-hydrogen / fossil-derived, rather than per
    pathway). For a mixed choice, use AirTransportCO2EmissionsDetailedPlot
    directly with the ``efficiency_granularity`` / ``energy_granularity`` keywords.
    """

    def __init__(
        self,
        process,
        figsize=None,
        efficiency_granularity="category",
        energy_granularity="origin",
        **kwargs,
    ):
        super().__init__(
            process,
            figsize=figsize,
            efficiency_granularity=efficiency_granularity,
            energy_granularity=energy_granularity,
            **kwargs,
        )


class AirTransportCO2EmissionsPerMarketPlot(SingleScenarioPlot):
    """
    Small-multiples decomposition of the CO2 levers of action per market.

    One panel per lever of action (aircraft efficiency, fleet operations, load
    factor, aircraft energy); within each panel the annual CO2 contribution of
    every market is drawn as a signed line (positive = emissions avoided w.r.t.
    the last-historical-year technology), together with the cross-market-mix
    residual. Market colours are kept consistent across panels.

    A faceted layout is used on purpose: several per-market contributions turn
    negative over time, for which a single stacked chart would be order-dependent
    and misleading. Requires DetailedCo2EmissionsPerMarket.
    """

    # (lever key as produced by DetailedCo2EmissionsPerMarket, panel title)
    _LEVERS = [
        ("efficiency", "Aircraft efficiency"),
        ("operations", "Fleet operations"),
        ("loadfactor", "Load factor"),
        ("energy", "Aircraft energy"),
    ]

    required_outputs = [market_lever_column("efficiency", MARKET_CROSS_MIX)]

    def __init__(self, process, figsize=None, **kwargs):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize, **kwargs)

    def _get_default_figsize(self):
        return (plot_1_x, plot_1_y)

    def _ordered_market_ids(self):
        """Canonical market order: passenger markets (config order) then freight."""
        markets = self.process.markets
        return [m.id for m in markets.get(traffic_type="passenger")] + [
            m.id for m in markets.get(traffic_type="freight")
        ]

    def create_plot(self):
        # Replace the single default axes by a 2x2 grid of lever panels.
        self.ax.remove()
        self.facet_axes = self.fig.subplots(2, 2).flatten()
        self._draw_facets()

    def _draw_facets(self):
        for legend in list(self.fig.legends):
            legend.remove()

        market_ids = self._ordered_market_ids()
        # Validated categorical palette, constant per market across panels.
        market_color = colors.market_colors(market_ids)
        names = market_lever_names(self.process.markets)
        years = self.prospective_years
        last_year = years[-1]

        for ax, (lever, title) in zip(self.facet_axes, self._LEVERS):
            ax.clear()
            ax.axhline(0, color="black", linewidth=0.6)
            for mid in market_ids:
                column = names.get((lever, mid))
                if column is None or column not in self.df.columns:
                    continue
                series = self.df.loc[years, column]
                ax.plot(
                    years,
                    series,
                    color=market_color[mid],
                    label=mid.replace("_", " ").title(),
                )
                # Direct end-label: secondary (non-colour) encoding of identity,
                # required alongside the market palette for CVD/contrast safety.
                ax.annotate(
                    mid.replace("_", " ").title(),
                    xy=(last_year, series.loc[last_year]),
                    xytext=(3, 0),
                    textcoords="offset points",
                    va="center",
                    fontsize=6,
                    color=market_color[mid],
                    clip_on=False,
                )
            cross_column = names.get((lever, MARKET_CROSS_MIX))
            if cross_column in self.df.columns:
                ax.plot(
                    years,
                    self.df.loc[years, cross_column],
                    color=colors.NEUTRAL,
                    linestyle=":",
                    label="Cross-market mix",
                )
            ax.set_title(title, fontsize=9)
            ax.grid(True, alpha=0.3)
            ax.tick_params(labelsize=7)

        self.fig.suptitle("CO₂ levers of action decomposed per market", fontsize=11)
        self.fig.supxlabel("Year", fontsize=8)
        self.fig.supylabel("Annual CO₂ avoided [MtCO₂]", fontsize=8)
        handles, labels = self.facet_axes[0].get_legend_handles_labels()
        if handles:
            self.fig.legend(
                handles,
                labels,
                loc="outside lower center",
                ncols=min(len(labels), 5),
                fontsize=7,
            )

    def _update_plot_elements(self):
        self._draw_facets()
        self.fig.canvas.draw()


class AirTransportClimateImpactsPlot(SingleScenarioPlot):
    required_outputs = [
        "co2_erf",
        "co2_h2o_erf",
        "co2_h2o_nox_erf",
        "co2_h2o_nox_contrails_erf",
        "aerosol_erf",
        "total_erf",
    ]

    def __init__(self, process, figsize=None, **kwargs):
        figsize = figsize or self._get_default_figsize()
        super().__init__(process, figsize, **kwargs)

    def _get_default_figsize(self):
        return (plot_1_x, plot_1_y)

    def create_plot(self):
        (self.line_co2_erf,) = self.ax.plot(
            self.years,
            self.df_climate.loc[self.years, "co2_erf"],
            color="black",
            linestyle="--",
            linewidth=1,
        )

        (self.line_co2_h2o_erf,) = self.ax.plot(
            self.years,
            self.df_climate.loc[self.years, "co2_h2o_erf"],
            color="black",
            linestyle="--",
            linewidth=1,
        )

        (self.line_co2_h2o_nox_erf,) = self.ax.plot(
            self.years,
            self.df_climate.loc[self.years, "co2_h2o_nox_erf"],
            color="black",
            linestyle="--",
            linewidth=1,
        )

        (self.line_co2_h2o_nox_contrails_erf,) = self.ax.plot(
            self.years,
            self.df_climate.loc[self.years, "co2_h2o_nox_contrails_erf"],
            linestyle="None",
        )

        (self.line_aerosol_erf,) = self.ax.plot(
            self.years,
            self.df_climate.loc[self.years, "aerosol_erf"],
            linestyle="None",
        )

        self.ax.plot(
            self.historic_years,
            self.df_climate.loc[self.historic_years, "total_erf"],
            color="black",
            linestyle="-",
            label="Net ERF - History",
            linewidth=4,
        )

        (self.line_total_erf,) = self.ax.plot(
            self.prospective_years,
            self.df_climate.loc[self.prospective_years, "total_erf"],
            color="green",
            linestyle="-",
            label="Net ERF - Projections",
            linewidth=4,
        )

        # Fill between
        self.ax.fill_between(
            self.years,
            np.zeros(len(self.years)),
            self.df_climate.loc[self.years, "co2_erf"],
            color="tomato",
            label="CO2",
        )

        self.ax.fill_between(
            self.years,
            self.df_climate.loc[self.years, "co2_erf"],
            self.df_climate.loc[self.years, "co2_h2o_erf"],
            color="lightskyblue",
            label="H2O",
        )

        self.ax.fill_between(
            self.years,
            self.df_climate.loc[self.years, "co2_h2o_erf"],
            self.df_climate.loc[self.years, "co2_h2o_nox_erf"],
            color="yellowgreen",
            label="NOx",
        )

        self.ax.fill_between(
            self.years,
            self.df_climate.loc[self.years, "co2_h2o_nox_erf"],
            self.df_climate.loc[self.years, "co2_h2o_nox_contrails_erf"],
            color="gold",
            label="Contrails",
        )

        self.ax.fill_between(
            self.years,
            np.zeros(len(self.years)),
            self.df_climate.loc[self.years, "aerosol_erf"],
            color="darkblue",
            label="Aerosols",
        )

        self.ax.grid()
        self.ax.set_title(
            "Evolution of climate impacts (via effective radiative forcing) from air transport"
        )
        self.ax.set_xlabel("Year")
        self.ax.set_ylabel("Effective radiative forcing [W/m²]")
        self.ax.legend(loc=2)
        self.ax.set_xlim(self.years[0], self.years[-1])

    def _update_plot_elements(self):
        self.line_co2_erf.set_ydata(self.df_climate.loc[self.years, "co2_erf"])

        self.line_co2_h2o_erf.set_ydata(self.df_climate.loc[self.years, "co2_h2o_erf"])

        self.line_co2_h2o_nox_erf.set_ydata(self.df_climate.loc[self.years, "co2_h2o_nox_erf"])

        self.line_co2_h2o_nox_contrails_erf.set_ydata(
            self.df_climate.loc[self.years, "co2_h2o_nox_contrails_erf"]
        )

        self.line_aerosol_erf.set_ydata(self.df_climate.loc[self.years, "aerosol_erf"])

        self.line_total_erf.set_ydata(self.df_climate.loc[self.prospective_years, "total_erf"])

        for collection in self.ax.collections:
            collection.remove()

        # Fill between
        self.ax.fill_between(
            self.years,
            np.zeros(len(self.years)),
            self.df_climate.loc[self.years, "co2_erf"],
            color="tomato",
            label="CO2",
        )

        self.ax.fill_between(
            self.years,
            self.df_climate.loc[self.years, "co2_erf"],
            self.df_climate.loc[self.years, "co2_h2o_erf"],
            color="lightskyblue",
            label="H2O",
        )

        self.ax.fill_between(
            self.years,
            self.df_climate.loc[self.years, "co2_h2o_erf"],
            self.df_climate.loc[self.years, "co2_h2o_nox_erf"],
            color="yellowgreen",
            label="NOx",
        )

        self.ax.fill_between(
            self.years,
            self.df_climate.loc[self.years, "co2_h2o_nox_erf"],
            self.df_climate.loc[self.years, "co2_h2o_nox_contrails_erf"],
            color="gold",
            label="Contrails",
        )

        self.ax.fill_between(
            self.years,
            np.zeros(len(self.years)),
            self.df_climate.loc[self.years, "aerosol_erf"],
            color="darkblue",
            label="Aerosols",
        )
        self.fig.canvas.draw()
