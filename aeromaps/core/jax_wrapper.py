"""
GEMSEO-JAX wrappers for AeroMAPS models.

This module provides discipline wrappers based on the ``gemseo-jax`` plugin so
that AeroMAPS models rewritten with pure ``jax.numpy`` operations benefit from
jit compilation and analytic derivatives through automatic differentiation.

Two wrappers mirror the two existing pandas-based wrappers:

* :class:`AeroMAPSJAXModelWrapper` — for ``model_type="custom"`` models. The
  model exposes ``jax_compute(input_data: dict) -> dict`` with the same
  contract as ``compute`` and unchanged ``input_names`` / ``output_names``.
* :class:`AeroMAPSAutoJAXModelWrapper` — for ``model_type="auto"`` models. The
  model exposes ``jax_compute(...)`` with the same signature and return
  variable names as ``compute``.

In both cases the model ``__init__`` signature and the ``compute`` method are
untouched: the JAX path is opt-in via ``create_process(..., use_jax=True)``.

Conventions for ``jax_compute``
-------------------------------
* Year-indexed quantities are flat ``jax.numpy`` arrays over the model's full
  year index ``range(historic_start_year, end_year + 1)`` (years for which the
  pandas version leaves NaN cells must hold NaN).
* Inputs listed in ``model.jax_static_input_names`` (e.g. years used as loop
  bounds) are frozen at discipline-build time and are not differentiable.
* Scalars are returned as 0-d/1-d arrays or floats; the wrapper converts
  outputs back to ``pd.Series`` / ``float`` according to the types declared by
  the pandas interface, so pandas-based disciplines can coexist downstream.
"""

from __future__ import annotations

import logging
import typing

import jax
import numpy as np
import pandas as pd

from gemseo_jax.auto_jax_discipline import AutoJAXDiscipline
from gemseo_jax.jax_discipline import JAXDiscipline

from aeromaps.models.base import AeroMAPSModel

jax.config.update("jax_enable_x64", True)

LOGGER = logging.getLogger(__name__)


def _to_numeric(value, full_index=None):
    """Convert a value exchanged between disciplines to a JAX-friendly type.

    Series are reindexed to ``full_index`` (NaN padding) so that all
    year-indexed arrays share the same length, mirroring pandas index
    alignment. Series starting before the model's first year (climate-indexed
    series) are kept as is.
    """
    if isinstance(value, pd.Series):
        if (
            full_index is not None
            and len(value) > 0
            and value.index[0] >= full_index[0]
            and not value.index.equals(full_index)
        ):
            value = value.reindex(full_index)
        return value.to_numpy(dtype=np.float64)
    if isinstance(value, (list, tuple)):
        return np.asarray(value, dtype=np.float64)
    if isinstance(value, (int, np.integer)):
        return float(value)
    if isinstance(value, np.ndarray) and value.dtype != np.float64:
        return value.astype(np.float64)
    return value


class _AeroMAPSJAXWrapperMixin:
    """Shared conversion logic between the custom and auto JAX wrappers."""

    model: AeroMAPSModel

    def _init_common(self, model: AeroMAPSModel, series_output_names):
        self.model = model
        self._series_output_names = set(series_output_names)
        self._output_indexes = dict(getattr(model, "jax_output_indexes", {}))
        self._full_index = model.df.index
        self._latest_outputs = {}
        self.name = model.__class__.__name__
        self._update_defaults_from_parameters()

    def _update_defaults_from_parameters(self):
        """Default input data from parameters and coupling seeds.

        Same precedence as the pandas wrappers: model-provided defaults, then
        parameters, then coupling seeds for still-missing couplings.
        """
        defaults = self.default_input_data
        full_index = self._full_index
        if getattr(self.model, "default_input_data", None):
            for key, value in self.model.default_input_data.items():
                if key in self.input_grammar.names:
                    defaults[key] = _to_numeric(value, full_index)
        for name in self.input_grammar.names:
            if hasattr(self.model.parameters, name):
                defaults[name] = _to_numeric(getattr(self.model.parameters, name), full_index)
        if hasattr(self.model, "_coupling_defaults"):
            for key, value in self.model._coupling_defaults.items():
                if key in self.input_grammar.names and key not in defaults:
                    defaults[key] = _to_numeric(value, full_index)

    def update_defaults(self):
        """Mirror the API of the other AeroMAPS wrappers."""
        self._update_defaults_from_parameters()

    def _output_index(self, name):
        return self._output_indexes.get(name, self._full_index)

    def _run(self, input_data):
        # Normalize incoming values (pd.Series / lists produced by pandas
        # disciplines) so the JAX call sees numeric arrays; original values are
        # restored afterwards because ``input_data`` is the discipline's io
        # data, which the chain propagates back into its shared local data.
        originals = {}
        for name in self.input_grammar.names:
            if name in input_data:
                value = input_data[name]
                numeric = _to_numeric(value, self._full_index)
                if numeric is not value:
                    originals[name] = value
                    input_data[name] = numeric

        super()._run(input_data)

        for name, value in originals.items():
            input_data[name] = value

        # Convert outputs back to the types declared by the pandas interface
        # so that downstream pandas-based disciplines keep working.
        data = self.io.data
        converted = {}
        for name in self.output_grammar.names:
            value = np.asarray(data[name], dtype=np.float64).ravel()
            if name in self._series_output_names:
                converted[name] = pd.Series(value, index=self._output_index(name), name=name)
            elif value.size == 1:
                converted[name] = float(value[0])
            else:
                # Vector outputs not declared as Series (e.g. constraint value
                # lists) are kept as plain arrays.
                converted[name] = value
        self.io.update_output_data(converted)
        self._latest_outputs = converted

    def _compute_jacobian(self, input_names=(), output_names=()):
        # Linearization may be requested with fresh (pandas) input data.
        data = self.io.data
        originals = {}
        for name in self.input_grammar.names:
            if name in data:
                value = data[name]
                numeric = _to_numeric(value, self._full_index)
                if numeric is not value:
                    originals[name] = value
                    data[name] = numeric
        try:
            super()._compute_jacobian(input_names, output_names)
        finally:
            for name, value in originals.items():
                data[name] = value

        # Partial-index Series inputs are reindexed to the full year index
        # before the JAX call, so the Jacobian has one column per full-index
        # year; slice back the columns matching the exchanged (partial) series
        # so shapes agree with the GEMSEO variable sizes.
        first_year = self._full_index[0]
        for name, value in originals.items():
            if (
                isinstance(value, pd.Series)
                and len(value) < len(self._full_index)
                and value.index[0] >= first_year
            ):
                offset = int(value.index[0]) - int(first_year)
                stop = offset + len(value)
                for jac_row in self.jac.values():
                    if name in jac_row:
                        jac_row[name] = jac_row[name][:, offset:stop]

        # NaN cells are used as "no value for this year" markers throughout the
        # AeroMAPS models; their derivatives are NaN by propagation and would
        # poison the coupled adjoint solve. Consumers of NaN-valued cells guard
        # them (fillna-style), so these sensitivities are structurally zero.
        for jac_row in self.jac.values():
            for name, block in jac_row.items():
                if not np.all(np.isfinite(block)):
                    jac_row[name] = np.nan_to_num(block, nan=0.0, posinf=0.0, neginf=0.0)

    def sync_model_df(self):
        """Store the latest outputs into ``model.df`` / ``model.float_outputs``.

        Called lazily (e.g. before data export) instead of at every execution
        to keep pandas out of the MDA/optimisation loops.
        """
        if self._latest_outputs:
            # Vector outputs that are not Series (e.g. constraint value lists)
            # are not storable in model.df.
            storable = {
                key: value
                for key, value in self._latest_outputs.items()
                if isinstance(value, (pd.Series, float))
            }
            # ``jax_compute`` returns climate-indexed Series for every output the
            # pandas ``compute`` builds on the climate index. Only the outputs
            # the pandas version actually keeps in ``df_climate`` are declared in
            # ``jax_climate_output_names``; the others are stored in ``model.df``
            # and must be truncated back to the model year index, exactly as the
            # pandas assignment ``self.df.loc[:, name] = series`` does.
            # Outputs the pandas compute files under another column name.
            for name, column in getattr(self.model, "jax_df_output_names", {}).items():
                if name in storable:
                    storable[column] = storable.pop(name)

            climate_names = set(getattr(self.model, "jax_climate_output_names", ()))
            climate_keys = [key for key in storable if key in climate_names] or None
            for key, value in storable.items():
                if (
                    key not in climate_names
                    and isinstance(value, pd.Series)
                    and not value.index.equals(self._full_index)
                ):
                    storable[key] = value.reindex(self._full_index)
            self.model._store_outputs(storable, climate_outputs_keys=climate_keys)

    def _get_static_input_data(self):
        """Values of the static configuration inputs, frozen at build time."""
        static_names = set(getattr(self.model, "jax_static_input_names", ()))
        static_data = {}
        for name in static_names:
            if hasattr(self.model.parameters, name):
                static_data[name] = _to_numeric(
                    getattr(self.model.parameters, name), self._full_index
                )
            elif isinstance(getattr(self.model, "input_names", None), dict):
                static_data[name] = _to_numeric(self.model.input_names[name], self._full_index)
        return static_data


class AeroMAPSJAXModelWrapper(_AeroMAPSJAXWrapperMixin, JAXDiscipline):
    """JAX discipline for ``model_type="custom"`` models with ``jax_compute``."""

    def __init__(self, model: AeroMAPSModel, differentiation_method="auto"):
        static_names = set(getattr(model, "jax_static_input_names", ()))
        input_names = [n for n in model.input_names if n not in static_names]
        # Intermediates the pandas compute only writes to ``model.df`` are
        # declared as outputs here so ``jax_compute`` can return them and
        # ``sync_model_df`` can store them (see ``jax_extra_output_names``).
        extra_names = [
            n for n in getattr(model, "jax_extra_output_names", ()) if n not in model.output_names
        ]
        output_names = list(model.output_names) + extra_names

        # Static configuration inputs are frozen at build time and re-injected
        # into every jax_compute call without being traced.
        static_data = {}
        for name in static_names:
            if hasattr(model.parameters, name):
                static_data[name] = _to_numeric(getattr(model.parameters, name), model.df.index)
            elif isinstance(model.input_names, dict):
                static_data[name] = _to_numeric(model.input_names[name], model.df.index)

        def function(input_data):
            return model.jax_compute({**static_data, **input_data})

        super().__init__(
            function=function,
            input_names=input_names,
            output_names=output_names,
            default_inputs={},
            differentiation_method=differentiation_method,
            name=model.__class__.__name__,
        )

        series_output_names = [
            name
            for name, value in (
                model.output_names.items() if isinstance(model.output_names, dict) else []
            )
            if isinstance(value, pd.Series)
        ]
        self._init_common(model, series_output_names + extra_names)


class AeroMAPSAutoJAXModelWrapper(_AeroMAPSJAXWrapperMixin, AutoJAXDiscipline):
    """JAX discipline for ``model_type="auto"`` models with ``jax_compute``.

    ``jax_compute`` must have the same signature as ``compute`` (inputs from
    argument names, outputs from the names of the returned variables).
    """

    def __init__(self, model: AeroMAPSModel, differentiation_method="auto"):
        static_args = {}
        for name in set(getattr(model, "jax_static_input_names", ())):
            if hasattr(model.parameters, name):
                static_args[name] = _to_numeric(getattr(model.parameters, name), model.df.index)

        super().__init__(
            function=model.jax_compute,
            static_args=static_args,
            differentiation_method=differentiation_method,
            name=model.__class__.__name__,
        )

        self._init_common(model, self._series_outputs_from_annotations(model))

    def _series_outputs_from_annotations(self, model):
        """Output names declared as ``pd.Series`` by the pandas ``compute``.

        The return annotation of ``compute`` (``Tuple[pd.Series, float, ...]``)
        is mapped positionally onto the output names parsed from
        ``jax_compute``'s return statement.
        """
        output_names = list(self.output_grammar.names)
        try:
            hints = typing.get_type_hints(model.compute.__func__)
        except Exception:  # pragma: no cover - annotation edge cases
            hints = {}
        ret = hints.get("return")
        if ret is None:
            # No annotation: assume every output is a Series (the common case).
            return output_names
        args = typing.get_args(ret)
        if not args:
            args = (ret,)
        extra_names = set(getattr(model, "jax_extra_output_names", ()))
        return [
            name
            for name, ann in zip(output_names, args)
            if ann is pd.Series or getattr(ann, "__origin__", None) is pd.Series
        ] + [name for name in output_names if name in extra_names]
