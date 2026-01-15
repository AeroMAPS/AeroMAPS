import matplotlib.pyplot as plt
from abc import ABC, abstractmethod


class MultiScenarioPlot(ABC):
    """
    Base class for plots involving multiple aeromaps scenarios.

    This class handles common initialization and update patterns for plots
    that compare or visualize data from multiple processes/scenarios.
    """

    def __init__(self, processes, figsize=None):
        """
        Initialize the plot with data from multiple processes.

        Parameters
        ----------
        processes : list or dict
            List or dictionary of process objects containing the data to plot
        figsize : tuple, optional
            Figure size as (width, height). If None, uses default from subclass
        """
        # Store processes
        self.processes = processes

        # Extract data from all processes
        self._extract_all_data()

        # Create figure and axes
        figsize = figsize or self._get_default_figsize()
        self.fig, self.ax = plt.subplots(figsize=figsize)

        # Configure canvas
        self._configure_canvas()

        # Create the actual plot (implemented by subclass)
        self.create_plot()

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