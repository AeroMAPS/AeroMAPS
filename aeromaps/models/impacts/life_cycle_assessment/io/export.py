"""
This module enables to compile an LCA algebraic model into a serializable Model object.

Credits: lca_algebraic-web-app from Raphael Jolivet (Mines ParisTech).
https://git.sophia.minesparis.psl.eu/oie/lca_algebraic-web-app/
This version was slightly adapted for compatibility with versions 1.2.x of lca_algebraic.
"""

from typing import Dict

try:
    from lca_algebraic import AxisDict, ParamDef
    from lca_algebraic.lca import _preMultiLCAAlgebric
    from lca_algebraic.params import _param_registry
    from lca_algebraic.stats import _round_expr
    import brightway2 as bw
except ImportError as e:
    raise ImportError(
        "Required libraries for Custom Life Cycle Assessment module are not installed. "
        "Please run 'pip install --upgrade aeromaps[lca]' to install them."
    ) from e
from aeromaps.models.impacts.life_cycle_assessment.io.common import FunctionalUnit, Lambda, Impact, Model, Param, is_expr, ParamType
from aeromaps.models.impacts.life_cycle_assessment.io.common import FUNCTIONAL_UNIT_KEY, TOTAL_AXIS_KEY


def round_expr(exp_or_dict, num_digits):
    if isinstance(exp_or_dict, dict) :
        return dict({key: (val if not is_expr(val) else _round_expr(val, num_digits)) for key, val in exp_or_dict.items()})
    else:
        return _round_expr(exp_or_dict, num_digits)


def paramDef_to_param(paramDef:ParamDef):
    print(f"Param : {paramDef.name} : {paramDef.type}")
    if paramDef.type == ParamType.FLOAT and (paramDef.min is None or paramDef.max is None):
        raise Exception(f"Param of type float '{paramDef.name} 'should have both min and max")

    return Param(
        name=paramDef.name,
        type=paramDef.type,
        unit=paramDef.unit,
        default=paramDef.default,
        label=paramDef.label,
        values=getattr(paramDef, "values", None),
        group=paramDef.group,
        min=paramDef.min,
        max=paramDef.max,
        description=paramDef.description)


def export_lca(
        system,
        functional_units: Dict[str, Dict] = {FUNCTIONAL_UNIT_KEY: {"quantity": 1.0, "unit": None}},
        methods_dict: Dict[str, tuple] = {},
        axes=None,
        num_digits=3):
    """
    :param system: Root inventory
    :param functional_units : Dict of Dict{unit, quantity}
    :param methods_dict: dict of method_name => method tuple
    :param axes: List of axes
    :param num_digits: Number of digits
    :return: an instance of "Model"
    """

    if axes is None:
        axes = [None]

    # Transform all lca_algebraic parameters to exported ones
    all_params = {param.name: paramDef_to_param(param) for param in _param_registry().all()}

    impacts_by_axis = dict()

    for axis in axes :
        print("Processing axis %s" % axis)

        lambdas = _preMultiLCAAlgebric(
            system,
            list(methods_dict.values()),
            axis=axis)

        if axis is None:
            axis = TOTAL_AXIS_KEY

        # Simplify
        for lambd, method_name in zip(lambdas, methods_dict.keys()):

            if isinstance(lambd.expr, AxisDict):
                lambd.expr = lambd.expr._dict
            lambd.expr = round_expr(lambd.expr, num_digits=num_digits)

        # Save
        impacts_by_axis[axis] = {
            method: Lambda(lambd.expr, all_params)
            for method, lambd in zip(methods_dict.keys(), lambdas)}

    # Dict of functional units
    functional_units = {
        name: FunctionalUnit(
            quantity=Lambda(fu["quantity"], all_params),
            unit=fu["unit"])
        for name, fu in functional_units.items()}

    # Build list of impacts
    impacts = {key: Impact(
        name=str(method),
        unit=bw.Method(method).metadata.get("unit", "")
    ) for key, method in methods_dict.items()}

    return Model(
        params=all_params,
        functional_units=functional_units,
        expressions=impacts_by_axis,
        impacts=impacts)