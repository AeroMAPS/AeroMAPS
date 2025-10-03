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
from numbers import Number
from typing import TYPE_CHECKING, ClassVar
from typing import Callable
from typing import Final
from typing import Union
from typing import get_type_hints
from typing import Any
from typing import cast
from multiprocessing import cpu_count

import numpy as np
import pandas as pd

# from gemseo.caches.memory_full_cache import MemoryFullCache
# from gemseo.core.data_converters.json import JSONGrammarDataConverter
from gemseo.core.data_converters.simple import SimpleGrammarDataConverter
from gemseo.core.grammars.simple_grammar import SimpleGrammar
from gemseo.core.grammars.json_grammar import JSONGrammar

# from gemseo.disciplines.auto_py import AutoPyDiscipline
# from numpy import array
from numpy import atleast_2d
from numpy import ndarray
from numpy import array
from typing_extensions import get_args
from typing_extensions import get_origin

from gemseo.core.discipline.data_processor import DataProcessor
from gemseo.utils.data_conversion import split_array_to_dict_of_arrays
from gemseo.utils.source_parsing import get_callable_argument_defaults
from gemseo.disciplines.auto_py import AutoPyDiscipline
from gemseo.core.discipline import Discipline

from aeromaps.models.base import AeroMAPSModel

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Sequence
    from gemseo.typing import NumberArray

    ValueType = Union[int, float, complex, NumberArray]

DataType = Union[float, ndarray]

LOGGER = logging.getLogger(__name__)


class ExtendedJSONGrammar(JSONGrammar):
    DATA_CONVERTER_CLASS: ClassVar[str] = "CustomDataConverter"
    __PYTHON_TO_JSON_TYPES: Final[dict[type, str]] = {
        **JSONGrammar._JSONGrammar__PYTHON_TO_JSON_TYPES,
        # Add your additional types here
        Number: "number",
        pd.Series: "array",
    }


# TRY TO BE CLEAN WITH JSON GRAMMAR DATA CONVERTER
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
        array_ = np.nan_to_num(array_, nan=-999999)
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


class AeroMAPSModelWrapper(AutoPyDiscipline):
    """
    Wraps the AeroMAPSModel class into a discipline.
    Inputs and outputs are automatically declared from the model's compute() function signature.
    """

    def __init__(self, model):
        self.model: AeroMAPSModel = model

        self.default_grammar_type = Discipline.GrammarType.SIMPLE

        super(AeroMAPSModelWrapper, self).__init__(
            py_func=self.model.compute,
            use_arrays=True,
        )

        if hasattr(self.model, "auto_inputs"):
            self.input_grammar.update_from_types(
                self.model.auto_inputs
            )  # Explicit addition of auto-generated inputs
            if "kwargs" in self.input_grammar.names:
                self.input_grammar.required_names.remove("kwargs")

        if hasattr(self.model, "auto_outputs"):
            self.output_grammar.update_from_types(
                self.model.auto_outputs
            )  # Explicit addition of auto-generated outputs

        self.name = model.__class__.__name__

        self.update_defaults()

    def update_defaults(self):
        for input in self.input_names:
            # if self.model.parameters is None:
            #     self.default_inputs[input] = array([0])
            if hasattr(self.model.parameters, input):
                self.default_input_data[input] = getattr(self.model.parameters, input)
