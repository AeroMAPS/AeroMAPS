import matplotlib.pyplot as plt
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
DEFAULT_LINESTYLES = ['-', '--', '-.', ':']

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
                 scenario_groups=None, fig=None, ax=None, legend=True, colors=None):
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
        """
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
        elif isinstance(legend, str):
            handles, labels = self.ax.get_legend_handles_labels()
            if handles:
                self.ax.legend(handles, labels, loc=legend)

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

    @abstractmethod
    def _update_plot_elements(self):
        """
        Update plot elements with new data.

        This method should be implemented by subclasses to update
        line data, bar heights, etc. for all scenarios.
        """
        pass

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
        pd.Series or None
            Aggregated energy consumption, or *None* if no matching columns
            were found in *df*.
        """
        total = None
        for pathway in pathways:
            col = f"{pathway.name}_energy_consumption"
            if col in df.columns:
                values = df.loc[years, col].fillna(0)
                total = values if total is None else total + values
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

