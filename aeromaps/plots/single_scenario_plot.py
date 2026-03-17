import matplotlib.pyplot as plt
from abc import ABC, abstractmethod
import warnings

# Figure sizes
plot_1_x = 8.5
plot_1_y = 4
plot_2_x = 4.5
plot_2_y = 3.4
plot_3_x = 4
plot_3_y = 4


class SingleScenarioPlot(ABC):
    """
    Base class for plots involving a single aeromaps scenario.

    This class handles common initialization and update patterns for plots
    that visualize data from a single process/scenario.
    
    Attributes
    ----------
    required_outputs : list of str
        List of output field names required for this plot. Subclasses should
        override this to specify their data requirements.
    """
    
    # Default: no required outputs (subclasses should override)
    required_outputs = []

    def __init__(self, process, figsize=None, check_outputs=True, required_outputs=None, **kwargs):
        """
        Initialize the plot with data from a process.

        Parameters
        ----------
        process : Process
            The process object containing the data to plot
        figsize : tuple, optional
            Figure size as (width, height). If None, uses default from subclass
        check_outputs : bool, optional
            Whether to validate that required outputs are present in the data.
            Default is True. If False, validation is skipped.
        required_outputs : list of str, optional
            List of output field names required for this plot. If provided,
            overrides the class-level required_outputs. If None, uses class default.
        """
        # Store the process object for access by subclasses
        self.process = process
        
        # Set instance-level required_outputs (override class default if provided)
        if required_outputs is not None:
            self.required_outputs = required_outputs
        else:
            # Use class attribute - create instance copy to avoid mutation
            self.required_outputs = self.__class__.required_outputs.copy() if self.__class__.required_outputs else []
        
        # Validate required outputs if requested
        if check_outputs and self.required_outputs:
            self._validate_required_outputs(process.data)
        
        # Extract data from process
        self._extract_data(process.data)
        self.pathways_manager = process.pathways_manager

        # Create figure and axes
        figsize = figsize or self._get_default_figsize()
        self.fig, self.ax = plt.subplots(
            figsize=figsize, layout='constrained', **kwargs
        )

        # Configure canvas
        self._configure_canvas()

        # Create the actual plot (implemented by subclass)
        self.create_plot()

    def _validate_required_outputs(self, data):
        """
        Validate that all required outputs are present in the data.
        
        Issues warnings for missing outputs but does not raise exceptions,
        allowing plots to attempt rendering even with incomplete data.

        Parameters
        ----------
        data : dict
            Data dictionary from the process
        """
        missing_outputs = []
        
        # Check in vector_outputs
        if "vector_outputs" in data and data["vector_outputs"] is not None:
            df = data["vector_outputs"]
            for output in self.required_outputs:
                if output not in df.columns:
                    missing_outputs.append(output)
        else:
            # No vector_outputs at all
            missing_outputs = self.required_outputs.copy()
        
        if missing_outputs:
            warnings.warn(
                f"{self.__class__.__name__} requires outputs {self.required_outputs} "
                f"but the following are missing: {missing_outputs}. "
                f"The plot may not render correctly.",
                UserWarning
            )
    
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
    
    def _extract_data(self, data):
        """
        Extract and store data attributes from the process data dictionary.

        Parameters
        ----------
        data : dict
            Data dictionary from the process
        """
        self.parameters = data["float_inputs"]
        self.df = data.get("vector_outputs")
        self.df_climate = data.get("climate_outputs")
        self.float_outputs = data.get("float_outputs")

        years = data.get("years", {})
        self.years = years.get("full_years")
        self.historic_years = years.get("historic_years")
        self.prospective_years = years.get("prospective_years")

    def _configure_canvas(self):
        """Configure matplotlib canvas properties."""
        if hasattr(self.fig.canvas, "header_visible"):
            self.fig.canvas.header_visible = False
        if hasattr(self.fig.canvas, "toolbar_position"):
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

        # Clear existing fill_between collections before subclass recreates them
        self._refresh_collections()

        # Update plot elements (implemented by subclass)
        self._update_plot_elements()

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
        """Remove existing collections (fill_between/stackplot areas) from the axes before they are redrawn."""
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