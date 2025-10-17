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

import logging
from typing import TYPE_CHECKING, Any
from typing import Union
import pandas as pd
from gemseo.core.data_converters.simple import SimpleGrammarDataConverter
from gemseo.core.grammars.simple_grammar import SimpleGrammar
# from gemseo.core.grammars.simpler_grammar import SimplerGrammar
from gemseo.disciplines.auto_py import AutoPyDiscipline
from numpy import ndarray
from gemseo.core.discipline import Discipline
from aeromaps.models.base import AeroMAPSModel

if TYPE_CHECKING:
    from gemseo.typing import NumberArray

    ValueType = Union[int, float, complex, NumberArray]

DataType = Union[float, ndarray]
LOGGER = logging.getLogger(__name__)


class DataConverter(SimpleGrammarDataConverter):
    """A data converter where ``x_shared`` is not a ndarray and handles pd.Series."""

    def convert_value_to_array(self, name: str, value: Any) -> ndarray:  # noqa: D102 # pragma: no cover
        print(f"(Undesired loop ?) using custom data converter for {name}; {value}")
        if isinstance(value, pd.Series):
            return value.values
        return super().convert_value_to_array(name, value)


SimpleGrammar.DATA_CONVERTER_CLASS = DataConverter


class AeroMAPSAutoModelWrapper(AutoPyDiscipline):
    """
    Wraps the AeroMAPSModel class into a discipline.
    Inputs and outputs are automatically declared from the model's compute() function signature.
    """

    def __init__(self, model):
        self.model: AeroMAPSModel = model

        # TODO: Explore possibility to use json grammar
        self.default_grammar_type = Discipline.GrammarType.SIMPLE

        super(AeroMAPSAutoModelWrapper, self).__init__(
            py_func=self.model.compute,
        )
        # self.io.data_processor = AutoDiscDataProcessor()

        self.name = model.__class__.__name__

        self.update_defaults()

    def update_defaults(self):
        for input in self.get_input_data():
            # if self.model.parameters is None:
            #     self.default_inputs[input] = array([0])
            if hasattr(self.model.parameters, input):
                self.default_input_data[input] = getattr(self.model.parameters, input)


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

        # TODO: explore data converters e.g. to convert pd.Series to np.array for MDA handling -- > Done in optim branch
        # self.io.data_processor = AutoDiscDataProcessor()

    def _run(self, input_data):
        if hasattr(self.model, "compute"):
            return self.model.compute(input_data)
        else:
            raise AttributeError(f"Model {self.name} does not have a compute method")

    def update_defaults(self):

        # Set default values if provided internally by the model (see e.g. LCA module)
        if self.model.default_input_data:
            self.default_input_data.update(self.model.default_input_data)

        # TODO: check if the following is still used because main branch uses obsolete self.default_inputs instead of self.default_input_data and still works
        for input in self.get_input_data():
            if hasattr(self.model.parameters, input):
                self.default_input_data[input] = getattr(self.model.parameters, input)
