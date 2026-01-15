import matplotlib.pyplot as plt
from abc import ABC, abstractmethod


class SingleScenarioPlot(ABC):
    """
    Base class for plots involving a single aeromaps scenario.

    This class handles common initialization and update patterns for plots
    that visualize data from a single process/scenario.
    """

    def __init__(self, process, figsize=None):
        """
        Initialize the plot with data from a process.

        Parameters
        ----------
        process : Process
            The process object containing the data to plot
        figsize : tuple, optional
            Figure size as (width, height). If None, uses default from subclass
        """
        # Extract data from process
        self._extract_data(process.data)

        # Create figure and axes
        figsize = figsize or self._get_default_figsize()
        self.fig, self.ax = plt.subplots(figsize=figsize)

        # Configure canvas
        self._configure_canvas()

        # Create the actual plot (implemented by subclass)
        self.create_plot()

    def _extract_data(self, data):
        """
        Extract and store data attributes from the process data dictionary.

        Parameters
        ----------
        data : dict
            Data dictionary from the process
        """
        self.df = data.get("vector_outputs")
        self.df_climate = data.get("climate_outputs")
        self.float_outputs = data.get("float_outputs")

        years = data.get("years", {})
        self.years = years.get("full_years")
        self.historic_years = years.get("historic_years")
        self.prospective_years = years.get("prospective_years")

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
        the specific plot visualization.
        """
        pass

    def update(self, data):
        """
        Update the plot with new data.

        Parameters
        ----------
        data : dict
            New data dictionary from the process
        """
        # Extract new data
        self._extract_data(data)

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
        line data, bar heights, etc.
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

    def _set_x_limits(self):
        """Set x-axis limits to span the full years range."""
        if self.years is not None and len(self.years) > 0:
            self.ax.set_xlim(self.years[0], self.years[-1])