import json
import os
from importlib.resources import open_text
from abc import ABC, abstractmethod

import bw2io
from jsonschema import validate
import lca_algebraic as agb
from lca_algebraic.log import warn
import brightway2 as bw
from sympy import sympify
import logging
import os.path as pth
from ruamel.yaml import YAML
from dotenv import load_dotenv
import premise as pm

from aeromaps.models.impacts.life_cycle_assessment import resources
from lca_algebraic.params import (
    ParamDef, all_params
)
from lca_algebraic.activity import ActivityOrActivityAmount, newActivity, ActivityExtended
from typing import Dict, List, Union, Tuple
from functools import reduce
from collections import defaultdict
from aeromaps.models.impacts.life_cycle_assessment.helpers import safe_delete_brightway_project

BIOSPHERE3_DB_NAME = "biosphere3"

_LOGGER = logging.getLogger(__name__)

JSON_SCHEMA_NAME = "configuration.json"
USER_DB = 'Foreground DB'
KEY_PROJECT = 'project'
KEY_ECOINVENT = 'ecoinvent'
KEY_VERSION = 'version'
KEY_MODEL = 'model'
KEY_NORMALIZED_MODEL = 'normalized model'
KEY_EXCHANGE = 'amount'
KEY_SWITCH = 'is_switch'
# KEY_FUNCTIONAL_VALUE = 'functional_unit_scaler'
KEY_NAME = 'name'
KEY_LOCATION = 'loc'
KEY_CATEGORIES = 'categories'
KEY_UNIT = 'unit'
KEY_CUSTOM_ATTR = 'custom_attributes'
KEY_ATTR_NAME = 'attribute'
KEY_ATTR_VALUE = 'value'
EXCHANGE_DEFAULT_VALUE = 1.0  # default value for the exchange between two activities
SWITCH_DEFAULT_VALUE = False  # default foreground activity type (True: it is a switch activity; False: it is a regular activity)
KEY_METHODS = 'methods'
KEY_PREMISE = 'premise'
KEY_SCENARIOS = 'scenarios'
KEY_YEAR = 'year'
KEY_PATHWAY = 'pathway'
KEY_UPDATE_PREMISE = 'update'
KEY_UPDATE_ACT = 'update'
KEY_INPUT_ACT = 'input_activity'
KEY_NEW_VAL = 'new_value'
KEY_DELETE = 'delete'
KEY_ADD = 'add'


def _get_unique_activity_name(key):
    """
    Returns a unique activity name by incrementing a suffix number.
    """
    i = 1
    while agb.findActivity(f'{key}_{i}', db_name=USER_DB, single=False):
        i += 1
    new_key = f'{key}_{i}'
    return new_key


def _parse_exchange(table: dict, act: ActivityExtended = None):
    """
    Gets the exchange expression from the table of options for the activity, then creates the input parameters and returns the symbolic expression of the exchange

    :param table: the table of options for the activity
    :return expr: the symbolic expression
    """

    # Get the 'exchange' value. If it doesn't exist then set the exchange value to 1
    exchange = table.get(KEY_EXCHANGE, EXCHANGE_DEFAULT_VALUE)

    # Special formulas
    if 'sum(' in str(exchange) and act:
        selected_exchanges = str(exchange).split('sum(')[1].split(')')[0]
        if selected_exchanges:
            sum_value = str(sum_amounts(act, selected_exchanges))
            exchange = str(exchange).replace(f'sum({selected_exchanges})', sum_value)

    # Parse the string expression
    expr = sympify(exchange)

    # Get the parameters involved in the expression
    parameters = expr.free_symbols

    # Create the parameters
    for param in parameters:
        if param == agb.old_amount:
            continue
        if param not in all_params():
            agb.newFloatParam(
                param.name,  # name of the parameter
                default=1.0,  # default value
                min=1.0,
                max=1.0,
                dbname=USER_DB  # we define the parameter in the foreground database
            )

    return expr


def sum_amounts(act, exchange_name):
    """
    Sums the amounts of all exchanges with the same name in the activity.
    Useful when exchange_name contains wildcard `*` to refer to multiple exchanges.
    :param act: activity to sum the exchanges amounts
    :param exchange_name: name of the exchange to sum. Can be a wildcard `*` to refer to multiple exchanges.
    :return: the sum of all exchanges amounts
    """
    exchs = act.getExchange(exchange_name, single=False)
    total = sum(exch['amount'] for exch in exchs)
    return total


def newMultiSwitchAct(dbname, name, paramDefList: Union[List[ParamDef], ParamDef],
                      acts_dict: Union[
                          Dict[str, ActivityOrActivityAmount], Dict[Tuple[str], ActivityOrActivityAmount]]):
    """
    Creates a new switch activity with multiple switch parameters.
    A child activity is selected based on the combination of the switch parameters.
    This is a modification of newSwitchAct from lca_algebraic library.

    Parameters
    ----------
    dbname:
        name of the target DB
    name:
        Name of the new activity
    paramDefList :
        List of enum parameters
    acts_dict :
        dict of (("enum_1_value", ..., "enum_n_value") => activity or (activity, amount)

    Examples
    --------
    > newMultiSwitchAct(MYDB, "MultiSwitchAct", [switchParam1, switchParam2], {
    >    ("switchParam1_val1", switchParam2_val1) : act1  # Amount is 1
    >    ("switchParam1_val2", switchParam2_val2) : (act2, 0.4) # Different amount
    >    ("switchParam1_val1", switchParam2_val2) : (act3, b + 6) # Amount with formula
    > }
    """
    # Transform map of enum values to corresponding formulas <param_name>_<enum_value>
    exch = defaultdict(lambda: 0)

    # Forward last unit as unit of the switch
    unit = None
    for key, act in acts_dict.items():
        amount = 1
        if isinstance(act, (list, tuple)):
            act, amount = act
        if isinstance(paramDefList, list):
            exch[act] += amount * reduce(lambda x, y: x * y,
                                         [paramDef.symbol(key[i]) for i, paramDef in enumerate(paramDefList)])
        else:
            exch[act] += amount * paramDefList.symbol(key)  # Regular switch activity
        unit = act["unit"]

    res = newActivity(dbname, name, unit=unit, exchanges=exch)

    return res


class LCAProblemConfigurator:
    """
    class for configuring an LCA_algebraic problem from a configuration file

    See :ref:`description of configuration file <configuration-file>`.

    :param conf_file_path: if provided, configuration will be read directly from it
    """

    def __init__(self, conf_file_path=None):
        self._conf_file = None
        self._serializer = _YAMLSerializer()

        if conf_file_path:
            self.load(conf_file_path)

    def generate(self, reset: bool = False):
        """
        Creates the LCA activities and parameters as defined in the configuration file.
        Also gets the LCIA methods defined in the conf file.
        :return: model: the top-level activity corresponding to the functional unit
        :return: methods: the LCIA methods
        """
        # Create model from configuration file
        project_name, model = self._build_model(reset=reset)

        # Get LCIA methods if declared
        methods = [eval(m) for m in self._serializer.data.get(KEY_METHODS, [])]

        return project_name, model, methods

    def load(self, conf_file):
        """
        Reads the problem definition

        :param conf_file: Path to the file to open or a file descriptor
        """

        self._conf_file = pth.abspath(conf_file)  # for resolving relative paths

        self._serializer = _YAMLSerializer()
        self._serializer.read(self._conf_file)

        # Syntax validation
        with open_text(resources, JSON_SCHEMA_NAME) as json_file:
            json_schema = json.loads(json_file.read())

        validate(self._serializer.data, json_schema)
        # Issue a simple warning for unknown keys at root level
        for key in self._serializer.data:
            if key not in json_schema["properties"].keys():
                _LOGGER.warning(f"Configuration file: {key} is not a key declared in LCAv.")

    def _setup_premise(self, new_premise_scenarios):
        """
        Generates the prospective databases with premise
        """
        if not new_premise_scenarios:
            return
        else:
            print("Generating new prospective databases with premise: \n" + ",\n".join([f"{s[KEY_MODEL]}_{s[KEY_PATHWAY]}_{s[KEY_YEAR]}" for s in new_premise_scenarios]))
        if "biosphere3" not in bw.databases:
            raise ValueError(
                f"Biosphere database must be named 'biosphere3' for premise, or is missing. "
                f"Consider resetting the project with 'safe_delete_brightway_project(projectname)' helper function."
            )
        pm.clear_cache()  # fresh start
        ndb = pm.NewDatabase(
            scenarios=new_premise_scenarios,
            source_type="brightway",
            source_db=self.source_ei_name,
            source_version=self.ei_version,
            system_model=self.ei_model,
            key='tUePmX_S5B8ieZkkM7WUU2CnO8SmShwmAeWK9x2rTFo=',  # TODO: set as environment variable
            quiet=True
        )
        premise_dict = self._serializer.data.get(KEY_PREMISE, dict())
        sectors_to_update = premise_dict.get(KEY_UPDATE_PREMISE)
        if sectors_to_update == 'all':
            ndb.update()
        elif isinstance(sectors_to_update, list):
            ndb.update(sectors_to_update)
        ndb.write_db_to_brightway()

    def _setup_project(self, reset: bool = False):
        """
        Sets the brightway2 project and import the databases
        """
        if self._serializer.data is None:
            raise RuntimeError("read configuration file first")

        ### Init the brightway2 project
        project_name = self._serializer.data.get(KEY_PROJECT)
        if reset:
            safe_delete_brightway_project(project_name)
        bw.projects.set_current(project_name)
        ei_dict = self._serializer.data.get(KEY_ECOINVENT)
        ei_version = self.ei_version = ei_dict[KEY_VERSION]
        ei_model = self.ei_model = ei_dict[KEY_MODEL]
        self.source_ei_name = f"ecoinvent-{ei_version}-{ei_model}"  # store for future use
        premise_dict = self._serializer.data.get(KEY_PREMISE, dict())
        self.premise_scenarios = premise_dict.get(KEY_SCENARIOS)

        if self.source_ei_name in bw.databases and not reset:  # TODO: enable to install only additional premise dbs not declared previously
            print("Initial setup of EcoInvent already done, skipping. "
                  "To reset the project use option `reset=True`.")

        else:  ### Import Ecoinvent DB
            # User must create a file named .env, that he will not share /commit, and contains the following :
            # ECOINVENT_LOGIN=<your_login>
            # ECOINVENT_PASSWORD=<your_password>
            load_dotenv()  # This load .env file that contains the credential for EcoInvent into os.environ
            if not os.getenv("ECOINVENT_LOGIN") or not os.getenv("ECOINVENT_PASSWORD"):
                raise RuntimeError(
                    "Missing Ecoinvent credentials. Please set them in a .env file in the root of the project. \n"
                    "The file should contain the following lines : \n"
                    "ECOINVENT_LOGIN=<your_login>\n"
                    "ECOINVENT_PASSWORD=<your_password>\n")

            # This downloads ecoinvent and installs biopshere + technosphere + LCIA methods
            bw2io.import_ecoinvent_release(
                version=ei_version,
                system_model=ei_model,
                biosphere_name=BIOSPHERE3_DB_NAME,  # <-- premise requires the biosphere to be named "biosphere3"
                username=os.environ["ECOINVENT_LOGIN"],  # Read for .env file
                password=os.environ["ECOINVENT_PASSWORD"],  # Read from .env file
                use_mp=True)

        ### Generate prospective databases with premise
        new_premise_scenarios = []
        for scenario in self.premise_scenarios:
            model = scenario[KEY_MODEL]
            pathway = scenario[KEY_PATHWAY]
            year = scenario[KEY_YEAR]
            db_name = f"ecoinvent_{ei_model}_{ei_version.replace('3.9.1', '3.9')}_{model}_{pathway}_{year}"
            if db_name not in bw.databases:
                new_premise_scenarios.append(scenario)
        self._setup_premise(new_premise_scenarios)

        ### Set the foreground database
        agb.resetDb(USER_DB)  # cleanup the whole foreground model to avoid errors
        agb.setForeground(USER_DB)
        # You may remove this line if you import a project and parameters from an external source (see loadParam(..))
        agb.resetParams()  # reset parameters stored at project level

        return project_name

    def _build_model(self, reset: bool = False):
        """
        Builds the LCA model as defined in the configuration file.
        """

        ### Set up the project
        project_name = self._setup_project(reset=reset)

        ### Build the model
        print("Building LCA model from configuration file...", end=' ')
        # Get model definition from configuration file
        model_definition = self._serializer.data.get(KEY_MODEL)
        model = agb.newActivity(
            db_name=USER_DB,
            name=KEY_MODEL,
            unit=None
        )

        self._parse_problem_table(model, model_definition)

        # Functional unit scaling
        # if KEY_FUNCTIONAL_VALUE in model_definition and model_definition[KEY_FUNCTIONAL_VALUE] != 1.0:
        #   # create a normalized model whose exchange with the model is equal to the functional value
        #   model_definition[KEY_EXCHANGE] = model_definition[KEY_FUNCTIONAL_VALUE]
        #    functional_value = self._parse_exchange(model_definition)
        #    normalized_model = agb.newActivity(
        #        db_name=USER_DB,
        #        name=KEY_NORMALIZED_MODEL,
        #        unit=None,
        #        exchanges={model: functional_value}
        #    )
        #    problem.model = normalized_model
        print("Done.")

        return project_name, model

    def _get_tech_activity(self, name, loc, unit, code: str = None, copy_act: bool = True):
        """
        Searches for an ecoinvent activity (or a previously defined one if '#' is prefixes the name).
        The activity is then copied to the foreground database to avoid any modification of the background database.
        :param name: name of the activity to search
        :param loc: geographical location
        :param unit: unit of activity
        :param code: new name to give to activity when it will be copied to the foreground database
        :return: a copy of the activity in the foreground database
        """

        # Previously defined foreground activity
        if name.startswith('#'):
            act = agb.findActivity(name[1:], single=False, db_name=USER_DB)
            if not act:
                raise ValueError(f"Activity with name '{name}' not found.")
            elif isinstance(act, list):
                _LOGGER.warning(f"Multiple activities found with name '{name}'.")
                act = act[0]
            return act

        # Background activity
        # Check if not already defined as a copy in the foreground database
        act = agb.findActivity(name=name, loc=loc, unit=unit, db_name=USER_DB, single=False)
        if not act:  # If not, get it from the background database and copy it to the foreground database
            act = agb.findActivity(
                name=name,
                loc=loc,
                unit=unit,
                db_name=self.source_ei_name
            )
            # Copy activity to foreground database so that we can safely modify it in the future
            if copy_act:
                act = agb.copyActivity(
                    USER_DB,
                    act,
                    code
                )
            # Fix for mismatch chemical formulas (until fixed by future brightway/lca-algebraic releases)
            for ex in act.exchanges():
                if "formula" in ex:
                    del ex["formula"]
                    ex.save()
        return act

    def _get_tech_activity_premise(self, name, loc, unit, copy_act: bool = True):
        """
        Searches for an ecoinvent activity in all databases generated by premise.
        The activities are copied in the foreground database to avoid any modification of the background databases.
        :param name: name of the activity to search
        :param loc: geographical location
        :param unit: unit of activity
        :return: a dict of (model, pathway, year): activity in the corresponding database
        """
        if not self.premise_scenarios:
            return []

        acts = {}
        for scenario in self.premise_scenarios:
            model = scenario[KEY_MODEL]
            pathway = scenario[KEY_PATHWAY]
            year = scenario[KEY_YEAR]
            db_name = f"ecoinvent_{self.ei_model}_{self.ei_version.replace('3.9.1', '3.9')}_{model}_{pathway}_{year}"
            code = name + f"\n[{loc}]\n({model}_{pathway.replace('-', '_')}_{year})" if loc else name + f"\n({model}_{pathway.replace('-', '_')}_{year})"

            # Check if activity not already defined as a copy in the foreground database
            act = agb.findActivity(name=code, loc=loc, unit=unit, db_name=USER_DB, single=False)
            if not act:  # If not, get it from the background database
                act = agb.findActivity(  # This is the activity for a given model, pathway and year
                        name=name,
                        loc=loc,
                        unit=unit,
                        db_name=db_name
                    )
                # default behaviour: copy it to the foreground database to avoid unwanted modification of background db
                if copy_act:
                    act = agb.copyActivity(  # safe copy of background act
                        db_name=USER_DB,
                        activity=act,
                        code=code  #name + f"\n({model}_{pathway.replace('-', '_')}_{year})"
                    )
            acts[(model, pathway.replace('-', '_'), year)] = act
        return acts

    def _create_proxy_activity_premise(self, name, loc, unit, code):
        """
        Searches for an ecoinvent activity in the prospective databases and build a parent activity
        that enables to switch between scenarios with dedicated parameters.
        :param name: name of the activity to search
        :param loc: geographical location
        :param unit: unit of activity
        :param code: new name to give to activity when it will be copied to the foreground database
        :return: a multiswitch activity that points to the activity in the different prospective databases
        """

        # previously defined foreground activity --> not in premise. Regular search.
        if name.startswith('#'):
            return self._get_tech_activity(name, loc, unit)

        # Create parameters for year, model and pathway
        years = list(set([scenario[KEY_YEAR] for scenario in self.premise_scenarios]))
        models = list(set([scenario[KEY_MODEL] for scenario in self.premise_scenarios]))
        pathways = list(set([scenario[KEY_PATHWAY].replace('-', '_') for scenario in self.premise_scenarios]))
        # nb: replaced '-' by '_' in pathway names to avoid issues with lca parameters definition
        year_param = agb.params.all_params().get(
            KEY_YEAR,  # get parameter if already defined
            agb.newFloatParam(  # create float parameter if not already exists
                name=KEY_YEAR,
                default=years[0],
                min=min(years),
                max=max(years),
                dbname=USER_DB
            )
        )
        model_param = agb.params.all_params().get(
            KEY_MODEL,  # get switch parameter if already defined
            agb.newEnumParam(  # create switch parameter if not already exists
                name=KEY_MODEL,
                values=models,
                default=models[0],
                dbname=USER_DB
            )
        )
        pathway_param = agb.params.all_params().get(
            KEY_PATHWAY,  # get switch parameter if already defined
            agb.newEnumParam(  # create switch parameter if not already exists
                name=KEY_PATHWAY,
                values=pathways,
                default=pathways[0],
                dbname=USER_DB
            )
        )

        # Get the ecoinvent activity for each combination of model, pathway, and year
        acts = self._get_tech_activity_premise(name, loc, unit)

        # Dictionary to hold the lists of years for each (model, pathway)
        model_pathway_years = {}
        for model, pathway, year in acts.keys():
            model_pathway = (model, pathway)
            if model_pathway not in model_pathway_years:
                model_pathway_years[model_pathway] = []
            model_pathway_years[model_pathway].append(year)

        # Dictionary to hold the activities that point to the different years for each (model, pathway)
        acts_dict = {}
        for model_pathway, years in model_pathway_years.items():
            model = model_pathway[0]
            pathway = model_pathway[1]
            if len(years) == 1:
                acts_dict[model_pathway] = acts[(model, pathway, years[0])]
            else:  # create intermediate activity that is a linear interpolation between years
                acts_dict[model_pathway] = agb.interpolate_activities(
                    db_name=USER_DB,
                    act_name=name + f"\n[{loc}]\n({model}_{pathway})" if loc else name + f"\n({model}_{pathway})",
                    param=year_param,
                    act_per_value={
                        year: acts[(model, pathway, year)] for year in years
                    },
                )

        # Create parent activity that enables to switch between each (model, pathway)
        act = newMultiSwitchAct(
            dbname=USER_DB,
            name=code,
            paramDefList=[model_param, pathway_param],
            acts_dict=acts_dict
        )

        return act

    def _parse_problem_table(self, group, table: dict, group_switch_param=None):
        """
        Feeds provided group, using definition in provided table.

        :param group:
        :param table:
        """

        if KEY_NAME in table:
            # The defined table is only a background activity
            name = table[KEY_NAME]
            loc = table.get(KEY_LOCATION, None)
            unit = table.get(KEY_UNIT, None)
            categories = table.get(KEY_CATEGORIES, None)
            exchange = _parse_exchange(table)
            custom_attributes = table.get(KEY_CUSTOM_ATTR, [])
            update_exchanges = table.get(KEY_UPDATE_ACT, [])
            delete_exchanges = table.get(KEY_DELETE, [])
            add_exchanges = table.get(KEY_ADD, [])
            try:
                sub_act = self._get_tech_activity(name, loc, unit) if not self.premise_scenarios else \
                    self._create_proxy_activity_premise(name, loc, unit, code=name)
                # Add custom attributes
                for attr in custom_attributes:
                    attr_dict = {attr.get(KEY_ATTR_NAME): attr.get(KEY_ATTR_VALUE)}
                    sub_act.updateMeta(**attr_dict)
                # Add exchanges if defined in the configuration file
                if add_exchanges:
                    act_meta = {KEY_NAME: name, KEY_LOCATION: loc, KEY_UNIT: unit}
                    self._add_exchanges(sub_act, act_meta, add_exchanges)
                # Update exchanges if defined in the configuration file
                if update_exchanges:
                    act_meta = {KEY_NAME: name, KEY_LOCATION: loc, KEY_UNIT: unit}
                    self._update_exchanges(sub_act, act_meta, update_exchanges)
                # Delete exchanges if defined in the configuration file
                if delete_exchanges:
                    act_meta = {KEY_NAME: name, KEY_LOCATION: loc, KEY_UNIT: unit}
                    self._delete_exchanges(sub_act, act_meta, delete_exchanges)
            except:  # Search activity in biosphere3 db
                sub_act = agb.findBioAct(
                    name=name,
                    loc=loc,
                    categories=categories,
                    unit=unit
                )
            group.addExchanges({sub_act: exchange})

        for key, value in table.items():
            if isinstance(value, dict):  # value defines a sub activity
                # Check if an activity with this key as already been defined to avoid overriding it
                if agb.findActivity(key, db_name=USER_DB, single=False):
                    warn(f"Activity with name '{key}' defined multiple times. "
                         f"Adding suffix increments to labels. "
                         f"To refer to pre-existing activity, use name: '#activity_name'.")
                    key = _get_unique_activity_name(key)

                name = value.get(KEY_NAME, '')
                if name:  # It is a background activity (or a previously defined activity)
                    loc = value.get(KEY_LOCATION, None)
                    unit = value.get(KEY_UNIT, None)
                    categories = value.get(KEY_CATEGORIES, None)
                    exchange = _parse_exchange(value)
                    custom_attributes = value.get(KEY_CUSTOM_ATTR, [])
                    update_exchanges = value.get(KEY_UPDATE_ACT, [])
                    delete_exchanges = value.get(KEY_DELETE, [])
                    add_exchanges = value.get(KEY_ADD, [])
                    try:  # Search activity in ecoinvent db
                        sub_act = self._get_tech_activity(name, loc, unit, key) if not self.premise_scenarios else \
                            self._create_proxy_activity_premise(name, loc, unit, code=key)
                        # Add custom attributes
                        for attr in custom_attributes:
                            attr_dict = {attr.get(KEY_ATTR_NAME): attr.get(KEY_ATTR_VALUE)}
                            sub_act.updateMeta(**attr_dict)
                        # Add exchanges if defined in the configuration file
                        if add_exchanges:
                            act_meta = {KEY_NAME: name, KEY_LOCATION: loc, KEY_UNIT: unit}
                            self._add_exchanges(sub_act, act_meta, add_exchanges)
                        # Update exchanges if defined in the configuration file
                        if update_exchanges:
                            act_meta = {KEY_NAME: name, KEY_LOCATION: loc, KEY_UNIT: unit}
                            self._update_exchanges(sub_act, act_meta, update_exchanges)
                        # Delete exchanges if defined in the configuration file
                        if delete_exchanges:
                            act_meta = {KEY_NAME: name, KEY_LOCATION: loc, KEY_UNIT: unit}
                            self._delete_exchanges(sub_act, act_meta, delete_exchanges)
                    except:  # Could not find activity in ecoinvent. Search activity in biosphere.
                        sub_act = agb.findBioAct(
                            name=name,
                            loc=loc,
                            categories=categories,
                            unit=unit
                        )

                    if group_switch_param:
                        # Parent group is a switch activity
                        switch_value = key.replace('_',
                                                   '')  # trick since lca algebraic does not handles correctly switch values with underscores
                        group.addExchanges({sub_act: exchange * group_switch_param.symbol(switch_value)})
                    else:
                        # Parent group is a regular activity
                        group.addExchanges({sub_act: exchange})
                else:
                    # It is a group
                    exchange = _parse_exchange(value)  # exchange with parent group
                    unit = value.get(KEY_UNIT, None)  # activity unit
                    is_switch = value.get(KEY_SWITCH, None)
                    switch_param = None
                    if not is_switch:
                        # It is a regular activity
                        sub_act = agb.newActivity(
                            db_name=USER_DB,
                            name=key,
                            unit=unit
                        )
                        # Add custom attributes
                        for attr in value.get(KEY_CUSTOM_ATTR, []):
                            attr_dict = {attr.get(KEY_ATTR_NAME): attr.get(KEY_ATTR_VALUE)}
                            sub_act.updateMeta(**attr_dict)
                    else:
                        # It is a switch activity
                        switch_values = value.copy()
                        switch_values.pop(KEY_EXCHANGE, None)
                        switch_values.pop(KEY_SWITCH)
                        switch_values = list(
                            switch_values.keys())  # [val + '_enum' for val in list(switch_values.keys())]
                        switch_values = [val.replace('_', '') for val in
                                         switch_values]  # trick since lca algebraic does not handles correctly switch values with underscores
                        switch_param = agb.newEnumParam(
                            name=key + '_switch_param',  # name of switch parameter
                            values=switch_values,  # possible values
                            default=switch_values[0],  # default value
                            dbname=USER_DB  # parameter defined in foreground database
                        )
                        sub_act = agb.newSwitchAct(
                            dbname=USER_DB,
                            name=key,
                            paramDef=switch_param,
                            acts_dict={}
                        )
                        # Add custom attributes
                        for attr in value.get(KEY_CUSTOM_ATTR, []):
                            attr_dict = {attr.get(KEY_ATTR_NAME): attr.get(KEY_ATTR_VALUE)}
                            sub_act.updateMeta(**attr_dict)

                    # Check if parent group is a switch activity or a regular activity
                    if group_switch_param:
                        # Parent group is a switch activity
                        switch_value = key.replace('_',
                                                   '')  # trick since lca algebraic does not handles correctly switch values with underscores
                        group.addExchanges({sub_act: exchange * group_switch_param.symbol(switch_value)})
                    else:
                        # Parent group is a regular activity
                        group.addExchanges({sub_act: exchange})
                    self._parse_problem_table(sub_act, value, switch_param)

    def _update_exchanges(self, act, act_meta, update_exchanges):
        """
        Updates exchanges of an activity with new values.
        :param act: activity to be updated
        :param act_meta: dictionary of (name, loc, unit) of the original activity in ecoinvent
        :param update_exchanges: exchanges of the activity to be updated
        :return:
        """

        if act_meta.get(KEY_NAME).startswith('#'):
            _LOGGER.warning(f"Updating exchanges for a previously defined activity is not supported.")

        exchanges_to_update = {}
        premise_exchanges_to_update = {}

        for update in update_exchanges:
            input_activity = update.get(KEY_INPUT_ACT)
            new_value = update.get(KEY_NEW_VAL)

            if not isinstance(new_value, dict):
                raise ValueError(f"Invalid format for 'new_value' in 'update'. Expected a dictionary.")

            # TODO: refactor to allow sum() formula in new amount. See _add_exchanges() for example
            if KEY_EXCHANGE in new_value and len(new_value) == 1:  # update the amount only
                new_amount = _parse_exchange(new_value)
                new_input = None
            elif KEY_EXCHANGE not in new_value:  # update the input activity only
                new_amount = None
                new_input = self._get_new_input(new_value)
            else:  # update both amount and input activity
                new_amount = _parse_exchange(new_value)
                new_input = self._get_new_input(new_value)

            if not self.premise_scenarios:
                if new_input is None:
                    exchanges_to_update[input_activity] = dict(amount=new_amount)
                elif new_amount is None:
                    exchanges_to_update[input_activity] = dict(input=new_input)
                else:
                    exchanges_to_update[input_activity] = dict(amount=new_amount, input=new_input)

            else:
                if isinstance(new_input, dict):
                    for key in new_input.keys():
                        if key not in premise_exchanges_to_update:
                            premise_exchanges_to_update[key] = {}
                        if new_amount is None:
                            premise_exchanges_to_update[key][input_activity] = dict(input=new_input[key])
                        else:
                            premise_exchanges_to_update[key][input_activity] = dict(amount=new_amount, input=new_input[key])
                else:
                    if 'default' not in premise_exchanges_to_update:
                        premise_exchanges_to_update['default'] = {}
                    if new_input is None:
                        premise_exchanges_to_update['default'][input_activity] = dict(amount=new_amount)
                    elif new_amount is None:
                        premise_exchanges_to_update['default'][input_activity] = dict(input=new_input)
                    else:
                        premise_exchanges_to_update['default'][input_activity] = dict(amount=new_amount, input=new_input)

        if not self.premise_scenarios:
            act.updateExchanges(exchanges_to_update)
        else:
            self._update_multiple_databases(act_meta, premise_exchanges_to_update)

    def _delete_exchanges(self, act, act_meta, delete_exchanges):
        """
        Deletes exchanges of an activity.
        :param act: activity to be updated
        :param act_meta: dictionary of (name, loc, unit) of the original activity in ecoinvent
        :param delete_exchanges: exchanges of the activity to be deleted
        :return:
        """

        if act_meta.get(KEY_NAME).startswith('#'):
            _LOGGER.warning(f"Deleting exchanges for a previously defined activity is not supported.")
            return

        acts_premise = self._get_tech_activity_premise(
            name=act_meta.get(KEY_NAME),
            loc=act_meta.get(KEY_LOCATION),
            unit=act_meta.get(KEY_UNIT)
        )

        for delete in delete_exchanges:
            input_activity = delete.get(KEY_INPUT_ACT)
            if not self.premise_scenarios:
                act.deleteExchanges(input_activity, single=False)
            else:
                for act_premise in acts_premise.values():
                    act_premise.deleteExchanges(input_activity, single=False)

    def _add_exchanges(self, act, act_meta, add_exchanges):
        """
        Adds exchanges to an activity.
        :param act: activity to be updated
        :param act_meta: dictionary of (name, loc, unit) of the original activity in ecoinvent
        :param add_exchanges: exchanges to be added to the activity
        :return:
        """

        if act_meta.get(KEY_NAME).startswith('#'):
            _LOGGER.warning(f"Adding exchanges for a previously defined activity is not supported.")
            return

        exchanges_to_add = {}
        premise_exchanges_to_add = {}
        acts_premise = self._get_tech_activity_premise(
            name=act_meta.get(KEY_NAME),
            loc=act_meta.get(KEY_LOCATION),
            unit=act_meta.get(KEY_UNIT)
        )

        for add in add_exchanges:
            new_input = self._get_new_input(add)

            if not self.premise_scenarios:
                new_amount = _parse_exchange(add, act=act)
                exchanges_to_add[new_input] = new_amount

            else:
                for key, act_premise in acts_premise.items():
                    if key not in premise_exchanges_to_add:
                        premise_exchanges_to_add[key] = {}
                    new_amount = _parse_exchange(add, act=act_premise)
                    if isinstance(new_input, dict):
                        premise_exchanges_to_add[key][new_input[key]] = new_amount
                    else:
                        premise_exchanges_to_add[key][new_input] = new_amount

        if not self.premise_scenarios:
            act.addExchanges(exchanges_to_add)
        else:
            self._add_multiple_databases(act_meta, premise_exchanges_to_add)

    def _get_new_input(self, new_value):
        name = new_value.get(KEY_NAME)
        loc = new_value.get(KEY_LOCATION)
        unit = new_value.get(KEY_UNIT)
        categories = new_value.get(KEY_CATEGORIES)

        if name:  # background activity or previously defined foreground activity
            try:
                if not self.premise_scenarios or name.startswith('#'):
                    return self._get_tech_activity(name, loc, unit, copy_act=False) # copy act would be a bit overkill here
                else:
                    return self._get_tech_activity_premise(name, loc, unit, copy_act=False)
            except:
                return agb.findBioAct(name=name, loc=loc, categories=categories, unit=unit)
        else:  # new foreground activity
            new_act = new_value.copy()
            if KEY_EXCHANGE in new_act:
                new_act.pop(KEY_EXCHANGE)
            if len(new_act) > 1:
                _LOGGER.warning("Multiple activities defined as new input activity in 'new_value' in 'update'. "
                                "Only the first one will be considered.")
            key, value = next(iter(new_act.items()))
            unit = value.get(KEY_UNIT)
            if value.get(KEY_SWITCH):
                _LOGGER.warning("'is_switch' cannot be used when declaring new input activity in 'update'. Skipping.")
            new_input = agb.newActivity(db_name=USER_DB, name=key, unit=unit)
            self._parse_problem_table(new_input, value)
            return new_input

    def _update_multiple_databases(self, act_meta, premise_exchanges_to_update):
        acts_premise = self._get_tech_activity_premise(
            name=act_meta.get(KEY_NAME),
            loc=act_meta.get(KEY_LOCATION),
            unit=act_meta.get(KEY_UNIT)
        )

        for key, exchanges in premise_exchanges_to_update.items():
            if key == 'default':
                for premise_key in acts_premise.keys():
                    acts_premise[premise_key].updateExchanges(exchanges)
            else:
                acts_premise[key].updateExchanges(exchanges)

    def _add_multiple_databases(self, act_meta, premise_exchanges_to_add):
        acts_premise = self._get_tech_activity_premise(
            name=act_meta.get(KEY_NAME),
            loc=act_meta.get(KEY_LOCATION),
            unit=act_meta.get(KEY_UNIT)
        )

        for key, exchanges in premise_exchanges_to_add.items():
            if key == 'default':
                for premise_key in acts_premise.keys():
                    acts_premise[premise_key].addExchanges(exchanges)
            else:
                acts_premise[key].addExchanges(exchanges)


class _IDictSerializer(ABC):
    """Interface for reading and writing dict-like data"""

    @property
    @abstractmethod
    def data(self) -> dict:
        """
        The data that have been read, or will be written.
        """

    @abstractmethod
    def read(self, file_path: str):
        """
        Reads data from provided file.
        :param file_path:
        """

    @abstractmethod
    def write(self, file_path: str):
        """
        Writes data to provided file.
        :param file_path:
        """


class _YAMLSerializer(_IDictSerializer):
    """YAML-format serializer."""

    def __init__(self):
        self._data = None

    @property
    def data(self):
        return self._data

    def read(self, file_path: str):
        yaml = YAML(typ="safe")
        with open(file_path) as yaml_file:
            self._data = yaml.load(yaml_file)

    def write(self, file_path: str):
        yaml = YAML()
        yaml.default_flow_style = False
        with open(file_path, "w") as file:
            yaml.dump(self._data, file)