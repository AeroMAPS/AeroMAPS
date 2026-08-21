# Copyright 2021 IRT Saint Exupéry, https://www.irt-saintexupery.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License version 3 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
# Contributors:
#    INITIAL AUTHORS - initial API and implementation and/or
#                      initial documentation
#        :author:  Francois Gallard
#    OTHER AUTHORS   - MACROSCOPIC CHANGES
"""A discipline interfacing a Python function.

Tuning an ``MDAChain`` (three traps, all silent)
------------------------------------------------

1. ``tolerance``, ``max_mda_iter`` and ``log_convergence`` are tuned **on the chain**::

       process.mda_chain.settings.tolerance = 1e-8

   Never on an inner MDA. ``MDAChain_Settings`` cascades those three down to the inner
   MDAs from a pydantic validator that re-runs on *any* assignment to the chain's
   settings -- including the ``initialize_defaults = False`` that ``MDAChain.execute``
   performs on its first run. A value written on ``inner_mdas[i].settings`` is therefore
   reverted to the chain's the moment the chain executes.

2. ``over_relaxation_factor`` and ``acceleration_method`` are the opposite case. They do
   not belong to ``BaseMDASettings``, so the chain neither forwards nor cascades them:
   passed as ``MDAChain`` kwargs they configure the outer chain alone and are ignored by
   the solver that actually iterates. At construction they go through
   ``inner_mda_settings``; afterwards, through the inner solver's *properties*::

       process.mda_chain.inner_mdas[0].over_relaxation_factor = 0.7

   ``BaseMDASolver.__init__`` builds its ``RelaxationAcceleration`` from the settings
   once and never re-reads them, so assigning to ``inner_mdas[i].settings.*`` does
   nothing at all.

3. A chain that does not converge still returns a full set of outputs, and GEMSEO only
   logs a warning. :func:`check_mda_convergence` turns that into an error -- including
   the case where the residual *does* reach the tolerance because the coupling variables
   have gone NaN and the NaN sentinel differences against itself to exactly zero.
"""

from __future__ import annotations

import inspect
import logging
import sys
import traceback
from numbers import Number
from typing import TYPE_CHECKING, ClassVar
from typing import Final
from typing import Union
from typing import Any
from typing import cast

import numpy as np
import pandas as pd

from gemseo.core.data_converters.simple import SimpleGrammarDataConverter
from gemseo.core.grammars.simple_grammar import SimpleGrammar
from gemseo.core.grammars.json_grammar import JSONGrammar

from numpy import ndarray
from gemseo.disciplines.auto_py import AutoPyDiscipline
from gemseo.core.discipline import Discipline

from aeromaps.models.base import AeroMAPSModel

if TYPE_CHECKING:
    from gemseo.typing import NumberArray

    ValueType = Union[int, float, complex, NumberArray]


DataType = Union[float, ndarray]
LOGGER = logging.getLogger(__name__)

# Global flag to track if we've patched GEMSEO's ExecutionStatistics
_EXECUTION_STATISTICS_PATCHED = False


def disable_gemseo_execution_statistics():
    """Disable GEMSEO's execution statistics shared memory.

    GEMSEO's ExecutionStatistics creates semaphores for each discipline via
    multiprocessing.Value(). With many disciplines (20+ regions × 50+ models),
    this exhausts macOS semaphore limits (kern.sysv.shmmni=32).

    This function patches ExecutionStatistics to use regular Python attributes
    instead of shared memory, avoiding semaphore creation.

    Safe to call multiple times (only patches once).
    # TODO: Investigate possibilities with gemseo.configure ?
    """
    global _EXECUTION_STATISTICS_PATCHED

    if _EXECUTION_STATISTICS_PATCHED:
        return

    try:
        from gemseo.core.execution_statistics import ExecutionStatistics

        def _patched_init(self, *args, **kwargs):
            """Skip shared memory initialization to avoid semaphore exhaustion."""
            # Initialize as regular attributes instead of shared memory
            self._ExecutionStatistics__duration = 0.0
            self._ExecutionStatistics__n_executions = 0
            self._ExecutionStatistics__n_linearizations = 0
            self._ExecutionStatistics__n_calls_to_jacobian = 0
            self._ExecutionStatistics__execution_time = {}

        ExecutionStatistics._init_shared_memory_attrs_before = _patched_init
        _EXECUTION_STATISTICS_PATCHED = True
        LOGGER.debug("Patched GEMSEO ExecutionStatistics to use non-shared state")
    except Exception as patch_err:
        LOGGER.warning(f"Could not patch GEMSEO ExecutionStatistics: {patch_err}")


def _format_model_traceback(model_file: str) -> str:
    """Extract and format traceback frames originating from the given model file."""
    exc_tb = sys.exc_info()[2]
    if exc_tb is None:
        return ""
    frames = [f for f in traceback.extract_tb(exc_tb) if f.filename == model_file]
    if not frames:
        return ""
    return "".join(traceback.StackSummary.from_list(frames).format())


class ExtendedJSONGrammar(JSONGrammar):
    DATA_CONVERTER_CLASS: ClassVar[str] = "CustomDataConverter"
    __PYTHON_TO_JSON_TYPES: Final[dict[type, str]] = {
        **JSONGrammar._JSONGrammar__PYTHON_TO_JSON_TYPES,
        # Add your additional types here
        Number: "number",
        pd.Series: "array",
    }


# class DataConverter(SimpleGrammarDataConverter):
#    """A data converter where ``x_shared`` is not a ndarray and handles pd.Series."""
#
#    def convert_value_to_array(self, name: str, value: Any) -> ndarray:  # noqa: D102 # pragma: no cover
#        print(f"(Undesired loop ?) using custom data converter for {name}; {value}")
#        if isinstance(value, pd.Series):
#            return value.values
#        return super().convert_value_to_array(name, value)


class CustomDataConverter(SimpleGrammarDataConverter):
    _IS_CONTINUOUS_TYPES: ClassVar[tuple[type, ...]] = (float, complex, pd.Series, list)
    _IS_NUMERIC_TYPES: ClassVar[tuple[type, ...]] = (int, *_IS_CONTINUOUS_TYPES)

    _list_names = set()
    _series_names = set()
    _series_indexes = {}

    def convert_value_to_array(self, name: str, value: Any) -> ndarray:
        if isinstance(value, (list, tuple)):
            # print(name, value)
            self._list_names.add(name)
            value = np.array(value, dtype=float)

        if isinstance(value, pd.Series):
            value = value.fillna(-999999)
            self._series_names.add(name)
            self._series_indexes[name] = value.index
            return value.values
        return super().convert_value_to_array(name, value)

    def convert_array_to_value(self, name: str, array_: Any) -> Any:
        array_ = np.asarray(array_, dtype=float)
        array_ = np.where(array_ == -999999, np.nan, array_)
        # TODO check if we shoudl keep large value or nan
        if isinstance(array_, ndarray) and name in self._series_names:
            return pd.Series(array_, index=self._series_indexes[name], name=name)  # very provisory
        if name in self._list_names and not isinstance(array_, list):
            array_ = list(array_)
        return super().convert_array_to_value(name, array_)

    # Overrides GEMSEO function to handle lists.
    @classmethod
    def get_value_size(cls, name: str, value: ValueType) -> int:
        """Return the size of a data value.

        The size is typically what is returned by ``ndarray.size`` or ``len(list)``.
        The size of a number is 1.


        Args:
            name: The data name.
            value: The data value to get the size from.

        Returns:
            The size.
        """
        if isinstance(value, cls._NON_ARRAY_TYPES):
            return 1
        elif isinstance(value, (list, tuple)):
            return len(value)
        return cast("NumberArray", value).size


SimpleGrammar.DATA_CONVERTER_CLASS = CustomDataConverter


class AeroMAPSAutoModelWrapper(AutoPyDiscipline):
    """
    Wraps the AeroMAPSModel class into a discipline.
    Inputs and outputs are automatically declared from the model's compute() function signature.
    """

    def __init__(self, model):
        self.model: AeroMAPSModel = model

        self.default_grammar_type = Discipline.GrammarType.SIMPLE

        super(AeroMAPSAutoModelWrapper, self).__init__(
            py_func=self.model.compute,
        )
        # self.io.data_processor = AutoDiscDataProcessor()

        self.name = model.__class__.__name__

        self.update_defaults()

    def update_defaults(self):
        for input in self.input_grammar.names:
            # if self.model.parameters is None:
            #     self.default_inputs[input] = array([0])
            if hasattr(self.model.parameters, input):
                self.default_input_data[input] = getattr(self.model.parameters, input)
        # Also register coupling defaults from the model (seed values for MDA initialization)
        if hasattr(self.model, "_coupling_defaults"):
            for key, value in self.model._coupling_defaults.items():
                if key in self.input_grammar.names and key not in self.default_input_data:
                    self.default_input_data[key] = value

    def _run(self, input_data):
        try:
            return super()._run(input_data)
        except Exception:
            model_file = inspect.getfile(type(self.model))
            model_tb = _format_model_traceback(model_file)
            LOGGER.error(
                "An error occurred when executing model: %s (file: %s)\n%s",
                self.model.name,
                model_file,
                model_tb,
            )
            raise


class AeroMAPSCustomModelWrapper(Discipline):
    """
    Wraps the AeroMAPSModel class into a discipline.
    Inputs and outputs are declared through the attributes 'input_names' and 'output_names' of the model.
    """

    def __init__(self, model):
        super().__init__()

        # Whether to skip data type validation (at your own risk)
        if getattr(model, "_skip_data_type_validation", False):
            # self.input_grammar = SimplerGrammar("InputGrammar")
            # self.output_grammar = SimplerGrammar("OutputGrammar")
            self.input_grammar._validate = lambda data, msg: True
            self.output_grammar._validate = lambda data, msg: True

        # Set input and output grammars from model attributes
        if isinstance(model.input_names, dict):
            self.input_grammar.update_from_data(model.input_names)
        else:  # assume list of names
            self.input_grammar.update_from_names(model.input_names)

        if isinstance(model.output_names, dict):
            self.output_grammar.update_from_data(model.output_names)
        else:  # assume list of names
            self.output_grammar.update_from_names(model.output_names)

        # Set the model
        self.model: AeroMAPSModel = model
        self.name = model.__class__.__name__

        # Initialize default input data
        self.update_defaults()
        # self.io.data_processor = AutoDiscDataProcessor()

    def _run(self, input_data):
        if hasattr(self.model, "compute"):
            try:
                return self.model.compute(input_data)
            except Exception:
                model_file = inspect.getfile(type(self.model))
                model_tb = _format_model_traceback(model_file)
                LOGGER.error(
                    "An error occurred when executing model: %s (file: %s)\n%s",
                    self.model.name,
                    model_file,
                    model_tb,
                )
                raise
        else:
            raise AttributeError(f"Model {self.name} does not have a compute method")

    def update_defaults(self):
        # Set default values if provided internally by the model (see e.g. LCA module)
        if self.model.default_input_data:
            self.default_input_data.update(self.model.default_input_data)

        for input in self.input_grammar.names:
            if hasattr(self.model.parameters, input):
                self.default_input_data[input] = getattr(self.model.parameters, input)

        # Also register coupling defaults from the model (seed values for MDA
        # initialization), mirroring AeroMAPSAutoModelWrapper. A parameter value
        # (set just above) still wins over the coupling seed.
        if hasattr(self.model, "_coupling_defaults"):
            for key, value in self.model._coupling_defaults.items():
                if key in self.input_grammar.names and key not in self.default_input_data:
                    self.default_input_data[key] = value


# =============================================================================
# Multi-Regional Namespace Utilities
# =============================================================================


def apply_namespace_to_discipline(discipline: Discipline, namespace: str) -> Discipline:
    """Apply a namespace prefix to all inputs and outputs of a GEMSEO discipline.

    This function creates a deep copy of the discipline and applies the namespace
    to isolate regional I/O variables. This is essential for multi-regional scenarios
    where multiple instances of the same discipline must coexist without variable conflicts.

    Parameters
    ----------
    discipline
        The GEMSEO discipline to namespace. Will be deep-copied to avoid
        modifying the original.
    namespace
        The namespace prefix to apply (e.g., "FR", "DE"). Variables will be
        renamed from "var_name" to "{namespace}:var_name".

    Returns
    -------
    Discipline
        A new discipline instance with namespaced inputs and outputs.

    Notes
    -----
    The deep copy is necessary because `add_namespace_to_input/output()` modifies
    the discipline in place. Without it, we would modify the original disciplines
    stored in the process objects.

    Examples
    --------
    >>> from aeromaps.core.gemseo import apply_namespace_to_discipline
    >>> namespaced_disc = apply_namespace_to_discipline(discipline, "FR")
    >>> # Now inputs/outputs are prefixed: "co2_emissions" -> "FR:co2_emissions"
    """
    from copy import deepcopy

    ns_disc = deepcopy(discipline)

    # Collect all variable names first for consistency
    input_names = list(ns_disc.input_grammar.names)
    output_names = list(ns_disc.output_grammar.names)

    # Apply namespace to all inputs and outputs
    for name in input_names:
        ns_disc.add_namespace_to_input(name, namespace)
    for name in output_names:
        ns_disc.add_namespace_to_output(name, namespace)

    # Update discipline name to include region identifier
    ns_disc.name = f"{namespace}_{ns_disc.name}"

    return ns_disc


def apply_namespace_to_disciplines(
    disciplines: list[Discipline], namespace: str
) -> list[Discipline]:
    """Apply a namespace to a list of disciplines.

    Convenience function to namespace multiple disciplines at once.

    Parameters
    ----------
    disciplines
        List of GEMSEO disciplines to namespace.
    namespace
        The namespace prefix to apply.

    Returns
    -------
    list[Discipline]
        List of new discipline instances with namespaced I/O.
    """
    return [apply_namespace_to_discipline(d, namespace) for d in disciplines]


def build_namespaced_inputs(parameters, namespace: str) -> dict:
    """Build a namespaced input dictionary from an AeroMAPS parameters object.

    This function converts all parameters into a dictionary with namespaced keys,
    suitable for execution of a multi-regional MDAChain.

    Parameters
    ----------
    parameters
        AeroMAPS Parameters object containing model inputs.
    namespace
        The namespace prefix to apply to all parameter names.

    Returns
    -------
    dict
        Dictionary with namespaced keys mapping to parameter values.
        E.g., {"FR:rpk_init": <value>, "FR:energy_consumption_init": <value>, ...}
    """
    input_data = {}
    params_dict = parameters.to_dict()

    for key, value in params_dict.items():
        namespaced_key = f"{namespace}:{key}"
        input_data[namespaced_key] = value

    return input_data


class MDAConvergenceError(RuntimeError):
    """Raised when an MDA stopped before reaching its convergence tolerance.

    The results of such a run are not a solution of the coupled system: the
    coupling variables are still moving when the solver gives up. Reporting this
    as an error rather than a warning is deliberate -- a silently unconverged run
    is indistinguishable from a converged one in the output DataFrames.
    """


def _worst_residual_contributors(mda, count: int = 5) -> str:
    """Best-effort list of the coupling variables holding the residual up.

    Reads a private GEMSEO attribute, so it degrades to an empty string rather
    than failing if GEMSEO renames it.
    """
    try:
        residuals = mda._BaseMDASolver__current_residuals
        ranked = sorted(
            ((float(np.linalg.norm(value)), name) for name, value in residuals.items()),
            reverse=True,
        )[:count]
    except Exception:  # noqa: BLE001 - diagnostics must never mask the real error
        return ""
    if not ranked:
        return ""
    listed = ", ".join(f"{name} ({norm:.2e})" for norm, name in ranked)
    return f"\n  Largest residual contributors: {listed}."


def _couplings_with_spread_nans(mda, count: int = 5) -> list[str]:
    """Coupling variables holding a NaN *after* a real value, i.e. NaN that spread.

    AeroMAPS series are legitimately NaN over the historical years, and a coupling
    belonging to a pathway the scenario does not use is legitimately NaN throughout.
    Neither produces a NaN after a real value; a variable blowing up during the solve
    does, and that is the signature this looks for.
    """
    spread = []
    for name in sorted(mda.coupling_structure.strong_couplings):
        value = mda.io.data.get(name)
        if value is None:
            continue
        try:
            nans = np.isnan(np.asarray(value, dtype=float))
        except (TypeError, ValueError):
            continue
        if not nans.any() or nans.all():
            continue
        if nans[int(np.argmax(~nans)) :].any():
            spread.append(name)
    return spread


def check_mda_convergence(mda_chain, context: str = "", on_failure: str = "raise") -> list[str]:
    """Check that every solver inside ``mda_chain`` reached its tolerance.

    A chain with no strongly coupled disciplines has no solver to check and
    always passes.

    Parameters
    ----------
    mda_chain
        The executed ``MDAChain`` whose ``inner_mdas`` are inspected.
    context
        Prefix identifying the run in the message, e.g. a region name.
    on_failure
        ``"raise"`` (default) to raise :class:`MDAConvergenceError`, ``"warn"``
        to log a warning, ``"ignore"`` to only return the messages.

    Returns
    -------
    failures
        One message per solver that did not converge; empty if all did.
    """
    if on_failure not in ("raise", "warn", "ignore"):
        raise ValueError(f"on_failure must be 'raise', 'warn' or 'ignore', got {on_failure!r}.")

    failures = []
    for mda in getattr(mda_chain, "inner_mdas", []):
        history = list(getattr(mda, "residual_history", []))
        if not history:
            # The solver never ran: nothing was asked of it.
            continue
        residual = float(history[-1])
        tolerance = float(mda.settings.tolerance)

        # A converged residual is not by itself proof of a solution. NaN converts to the
        # -999999 sentinel, so once a coupling variable has gone NaN it differences
        # against itself to exactly zero and the solver reports convergence on a state
        # that carries no values at all. Checked first: it explains the residual, rather
        # than the other way round.
        spread = _couplings_with_spread_nans(mda)
        if spread:
            failures.append(
                f"{context}{mda.name} converged on NaN: {len(spread)} of "
                f"{len(mda.coupling_structure.strong_couplings)} coupling variables hold "
                f"a NaN after a real value, so the residual ({residual:.3e}) is measuring "
                f"the NaN sentinel differencing against itself, not a solution. First "
                f"few: {', '.join(spread[:5])}."
            )
            continue

        if residual <= tolerance:
            continue

        iterations = len(history)
        max_iterations = mda.settings.max_mda_iter
        # Whether more iterations would help is what separates the two fixes, and it is
        # not the same question as whether the iteration cap was reached.
        recent = history[-min(iterations, 10) :]
        still_decreasing = recent[-1] < recent[0]
        if iterations >= max_iterations and still_decreasing:
            cause = (
                f"it ran out of iterations ({iterations}/{max_iterations}) with the "
                "residual still decreasing; raise max_mda_iter"
            )
        elif still_decreasing:
            cause = (
                f"it stopped after {iterations} of {max_iterations} iterations with the "
                "residual still decreasing, which is GEMSEO's divergence guard "
                "(max_consecutive_unsuccessful_iterations)"
            )
        else:
            cause = (
                f"the residual stopped decreasing after {iterations} of "
                f"{max_iterations} iterations; damping (over_relaxation_factor) or an "
                "acceleration_method is what this needs, not more iterations"
            )
        failures.append(
            f"{context}{mda.name} did not converge: residual {residual:.3e} is above "
            f"the requested tolerance {tolerance:.1e} over {len(mda.disciplines)} "
            f"strongly coupled disciplines -- {cause}."
            f"{_worst_residual_contributors(mda)}"
        )

    if failures:
        message = "\n".join(failures)
        if on_failure == "raise":
            raise MDAConvergenceError(message)
        if on_failure == "warn":
            logging.warning(message)
    return failures
