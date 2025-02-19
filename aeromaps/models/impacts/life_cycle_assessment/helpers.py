import lca_algebraic as agb
import pandas as pd
from sympy.parsing.sympy_parser import parse_expr
from sympy.printing.str import StrPrinter
from sympy import Float, factor
import bw2data

USER_DB = 'Foreground DB'
DEFAULT_PROJECT = 'lca_modeller_default_project'


def list_processes(model, foreground_only: bool = True, custom_attribute: str = None) -> pd.DataFrame:
    """
    Traverses the tree of sub-activities (sub-processes) until the background database is reached.
    """

    def _recursive_activities(act, activities, units, locations, parents, amounts, levels, dbs, custom_attributes,
                              parent: str = "", exc: dict = None, level: int = 0):

        if exc is None:
            exc = {}
        name = act.as_dict()['name']
        unit = act.as_dict()['unit']
        loc = act.as_dict().get('location', "")
        if loc not in ['GLO', ''] and f'[{loc}]' not in name:
            name += f' [{loc}]'
        amount = _getAmountOrFormula(exc)
        db = act.as_dict()['database']
        custom_attr = act.as_dict().get(custom_attribute, "")  # get any additional attribute asked by the user

        # Stop BEFORE reaching the first level of background activities
        if foreground_only and db != USER_DB:
            return

        if name in activities:  # Multiple parents for the same activity.
            # TODO: implement better check than just the name and database, e.g. by adding the act object in the lists (but not in the final df)
            # Populate lists accordingly and stop recursion since the activity has already been processed
            idx = activities.index(name)
            if dbs[idx] == db:
                parents[idx].append(parent)
                amounts[idx].append(amount)
                return

        activities.append(name)
        units.append(unit)
        locations.append(loc)
        parents.append([parent])
        amounts.append([amount])
        levels.append(level)
        dbs.append(db)
        custom_attributes.append(custom_attr)

        # Stop AFTER reaching the first level of background activities
        if db != USER_DB:
            return

        for exc in act.exchanges():
            if agb.base_utils._isOutputExch(exc):  # skip production exchange to only go down the tree
                continue
            _recursive_activities(exc.input, activities, units, locations, parents, amounts, levels, dbs, custom_attributes,
                                  parent=name,
                                  exc=exc,
                                  level=level + 1)
        return

    # Initialize lists
    activities = []
    units = []
    locations = []
    parents = []
    amounts = []
    levels = []
    dbs = []
    custom_attributes = []

    # Recursively populate lists
    _recursive_activities(model, activities, units, locations, parents, amounts, levels, dbs, custom_attributes)
    data = {'activity': activities,
            'unit': units,
            'location': locations,
            'level': levels,
            'database': dbs,
            'parents': parents,
            'amounts': amounts,
            }
    if custom_attribute:
        data[custom_attribute] = custom_attributes

    # Create DataFrame
    df = pd.DataFrame(data, index=activities)

    return df


def get_parameter(key: str):
    param = agb.params._param_registry().__getitem__(key)
    return param


def expandParams(param, value=None):
    """
    Modified version of expandParams from classes EnumParam and ParamDef from lca_algebraic library.
    For enum (switch) parameters, returns a dictionary of single enum values as sympy symbols,
    with only a single one set to 1.
    For float parameters, returns a dictionary with either the user-provided value or the default parameter value.
    """

    # Enum (e.g. switch) parameters
    if param['type'] == 'enum':
        values = param['values'] + [None]

        # Bad value ?
        if value not in values:
            raise Exception("Invalid value %s for param %s. Should be in %s" %
                            (value, param['name'], str(param['values'])))

        res = dict()
        for enum_val in values:
            var_name = "%s_%s" % (param['name'], enum_val if enum_val is not None else "default")
            res[var_name] = 1.0 if enum_val == value else 0.0
        return res

    # Float parameters
    else:
        if value is None:
            value = param['default']
        return {param['name']: value}


def completeParamValues(params, param_registry, setDefaults=True):
    """
    Modified version of completeParamValues from lca_algebraic library.
    Sets default values for missing parameters and expand enum params.

    Returns
    -------
        Dict of param_name => float value
    """

    # Set default variables for missing values
    if setDefaults:
        for name, param in param_registry.items():
            if not name in params:
                params[name] = param['default']
                agb.warn(
                    "Required param '%s' was missing, replacing by default value : %s" % (name, str(param['default'])))

    res = dict()
    for key, val in params.items():
        if key in param_registry:
            param = param_registry[key]
        else:
            continue
            # raise Exception("Parameter not found : %s. Valid parameters : %s" % (key, list(param_registry.keys())))

        if isinstance(val, list):
            newvals = [expandParams(param, val) for val in val]
            res.update(agb.params._listOfDictToDictOflist(newvals))
        else:
            res.update(expandParams(param, val))

    return res


def format_number(num, precision=2):
    """
    This function takes a number (either a Python float or a SymPy Float) and a precision,
    and returns a string that represents the number with the given precision.
    If the number is too large or too small, it switches to scientific notation.

    :param num: The number to format.
    :param precision: The number of decimal places to use.
    :return: A string that represents the number with the given precision.
    """
    if isinstance(num, Float):  # SymPy float
        num = num.evalf()
    sci_num = "{:.{}e}".format(num, precision)
    if 'e+00' in sci_num:
        return "{:.{}f}".format(num, precision)
    else:
        return sci_num


class CustomStrPrinter(StrPrinter):
    def _print_Float(self, expr):
        return '{:.2e}'.format(expr)


def _getAmountOrFormula(ex):
    """ Return either a fixed float value or an expression for the amount of this exchange"""
    if 'formula' in ex:
        expr = parse_expr(ex['formula'], evaluate=False)
        return CustomStrPrinter().doprint(factor(expr))
    elif 'amount' in ex:
        return format_number(ex['amount'])
    return ""


def safe_delete_brightway_project(projectname: str) -> None:
    try:
        bw2data.projects.delete_project(
            name = projectname,
            delete_dir = True
        )
    except:
        pass