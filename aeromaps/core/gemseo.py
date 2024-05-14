"""A discipline interfacing a Python function."""
from __future__ import annotations

import ast
from inspect import getfullargspec
from inspect import getsource
from typing import Callable
from typing import Iterable
from typing import Sequence
from typing import Union
from typing import get_type_hints

from numpy import array
from numpy import atleast_2d
from numpy import ndarray
import pandas as pd

from gemseo.core.data_processor import DataProcessor
from gemseo.core.discipline import MDODiscipline
from gemseo.utils.data_conversion import split_array_to_dict_of_arrays

from aeromaps.models.base import AeroMAPSModel

DataType = Union[float, ndarray]


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

    Example:
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
        >>> discipline.execute({'x': array([1.]), 'y':array([-3.2])})
        {'x': array([1.]), 'y': array([-3.2]), 'z1': array([-5.4]), 'z2': array([-4.4])}
    """

    py_func: Callable[[DataType, ..., DataType], DataType]
    """The Python function to compute the outputs from the inputs."""

    use_arrays: bool
    """Whether the function is expected to take arrays as inputs and give outputs as
    arrays."""

    py_jac: Callable[[DataType, ..., DataType], ndarray] | None
    """The Python function to compute the Jacobian from the inputs."""

    input_names: list[str]
    """The names of the inputs."""

    output_names: list[str]
    """The names of the outputs."""

    data_processor: AutoDiscDataProcessor
    """A data processor forcing input data to float and output data to arrays."""

    sizes: dict[str, int]
    """The sizes of the input and output variables."""

    def __init__(
        self,
        py_func: Callable[[DataType, ..., DataType], DataType],
        py_jac: Callable[[DataType, ..., DataType], ndarray] | None = None,
        name: str | None = None,
        use_arrays: bool = False,
        grammar_type: MDODiscipline.GrammarType = MDODiscipline.GrammarType.JSON,
    ) -> None:
        """
        Args:
            py_func: The Python function to compute the outputs from the inputs.
            py_jac: The Python function to compute the Jacobian from the inputs;
                its output value must be a 2D NumPy array
                with rows correspond to the outputs
                and columns to the inputs.
            name: The name of the discipline. If ``None``, use the name of the Python
                function.
            use_arrays: Whether the function is expected
                to take arrays as inputs and give outputs as arrays.

        Raises:
            TypeError: When ``py_func`` is not callable.
        """  # noqa: D205 D212 D415
        if not callable(py_func):
            raise TypeError("py_func must be callable.")

        super().__init__(name=name or py_func.__name__, grammar_type=grammar_type)
        self.py_func = py_func
        self.use_arrays = use_arrays
        self.py_jac = py_jac
        self.input_names = getfullargspec(py_func)[0]
        if "self" in self.input_names:
            self.input_names.remove("self")
        self.input_grammar.update_from_names(self.input_names)
        self.output_names = []
        for node in ast.walk(ast.parse(getsource(py_func).strip())):
            if isinstance(node, ast.Return):
                value = node.value
                if isinstance(value, ast.Tuple):
                    temp_output_names = [elt.id for elt in value.elts]
                else:
                    temp_output_names = [value.id]

                if self.output_names and self.output_names != temp_output_names:
                    raise ValueError(
                        "Two return statements use different variable names; "
                        f"{self.output_names} and {temp_output_names}."
                    )
                else:
                    self.output_names = temp_output_names

        self.output_grammar.update_from_names(self.output_names)

        if not use_arrays:
            self.data_processor = AutoDiscDataProcessor(self.output_names)

        if self.py_jac is None:
            self.set_jacobian_approximation()

        self.default_inputs = to_arrays_dict(self._get_defaults())
        self.__sizes = {}
        self.__jac_shape = []
        self.__input_names_with_namespaces = []
        self.__output_names_with_namespaces = []

    def _get_defaults(self) -> dict[str, DataType]:
        """Return the default values of the input variables when available.

        The values are read from the signature of the Python function.

        Returns:
            The default values of the input variables.
        """
        args, _, _, defaults, _, _, _ = getfullargspec(self.py_func)
        if defaults is None:
            return {}

        n_defaults = len(defaults)
        names = args[-n_defaults:]
        return {names[i]: defaults[i] for i in range(n_defaults)}

    def _run(self) -> None:
        input_vals = self.get_input_data(with_namespaces=False)
        input_vals = self._convert_inputs(input_vals)
        output_values = self.py_func(**input_vals)
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
            raise RuntimeError("The analytic Jacobian is missing.")

        if not self.__sizes:
            self.__sizes = {k: v.size for k, v in self.local_data.items()}

            in_to_ns = self.input_grammar.to_namespaced
            self.__input_names_with_namespaces = [
                in_to_ns[input_name] if input_name in in_to_ns else input_name
                for input_name in self.input_names
            ]
            out_to_ns = self.output_grammar.to_namespaced
            self.__output_names_with_namespaces = [
                out_to_ns[output_name] if output_name in out_to_ns else output_name
                for output_name in self.output_names
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
            raise ValueError(
                f"The shape {func_jac.shape} "
                "of the Jacobian matrix "
                f"of the discipline {self.name} "
                f"provided by py_jac "
                "does not match "
                f"(output_size, input_size)={self.__jac_shape}."
            )

        self.jac = split_array_to_dict_of_arrays(
            func_jac,
            self.__sizes,
            self.__output_names_with_namespaces,
            self.__input_names_with_namespaces,
        )

    def _convert_inputs(self, input_vals):
        for name, val in input_vals.items():
            if issubclass(self._get_input_types()[name], pd.Series):
                if len(val) == len(self.model.df.index):
                    input_vals[name] = pd.Series(val, index=self.model.df.index)
                # TODO: make this more generic with module approach
                elif len(val) == len(self.model.df_climate.index):
                    input_vals[name] = pd.Series(val, index=self.model.df_climate.index)
                else:
                    raise ValueError(
                        f"The length of the input {name} is not consistent with the length of the model."
                    )

            elif issubclass(self._get_input_types()[name], int):
                input_vals[name] = int(val)
            else:
                pass
        return input_vals


class AutoDiscDataProcessor(DataProcessor):
    """A data processor forcing input data to float and output data to arrays.

    Convert all |g| scalar input data to floats, and convert all discipline output data
    to NumPy arrays.
    """

    out_names: Sequence[str]
    """The names of the outputs."""

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
                try:
                    processed_data[key] = float(val[0])
                except:
                    processed_data[key] = val[0]

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
                if issubclass(self._get_input_types()[input], pd.Series):
                    self.default_inputs[input] = array(getattr(self.model.parameters, input))
                else:
                    self.default_inputs[input] = array([getattr(self.model.parameters, input)])

    def _get_input_types(self):
        all_types = get_type_hints(self.py_func)
        input_types = {i: all_types[i] for i in all_types if i != "return"}
        return input_types

    def _get_output_types(self):
        all_types = get_type_hints(self.py_func)
        if "return" in all_types:
            types = all_types["return"]
            if hasattr(types, "__args__"):
                output_types_list = all_types["return"].__args__
            else:
                output_types_list = [types]
        else:
            output_types_list = []
        output_names = self.output_names

        output_types = {}
        for indx, output_type in enumerate(output_types_list):
            output_types[output_names[indx]] = output_type

        return output_types

    def update_elements(
        self,
        python_typing=False,  # type: bool
        **elements,  # type: Mapping[str,type]
    ):  # type: (...) -> None
        if python_typing:
            for element_name, element_value in elements.items():
                elements[element_name] = self.get_type_from_python_type(element_value)

        self._names_to_types.update(**elements)
        self._check_types()
