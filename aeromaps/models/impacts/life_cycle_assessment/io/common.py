"""
Credits: lca_algebraic-web-app from Raphael Jolivet (Mines ParisTech).
https://git.sophia.minesparis.psl.eu/oie/lca_algebraic-web-app/
"""
import warnings
from enum import Enum
from typing import Dict
from sympy import Expr, Float, parse_expr, lambdify, Basic
import json
from typing import List
from tqdm.notebook import tqdm

FUNCTIONAL_UNIT_KEY = "air_transport"
TOTAL_AXIS_KEY = "total"


class ParamType(str, Enum):
    BOOLEAN = "bool"
    ENUM = "enum"
    FLOAT = "float"


def is_expr(exp):
    return isinstance(exp, Basic)


class FunctionalUnit :
    def __init__(self, quantity, unit):
        self.quantity = quantity
        self.unit = unit


def _lambdify(expr, expanded_params):
    if isinstance(expr, Expr):
        return lambdify(expanded_params, expr, 'numpy')
        # expr_simplified = expr.simplify()
        # return lambdify(expanded_params, expr_simplified, 'numpy')
    else:
        # Not an expression : return statis func
        def static_func(*args, **kargs):
            return expr
        return static_func


class Lambda:
    """
    This class represents a compiled (lambdified) expression together with the list of requirement parameters and the source expression
    """
    def __init__(self, expr, all_params):

        if isinstance(expr, dict):

            self.lambd = dict()

            # First, gather all expanded parameters
            all_expanded_params = set()
            for key, sub_expr in expr.items():
                if not is_expr(sub_expr):
                    continue
                expanded_params = list(str(symbol) for symbol in sub_expr.free_symbols)
                all_expanded_params.update(expanded_params)

            all_expanded_params = list(all_expanded_params)

            # Transform them into list of params
            self.params = unexpand_param_names(all_params, all_expanded_params)
            reexpanded_params = expand_param_names(all_params, self.params)

            # Lambdify with all expanded params
            for key, sub_expr in expr.items():
                self.lambd[key] = _lambdify(sub_expr, reexpanded_params)

        else:
            if not isinstance(expr, Expr):
                expr = Float(expr)

            expanded_params = list(str(symbol) for symbol in expr.free_symbols)
            self.params = unexpand_param_names(all_params, expanded_params)

            # Reexpend symbols, to ensure all enum values are present as a parameter
            reexpanded_params = expand_param_names(all_params, self.params)

            self.lambd = _lambdify(expr, reexpanded_params)

        self.expr = expr

    def evaluate(self, all_params, param_values):

        # First, set default values
        values = {key: all_params[key].default for key in self.params}

        # Override with actual values
        values.update({key: val for key, val in param_values.items() if key in self.params})

        # Expand
        expanded_values = dict()
        for param_name, val in values.items():
            param = all_params[param_name]
            expanded_values.update(param.expand_values(val))

        if isinstance(self.lambd, dict):
            return {key: lambd(**expanded_values) for key, lambd in self.lambd.items()}
        else:
            return self.lambd(**expanded_values)

    def __json__(self):
        if isinstance(self.expr, dict):
            expr = {key: str(expr) for key, expr in self.expr.items()}
        else:
            expr = str(self.expr)

        return dict(
            params=self.params,
            expr=expr)

    @classmethod
    def from_json(cls, js, all_params):
        expr = js["expr"]
        if isinstance(expr, dict):
            expr = {key: parse_expr(expr) for key, expr in expr.items()}
        else:
            expr = parse_expr(expr)

        return cls(expr=expr, all_params=all_params)


class Param:

    def __init__(
            self,
            name: str,
            type: ParamType,
            unit: str,
            default: float,
            values: List[str] = None,
            min: float = None,
            max: float = None,
            description: str = None,
            label: str = None,
            group: str = None):

        self.name: str = name
        self.label: str = label
        self.type: ParamType = type
        self.default: Float = default
        self.unit: str = unit
        self.group: str = group
        self.description: str = description
        if values:
            self.values = values
        else:
            self.min = min
            self.max = max

    @classmethod
    def from_json(cls, js):
        return cls(**js)

    def expand_values(self, value):

        # Simple case
        if self.type != ParamType.ENUM:
            return {self.name: value}

        # Enum ? generate individual boolean param values
        return {"%s_%s" % (self.name, enum): 1 if value == enum else 0 for enum in self.values}

    def expand_names(self):

        if self.type != ParamType.ENUM:
            return [self.name]

        # Enum ? generate individual boolean param values
        return ["%s_%s" % (self.name, enum) for enum in self.values]

    def __json__(self):
        return self.__dict__


def expand_param_names(all_params, param_names):
    res = []
    for param_name in param_names:
        param = all_params[param_name]
        res.extend(param.expand_names())
    return res


def unexpand_param_names(all_params, expanded_param_names):
    """Build a dict of expended_param => param"""
    expanded_params_to_params = {name:param.name for param in all_params.values() for name in param.expand_names() }
    return list(set(expanded_params_to_params[name] for name in expanded_param_names))


class Impact():
    def __init__(self, name, unit):
        self.name = name,
        self.unit = unit


class Model:

    def __init__(
            self,
            params: Dict,
            expressions: Dict[str, Dict[str, Lambda]],
            functional_units: Dict[str, FunctionalUnit],
            impacts: Dict[str, Impact]):
        """
        :param params: List of all parameters
        :param expressions: Dict of Dict {axis => {method => Lambda}}
        :param functional_units: Dict of function unit name => formula
        :param impacts : Dict of impacts with their units
        """
        self.params: Dict[str, Param] = params
        self.expressions: Dict[str, Dict[str, Lambda]] = expressions
        self.functional_units: Dict[str, FunctionalUnit] = functional_units
        self.impacts: Dict[str, Impact] = impacts

    def __json__(self):
        return self.__dict__

    def evaluate(self, impact, functional_unit=FUNCTIONAL_UNIT_KEY, axis=TOTAL_AXIS_KEY, **param_values):
        """
        :param axis: Axis to consider
        :param impact: Impact to consider
        :param functional_unit: Function unit
        :param param_values: List of parameters
        :return: <Value of impact, or dict of values, in case one axis is used>, <unit>
        """

        if not axis in self.expressions:
            raise Exception("Wrong axis '%s'. Expected one of %s" % (axis, list(self.expressions.keys())))

        expressions_by_impact = self.expressions[axis]

        if not impact in expressions_by_impact:
            raise Exception("Wrong impact '%s'. Expected one of %s" % (impact, list(expressions_by_impact.keys())))

        lambd = expressions_by_impact[impact]
        impact_obj = self.impacts[impact]
        functional_unit = self.functional_units[functional_unit]

        # Compute value of functional unit
        fu_val = functional_unit.quantity.evaluate(self.params, param_values)

        # Compute value of impacts
        impacts = lambd.evaluate(self.params, param_values)

        # Filter out "null"=zero axis

        unit = impact_obj.unit

        if functional_unit.unit is not None :
            unit += "/" + functional_unit.unit

        # Divide the two
        if isinstance(impacts, dict):

            # Filter out "null"=zero axis
            impacts = {key: val for key, val in impacts.items() if not (key == "null" and val == 0.0)}

            vals = {key: val / fu_val for key, val in impacts.items()}
        else:
            vals = impacts / fu_val

        return vals, unit

    @classmethod
    def from_json(cls, js, axis=None):

        all_params = {key: Param.from_json(val) for key, val in js["params"].items()}

        expr_items = js["expressions"].items()
        if axis is not None:  # Get only one axis if specified
            if axis not in js["expressions"]:
                warnings.warn(f"Axis '{axis}' not found in model expressions. Using first available axis instead.")
                axis = list(js["expressions"].keys())[0]  # Fallback to first axis
            expr_items = [(axis, js["expressions"][axis])]
        expressions = {
            axis: {
                method: Lambda.from_json(lambd, all_params)
                for method, lambd in impacts.items()}
            for axis, impacts in expr_items}

        functional_units = {
            key: FunctionalUnit(
                quantity=Lambda.from_json(fu["quantity"], all_params),
                unit=fu["unit"])

            for key, fu in js["functional_units"].items()}

        impacts = {key: Impact(impact["name"], impact["unit"]) for key, impact in js["impacts"].items()}

        return cls(all_params, expressions, functional_units, impacts)

    @classmethod
    def from_json_with_progress_bar(cls, js, axis=None):
        # Params
        all_params = {}
        for key, val in tqdm(js["params"].items(), desc="Import LCA Parameters"):
            all_params[key] = Param.from_json(val)

        # Expressions
        expressions = {}
        expr_items = js["expressions"].items()
        if axis is not None:  # Get only one axis if specified
            if axis not in js["expressions"]:
                warnings.warn(f"Axis '{axis}' not found in model expressions. Using first available axis instead.")
                axis = list(js["expressions"].keys())[0]  # Fallback to first axis
            expr_items = [(axis, js["expressions"][axis])]
        for ax, impacts in expr_items:
            expressions[ax] = {}
            for method, lambd in tqdm(impacts.items(), desc=f"Import LCIA functions (axis '{ax}')", leave=True):
                expressions[ax][method] = Lambda.from_json(lambd, all_params)

        # Functional units
        functional_units = {}
        for key, fu in tqdm(js["functional_units"].items(), desc="Import functional units"):
            functional_units[key] = FunctionalUnit(
                quantity=Lambda.from_json(fu["quantity"], all_params),
                unit=fu["unit"],
            )

        # Impacts
        impacts = {}
        for key, impact in tqdm(js["impacts"].items(), desc="Import impacts metadata"):
            impacts[key] = Impact(impact["name"], impact["unit"])

        return cls(all_params, expressions, functional_units, impacts)

    def to_file(self, filename):
        js = serialize_model(self)
        with open(filename, "w") as f:
            json.dump(js, f, indent=4)

    @classmethod
    def from_file(cls, filename, progress_bar=False, axis=None):
        with open(filename, "r") as f:
            js = json.load(f)
            if progress_bar:
                return Model.from_json_with_progress_bar(js, axis)
            return Model.from_json(js, axis)


def serialize_model(obj):
    if isinstance(obj, dict):
        return {str(key): serialize_model(val) for key, val in obj.items()}

    if hasattr(obj, "__json__"):
        return serialize_model(obj.__json__())

    if hasattr(obj, "__dict__"):
        return serialize_model(obj.__dict__)

    return obj



