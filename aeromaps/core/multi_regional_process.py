"""Multi-regional AeroMAPS process orchestration.

This module defines the MultiRegionalProcess class that orchestrates multiple
regional AeroMAPS processes and aggregates their results.

Architecture follows AeroMAPSProcess patterns:
- All outputs stored in `data["vector_outputs"]` with namespace prefixes
  (e.g., "FR:co2_emissions", "overall:co2_emissions")
- Aggregator stored in `self.models["aggregator"]` like any AeroMAPSModel

Two execution modes are supported:
- unified_mda: All regional disciplines combined into a single MDAChain
- separate_processes: Each regional process executed independently, then aggregated
"""

# Standard library imports
import logging
import os
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from copy import deepcopy
from typing import Dict, List, Optional, Literal

# Third-party imports
import numpy as np
import pandas as pd
from gemseo.mda.mda_chain import MDAChain
from tqdm.auto import tqdm

# Local application imports
from aeromaps.core.process import AeroMAPSProcess
from aeromaps.core.gemseo import (
    AeroMAPSCustomModelWrapper,
    apply_namespace_to_disciplines,
    build_namespaced_inputs,
)
from aeromaps.models.multi_regional.regional_aggregator import RegionalAggregator


# Type alias for execution modes
ExecutionMode = Literal["unified_mda", "separate_processes"]


class MultiRegionalProcess(AeroMAPSProcess):
    """Multi-regional AeroMAPS process that orchestrates multiple regional scenarios.

    This class extends AeroMAPSProcess to handle multi-regional scenarios where
    multiple regions are simulated and their results aggregated. It supports two
    execution modes:

    - **unified_mda**: All regional disciplines are combined into a single MDAChain.
      This is memory-intensive but allows GEMSEO to handle the full coupling.
      Best for scenarios with few regions or when regions have coupling.

    - **separate_processes**: Each regional process is executed independently,
      then results are aggregated. This is more scalable and allows parallel
      execution. Best for many regions without inter-regional coupling.

    Parameters
    ----------
    configuration_file
        Path to the main configuration YAML file containing the 'regionalisation'
        section.
    custom_models
        Dictionary of additional model instances to merge with standard models.
    disable_execution_statistics
        Whether to disable GEMSEO's execution statistics (auto for unified_mda mode).

    Attributes
    ----------
    regional_processes : Dict[str, AeroMAPSProcess]
        Dictionary mapping region IDs to their AeroMAPSProcess instances.
    execution_mode : str
        The execution mode ("unified_mda" or "separate_processes").
    global_namespace : str
        Namespace prefix for aggregated global outputs (e.g., "overall").

    Examples
    --------
    >>> # Using separate_processes mode (recommended for many regions)
    >>> process = MultiRegionalProcess(
    ...     configuration_file="config_with_regionalisation.yaml"
    ... )
    >>> process.compute()
    >>>
    >>> # Access regional results
    >>> fr_process = process.regional_processes["FR"]
    >>> fr_process.plot("co2_emissions")
    >>>
    >>> # Access outputs via namespaced vector_outputs (AeroMAPSProcess pattern)
    >>> fr_emissions = process.data["vector_outputs"]["FR:co2_emissions"]
    >>> global_emissions = process.data["vector_outputs"]["overall:co2_emissions"]
    """

    def __init__(
        self,
        configuration_file: str,
        custom_models: Optional[dict] = None,
        disable_execution_statistics: Optional[bool] = None,
    ):
        """Initialize a MultiRegionalProcess instance.

        This method loads the regionalisation configuration, creates regional
        processes, and sets up the execution mode.

        Parameters
        ----------
        configuration_file
            Path to the main configuration YAML file.
        custom_models
            Dictionary of additional models to merge with standard models.
        disable_execution_statistics
            Whether to disable GEMSEO's execution statistics.
        """
        # Suppress GEMSEO source_parsing warnings about docstring style
        # (GEMSEO expects Google-style "Args:" but AeroMAPS uses NumPy-style "Parameters")
        # TODO: discuss if that is not satisfactory.
        logging.getLogger("gemseo.utils.source_parsing").setLevel(logging.ERROR)

        # Store configuration file path early (before parent init)
        self.configuration_file = os.path.abspath(os.fspath(configuration_file))

        # Initialize configuration parsing (without full parent init)
        self._initialize_configuration_only()

        # Read regionalisation config to determine execution mode
        self._read_regionalisation_config()

        # Set execution mode from config (default: separate_processes for scalability)
        self._execution_mode: ExecutionMode = self._regionalisation_config.get(
            "execution_mode", "separate_processes"
        )

        # Handle execution statistics based on mode
        if disable_execution_statistics is None:
            # Auto-disable for unified_mda mode (many disciplines = semaphore issues)
            disable_execution_statistics = self._execution_mode == "unified_mda"

        if disable_execution_statistics:
            from aeromaps.core.gemseo import disable_gemseo_execution_statistics

            disable_gemseo_execution_statistics()
            logging.info("Disabled GEMSEO execution statistics")

        # Store custom models for regional process creation
        self._custom_models = custom_models

        # Initialize regional processes
        self._regional_processes: Dict[str, AeroMAPSProcess] = {}
        self._create_regional_processes()

        # Initialize models dict (following AeroMAPSProcess pattern)
        self.models = {}
        self._create_aggregator()

        # Mode-specific setup
        if self._execution_mode == "unified_mda":
            self._setup_unified_mda()
        else:
            # For separate_processes mode, we don't need an MDAChain
            # Each regional process has its own
            self.mda_chain = None
            self.disciplines = []

        # Initialize data containers for aggregated results
        self._initialize_data_containers()

        logging.info(
            f"MultiRegionalProcess initialized with {len(self._region_ids)} regions "
            f"in '{self._execution_mode}' mode"
        )

    def _initialize_configuration_only(self):
        """Load configuration without triggering full AeroMAPSProcess initialization."""
        from aeromaps.utils.yaml import read_yaml_file

        # Load default config
        from aeromaps.core.process import DEFAULT_CONFIG_PATH, DEFAULT_RESOURCES_DATA_DIR

        self._default_config = read_yaml_file(DEFAULT_CONFIG_PATH)
        self.config = deepcopy(self._default_config)
        self._config_base_dir = DEFAULT_RESOURCES_DATA_DIR
        self._user_config = {}

        # Load user config if provided
        if self.configuration_file is not None:
            self._user_config = read_yaml_file(self.configuration_file)
            self._config_base_dir = os.path.dirname(self.configuration_file)
            self._deep_merge_config(self.config, self._user_config)

    # Note: _deep_merge_config and _get_user_config_value are inherited from AeroMAPSProcess

    def _read_regionalisation_config(self):
        """Read and validate the regionalisation configuration."""
        regionalisation_config = self._get_user_config_value("regionalisation", default=None)

        if regionalisation_config is None:
            raise ValueError(
                "MultiRegionalProcess requires a 'regionalisation' section in the config file."
            )

        self._regionalisation_config = regionalisation_config

        # Extract region definitions
        regions_config = regionalisation_config.get("regions", {})
        if not regions_config:
            raise ValueError(
                "Regionalisation config must specify at least one region under 'regions' key."
            )

        self._region_ids = list(regions_config.keys())
        self._region_configs = {}

        # Resolve region config file paths
        for region_id, region_data in regions_config.items():
            config_file = region_data.get("config_file")
            if config_file is None:
                raise ValueError(f"Region '{region_id}' must specify a 'config_file'.")

            if not os.path.isabs(config_file):
                config_file = os.path.normpath(os.path.join(self._config_base_dir, config_file))

            self._region_configs[region_id] = config_file

        # Store aggregation config and global namespace
        self._aggregation_config = regionalisation_config.get("aggregation", {})
        self._global_namespace = regionalisation_config.get("global_namespace", "overall")

        logging.info(
            f"Multi-regional configuration: {len(self._region_ids)} regions, "
            f"execution_mode='{self._regionalisation_config.get('execution_mode', 'separate_processes')}'"
        )

    def _create_regional_processes(self):
        """Create individual AeroMAPSProcess instances for each region with progress bar."""
        pbar = tqdm(
            self._region_configs.items(),
            desc="Initializing regional processes",
            unit="region",
            total=len(self._region_configs),
        )
        for region_id, config_file in pbar:
            pbar.set_postfix_str(f"Region: {region_id}")

            with self._regional_warning_context(region_id):
                regional_process = AeroMAPSProcess(
                    configuration_file=config_file,
                    custom_models=self._custom_models,
                    optimisation=False,
                )

            self._regional_processes[region_id] = regional_process

    def _create_aggregator(self):
        """Create the RegionalAggregator model and store in self.models."""
        # Use parameters from the first regional process for year indexing
        first_region = self._region_ids[0]
        reference_parameters = self._regional_processes[first_region].parameters

        aggregator = RegionalAggregator(
            name="RegionalAggregator",
            regions=self._region_ids,
            aggregation_config=self._aggregation_config,
            global_namespace=self._global_namespace,
            parameters=reference_parameters,
        )

        # Store in models dict following AeroMAPSProcess pattern
        self.models["aggregator"] = aggregator

        logging.info(
            f"Aggregator created: {len(aggregator.input_names)} inputs, "
            f"{len(aggregator.output_names)} outputs"
        )

    def _setup_unified_mda(self):
        """Set up unified MDA mode with all disciplines in one MDAChain."""
        self._regional_disciplines = {}

        # Apply namespaces to each region's disciplines
        for region_id, regional_process in self._regional_processes.items():
            namespaced_disciplines = apply_namespace_to_disciplines(
                regional_process.disciplines, region_id
            )
            self._regional_disciplines[region_id] = namespaced_disciplines

        # Combine all disciplines
        all_disciplines = []
        for region_id in self._region_ids:
            all_disciplines.extend(self._regional_disciplines[region_id])

        # Add aggregator as a discipline
        aggregator_discipline = AeroMAPSCustomModelWrapper(model=self.models["aggregator"])
        all_disciplines.append(aggregator_discipline)

        self.disciplines = all_disciplines

        # Build MDAChain
        # TODO: Make these kwargs available at a higher level (e.g. config file).
        self.mda_chain = MDAChain(
            disciplines=all_disciplines,
            tolerance=1e-5,
            initialize_defaults=True,
            inner_mda_name="MDAGaussSeidel",
            log_convergence=True,
        )

        logging.info(f"Unified MDAChain created with {len(all_disciplines)} disciplines")

    def _initialize_data_containers(self):
        """Initialize data containers following AeroMAPSProcess structure.

        All outputs will use namespaced keys in vector_outputs:
        - Regional: "FR:co2_emissions", "DE:rpk", etc.
        - Global: "overall:co2_emissions", "overall:rpk", etc.

        Same pattern applies to float_outputs and climate_outputs.
        """
        # Get year index from first regional process
        first_process = self._regional_processes[self._region_ids[0]]

        # Follow AeroMAPSProcess data structure exactly
        self.data = {
            "years": first_process.data.get("years", {}),
            "float_inputs": {},
            "str_inputs": {},
            "vector_inputs": {},
            "float_outputs": {},  # Keys will be namespaced: "FR:metric", "overall:metric"
            "vector_outputs": pd.DataFrame(
                index=first_process.data.get("years", {}).get("full_years", [])
            ),
            "climate_outputs": pd.DataFrame(
                index=first_process.data.get("years", {}).get("climate_full_years", [])
            ),
            "lca_outputs": None,  # xarray - handled separately per region
        }

        # Reference to parameters from first region (for year indexing, etc.)
        self.parameters = first_process.parameters

    # =========================================================================
    # Public API
    # =========================================================================

    @property
    def regional_processes(self) -> Dict[str, AeroMAPSProcess]:
        """Get the dictionary of regional AeroMAPSProcess instances.

        Returns
        -------
        Dict[str, AeroMAPSProcess]
            Dictionary mapping region IDs to their process instances.
        """
        return self._regional_processes

    @property
    def execution_mode(self) -> ExecutionMode:
        """Get the current execution mode.

        Returns
        -------
        str
            Either "unified_mda" or "separate_processes".
        """
        return self._execution_mode

    @property
    def global_namespace(self) -> str:
        """Get the global namespace prefix for aggregated outputs.

        Returns
        -------
        str
            The global namespace (e.g., "overall").
        """
        return self._global_namespace

    def compute(
        self,
        parallel: bool = False,
        max_workers: Optional[int] = None,
    ):
        """Run the multi-regional computation.

        For unified_mda mode, executes the combined MDAChain.
        For separate_processes mode, executes each regional process independently
        (optionally in parallel) and then aggregates the results.

        Parameters
        ----------
        parallel
            Whether to execute regional processes in parallel (only applies
            to separate_processes mode). Default is False for safer execution.
        max_workers
            Maximum number of parallel workers. If None, uses min(n_regions, 4).
            Only applies when parallel=True.
        """
        logging.info(f"Starting multi-regional computation ({self._execution_mode} mode)...")

        if self._execution_mode == "unified_mda":
            self._compute_unified_mda()
        else:
            self._compute_separate_processes(parallel=parallel, max_workers=max_workers)

        logging.info("Multi-regional computation completed.")

    def _compute_unified_mda(self):
        """Execute computation using unified MDA mode."""
        # Build combined namespaced input data
        input_data = {}
        for region_id, regional_process in self._regional_processes.items():
            regional_inputs = build_namespaced_inputs(regional_process.parameters, region_id)
            input_data.update(regional_inputs)

        # Execute MDAChain
        self.mda_chain.execute(input_data)

        # Update data from MDA results
        self._update_data_from_unified_mda()

    def _compute_separate_processes(
        self,
        parallel: bool = False,
        max_workers: Optional[int] = None,
    ):
        """Execute computation using separate processes mode.

        NOTE: In this mode regional processes are executed independently
        (either in parallel or sequentially). Inter-regional coupling
        (i.e., coupling solved across regions) is NOT supported here.
        To simulate coupling between regions use the "unified_mda"
        execution mode which combines regional disciplines into a single
        MDAChain. Inter-regional coupling are not tested yet. In the backlog.
        """
        warnings.warn(
            "'separate_processes' mode does not support solving coupling between regions; "
            "use 'unified_mda' mode for inter-regional coupling.",
            UserWarning,
        )
        if parallel:
            self._execute_parallel(max_workers=max_workers)
        else:
            self._execute_sequential()

        # Aggregate results from all regional processes
        self._aggregate_regional_outputs()

    @contextmanager
    def _regional_warning_context(self, region_id: str):
        """Context manager to prefix warnings with region ID.

        Parameters
        ----------
        region_id
            The region identifier to prefix warnings with.

        Yields
        ------
        None
            Context where warnings are prefixed with [region_id].
        """
        original_showwarning = warnings.showwarning

        def regional_showwarning(message, category, filename, lineno, file=None, line=None):
            # Prefix the warning message with region ID
            prefixed_message = f"Region: [{region_id}] {message}"
            original_showwarning(prefixed_message, category, filename, lineno, file, line)

        try:
            warnings.showwarning = regional_showwarning
            yield
        finally:
            warnings.showwarning = original_showwarning

    def _execute_sequential(self):
        """Execute all regional processes sequentially with progress bar."""
        pbar = tqdm(
            self._regional_processes.items(),
            desc="Computing regions",
            unit="region",
            total=len(self._regional_processes),
        )
        for region_id, regional_process in pbar:
            pbar.set_postfix_str(f"Region: {region_id}")
            with self._regional_warning_context(region_id):
                regional_process.compute()

    def _execute_parallel(self, max_workers: Optional[int] = None):
        """Execute regional processes in parallel using ThreadPoolExecutor with progress bar."""
        if max_workers is None:
            max_workers = min(len(self._region_ids), 4)

        def compute_region(region_id: str) -> str:
            """Compute a single region and return its ID."""
            with self._regional_warning_context(region_id):
                self._regional_processes[region_id].compute()
            return region_id

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(compute_region, region_id): region_id
                for region_id in self._region_ids
            }

            pbar = tqdm(
                as_completed(futures),
                desc=f"Computing regions (workers={max_workers})",
                unit="region",
                total=len(futures),
            )
            for future in pbar:
                region_id = futures[future]
                try:
                    future.result()
                    pbar.set_postfix_str(f"Completed: {region_id}")
                except Exception as e:
                    pbar.set_postfix_str(f"Failed: {region_id}")
                    logging.error(f"Region '{region_id}' failed: {e}")
                    raise

    def _aggregate_regional_outputs(self):
        """Aggregate outputs from all regional processes.

        Populates all data structures with namespaced keys:
        - vector_outputs: "FR:co2_emissions", "overall:co2_emissions"
        - float_outputs: "FR:metric", "overall:metric"
        - climate_outputs: "FR:temperature", "overall:temperature"

        All output types are passed to the aggregator for potential aggregation.
        """
        # Build aggregator input from ALL regional outputs
        # Collect all series to avoid DataFrame fragmentation from repeated inserts
        aggregator_input = {}
        vector_series = {}
        climate_series = {}
        climate_years = self.data["years"].get("climate_full_years", [])

        for region_id, regional_process in self._regional_processes.items():
            # Get vector_outputs from regional process data (already populated by compute())
            regional_vectors = regional_process.data.get("vector_outputs")
            if regional_vectors is not None and not regional_vectors.empty:
                for col in regional_vectors.columns:
                    namespaced_key = f"{region_id}:{col}"
                    aggregator_input[namespaced_key] = regional_vectors[col]
                    vector_series[namespaced_key] = regional_vectors[col]

            # Get float_outputs from regional process data
            regional_floats = regional_process.data.get("float_outputs", {})
            for key, value in regional_floats.items():
                namespaced_key = f"{region_id}:{key}"
                aggregator_input[namespaced_key] = value
                self.data["float_outputs"][namespaced_key] = value

            # Get climate_outputs from regional process data
            regional_climate = regional_process.data.get("climate_outputs")
            if regional_climate is not None and not regional_climate.empty:
                for col in regional_climate.columns:
                    namespaced_key = f"{region_id}:{col}"
                    aggregator_input[namespaced_key] = regional_climate[col]
                    climate_series[namespaced_key] = regional_climate[col]

        # Run aggregator on ALL inputs (it will aggregate what's in its config)
        global_outputs = self.models["aggregator"].compute(aggregator_input)

        # Store global outputs based on their type
        for key, value in global_outputs.items():
            if isinstance(value, pd.Series):
                # Check if it belongs in climate_outputs (by checking index length)
                if len(value) == len(climate_years) and climate_years:
                    climate_series[key] = value
                else:
                    vector_series[key] = value
            elif isinstance(value, (int, float)):
                self.data["float_outputs"][key] = value

        # Build DataFrames efficiently using concat to avoid fragmentation
        if vector_series:
            self.data["vector_outputs"] = pd.concat(
                [self.data["vector_outputs"]]
                + [pd.DataFrame({k: v}) for k, v in vector_series.items()],
                axis=1,
            )
        if climate_series:
            self.data["climate_outputs"] = pd.concat(
                [self.data["climate_outputs"]]
                + [pd.DataFrame({k: v}) for k, v in climate_series.items()],
                axis=1,
            )

    def _update_data_from_unified_mda(self):
        """Update all data structures from unified MDA results.

        In unified_mda mode, the MDAChain runs all namespaced disciplines together.
        We gather outputs the same way as separate_processes: from regional process data.
        """
        # Collect all series to avoid DataFrame fragmentation from repeated inserts
        vector_series = {}
        climate_series = {}
        climate_years = self.data["years"].get("climate_full_years", [])

        for region_id, regional_process in self._regional_processes.items():
            # Get vector_outputs from regional process data
            regional_vectors = regional_process.data.get("vector_outputs")
            if regional_vectors is not None and not regional_vectors.empty:
                for col in regional_vectors.columns:
                    namespaced_key = f"{region_id}:{col}"
                    vector_series[namespaced_key] = regional_vectors[col]

            # Get float_outputs from regional process data
            regional_floats = regional_process.data.get("float_outputs", {})
            for key, value in regional_floats.items():
                namespaced_key = f"{region_id}:{key}"
                self.data["float_outputs"][namespaced_key] = value

            # Get climate_outputs from regional process data
            regional_climate = regional_process.data.get("climate_outputs")
            if regional_climate is not None and not regional_climate.empty:
                for col in regional_climate.columns:
                    namespaced_key = f"{region_id}:{col}"
                    climate_series[namespaced_key] = regional_climate[col]

        # Get global (aggregated) outputs from MDA local_data
        local_data = self.mda_chain.local_data
        global_prefix = f"{self._global_namespace}:"

        for key, value in local_data.items():
            if key.startswith(global_prefix):
                if isinstance(value, pd.Series):
                    if len(value) == len(climate_years) and climate_years:
                        climate_series[key] = value
                    else:
                        vector_series[key] = value
                elif isinstance(value, (int, float)):
                    self.data["float_outputs"][key] = value

        # Build DataFrames efficiently using concat to avoid fragmentation
        if vector_series:
            self.data["vector_outputs"] = pd.concat(
                [self.data["vector_outputs"]]
                + [pd.DataFrame({k: v}) for k, v in vector_series.items()],
                axis=1,
            )
        if climate_series:
            self.data["climate_outputs"] = pd.concat(
                [self.data["climate_outputs"]]
                + [pd.DataFrame({k: v}) for k, v in climate_series.items()],
                axis=1,
            )

    # =========================================================================
    # Data Access Methods
    # =========================================================================

    def get_regional_process(self, region_id: str) -> AeroMAPSProcess:
        """Get the AeroMAPSProcess instance for a specific region.

        Parameters
        ----------
        region_id
            The region identifier (e.g., "FR", "DE").

        Returns
        -------
        AeroMAPSProcess
            The regional process instance.

        Raises
        ------
        KeyError
            If region_id is not found.
        """
        if region_id not in self._regional_processes:
            raise KeyError(
                f"Region '{region_id}' not found. Available: {list(self._regional_processes.keys())}"
            )
        return self._regional_processes[region_id]

    def get_regional_outputs(self, region_id: str) -> pd.DataFrame:
        """Get outputs for a specific region from vector_outputs.

        Parameters
        ----------
        region_id
            The region identifier (e.g., "FR", "DE").

        Returns
        -------
        pd.DataFrame
            DataFrame with outputs for the specified region (namespace removed from columns).
        """
        if region_id not in self._region_ids:
            raise KeyError(f"Region '{region_id}' not found. Available: {self._region_ids}")

        # Filter columns for this region and remove namespace prefix
        prefix = f"{region_id}:"
        region_cols = [c for c in self.data["vector_outputs"].columns if c.startswith(prefix)]

        result = self.data["vector_outputs"][region_cols].copy()
        result.columns = [c[len(prefix) :] for c in region_cols]
        return result

    def get_global_outputs(self) -> pd.DataFrame:
        """Get aggregated global outputs from vector_outputs.

        Returns
        -------
        pd.DataFrame
            DataFrame with global outputs (namespace removed from columns).
        """
        prefix = f"{self._global_namespace}:"
        global_cols = [c for c in self.data["vector_outputs"].columns if c.startswith(prefix)]

        result = self.data["vector_outputs"][global_cols].copy()
        result.columns = [c[len(prefix) :] for c in global_cols]
        return result

    def list_regions(self) -> List[str]:
        """List all region identifiers.

        Returns
        -------
        List[str]
            List of region IDs.
        """
        return self._region_ids.copy()

    # =========================================================================
    # Plotting Methods
    # =========================================================================

    def plot(
        self,
        name: str,
        region: Optional[str] = None,
        save: bool = False,
        size_inches: Optional[tuple] = None,
        remove_title: bool = False,
    ):
        """Generate a plot for a specific region or raise an error for global plots.

        For regional plots, delegates to the regional process's plot method.
        Global (aggregated) plots require explicit implementation.

        Parameters
        ----------
        name
            Identifier of the plot to generate.
        region
            Region ID for regional plots. If None, attempts global plot.
        save
            Whether to save the generated plot as a PDF file.
        size_inches
            Optional figure size in inches as a tuple.
        remove_title
            Whether to remove the plot title.

        Returns
        -------
        fig
            The matplotlib figure object.
        """
        if region is not None:
            # Delegate to regional process
            regional_process = self.get_regional_process(region)
            return regional_process.plot(
                name, save=save, size_inches=size_inches, remove_title=remove_title
            )
        else:
            # Global plot - needs specific implementation
            # TODO: Implement global plotting using aggregated data
            raise NotImplementedError(
                "Global (aggregated) plotting not yet implemented. "
                "Specify a region using region='FR' to plot regional data."
            )

    def plot_regional_comparison(
        self,
        variable: str,
        regions: Optional[List[str]] = None,
        **kwargs,
    ):
        """Plot a comparison of a variable across multiple regions.

        Parameters
        ----------
        variable
            The variable name to compare.
        regions
            List of region IDs to include. If None, includes all regions.
        **kwargs
            Additional arguments passed to the plotting function.

        Returns
        -------
        fig
            The matplotlib figure object.
        """
        # TODO: Implement regional comparison plotting
        raise NotImplementedError("Regional comparison plotting not yet implemented.")

    # =========================================================================
    # Export Methods
    # =========================================================================

    def get_dataframes(self) -> dict:
        """Return all main DataFrames as a dictionary.

        Returns
        -------
        dict
            Dictionary mapping DataFrame names to pandas DataFrame instances.
            Includes vector_outputs, climate_outputs, float_outputs, and global_outputs.
        """
        return {
            "vector_outputs": self.data["vector_outputs"].copy(),
            "climate_outputs": self.data["climate_outputs"].copy(),
            "float_outputs": self._get_float_outputs_df(),
            "global_outputs": self.get_global_outputs(),
        }

    def write_json(self, file_name: str):
        """Write aggregated outputs to a JSON file.

        Parameters
        ----------
        file_name
            Path to the output JSON file.
        """
        import json

        # Convert Series to lists for JSON serialization
        def serialize(obj):
            if isinstance(obj, pd.Series):
                return obj.tolist()
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            return obj

        # Organize by namespace from vector_outputs
        json_data = {"vector_outputs": {}, "float_outputs": {}, "climate_outputs": {}}

        for col in self.data["vector_outputs"].columns:
            if ":" in col:
                namespace, var_name = col.split(":", 1)
            else:
                namespace, var_name = "default", col

            if namespace not in json_data["vector_outputs"]:
                json_data["vector_outputs"][namespace] = {}
            json_data["vector_outputs"][namespace][var_name] = serialize(
                self.data["vector_outputs"][col]
            )

        # Add float_outputs (already namespaced keys)
        json_data["float_outputs"] = serialize(self.data["float_outputs"])

        # Add climate_outputs
        for col in self.data["climate_outputs"].columns:
            if ":" in col:
                namespace, var_name = col.split(":", 1)
            else:
                namespace, var_name = "default", col

            if namespace not in json_data["climate_outputs"]:
                json_data["climate_outputs"][namespace] = {}
            json_data["climate_outputs"][namespace][var_name] = serialize(
                self.data["climate_outputs"][col]
            )

        os.makedirs(os.path.dirname(file_name) or ".", exist_ok=True)
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2)

    def write_excel(self, file_name: str):
        """Write aggregated outputs to an Excel file.

        Parameters
        ----------
        file_name
            Path to the output Excel file.
        """
        with pd.ExcelWriter(file_name) as writer:
            # Global outputs sheet
            global_df = self.get_global_outputs()
            if not global_df.empty:
                global_df.to_excel(writer, sheet_name="Global Outputs")

            # Climate outputs sheet (all namespaced)
            if not self.data["climate_outputs"].empty:
                self.data["climate_outputs"].to_excel(writer, sheet_name="Climate Outputs")

            # Float outputs sheet
            if self.data["float_outputs"]:
                float_df = pd.DataFrame(
                    {
                        "Name": list(self.data["float_outputs"].keys()),
                        "Value": list(self.data["float_outputs"].values()),
                    }
                )
                float_df.to_excel(writer, sheet_name="Float Outputs", index=False)

            # Regional outputs (one sheet per region, limited to avoid Excel limits)
            for region_id in self._region_ids[:20]:  # Excel has sheet limits
                regional_df = self.get_regional_outputs(region_id)
                if not regional_df.empty:
                    regional_df.to_excel(writer, sheet_name=f"Region_{region_id}")
