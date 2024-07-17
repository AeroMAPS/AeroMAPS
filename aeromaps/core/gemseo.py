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
"""A discipline interfacing a Python function."""

from __future__ import annotations

import ast
import logging
from inspect import getfullargspec
from inspect import getsource
from typing import TYPE_CHECKING
from typing import Callable
from typing import Final
from typing import Union
from typing import get_type_hints

from numpy import array
from numpy import atleast_2d
from numpy import ndarray
from typing_extensions import get_args
from typing_extensions import get_origin

from gemseo.core.data_processor import DataProcessor
from gemseo.core.discipline import MDODiscipline
from gemseo.utils.data_conversion import split_array_to_dict_of_arrays
from gemseo.utils.source_parsing import get_callable_argument_defaults

from aeromaps.models.base import AeroMAPSModel

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Sequence

DataType = Union[float, ndarray]

LOGGER = logging.getLogger(__name__)

import logging
from itertools import repeat
from multiprocessing import cpu_count
from pathlib import Path
from typing import TYPE_CHECKING

from numpy import array

from gemseo import create_mda
from gemseo.core.chain import MDOChain
from gemseo.core.chain import MDOParallelChain
from gemseo.core.discipline import MDODiscipline
from gemseo.core.execution_sequence import SerialExecSequence
from gemseo.mda.initialization_chain import MDOInitializationChain
from gemseo.mda.mda import MDA

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Mapping
    from collections.abc import Sequence
    from typing import Any

    from gemseo.core.coupling_structure import MDOCouplingStructure
    from gemseo.core.discipline_data import DisciplineData
    from gemseo.utils.matplotlib_figure import FigSizeType

LOGGER = logging.getLogger(__name__)

N_CPUS = cpu_count()


class AutoPyDiscipline(MDODiscipline):
    """Wrap a Python function into a discipline.

    A simplified and straightforward way of integrating a discipline
    from a Python function.

    The Python function can take and return only numbers and NumPy arrays.

    The Python function may or may not include default values for input arguments,
    however, if the resulting :class:`.AutoPyDiscipline` is going to be placed inside
    an :class:`.MDF`, a :class:`.BiLevel` formulation or an :class:`.MDA`
    with strong couplings, then the Python function **must** assign default values for
    its input arguments.

    Examples:
        >>> from gemseo.disciplines.auto_py import AutoPyDiscipline
        >>> from numpy import array
        >>> def my_function(x=0., y=0.):
        >>>     z1 = x + 2*y
        >>>     z2 = x + 2*y + 1
        >>>     return z1, z2
        >>>
        >>> discipline = AutoPyDiscipline(my_function)
        >>> discipline.execute()
        {'x': array([0.]), 'y': array([0.]), 'z1': array([0.]), 'z2': array([1.])}
        >>> discipline.execute({"x": array([1.0]), "y": array([-3.2])})
        {'x': array([1.]), 'y': array([-3.2]), 'z1': array([-5.4]), 'z2': array([-4.4])}
    """

    py_func: Callable
    """The Python function to compute the outputs from the inputs."""

    py_jac: Callable | None
    """The Python function to compute the Jacobian from the inputs."""

    # TODO: API: remove since it is not used.
    use_arrays: bool
    """Whether the function is expected to take arrays as inputs and give outputs as
    arrays."""

    # TODO: API: remove since this feature is provided by the base class.
    input_names: list[str]
    """The names of the inputs."""

    # TODO: API: remove since this feature is provided by the base class.
    output_names: list[str]
    """The names of the outputs."""

    data_processor: AutoDiscDataProcessor
    """A data processor forcing input data to float and output data to arrays."""

    sizes: dict[str, int]
    """The sizes of the input and output variables."""

    __LOG_PREFIX: Final[str] = "Discipline %s: py_func has"

    def __init__(
        self,
        py_func: Callable,
        py_jac: Callable | None = None,
        name: str | None = None,
        use_arrays: bool = False,
        grammar_type: MDODiscipline.GrammarType = MDODiscipline.GrammarType.JSON,
    ) -> None:
        """
        Args:
            py_func: The Python function to compute the outputs from the inputs.
            py_jac: The Python function to compute the Jacobian from the inputs;
                its output value must be a 2D NumPy array
                with rows corresponding to the outputs and columns to the inputs.
            name: The name of the discipline.
                If ``None``, use the name of the Python function.
            use_arrays: Whether the function is expected
                to take arrays as inputs and give outputs as arrays.

        Raises:
            TypeError: When ``py_func`` is not callable.
        """  # noqa: D205 D212 D415
        if not callable(py_func):
            msg = "py_func must be callable."
            raise TypeError(msg)

        super().__init__(name=name or py_func.__name__, grammar_type=grammar_type)
        self.py_func = py_func
        self.use_arrays = use_arrays
        self.py_jac = py_jac
        self.input_names = getfullargspec(self.py_func).args
        if "self" in self.input_names:
            self.input_names.remove("self")
        self.output_names = self.__create_output_names()
        have_type_hints = self.__create_grammars()

        if not have_type_hints and not use_arrays:
            # When type hints are used, the conversions will be handled automatically
            # by the grammars.
            self.data_processor = AutoDiscDataProcessor(self.output_names)

        if self.py_jac is None:
            self.set_jacobian_approximation()

        self.__sizes = {}
        self.__jac_shape = []
        self.__input_names_with_namespaces = []
        self.__output_names_with_namespaces = []

    def __create_grammars(self) -> bool:
        """Create the grammars.

        The grammars use type hints from the function if both the arguments and the
        return value have complete type hints. Otherwise, the grammars will have ndarray
        types.

        Returns:
            Whether type hints are used.
        """
        type_hints = get_type_hints(self.py_func)
        return_type = type_hints.pop("return", None)

        # First, determine if both the inputs and outputs have type hints, otherwise
        # that would make things complicated for no good reason.
        names_to_input_types = {}

        if type_hints:
            missing_args_types = set(self.input_names).difference(type_hints.keys())
            if missing_args_types:
                msg = f"{self.__LOG_PREFIX} missing type hints for the arguments: %s."
                LOGGER.warning(msg, self.name, ",".join(missing_args_types))
            else:
                names_to_input_types = type_hints

        names_to_output_types = {}

        if return_type is not None:
            # There could be only one return value of type tuple, or multiple return
            # values that would also be type hinted with tuple.
            if len(self.output_names) == 1:
                names_to_output_types = {self.output_names[0]: return_type}
            else:
                origin = get_origin(return_type)
                if origin is not tuple:
                    msg = (
                        f"{self.__LOG_PREFIX} bad return type hints: "
                        "expecting a tuple of types, got %s."
                    )
                    LOGGER.warning(msg, self.name, return_type)
                else:
                    type_args = get_args(return_type)
                    n_type_args = len(type_args)
                    n_output_names = len(self.output_names)
                    if n_type_args != n_output_names:
                        msg = (
                            f"{self.__LOG_PREFIX} bad return type hints: "
                            "the number of return values and return types shall be "
                            "equal: "
                            "%i return values but %i return type hints."
                        )
                        LOGGER.warning(msg, self.name, n_output_names, n_type_args)
                    else:
                        names_to_output_types = dict(zip(self.output_names, type_args))

        defaults = get_callable_argument_defaults(self.py_func)

        # Second, create the grammar according to the pre-processing above.
        if names_to_input_types and names_to_output_types:
            self.input_grammar.update_from_types(names_to_input_types)
            self.input_grammar.defaults = defaults
            self.output_grammar.update_from_types(names_to_output_types)
            return True

        msg = (
            f"{self.__LOG_PREFIX} inconsistent type hints: "
            "either both the signature arguments and the return values shall have "
            "type hints or none. "
            "The grammars will not use the type hints at all."
        )
        LOGGER.warning(msg, self.name)
        self.input_grammar.update_from_names(self.input_names)

        for key, value in defaults.items():
            if not isinstance(value, ndarray):
                defaults[key] = array([value])
        self.input_grammar.defaults = defaults

        self.output_grammar.update_from_names(self.output_names)
        return False

    def __create_output_names(self) -> list[str]:
        """Create the names of the outputs.

        Returns:
            The names of the outputs.
        """
        output_names = []

        for node in ast.walk(ast.parse(getsource(self.py_func).strip())):
            if not isinstance(node, ast.Return):
                continue

            value = node.value

            if isinstance(value, ast.Tuple):
                temp_output_names = [elt.id for elt in value.elts]
            else:
                temp_output_names = [value.id]

            if output_names and output_names != temp_output_names:
                msg = (
                    "Two return statements use different variable names; "
                    f"{output_names} and {temp_output_names}."
                )
                raise ValueError(msg)

            output_names = temp_output_names

        return output_names

    def _run(self) -> None:
        output_values = self.py_func(**self.get_input_data(with_namespaces=False))
        if len(self.output_names) == 1:
            output_values = {self.output_names[0]: output_values}
        else:
            output_values = dict(zip(self.output_names, output_values))
        self.store_local_data(**output_values)

    def _compute_jacobian(
        self,
        inputs: Iterable[str] | None = None,
        outputs: Iterable[str] | None = None,
    ) -> None:
        """
        Raises:
            RuntimeError: When the analytic Jacobian :attr:`.py_jac` is ``None``.
            ValueError: When the Jacobian shape is inconsistent.
        """  # noqa: D205 D212 D415
        if self.py_jac is None:
            msg = "The analytic Jacobian is missing."
            raise RuntimeError(msg)

        if not self.__sizes:
            for name, value in self._local_data.items():
                if name in self.input_grammar:
                    converter = self.input_grammar.data_converter
                else:
                    converter = self.output_grammar.data_converter
                self.__sizes[name] = converter.get_value_size(name, value)

            in_to_ns = self.input_grammar.to_namespaced
            self.__input_names_with_namespaces = [
                in_to_ns.get(input_name, input_name) for input_name in self.input_names
            ]
            out_to_ns = self.output_grammar.to_namespaced
            self.__output_names_with_namespaces = [
                out_to_ns.get(output_name, output_name) for output_name in self.output_names
            ]
            self.__jac_shape = (
                sum(
                    self.__sizes[output_name] for output_name in self.__output_names_with_namespaces
                ),
                sum(self.__sizes[input_name] for input_name in self.__input_names_with_namespaces),
            )

        func_jac = self.py_jac(**self.get_input_data(with_namespaces=False))
        if len(func_jac.shape) < 2:
            func_jac = atleast_2d(func_jac)
        if func_jac.shape != self.__jac_shape:
            msg = (
                f"The shape {func_jac.shape} "
                "of the Jacobian matrix "
                f"of the discipline {self.name} "
                f"provided by py_jac "
                "does not match "
                f"(output_size, input_size)={self.__jac_shape}."
            )
            raise ValueError(msg)

        self.jac = split_array_to_dict_of_arrays(
            func_jac,
            self.__sizes,
            self.__output_names_with_namespaces,
            self.__input_names_with_namespaces,
        )


class AutoDiscDataProcessor(DataProcessor):
    """A data processor forcing input data to float and output data to arrays.

    Convert all |g| scalar input data to floats, and convert all discipline output data
    to NumPy arrays.
    """

    # TODO: API: this is never used, remove?
    out_names: Sequence[str]
    """The names of the outputs."""

    # TODO: API: this is never used, remove?
    one_output: bool
    """Whether there is a single output."""

    def __init__(
        self,
        out_names: Sequence[str],
    ) -> None:
        """
        Args:
            out_names: The names of the outputs.
        """  # noqa: D205 D212 D415
        super().__init__()
        self.out_names = out_names
        self.one_output = len(out_names) == 1

    def pre_process_data(self, data: dict[str, DataType]) -> dict[str, DataType]:
        """Pre-process the input data.

        Execute a pre-processing of input data
        after they are checked by :meth:`~MDODiscipline.check_input_data`,
        and before the :meth:`~MDODiscipline._run` method of the discipline is called.

        Args:
            data: The data to be processed.

        Returns:
            The processed data
            where one-length NumPy arrays have been replaced with floats.
        """
        processed_data = data.copy()
        for key, val in data.items():
            if len(val) == 1:
                processed_data[key] = float(val[0])

        return processed_data

    def post_process_data(self, data: dict[str, DataType]) -> dict[str, ndarray]:
        """Post-process the output data.

        Execute a post-processing of the output data
        after the :meth:`~MDODiscipline._run` method of the discipline is called,
        and before they are checked by :meth:`~MDODiscipline.check_output_data`.

        Args:
            data: The data to be processed.

        Returns:
            The processed data with NumPy arrays as values.
        """
        processed_data = data.copy()
        for output_name, output_value in processed_data.items():
            if not isinstance(output_value, ndarray):
                processed_data[output_name] = array([output_value])

        return processed_data


# TODO: API: remove since it is not used.
def to_arrays_dict(data: dict[str, DataType]) -> dict[str, ndarray]:
    """Ensure that the values of a dictionary are NumPy arrays.

    Args:
        data: The dictionary whose values must be NumPy arrays.

    Returns:
        The dictionary with NumPy arrays as values.
    """
    for key, value in data.items():
        if not isinstance(value, ndarray):
            data[key] = array([value])
    return data


class AeroMAPSModelWrapper(AutoPyDiscipline):
    def __init__(self, model):
        self.model: AeroMAPSModel = model

        super(AeroMAPSModelWrapper, self).__init__(
            py_func=self.model.compute, grammar_type=MDODiscipline.GrammarType.SIMPLE
        )

        self.name = model.__class__.__name__

        self.update_defaults()

    def update_defaults(self):
        for input in self.get_input_data_names():
            # if self.model.parameters is None:
            #     self.default_inputs[input] = array([0])
            if hasattr(self.model.parameters, input):
                self.default_inputs[input] = getattr(self.model.parameters, input)





class MDAChain(MDA):
    """A chain of MDAs.

    The execution sequence is provided by the :class:`.DependencyGraph`.
    """

    inner_mdas: list[MDA]
    """The ordered MDAs."""

    __initialize_defaults: bool
    """Whether to compute the eventually missing :attr:`.default_inputs`."""

    def __init__(
        self,
        disciplines: Sequence[MDODiscipline],
        inner_mda_name: str = "MDAJacobi",
        max_mda_iter: int = 20,
        name: str | None = None,
        n_processes: int = N_CPUS,
        chain_linearize: bool = False,
        tolerance: float = 1e-6,
        linear_solver_tolerance: float = 1e-12,
        use_lu_fact: bool = False,
        grammar_type: MDODiscipline.GrammarType = MDODiscipline.GrammarType.JSON,
        coupling_structure: MDOCouplingStructure | None = None,
        sub_coupling_structures: Iterable[MDOCouplingStructure | None] | None = None,
        log_convergence: bool = False,
        linear_solver: str = "DEFAULT",
        linear_solver_options: Mapping[str, Any] | None = None,
        mdachain_parallelize_tasks: bool = False,
        mdachain_parallel_options: Mapping[str, int | bool] | None = None,
        initialize_defaults: bool = False,
        **inner_mda_options: float | int | bool | str | None,
    ) -> None:
        """
        Args:
            inner_mda_name: The class name of the inner-MDA.
            n_processes: The maximum simultaneous number of threads if ``use_threading``
                is set to True, otherwise processes, used to parallelize the execution.
            chain_linearize: Whether to linearize the chain of execution. Otherwise,
                linearize the overall MDA with base class method. This last option is
                preferred to minimize computations in adjoint mode, while in direct
                mode, linearizing the chain may be cheaper.
            sub_coupling_structures: The coupling structures to be used by the
                inner-MDAs. If ``None``, they are created from the sub-disciplines.
            mdachain_parallelize_tasks: Whether to parallelize the parallel tasks, if
                any.
            mdachain_parallel_options: The options of the MDOParallelChain instances, if
                any.
            initialize_defaults: Whether to create a :class:`.MDOInitializationChain`
                to compute the eventually missing :attr:`.default_inputs` at the first
                execution.
            **inner_mda_options: The options of the inner-MDAs.
        """  # noqa:D205 D212 D415
        self.n_processes = n_processes
        self.mdo_chain = None
        self._chain_linearize = chain_linearize
        self.inner_mdas = []

        # compute execution sequence of the disciplines
        super().__init__(
            disciplines,
            max_mda_iter=max_mda_iter,
            name=name,
            grammar_type=grammar_type,
            tolerance=tolerance,
            linear_solver_tolerance=linear_solver_tolerance,
            use_lu_fact=use_lu_fact,
            coupling_structure=coupling_structure,
            linear_solver=linear_solver,
            linear_solver_options=linear_solver_options,
        )

        if not self.coupling_structure.all_couplings and not self._chain_linearize:
            LOGGER.warning("No coupling in MDA, switching chain_linearize to True.")
            self._chain_linearize = True

        self._create_mdo_chain(
            disciplines,
            inner_mda_name=inner_mda_name,
            sub_coupling_structures=sub_coupling_structures,
            mdachain_parallelize_tasks=mdachain_parallelize_tasks,
            mdachain_parallel_options=mdachain_parallel_options,
            **inner_mda_options,
        )

        self.log_convergence = log_convergence
        self._initialize_grammars()
        self.__initialize_defaults = initialize_defaults
        self._check_consistency()
        self._compute_input_couplings()

        # cascade the tolerance
        for mda in self.inner_mdas:
            mda.tolerance = self.tolerance

    @property
    def max_mda_iter(self) -> int:
        """The maximum iterations number of each of the inner MDA algorithms."""
        return super().max_mda_iter

    @max_mda_iter.setter
    def max_mda_iter(self, max_mda_iter: int) -> None:  # noqa: D102
        self._max_mda_iter = max_mda_iter
        for mda in self.inner_mdas:
            mda.max_mda_iter = max_mda_iter

    @MDA.log_convergence.setter
    def log_convergence(  # noqa: D102
        self,
        value: bool,
    ) -> None:
        self._log_convergence = value
        for mda in self.inner_mdas:
            mda.log_convergence = value

    def _create_mdo_chain(
        self,
        disciplines: Sequence[MDODiscipline],
        inner_mda_name: str = "MDAJacobi",
        sub_coupling_structures: Iterable[MDOCouplingStructure | None] | None = None,
        mdachain_parallelize_tasks: bool = False,
        mdachain_parallel_options: Mapping[str, int | bool] | None = None,
        **inner_mda_options: float | int | bool | str | None,
    ) -> None:
        """Create an MDO chain from the execution sequence of the disciplines.

        Args:
            disciplines: The disciplines.
            inner_mda_name: The name of the class of the inner-MDAs.
            acceleration: The acceleration method to be used to improve the convergence
                rate of the fixed point iteration method.
            over_relax_factor: The over-relaxation factor.
            sub_coupling_structures: The coupling structures to be used by the inner
                MDAs. If ``None``, they are created from the sub-disciplines.
            mdachain_parallelize_tasks: Whether to parallelize the
                parallel tasks, if any.
            mdachain_parallel_options: The options of the MDOParallelChain instances,
                if any.
            **inner_mda_options: The options of the inner-MDAs.
        """
        if sub_coupling_structures is None:
            sub_coupling_structures = repeat(None)

        self.__sub_coupling_structures_iterator = iter(sub_coupling_structures)

        chained_disciplines = []
        for parallel_tasks in self.coupling_structure.sequence:
            process = self.__create_process_from_disciplines(
                disciplines,
                inner_mda_name,
                parallel_tasks,
                mdachain_parallelize_tasks,
                mdachain_parallel_options,
                inner_mda_options,
            )
            chained_disciplines.append(process)

        self.mdo_chain = MDOChain(
            chained_disciplines, name="MDA chain", grammar_type=self.grammar_type
        )

    def __create_process_from_disciplines(
        self,
        disciplines: Sequence[MDODiscipline],
        inner_mda_name: str,
        parallel_tasks: list[tuple[MDODiscipline]],
        mdachain_parallelize_tasks: bool,
        mdachain_parallel_options: Mapping[str, int | bool] | None,
        inner_mda_options: Mapping[str, float | int | bool | str | None],
    ) -> MDODiscipline:
        """Create a process from disciplines.

        This method creates a process that will be appended to the main inner
        :class:`.MDOChain` of the :class:`.MDAChain`. Depending on the number and type
        of disciplines, as well as the options provided by the user, the process may be
        a sole discipline, a :class:`.MDA`, a :class:`MDOChain`, or a
        :class:`MDOParallelChain`.

        Args:
            disciplines: The disciplines.
            inner_mda_name: The inner :class:`.MDA` class name.
            acceleration: The acceleration method to be used to improve the convergence
                rate of the fixed point iteration method.
            over_relax_factor: The over-relaxation factor.
            parallel_tasks: The parallel tasks to be processed.
            mdachain_parallelize_tasks: Whether to parallelize the parallel tasks,
                if any.
            mdachain_parallel_options: The :class:`MDOParallelChain` options.
            inner_mda_options: The inner :class:`.MDA` options.

        Returns:
            A process.
        """
        parallel_disciplines = self.__compute_parallel_disciplines(
            disciplines,
            inner_mda_name,
            parallel_tasks,
            inner_mda_options,
        )

        return self.__create_process_from_parallel_disciplines(
            parallel_disciplines,
            mdachain_parallelize_tasks,
            mdachain_parallel_options,
        )

    def __compute_parallel_disciplines(
        self,
        disciplines: Sequence[MDODiscipline],
        inner_mda_name: str,
        parallel_tasks: list[tuple[MDODiscipline]],
        inner_mda_options: Mapping[str, float | int | bool | str | None],
    ) -> Sequence[MDODiscipline | MDA]:
        """Compute the parallel disciplines.

        This method computes the parallel disciplines,
        if any.
        If there is any coupled disciplines in a parallel task,
        an :class:`.MDA` is created,
        based on the :class:`.MDA` options provided.

        Args:
            disciplines: The disciplines.
            inner_mda_name: The inner :class:`.MDA` class name.
            acceleration: The acceleration method to be used to improve the convergence
                rate of the fixed point iteration method.
            over_relax_factor: The over-relaxation factor.
            parallel_tasks: The parallel tasks.
            inner_mda_name: The inner :class:`.MDA` class name.
            inner_mda_options: The inner :class:`.MDA` options.

        Returns:
            The parallel disciplines.
        """
        parallel_disciplines = []
        for coupled_disciplines in parallel_tasks:
            is_one_discipline_self_coupled = self.__is_one_discipline_self_coupled(
                coupled_disciplines
            )
            if len(coupled_disciplines) > 1 or is_one_discipline_self_coupled:
                discipline = self.__create_inner_mda(
                    disciplines,
                    coupled_disciplines,
                    inner_mda_name,
                    inner_mda_options,
                )
                self.inner_mdas.append(discipline)
            else:
                discipline = coupled_disciplines[0]

            parallel_disciplines.append(discipline)
        return parallel_disciplines

    def __create_process_from_parallel_disciplines(
        self,
        parallel_disciplines: Sequence[MDODiscipline],
        mdachain_parallelize_tasks: bool,
        mdachain_parallel_options: Mapping[str, int | bool] | None,
    ) -> MDODiscipline | MDOChain | MDOParallelChain:
        """Create a process from parallel disciplines.

        Depending on the number of disciplines and the options provided,
        the returned GEMSEO process can be a sole :class:`.MDODiscipline` instance,
        an :class:`.MDOChain` or an :class:`.MDOParallelChain`.

        Args:
            parallel_disciplines: The parallel disciplines.
            mdachain_parallelize_tasks: Whether to parallelize the parallel tasks.
            mdachain_parallel_options: The options of the :class:`.MDOParallelChain`.

        Returns:
            A GEMSEO process instance.
        """
        if len(parallel_disciplines) == 1:
            return parallel_disciplines[0]

        return self.__create_sequential_or_parallel_chain(
            parallel_disciplines,
            mdachain_parallelize_tasks,
            mdachain_parallel_options,
        )

    def __create_inner_mda(
        self,
        disciplines: Sequence[MDODiscipline],
        coupled_disciplines: Sequence[MDODiscipline],
        inner_mda_name: str,
        inner_mda_options: Mapping[str, float | int | bool | str | None],
    ) -> MDA:
        """Create an inner MDA from the coupled disciplines and the MDA options.

        Args:
            disciplines: The disciplines.
            coupled_disciplines: The coupled disciplines.
            inner_mda_name: The inner :class:`.MDA` class name.
            inner_mda_options: The inner :class:`.MDA` options.
            acceleration: The acceleration method to be used to improve the convergence
                rate of the fixed point iteration method.
            over_relax_factor: The over-relaxation factor.

        Returns:
            The :class:`.MDA` instance.
        """
        inner_mda_disciplines = self.__get_coupled_disciplines_initial_order(
            coupled_disciplines, disciplines
        )
        mda = create_mda(
            inner_mda_name,
            inner_mda_disciplines,
            max_mda_iter=self.max_mda_iter,
            tolerance=self.tolerance,
            linear_solver_tolerance=self.linear_solver_tolerance,
            grammar_type=self.grammar_type,
            use_lu_fact=self.use_lu_fact,
            linear_solver=self.linear_solver,
            linear_solver_options=self.linear_solver_options,
            coupling_structure=next(self.__sub_coupling_structures_iterator),
            **inner_mda_options,
        )

        mda.n_processes = self.n_processes

        return mda

    def __is_one_discipline_self_coupled(
        self, disciplines: Sequence[MDODiscipline]
    ) -> bool:
        """Return whether only one self-coupled discipline which is also not an MDA.

        Args:
            disciplines: The disciplines.

        Returns:
            True if the sole discipline of coupled_disciplines is self-coupled
            and not an MDA.
        """
        first_discipline = disciplines[0]
        return (
            len(disciplines) == 1
            and self.coupling_structure.is_self_coupled(first_discipline)
            and not isinstance(disciplines[0], MDA)
        )

    @staticmethod
    def __get_coupled_disciplines_initial_order(
        coupled_disciplines: Sequence[MDODiscipline],
        disciplines: Sequence[MDODiscipline],
    ) -> list[MDODiscipline]:
        """Get the coupled disciplines in the same order as initially given by the user.

        Args:
            coupled_disciplines: The coupled disciplines.
            disciplines: The disciplines.

        Returns:
            The ordered list of coupled disciplines.
        """
        return [disc for disc in disciplines if disc in coupled_disciplines]

    def __create_sequential_or_parallel_chain(
        self,
        parallel_disciplines: Sequence[MDODiscipline],
        mdachain_parallelize_tasks: bool,
        mdachain_parallel_options: Mapping[str, int | bool] | None,
    ) -> MDOChain | MDOParallelChain:
        """Create an :class:`.MDOChain` or :class:`.MDOParallelChain`.

        Args:
            parallel_disciplines: The parallel disciplines.
            mdachain_parallelize_tasks: Whether to parallelize the parallel tasks,
                if any.
            mdachain_parallel_options: The :class:`MDOParallelChain options.

        Returns:
            Either an :class:`.MDOChain` or :class:`.MDOParallelChain instance.
        """
        if mdachain_parallelize_tasks:
            return self.__create_mdo_parallel_chain(
                parallel_disciplines,
                mdachain_parallel_options,
            )
        return MDOChain(parallel_disciplines, grammar_type=self.grammar_type)

    def __create_mdo_parallel_chain(
        self,
        parallel_disciplines: Sequence[MDODiscipline],
        mdachain_parallel_options: Mapping[str, int | bool] | None,
    ) -> MDOParallelChain:
        """Create an :class:`.MDOParallelChain`.

        Args:
            parallel_disciplines: The parallel disciplines.
            mdachain_parallel_options: The :class:`.MDOParallelChain` options.

        Returns:
            an :class:`.MDOParallelChain` instance.
        """
        if mdachain_parallel_options is None:
            mdachain_parallel_options = {}

        return MDOParallelChain(
            parallel_disciplines,
            grammar_type=self.grammar_type,
            name=None,
            **mdachain_parallel_options,
        )

    def _initialize_grammars(self) -> None:
        """Define all inputs and outputs of the chain."""
        if self.mdo_chain is None:  # First call by super class must be ignored.
            return
        self.input_grammar = self.mdo_chain.input_grammar.copy()
        self.output_grammar = self.mdo_chain.output_grammar.copy()

    def _check_consistency(self) -> None:
        """Check if there is no more than 1 equation per variable.

        For instance if a strong coupling is not also a self coupling.
        """
        if self.mdo_chain is None:  # First call by super class must be ignored.
            return
        super()._check_consistency()

    def execute(  # noqa:D102
        self, input_data: Mapping[str, Any] | None = None
    ) -> DisciplineData:
        if self.__initialize_defaults:
            init_chain = MDOInitializationChain(
                self.disciplines,
                grammar_type=self.grammar_type,
                available_data_names=input_data or ()
            )
            input_defaults = init_chain.execute(input_data)

            # Iterate over the input_defaults
            for key, value in input_defaults.items():
              # Check if the current input exists in the input_grammar
              if key in self.input_grammar:
                # If the input exists, update the default inputs with the value
                self.default_inputs[key] = value
            # self.default_inputs.update(input_defaults)
            self.__initialize_defaults = False
        return super().execute(input_data=input_data)

    def _run(self) -> None:
        super()._run()

        self.local_data = self.mdo_chain.execute(self.local_data)

        res_sum = 0.0
        for mda in self.inner_mdas:
            res_local = mda.local_data.get(self.RESIDUALS_NORM)
            if res_local is not None:
                res_sum += res_local[-1] ** 2
        self.local_data[self.RESIDUALS_NORM] = array([res_sum**0.5])

    def _compute_jacobian(
        self,
        inputs: Sequence[str] | None = None,
        outputs: Sequence[str] | None = None,
    ) -> None:
        if self._chain_linearize:
            self.mdo_chain.add_differentiated_inputs(inputs)
            self.mdo_chain.add_differentiated_outputs(outputs)
            # the Jacobian of the MDA chain is the Jacobian of the MDO chain
            self.mdo_chain.linearize(self.get_input_data())
            self.jac = self.mdo_chain.jac
        else:
            super()._compute_jacobian(inputs, outputs)

    def add_differentiated_inputs(  # noqa:D102
        self,
        inputs: Iterable[str] | None = None,
    ) -> None:
        MDA.add_differentiated_inputs(self, inputs)
        if self._chain_linearize:
            self.mdo_chain.add_differentiated_inputs(inputs)

    def add_differentiated_outputs(  # noqa: D102
        self,
        outputs: Iterable[str] | None = None,
    ) -> None:
        MDA.add_differentiated_outputs(self, outputs=outputs)
        if self._chain_linearize:
            self.mdo_chain.add_differentiated_outputs(outputs)

    @property
    def normed_residual(self) -> float:
        """The normed_residuals, computed from the sub-MDAs residuals."""
        return sum(mda.normed_residual**2 for mda in self.inner_mdas) ** 0.5

    @normed_residual.setter
    def normed_residual(
        self,
        normed_residual: float,
    ) -> None:
        """Set the normed_residual.

        Has no effect, since the normed residuals are defined by inner-MDAs residuals
        (see associated property).

        Here for compatibility with mother class.
        """

    def get_expected_dataflow(  # noqa:D102
        self,
    ) -> list[tuple[MDODiscipline, MDODiscipline, list[str]]]:
        return self.mdo_chain.get_expected_dataflow()

    def get_expected_workflow(self) -> SerialExecSequence:  # noqa:D102
        exec_s = SerialExecSequence()
        workflow = self.mdo_chain.get_expected_workflow()
        exec_s.extend(workflow)
        return exec_s

    def get_disciplines_in_dataflow_chain(self) -> list[MDODiscipline]:  # noqa: D102
        return self.mdo_chain.get_disciplines_in_dataflow_chain()

    def reset_statuses_for_run(self) -> None:  # noqa:D102
        super().reset_statuses_for_run()
        self.mdo_chain.reset_statuses_for_run()

    def plot_residual_history(  # noqa: D102
        self,
        show: bool = False,
        save: bool = True,
        n_iterations: int | None = None,
        logscale: tuple[int, int] | None = None,
        filename: Path | str = "",
        fig_size: FigSizeType = (50.0, 10.0),
    ) -> None:
        if filename:
            file_path = Path(filename)
        for mda in self.inner_mdas:
            if filename:
                path = file_path.parent / f"{mda.__class__.__name__}_{file_path.name}"
            else:
                path = filename
            mda.plot_residual_history(
                show, save, n_iterations, logscale, path, fig_size
            )
