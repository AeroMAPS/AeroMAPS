import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
import warnings
import itertools

from aeromaps.plots.single_scenario_plot import plot_1_x, plot_1_y


# Default color palette for scenario groups
DEFAULT_COLORS = [
    '#1f77b4',  # blue
    '#ff7f0e',  # orange
    '#2ca02c',  # green
    '#d62728',  # red
    '#9467bd',  # purple
    '#8c564b',  # brown
    '#e377c2',  # pink
    '#7f7f7f',  # gray
    '#bcbd22',  # olive
    '#17becf',  # cyan
]

# Default line styles for scenarios within a group
DEFAULT_LINESTYLES = ['-', ':', '-.', '--']

# Color palette for energy origins (used by energy/fuel supply plots)
ENERGY_ORIGIN_COLORS = {
    'fossil': '#d62728',      # red
    'biomass': '#2ca02c',     # green
    'electricity': '#1f77b4', # blue
}

# Fallback colors when energy_origin is not in the map above
ENERGY_ORIGIN_FALLBACK_COLORS = [
    '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
]


class MultiScenarioPlot(ABC):
    """
    Base class for plots involving multiple aeromaps scenarios.

    This class handles common initialization and update patterns for plots
    that compare or visualize data from multiple processes/scenarios.
    
    Attributes
    ----------
    required_outputs : list of str
        List of output field names required for this plot. Subclasses should
        override this to specify their data requirements.
    """
    
    # Default: no required outputs (subclasses should override)
    required_outputs = []

    def __init__(self, processes, figsize=None, check_outputs=True, required_outputs=None,
                 scenario_groups=None, fig=None, ax=None, legend=True, colors=None,
                 group_display="lines", group_envelope_middle="median",
                 group_envelope_alpha=0.25):
        """
        Initialize the plot with data from multiple processes.

        Parameters
        ----------
        processes : list or dict
            List or dictionary of process objects containing the data to plot
        figsize : tuple, optional
            Figure size as (width, height). If None, uses default from subclass
        check_outputs : bool, optional
            Whether to validate that required outputs are present in all scenarios.
            Default is True. Scenarios with missing outputs will be excluded with warnings.
        required_outputs : list of str, optional
            List of output field names required for this plot. If provided,
            overrides the class-level required_outputs. If None, uses class default.
        scenario_groups : dict, optional
            Dictionary mapping group names to lists of scenario names. Scenarios
            within a group will share the same color but use different line styles.
            Example: {"Baseline": ["s1", "s2"], "Optimistic": ["s3", "s4"]}
            If None, each scenario gets its own color.
        fig : matplotlib.figure.Figure, optional
            Existing figure to draw into. If provided together with ``ax``,
            no new figure/axes are created.
        ax : matplotlib.axes.Axes, optional
            Existing axes to draw into. Must be provided together with ``fig``.
        legend : bool or str, optional
            Controls the legend. ``True`` (default) keeps the legend as created
            by the plot. ``False`` hides it. A string value (e.g. ``"upper right"``)
            moves the legend to the given location.
        colors : list or dict, optional
            Custom colors for scenarios.  Two forms are accepted:

            * **list** – one color per scenario, in the same order as the
              scenarios appear in *processes* (dict order / list order).
              E.g. ``["red", "blue", "#2ca02c"]``.
            * **dict** – maps *group names* to colors when *scenario_groups*
              is used.  E.g. ``{"Baseline": "steelblue", "Optimistic": "green"}``.
              All scenarios within a group share that group's color.

            If ``None`` (default) the built-in ``DEFAULT_COLORS`` palette is used.
        group_display : str, optional
            How to render each scenario group. ``"lines"`` (default) draws one
            line per scenario (current behaviour). ``"envelope"`` draws a single
            ``fill_between`` band between the min and max of the group's
            scenarios at each year, plus a single middle line. Singleton groups
            always fall back to a single line.
        group_envelope_middle : str or dict, optional
            Selects the middle line in envelope mode.

            * ``"median"`` (default) – pointwise median across the group.
            * ``"mean"`` – pointwise mean across the group.
            * ``dict`` of ``{group_name: scenario_name}`` – use the given
              scenario as the middle line for that group. Groups omitted from
              the dict fall back to ``"median"``.
        group_envelope_alpha : float, optional
            Transparency of the ``fill_between`` band in envelope mode.
            Default ``0.25``.
        """
        if group_display not in ("lines", "envelope"):
            raise ValueError(
                f"group_display must be 'lines' or 'envelope', got {group_display!r}"
            )
        self.group_display = group_display
        self.group_envelope_middle = group_envelope_middle
        self.group_envelope_alpha = group_envelope_alpha

        # Store legend preference
        self._legend_setting = legend
        # Set instance-level required_outputs (override class default if provided)
        if required_outputs is not None:
            self.required_outputs = required_outputs
        else:
            # Use class attribute - create instance copy to avoid mutation
            self.required_outputs = self.__class__.required_outputs.copy() if self.__class__.required_outputs else []
        
        # Store custom colors
        self._custom_colors = colors

        # Store scenario grouping configuration
        self.scenario_groups = scenario_groups
        
        # Store processes
        self.processes = processes
        
        # Extract pathways_manager from first process (all should have same pathways)
        if isinstance(processes, dict):
            first_process = next(iter(processes.values()))
        else:
            first_process = processes[0] if processes else None
        
        self.pathways_manager = first_process.pathways_manager if first_process and hasattr(first_process, 'pathways_manager') else None
        
        # Validate and filter processes if requested
        if check_outputs and self.required_outputs:
            self.processes = self._filter_processes_by_outputs(self.required_outputs)
        
        # Setup scenario styles AFTER filtering so styles match the actual scenarios being plotted
        self._setup_scenario_styles(self.processes, scenario_groups, colors)

        # Extract data from all processes
        self._extract_all_data()

        # Create figure and axes (or reuse provided ones)
        if fig is not None and ax is not None:
            self.fig = fig
            self.ax = ax
        else:
            figsize = figsize or self._get_default_figsize()
            self.fig, self.ax = plt.subplots(figsize=figsize, layout="constrained")

        # Configure canvas
        self._configure_canvas()

        # Create the actual plot (implemented by subclass)
        self.create_plot()

        # Apply legend settings after plot creation
        self._apply_legend_setting()

    def _setup_scenario_styles(self, processes, scenario_groups, colors=None):
        """
        Setup color and line style mapping for scenarios.
        
        Parameters
        ----------
        processes : list or dict
            Process objects
        scenario_groups : dict or None
            Scenario grouping configuration
        colors : list or dict or None
            Custom colors.  A list assigns one color per scenario (in order);
            a dict maps group names to colors when *scenario_groups* is used.
        """
        self.scenario_styles = {}
        
        # Get scenario names
        if isinstance(processes, dict):
            scenario_names = list(processes.keys())
        else:
            scenario_names = [f"scenario_{i}" for i in range(len(processes))]
        
        if scenario_groups is None:
            # No grouping - each scenario gets its own color, solid line style
            if isinstance(colors, list):
                # Use provided list, cycling if too short
                color_cycle = itertools.cycle(colors)
            else:
                color_cycle = itertools.cycle(DEFAULT_COLORS)
            for scenario_name in scenario_names:
                self.scenario_styles[scenario_name] = {
                    'color': next(color_cycle),
                    'linestyle': '-',
                    'group': None
                }
        else:
            # With grouping - assign colors to groups, line styles within groups
            # Build group_colors from custom dict, list, or default palette
            group_names = list(scenario_groups.keys())
            if isinstance(colors, dict):
                # Explicit per-group colors; fall back to default for missing groups
                default_cycle = itertools.cycle(DEFAULT_COLORS)
                group_colors = {}
                for group_name in group_names:
                    group_colors[group_name] = colors.get(group_name, next(default_cycle))
            elif isinstance(colors, list):
                # One color per group in order
                color_cycle = itertools.cycle(colors)
                group_colors = {g: next(color_cycle) for g in group_names}
            else:
                color_cycle = itertools.cycle(DEFAULT_COLORS)
                group_colors = {g: next(color_cycle) for g in group_names}
            
            # Assign styles to scenarios within groups
            for group_name, group_scenarios in scenario_groups.items():
                color = group_colors[group_name]
                linestyle_cycle = itertools.cycle(DEFAULT_LINESTYLES)
                
                for scenario_name in group_scenarios:
                    if scenario_name in scenario_names:
                        self.scenario_styles[scenario_name] = {
                            'color': color,
                            'linestyle': next(linestyle_cycle),
                            'group': group_name
                        }
            
            # Handle ungrouped scenarios (if any)
            grouped_scenarios = set()
            for group_scenarios in scenario_groups.values():
                grouped_scenarios.update(group_scenarios)
            
            ungrouped = set(scenario_names) - grouped_scenarios
            if ungrouped:
                if isinstance(colors, list):
                    ungrouped_color_cycle = itertools.cycle(colors[len(scenario_groups):] or colors)
                else:
                    ungrouped_color_cycle = itertools.cycle(DEFAULT_COLORS[len(scenario_groups):])
                for scenario_name in ungrouped:
                    self.scenario_styles[scenario_name] = {
                        'color': next(ungrouped_color_cycle),
                        'linestyle': '-',
                        'group': None
                    }
    
    def get_scenario_style(self, scenario_name):
        """
        Get the color and line style for a scenario.
        
        Parameters
        ----------
        scenario_name : str
            Name of the scenario
            
        Returns
        -------
        dict
            Dictionary with 'color', 'linestyle', and 'group' keys
        """
        if scenario_name in self.scenario_styles:
            return self.scenario_styles[scenario_name]
        else:
            # Default style if not found
            return {'color': DEFAULT_COLORS[0], 'linestyle': '-', 'group': None}

    # ------------------------------------------------------------------
    # Group-aware drawing helpers (envelope mode support)
    # ------------------------------------------------------------------

    def _iter_scenario_groups(self):
        """
        Yield ``(group_name, group_color, [scenario_name, ...])`` for every
        scenario group present in ``self.scenario_styles``.

        Groups declared via ``scenario_groups`` come first in declaration
        order; any ungrouped scenarios follow as singleton groups labelled
        by the scenario name itself. Singletons are intentionally yielded
        so that :meth:`_draw_group_curve` can fall back to a plain line
        when envelope mode is requested but the group has only one member.
        """
        seen = set()

        if self.scenario_groups:
            for group_name, group_scenarios in self.scenario_groups.items():
                members = [s for s in group_scenarios if s in self.scenario_styles]
                if members:
                    group_color = self.scenario_styles[members[0]]['color']
                    seen.update(members)
                    yield group_name, group_color, members

        # Ungrouped scenarios become singleton groups
        for scenario_name, style in self.scenario_styles.items():
            if scenario_name not in seen:
                yield scenario_name, style['color'], [scenario_name]

    def _resolve_middle_index(self, group_name, scenario_names):
        """
        Resolve the index (into ``scenario_names``) of the scenario chosen
        as the envelope's middle line, or ``None`` if the middle should be
        computed pointwise (median / mean).

        Parameters
        ----------
        group_name : str
            Name of the scenario group being drawn.
        scenario_names : list of str
            Scenario names contained in the group, in the order they appear
            in the data matrix.

        Returns
        -------
        int or None
            Position in ``scenario_names`` of the chosen middle scenario,
            or ``None`` if the middle should be derived pointwise.
        """
        mode = self.group_envelope_middle
        if isinstance(mode, dict):
            picked = mode.get(group_name)
            if picked is None:
                return None  # Fall back to median for unspecified groups
            if picked not in scenario_names:
                raise KeyError(
                    f"group_envelope_middle[{group_name!r}] = {picked!r} "
                    f"is not a scenario in group {group_name!r} "
                    f"(group members: {scenario_names})"
                )
            return scenario_names.index(picked)
        if mode in ("median", "mean"):
            return None
        raise ValueError(
            f"group_envelope_middle must be 'median', 'mean' or a dict, "
            f"got {mode!r}"
        )

    def _scenario_xy(self, scenario_name, data):
        """
        Return ``(x, y)`` for one scenario.

        Default implementation reads a single column based on class attributes
        (so simple line-plot subclasses can avoid overriding anything):

        * ``column_name`` (required) – column to plot.
        * ``data_source``  – ``"df"`` (default) or ``"df_climate"``.
        * ``years_source`` – ``"years"`` (default) or ``"prospective_years"``.
        * ``y_scale``      – multiplier applied to the y values (default ``1.0``).

        Column presence is guaranteed by ``required_outputs`` +
        ``_filter_processes_by_outputs`` (which runs before ``create_plot``),
        so no per-scenario existence check is needed here.

        Subclasses can override this for derived/multi-column or
        pathway-aggregated series.
        """
        column = getattr(self, "column_name", None)
        if column is None:
            raise NotImplementedError(
                f"{type(self).__name__} must either set `column_name` "
                f"or override _scenario_xy()."
            )
        df = data[getattr(self, "data_source", "df")]
        x = data[getattr(self, "years_source", "years")]
        return x, df.loc[x, column] * getattr(self, "y_scale", 1.0)

    def _plot_grouped_series(self, *, linewidth=2):
        """
        Draw one curve per scenario group on ``self.ax``.

        Routes ``self._scenario_xy(scenario_name, data)`` through
        :meth:`_draw_group_curve`, so the same call honours both ``"lines"``
        and ``"envelope"`` display modes. List-mode scenarios (no scenario
        names) are drawn as individual lines labelled ``"Scenario N"``.

        ``_scenario_xy`` is expected to always return a valid ``(x, y)``
        pair; ``required_outputs`` validation already filters scenarios
        missing the relevant column before ``create_plot`` runs.

        Subclasses normally only need to set ``column_name`` (and optionally
        ``y_scale`` / ``data_source`` / ``years_source``) or override
        :meth:`_scenario_xy`.
        """
        if isinstance(self.scenario_data, dict):
            for group_name, _color, scenario_names in self._iter_scenario_groups():
                series = {}
                x = None
                for scenario_name in scenario_names:
                    x, y = self._scenario_xy(scenario_name, self.scenario_data[scenario_name])
                    series[scenario_name] = y
                self._draw_group_curve(group_name, x, series, linewidth=linewidth)
        else:
            for idx, data in enumerate(self.scenario_data):
                scenario_name = f"scenario_{idx}"
                x, y = self._scenario_xy(scenario_name, data)
                style = self.get_scenario_style(scenario_name)
                self.ax.plot(
                    x, y,
                    label=f"Scenario {idx+1}",
                    color=style['color'],
                    linestyle=style['linestyle'],
                    linewidth=linewidth,
                )

    def _draw_group_curve(self, group_name, x, series_by_scenario, *,
                          label=None, linewidth=2):
        """
        Draw one scenario group on ``self.ax`` honouring ``self.group_display``.

        In ``"lines"`` mode this reproduces the per-scenario ``ax.plot`` calls
        that subclasses used to make directly. In ``"envelope"`` mode it draws
        a ``fill_between(min, max)`` band plus a single middle line; groups
        with only one scenario fall back to a single line.

        Parameters
        ----------
        group_name : str
            Name of the scenario group; used as the legend label in envelope
            mode (unless ``label`` is provided).
        x : array-like
            Shared x-axis values for every scenario in the group.
        series_by_scenario : dict
            Mapping ``{scenario_name: y_values}`` with one entry per scenario
            in the group. Every value must have length ``len(x)``.
        label : str, optional
            Override the legend label in envelope mode. Ignored in lines mode
            (each scenario gets its own label).
        linewidth : float, optional
            Line width passed to ``ax.plot``. Default ``2``.
        """
        if not series_by_scenario:
            return

        scenario_names = list(series_by_scenario.keys())

        if self.group_display == "lines" or len(scenario_names) == 1:
            for scenario_name, y in series_by_scenario.items():
                style = self.get_scenario_style(scenario_name)
                self.ax.plot(
                    x, y,
                    label=scenario_name,
                    color=style['color'],
                    linestyle=style['linestyle'],
                    linewidth=linewidth,
                )
            return

        # Envelope mode with >=2 scenarios
        group_color = self.scenario_styles[scenario_names[0]]['color']
        arr = np.column_stack([np.asarray(series_by_scenario[s], dtype=float)
                               for s in scenario_names])
        y_min = np.nanmin(arr, axis=1)
        y_max = np.nanmax(arr, axis=1)

        picked = self._resolve_middle_index(group_name, scenario_names)
        if picked is None:
            if self.group_envelope_middle == "mean":
                y_mid = np.nanmean(arr, axis=1)
            else:
                y_mid = np.nanmedian(arr, axis=1)
        else:
            y_mid = arr[:, picked]

        self.ax.fill_between(
            x, y_min, y_max,
            color=group_color,
            alpha=self.group_envelope_alpha,
            linewidth=0,
        )
        # Always resolve to a concrete scenario index (closest to computed median/mean
        # when group_envelope_middle is "median"/"mean", or the user-picked index).
        if picked is None:
            diffs = [np.nansum(np.abs(arr[:, i] - y_mid)) for i in range(arr.shape[1])]
            effective_picked = int(min(range(len(diffs)), key=lambda i: diffs[i]))
        else:
            effective_picked = picked

        mid_scenario = scenario_names[effective_picked]
        mid_ls = self.get_scenario_style(mid_scenario)['linestyle']

        # Background lines: all scenarios except the last and the mid scenario,
        # each using its pre-assigned index-based linestyle from scenario_styles.
        for scenario_name in scenario_names[:-1]:
            if scenario_name == mid_scenario:
                continue
            style = self.get_scenario_style(scenario_name)
            self.ax.plot(
                x, series_by_scenario[scenario_name],
                color=group_color,
                linestyle=style['linestyle'],
                linewidth=linewidth,
            )
        # y_mid uses the mid scenario's pre-assigned linestyle.
        self.ax.plot(
            x, y_mid,
            color=group_color,
            linestyle=mid_ls,
            linewidth=linewidth,
        )

    def _filter_processes_by_outputs(self, required_outputs):
        """
        Filter processes to only include those with all required outputs.
        
        Issues warnings for scenarios with missing outputs and excludes them.

        Parameters
        ----------
        required_outputs : list of str
            List of output field names required for the plot

        Returns
        -------
        dict or list
            Filtered processes (same type as input)
            
        Raises
        ------
        ValueError
            If no scenarios have all required outputs
        """
        if isinstance(self.processes, dict):
            filtered = {}
            for scenario_name, process in self.processes.items():
                missing = self._check_missing_outputs(process.data, required_outputs)
                if not missing:
                    filtered[scenario_name] = process
                else:
                    warnings.warn(
                        f"Scenario '{scenario_name}' is missing required outputs: {missing}. "
                        f"It will be excluded from the plot.",
                        UserWarning
                    )
            
            if len(filtered) == 0:
                raise ValueError(
                    f"No scenarios have all required outputs: {required_outputs}"
                )
            
            return filtered
        else:
            # List of processes
            filtered = []
            for idx, process in enumerate(self.processes):
                missing = self._check_missing_outputs(process.data, required_outputs)
                if not missing:
                    filtered.append(process)
                else:
                    warnings.warn(
                        f"Scenario at index {idx} is missing required outputs: {missing}. "
                        f"It will be excluded from the plot.",
                        UserWarning
                    )
            
            if len(filtered) == 0:
                raise ValueError(
                    f"No scenarios have all required outputs: {required_outputs}"
                )
            
            return filtered
    
    def _check_missing_outputs(self, data, required_outputs):
        """
        Check which required outputs are missing from a scenario's data.
        
        Checks in both vector_outputs and climate_outputs, as different
        outputs may be stored in different places.
        
        Parameters
        ----------
        data : dict
            Data dictionary from a process
        required_outputs : list of str
            List of output field names to check for
            
        Returns
        -------
        list of str
            List of missing output names (empty if all present)
        """
        missing = []
        
        # Get the data frames
        vector_df = data.get("vector_outputs")
        climate_df = data.get("climate_outputs")
        
        # Check each required output
        for output in required_outputs:
            found = False
            
            # Check in vector_outputs
            if vector_df is not None and output in vector_df.columns:
                found = True
            
            # Check in climate_outputs
            if climate_df is not None and output in climate_df.columns:
                found = True
            
            if not found:
                missing.append(output)
        
        return missing
    
    @classmethod
    def get_required_outputs(cls):
        """
        Get the list of required outputs for this plot class.
        
        This returns the class-level default. Individual instances may override
        this via the required_outputs parameter in __init__().
        
        Returns
        -------
        list of str
            List of output field names required by this plot class
        """
        return cls.required_outputs
    
    def get_instance_required_outputs(self):
        """
        Get the list of required outputs for this plot instance.
        
        This returns the instance-level required outputs, which may differ
        from the class default if overridden at initialization.
        
        Returns
        -------
        list of str
            List of output field names required by this plot instance
        """
        return self.required_outputs
    
    def _extract_all_data(self):
        """
        Extract and store data from all processes.

        Stores data in dictionaries/lists indexed by process key/index.
        """
        if isinstance(self.processes, dict):
            self.scenario_data = {
                key: self._extract_scenario_data(proc.data)
                for key, proc in self.processes.items()
            }
        else:
            self.scenario_data = [
                self._extract_scenario_data(proc.data)
                for proc in self.processes
            ]

    def _extract_scenario_data(self, data):
        """
        Extract data attributes from a single scenario's data dictionary.

        Parameters
        ----------
        data : dict
            Data dictionary from a process

        Returns
        -------
        dict
            Dictionary containing extracted data fields
        """
        years = data.get("years", {})

        return {
            "df": data.get("vector_outputs"),
            "df_climate": data.get("climate_outputs"),
            "float_outputs": data.get("float_outputs"),
            "years": years.get("full_years"),
            "historic_years": years.get("historic_years"),
            "prospective_years": years.get("prospective_years"),
        }

    def _apply_legend_setting(self):
        """Apply the legend setting configured at initialisation."""
        legend = self._legend_setting
        if legend is False:
            leg = self.ax.get_legend()
            if leg is not None:
                leg.set_visible(False)
            return

        # Two-column legend for envelope mode with groups
        if self.group_display == "envelope" and self.scenario_groups:
            loc = legend if isinstance(legend, str) else "best"
            self._build_two_column_legend(loc=loc)
            return

        if isinstance(legend, str):
            handles, labels = self.ax.get_legend_handles_labels()
            if handles:
                self.ax.legend(handles, labels, loc=legend)

    def _build_two_column_legend(self, loc="best"):
        """
        Build a two-column legend for envelope mode.

        Left column  – one coloured fill patch per scenario group, labeled
                       with just the group name.
        Right column – one grey fill patch labeled ``"s0 to sLast range"``
                       (group name stripped from scenario names), followed by
                       one grey line per plotted variant (all except the last
                       scenario, which is only shown in the fill band).

        Linestyle entries are derived from the first group (linestyles are
        shared across groups by index position). The two columns are
        interleaved so that ``ncols=2`` places them side-by-side.
        """
        all_groups = list(self._iter_scenario_groups())
        if not all_groups:
            return

        # --- Left column: colored patches, one per group ---
        group_handles, group_labels = [], []
        for group_name, _, members in all_groups:
            color = self.scenario_styles[members[0]]['color']
            group_handles.append(
                mpatches.Patch(facecolor=color,
                               alpha=min(1.0, self.group_envelope_alpha + 0.4))
            )
            group_labels.append(group_name)

        # --- Right column: range patch + one line per plotted variant ---
        # Use the first group's member names as canonical variant labels.
        first_group_name, _, first_members = all_groups[0]

        style_handles, style_labels = [], []

        # Range entry (grey fill patch)
        first_unique = self._variant_label(first_group_name, first_members[0])
        last_unique = self._variant_label(first_group_name, first_members[-1])
        style_handles.append(
            mpatches.Patch(facecolor="grey", alpha=self.group_envelope_alpha + 0.15)
        )
        style_labels.append(f"{first_unique} to {last_unique} range")

        # One grey line per plotted variant (all except the last)
        for i, member in enumerate(first_members[:-1]):
            ls = DEFAULT_LINESTYLES[i % len(DEFAULT_LINESTYLES)]
            style_handles.append(
                mlines.Line2D([], [], color="grey", linestyle=ls, linewidth=2)
            )
            style_labels.append(self._variant_label(first_group_name, member))

        # --- Put all group entries first, then all style entries ---
        # matplotlib fills ncols=2 column-major (top-down per column), so
        # [g0, g1, …, gN, s0, s1, …, sN] → col0=[g0..gN], col1=[s0..sN]
        nrows = max(len(group_handles), len(style_handles))
        blank_line = mlines.Line2D([], [], color="none")
        blank_patch = mpatches.Patch(color="none")
        while len(group_handles) < nrows:
            group_handles.append(blank_patch)
            group_labels.append("")
        while len(style_handles) < nrows:
            style_handles.append(blank_line)
            style_labels.append("")

        combined_handles = group_handles + style_handles
        combined_labels = group_labels + style_labels

        self.ax.legend(combined_handles, combined_labels, ncols=2, loc=loc)

    @staticmethod
    def _variant_label(group_name: str, scenario_name: str) -> str:
        """
        Return the unique part of ``scenario_name`` relative to ``group_name``.

        Strips the group name prefix and any leading separators (``-``, ``_``,
        space), then replaces remaining underscores with spaces.

        Examples
        --------
        >>> _variant_label("SSP2", "SSP2-19")   # → "19"
        >>> _variant_label("Baseline", "Baseline_High")  # → "High"
        >>> _variant_label("MyGroup", "other")  # → "other"
        """
        if scenario_name.startswith(group_name):
            suffix = scenario_name[len(group_name):].lstrip('-_ ')
            return suffix.replace('_', ' ') if suffix else scenario_name
        return scenario_name.replace('_', ' ')

    def _configure_canvas(self):
        """Configure matplotlib canvas properties."""
        # These attributes only exist for ipywidgets/jupyter backends
        if hasattr(self.fig.canvas, 'header_visible'):
            self.fig.canvas.header_visible = False
        if hasattr(self.fig.canvas, 'toolbar_position'):
            self.fig.canvas.toolbar_position = "bottom"

    def _get_default_figsize(self):
        """
        Return the default figure size for this plot.

        Returns
        -------
        tuple
            Figure size as (width, height)
        """
        return (plot_1_x, plot_1_y)

    @abstractmethod
    def create_plot(self):
        """
        Create the plot elements (lines, fills, labels, etc.).

        This method should be implemented by subclasses to define
        the specific plot visualization comparing multiple scenarios.
        """
        pass

    def update(self, processes):
        """
        Update the plot with new data from multiple processes.

        Parameters
        ----------
        processes : list or dict
            New list or dictionary of process objects
        """
        # Store new processes
        self.processes = processes

        # Extract new data from all processes
        self._extract_all_data()

        # Update plot elements (implemented by subclass)
        self._update_plot_elements()

        # Clear and redraw fill_between collections
        self._refresh_collections()

        # Refresh the view
        self._refresh_view()

    def _update_plot_elements(self):
        """
        Update plot elements with new data.

        Default implementation clears the axes and re-runs :meth:`create_plot`,
        which is appropriate for every line-style multi-scenario plot.
        Subclasses that use multi-axes (per-scenario subplots) override this
        to clear the whole figure instead.
        """
        self.ax.clear()
        self.create_plot()

    def _refresh_collections(self):
        """Remove all collections (fill_between areas) from the axes."""
        for collection in self.ax.collections:
            collection.remove()

    def _refresh_view(self):
        """Refresh the axes view and redraw the canvas."""
        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()

    def _setup_grid_and_labels(self, title, xlabel, ylabel):
        """
        Configure common plot elements: grid, title, and axis labels.

        Parameters
        ----------
        title : str
            Plot title
        xlabel : str
            X-axis label
        ylabel : str
            Y-axis label
        """
        self.ax.grid()
        self.ax.set_title(title)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)

    def _set_x_limits(self, years):
        """
        Set x-axis limits to span the full years range.

        Parameters
        ----------
        years : array-like
            Array of years to use for x-axis limits
        """
        if years is not None and len(years) > 0:
            self.ax.set_xlim(years[0], years[-1])

    def _get_scenario_keys(self):
        """
        Get the keys/indices for iterating over scenarios.

        Returns
        -------
        list or dict_keys
            Keys for accessing scenarios
        """
        if isinstance(self.scenario_data, dict):
            return self.scenario_data.keys()
        else:
            return range(len(self.scenario_data))

    @staticmethod
    def _aggregate_pathways_energy(df, years, pathways):
        """
        Sum ``{pathway.name}_energy_consumption`` columns for the given pathways.

        Returns a zero-filled Series when no matching column is found, so
        callers can treat the result uniformly without ``None`` handling.

        Parameters
        ----------
        df : pd.DataFrame
            The vector_outputs DataFrame for one scenario.
        years : array-like
            Year index to slice on.
        pathways : list of EnergyCarrierMetadata
            Pathways whose energy consumption columns should be summed.

        Returns
        -------
        pd.Series
            Aggregated energy consumption (zeros if no matching columns were
            present in *df*).
        """
        total = pd.Series(0.0, index=list(years))
        for pathway in pathways:
            col = f"{pathway.name}_energy_consumption"
            if col in df.columns:
                total = total + df.loc[years, col].fillna(0)
        return total

    @staticmethod
    def _get_origin_color(energy_origin, fallback_index=0):
        """Return a colour for an energy origin, falling back to a rotating palette."""
        if energy_origin in ENERGY_ORIGIN_COLORS:
            return ENERGY_ORIGIN_COLORS[energy_origin]
        return ENERGY_ORIGIN_FALLBACK_COLORS[fallback_index % len(ENERGY_ORIGIN_FALLBACK_COLORS)]

    @staticmethod
    def _readable_label(raw_name):
        """Turn a snake_case pathway / origin name into a readable label."""
        return raw_name.replace('_', ' ').title()

