import matplotlib.pyplot as plt
from abc import ABC, abstractmethod
import warnings
import itertools


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
                 scenario_groups=None):
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
        """
        # Set instance-level required_outputs (override class default if provided)
        if required_outputs is not None:
            self.required_outputs = required_outputs
        else:
            # Use class attribute - create instance copy to avoid mutation
            self.required_outputs = self.__class__.required_outputs.copy() if self.__class__.required_outputs else []
        
        # Store scenario grouping configuration
        self.scenario_groups = scenario_groups
        self._setup_scenario_styles(processes, scenario_groups)
        
        # Store processes
        self.processes = processes
        
        # Validate and filter processes if requested
        if check_outputs and self.required_outputs:
            self.processes = self._filter_processes_by_outputs(self.required_outputs)

        # Extract data from all processes
        self._extract_all_data()

        # Create figure and axes
        figsize = figsize or self._get_default_figsize()
        self.fig, self.ax = plt.subplots(figsize=figsize)

        # Configure canvas
        self._configure_canvas()

        # Create the actual plot (implemented by subclass)
        self.create_plot()
    
    def _setup_scenario_styles(self, processes, scenario_groups):
        """
        Setup color and line style mapping for scenarios.
        
        Parameters
        ----------
        processes : list or dict
            Process objects
        scenario_groups : dict or None
            Scenario grouping configuration
        """
        self.scenario_styles = {}
        
        # Get scenario names
        if isinstance(processes, dict):
            scenario_names = list(processes.keys())
        else:
            scenario_names = [f"scenario_{i}" for i in range(len(processes))]
        
        if scenario_groups is None:
            # No grouping - each scenario gets its own color, solid line style
            color_cycle = itertools.cycle(DEFAULT_COLORS)
            for scenario_name in scenario_names:
                self.scenario_styles[scenario_name] = {
                    'color': next(color_cycle),
                    'linestyle': '-',
                    'group': None
                }
        else:
            # With grouping - assign colors to groups, line styles within groups
            color_cycle = itertools.cycle(DEFAULT_COLORS)
            group_colors = {}
            
            # Assign color to each group
            for group_name in scenario_groups.keys():
                group_colors[group_name] = next(color_cycle)
            
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
        
        if "vector_outputs" in data and data["vector_outputs"] is not None:
            df = data["vector_outputs"]
            for output in required_outputs:
                if output not in df.columns:
                    missing.append(output)
        else:
            # No vector_outputs at all
            missing = required_outputs.copy()
        
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

    def _configure_canvas(self):
        """Configure matplotlib canvas properties."""
        self.fig.canvas.header_visible = False
        self.fig.canvas.toolbar_position = "bottom"
        self.fig.tight_layout()

    @abstractmethod
    def _get_default_figsize(self):
        """
        Return the default figure size for this plot.

        Returns
        -------
        tuple
            Figure size as (width, height)
        """
        pass

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