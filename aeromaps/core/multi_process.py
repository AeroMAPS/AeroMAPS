"""Multi-process management for scenario comparison.

This module defines the MultiProcess class that manages multiple AeroMAPS
processes for scenario comparison and multi-scenario plotting.
"""

import logging
import warnings
from typing import Union, List, Dict


logger = logging.getLogger(__name__)


class MultiProcess:
    """
    Manager for multiple AeroMAPS processes to enable scenario comparison.
    
    This class provides a unified interface to work with multiple computed
    processes, enabling multi-scenario plotting and comparison while
    handling cases where different scenarios may have different outputs.
    
    Parameters
    ----------
    processes : dict or list
        Dictionary with scenario names as keys and process objects as values,
        or a list of process objects
    """
    
    def __init__(self, processes: Union[Dict, List]):
        """
        Initialize the multi-process manager.
        
        Parameters
        ----------
        processes : dict or list
            Dictionary mapping scenario names to process objects,
            or list of process objects
        """
        if isinstance(processes, list):
            # Convert list to dict with numeric keys
            self.processes = {f"scenario_{i}": proc for i, proc in enumerate(processes)}
        elif isinstance(processes, dict):
            self.processes = processes
        else:
            raise TypeError("processes must be a dict or list")
        
        if len(self.processes) == 0:
            raise ValueError("At least one process must be provided")
        
        # Import available plots - done here to avoid circular imports
        from aeromaps.plots.multi_scenario import available_multi_plots
        self._available_plots = available_multi_plots
    
    def compute_all(self):
        """
        Compute all processes in the multi-process manager.
        
        This method iterates through all managed processes and calls their
        compute() method. This is a convenience method to avoid having to
        compute each process individually before creating multi-scenario plots.
        
        Examples
        --------
        >>> multi = create_multi_process({"s1": proc1, "s2": proc2})
        >>> multi.compute_all()  # Computes both proc1 and proc2
        >>> multi.plot("co2_emissions_comparison")
        """
        for scenario_name, process in self.processes.items():
            logger.info(f"Computing scenario: {scenario_name}")
            process.compute()
    
    def list_available_plots(self) -> List[str]:
        """
        List the names of available multi-scenario plots.
        
        Returns
        -------
        list of str
            List of plot names that can be used with the plot() method
        """
        return list(self._available_plots.keys())
    
    def _check_required_outputs(self, required_outputs: List[str]) -> Dict[str, bool]:
        """
        Check which scenarios have all required outputs.
        
        Parameters
        ----------
        required_outputs : list of str
            List of output field names required for the plot
            
        Returns
        -------
        dict
            Dictionary mapping scenario names to boolean indicating
            if all required outputs are present
        """
        scenario_availability = {}
        
        for scenario_name, process in self.processes.items():
            has_all = True
            missing = []
            
            for output in required_outputs:
                # Check in vector_outputs
                if "vector_outputs" in process.data:
                    df = process.data["vector_outputs"]
                    if output not in df.columns:
                        has_all = False
                        missing.append(output)
                else:
                    has_all = False
                    missing.append(output)
            
            scenario_availability[scenario_name] = has_all
            
            if not has_all:
                warnings.warn(
                    f"Scenario '{scenario_name}' is missing required outputs: {missing}. "
                    f"It will be excluded from the plot.",
                    UserWarning
                )
        
        return scenario_availability
    
    def _filter_processes(self, required_outputs: List[str]) -> Dict:
        """
        Filter processes to only include those with required outputs.
        
        Parameters
        ----------
        required_outputs : list of str
            List of output field names required for the plot
            
        Returns
        -------
        dict
            Dictionary of processes that have all required outputs
        """
        scenario_availability = self._check_required_outputs(required_outputs)
        
        filtered_processes = {
            name: proc 
            for name, proc in self.processes.items()
            if scenario_availability[name]
        }
        
        if len(filtered_processes) == 0:
            raise ValueError(
                f"No scenarios have all required outputs: {required_outputs}"
            )
        
        return filtered_processes
    
    def plot(self, name: str, save: bool = False, size_inches=None, 
             remove_title: bool = False, check_outputs: bool = True):
        """
        Generate a multi-scenario comparison plot.
        
        Parameters
        ----------
        name : str
            Identifier of the plot to generate. Use list_available_plots()
            to see available options.
        save : bool, optional
            Whether to save the plot as a PDF file. Default is False.
        size_inches : tuple, optional
            Figure size in inches as (width, height)
        remove_title : bool, optional
            Whether to remove the plot title before saving. Default is False.
        check_outputs : bool, optional
            Whether to check for required outputs and filter scenarios.
            Default is True. If False, plot may fail if outputs are missing.
            
        Returns
        -------
        fig
            The created plot object
            
        Raises
        ------
        NameError
            If the plot name is not available
        ValueError
            If no scenarios have the required outputs
        """
        if name not in self._available_plots:
            available = list(self._available_plots.keys())
            raise NameError(
                f"Plot '{name}' is not available. "
                f"Available multi-scenario plots: {available}"
            )
        
        plot_class = self._available_plots[name]
        
        # Get required outputs from the plot class if available
        processes_to_use = self.processes
        if check_outputs and hasattr(plot_class, 'required_outputs'):
            required_outputs = plot_class.required_outputs
            processes_to_use = self._filter_processes(required_outputs)
            
            if len(processes_to_use) < len(self.processes):
                included = list(processes_to_use.keys())
                logger.info(
                    f"Plot '{name}' will use {len(processes_to_use)}/{len(self.processes)} "
                    f"scenarios: {included}"
                )
        
        # Create the plot
        fig = plot_class(processes_to_use)
        
        # Save if requested
        if save:
            if size_inches is not None:
                fig.fig.set_size_inches(size_inches)
            if remove_title:
                fig.fig.gca().set_title("")
            fig.fig.savefig(f"{name}.pdf", bbox_inches="tight")
        
        return fig
    
    def get_scenario_names(self) -> List[str]:
        """
        Get the names of all scenarios.
        
        Returns
        -------
        list of str
            List of scenario names
        """
        return list(self.processes.keys())
    
    def __len__(self) -> int:
        """Return the number of scenarios."""
        return len(self.processes)
    
    def __getitem__(self, key):
        """Get a process by scenario name or index."""
        if isinstance(key, int):
            keys = list(self.processes.keys())
            return self.processes[keys[key]]
        return self.processes[key]
