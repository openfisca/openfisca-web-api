# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014, 2015 OpenFisca Team
# https://github.com/openfisca
#
# This file is part of OpenFisca.
#
# OpenFisca is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""Root controllers"""


from __future__ import division

import collections
import copy
import datetime
import itertools
import multiprocessing
import os

import numpy as np
from openfisca_core import decompositions, legislations, periods, simulations

from . import conf, contexts, conv, model, urls, wsgihelpers


cpu_count = multiprocessing.cpu_count()
N_ = lambda message: message
router = None


@wsgihelpers.wsgify
def api1_calculate(req):
    ctx = contexts.Ctx(req)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx)

    assert req.method == 'POST', req.method

    if conf['load_alert']:
        try:
            load_average = os.getloadavg()
        except (AttributeError, OSError):
            # When load average is not available, always accept request.
            pass
        else:
            if load_average[0] / cpu_count > 1:
                return wsgihelpers.respond_json(ctx,
                    collections.OrderedDict(sorted(dict(
                        apiVersion = '1.0',
                        error = collections.OrderedDict(sorted(dict(
                            code = 503,  # Service Unavailable
                            message = ctx._(u'Server is overloaded: {} {} {}').format(*load_average),
                            ).iteritems())),
                        method = req.script_name,
                        url = req.url.decode('utf-8'),
                        ).iteritems())),
                    headers = headers,
                    )

    content_type = req.content_type
    if content_type is not None:
        content_type = content_type.split(';', 1)[0].strip()
    if content_type != 'application/json':
        return wsgihelpers.respond_json(ctx,
            collections.OrderedDict(sorted(dict(
                apiVersion = '1.0',
                error = collections.OrderedDict(sorted(dict(
                    code = 400,  # Bad Request
                    message = ctx._(u'Bad content-type: {}').format(content_type),
                    ).iteritems())),
                method = req.script_name,
                url = req.url.decode('utf-8'),
                ).iteritems())),
            headers = headers,
            )

    inputs, error = conv.pipe(
        conv.make_input_to_json(object_pairs_hook = collections.OrderedDict),
        conv.test_isinstance(dict),
        conv.not_none,
        )(req.body, state = ctx)
    if error is not None:
        return wsgihelpers.respond_json(ctx,
            collections.OrderedDict(sorted(dict(
                apiVersion = '1.0',
                error = collections.OrderedDict(sorted(dict(
                    code = 400,  # Bad Request
                    errors = [conv.jsonify_value(error)],
                    message = ctx._(u'Invalid JSON in request POST body'),
                    ).iteritems())),
                method = req.script_name,
                params = req.body,
                url = req.url.decode('utf-8'),
                ).iteritems())),
            headers = headers,
            )

    data, errors = conv.struct(
        dict(
            # api_key = conv.pipe(  # Shared secret between client and server
            #     conv.test_isinstance(basestring),
            #     conv.input_to_uuid_str,
            #     conv.not_none,
            #     ),
            context = conv.test_isinstance(basestring),  # For asynchronous calls
            intermediate_variables = conv.pipe(
                conv.test_isinstance((bool, int)),
                conv.anything_to_bool,
                conv.default(False),
                ),
            reform_names = conv.noop,  # Real conversion is done once tax-benefit system is known.
            scenarios = conv.pipe(
                conv.test_isinstance(list),
                conv.uniform_sequence(
                    conv.not_none,  # Real conversion is done once tax-benefit system is known.
                    ),
                conv.test(lambda scenarios: len(scenarios) >= 1, error = N_(u'At least one scenario is required')),
                conv.test(lambda scenarios: len(scenarios) <= 100,
                    error = N_(u"There can't be more than 100 scenarios")),
                conv.not_none,
                ),
            tax_benefit_system = model.TaxBenefitSystem.json_to_cached_or_new_instance,
            trace = conv.pipe(
                conv.test_isinstance((bool, int)),
                conv.anything_to_bool,
                conv.default(False),
                ),
            validate = conv.pipe(
                conv.test_isinstance((bool, int)),
                conv.anything_to_bool,
                conv.default(False),
                ),
            variables = conv.pipe(
                conv.test_isinstance(list),
                conv.uniform_sequence(
                    conv.pipe(
                        conv.test_isinstance(basestring),
                        conv.cleanup_line,
                        # Remaining of conversion is done once tax-benefit system is known.
                        conv.not_none,
                        ),
                    constructor = set,
                    ),
                conv.test(lambda variables: len(variables) >= 1, error = N_(u'At least one variable is required')),
                conv.not_none,
                ),
            ),
        )(inputs, state = ctx)

    if errors is None:
        tax_benefit_system = data['tax_benefit_system']
        data, errors = conv.struct(
            dict(
                reform_names = conv.pipe(
                    conv.test_isinstance(list),
                    conv.uniform_sequence(
                        conv.pipe(
                            conv.test_isinstance(basestring),
                            conv.cleanup_line,
                            conv.test_in(conf['reforms'].keys()),
                            ),
                        drop_none_items = True,
                        ),
                    conv.empty_to_none,
                    conv.test(lambda values: len(values) == 1, error = u'Only one reform name is accepted for now'),
                    ),
                ),
            default = conv.noop,
            )(data, state = ctx)

        if errors is None:
            if data['reform_names'] is None:
                with_reform = False
            else:
                with_reform = True
                reform_name = data['reform_names'][0]
                build_reform = conf['reforms'][reform_name]
                Reform = build_reform(tax_benefit_system)
                tax_benefit_system = Reform()
            reference_tax_benefit_system = tax_benefit_system.real_reference
            data, errors = conv.struct(
                dict(
                    scenarios = conv.uniform_sequence(
                        tax_benefit_system.Scenario.make_json_to_cached_or_new_instance(
                            cache_dir = conf['cache_dir'],
                            repair = data['validate'],
                            tax_benefit_system = tax_benefit_system,
                            )
                        ),
                    variables = conv.uniform_sequence(
                        conv.test_in(tax_benefit_system.column_by_name),
                        ),
                    ),
                default = conv.noop,
                )(data, state = ctx)

    if errors is not None:
        return wsgihelpers.respond_json(ctx,
            collections.OrderedDict(sorted(dict(
                apiVersion = '1.0',
                context = inputs.get('context'),
                error = collections.OrderedDict(sorted(dict(
                    code = 400,  # Bad Request
                    errors = [conv.jsonify_value(errors)],
                    message = ctx._(u'Bad parameters in request'),
                    ).iteritems())),
                method = req.script_name,
                params = inputs,
                url = req.url.decode('utf-8'),
                ).iteritems())),
            headers = headers,
            )

#    api_key = data['api_key']
#    account = model.Account.find_one(
#        dict(
#            api_key = api_key,
#            ),
#        as_class = collections.OrderedDict,
#        )
#    if account is None:
#        return wsgihelpers.respond_json(ctx,
#            collections.OrderedDict(sorted(dict(
#                apiVersion = '1.0',
#                context = data['context'],
#                error = collections.OrderedDict(sorted(dict(
#                    code = 401,  # Unauthorized
#                    message = ctx._('Unknown API Key: {}').format(api_key),
#                    ).iteritems())),
#                method = req.script_name,
#                params = inputs,
#                url = req.url.decode('utf-8'),
#                ).iteritems())),
#            headers = headers,
#            )

    suggestions = {}
    for scenario_index, scenario in enumerate(data['scenarios']):
        if data['validate']:
            original_test_case = scenario.test_case
            scenario.test_case = copy.deepcopy(original_test_case)
        suggestion = scenario.suggest()
        if data['validate']:
            scenario.test_case = original_test_case
        if suggestion is not None:
            suggestions.setdefault('scenarios', {})[scenario_index] = suggestion
    if not suggestions:
        suggestions = None

    if data['validate']:
        # Only a validation is requested. Don't launch simulation
        return wsgihelpers.respond_json(ctx,
            collections.OrderedDict(sorted(dict(
                apiVersion = '1.0',
                context = inputs.get('context'),
                method = req.script_name,
                params = inputs,
                repaired_scenarios = [
                    scenario.to_json()
                    for scenario in data['scenarios']
                    ],
                suggestions = suggestions,
                url = req.url.decode('utf-8'),
                ).iteritems())),
            headers = headers,
            )

    simulations = []
    for scenario in data['scenarios']:
        if with_reform:
            # First compute the reference simulation (ie without reform).
            simulation = scenario.new_simulation(trace = data['trace'], reference = True)
            for variable in data['variables']:
                simulation.calculate(variable)
            simulations.append(simulation)
        simulation = scenario.new_simulation(trace = data['trace'])
        for variable in data['variables']:
            simulation.calculate(variable)
        simulations.append(simulation)

    output_test_cases = []
    for scenario, simulation in itertools.izip(data['scenarios'], simulations):
        if data['intermediate_variables']:
            holders = []
            for step in simulation.traceback.itervalues():
                holder = step['holder']
                if holder not in holders:
                    holders.append(holder)
        else:
            holders = [
                simulation.get_holder(variable)
                for variable in data['variables']
                ]
        test_case = scenario.to_json()['test_case']
        for holder in holders:
            variable_value_json = holder.to_value_json()
            if variable_value_json is None:
                continue
            variable_name = holder.column.name
            test_case_entity_by_id = test_case[holder.entity.key_plural]
            if isinstance(variable_value_json, dict):
                for entity_index, test_case_entity in enumerate(test_case_entity_by_id.itervalues()):
                    test_case_entity[variable_name] = {
                        period: array_json[entity_index]
                        for period, array_json in variable_value_json.iteritems()
                        }
            else:
                for test_case_entity, cell_json in itertools.izip(test_case_entity_by_id.itervalues(),
                        variable_value_json):
                    test_case_entity[variable_name] = cell_json
        output_test_cases.append(test_case)

    if data['trace']:
        simulations_variables_json = []
        tracebacks_json = []
        for simulation in simulations:
            simulation_variables_json = {}
            traceback_json = []
            for (variable_name, period), step in simulation.traceback.iteritems():
                holder = step['holder']
                if variable_name not in simulation_variables_json:
                    variable_value_json = holder.to_value_json()
                    if variable_value_json is not None:
                        simulation_variables_json[variable_name] = variable_value_json
                column = holder.column
                input_variables_infos = step.get('input_variables_infos')
                used_periods = step.get('used_periods')
                traceback_json.append(dict(
                    cell_type = column.val_type,
                    default_input_variables = step.get('default_input_variables', False),
                    entity = column.entity,
                    input_variables = [
                        (input_variable_name, str(input_variable_period))
                        for input_variable_name, input_variable_period in input_variables_infos
                        ] if input_variables_infos else None,
                    is_computed = step.get('is_computed', False),
                    label = column.label,
                    name = variable_name,
                    period = str(period) if period is not None else None,
                    used_periods = [
                        str(used_period)
                        for used_period in used_periods
                        ] if used_periods is not None else None,
                    ))
            simulations_variables_json.append(simulation_variables_json)
            tracebacks_json.append(traceback_json)
    else:
        simulations_variables_json = None
        tracebacks_json = None

    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(dict(
            apiVersion = '1.0',
            context = data['context'],
            method = req.script_name,
            params = inputs,
            suggestions = suggestions,
            tracebacks = tracebacks_json,
            url = req.url.decode('utf-8'),
            value = output_test_cases,
            variables = simulations_variables_json,
            ).iteritems())),
        headers = headers,
        )


@wsgihelpers.wsgify
def api1_default_legislation(req):
    """Return default legislation in JSON format."""
    ctx = contexts.Ctx(req)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx)

    assert req.method == 'GET', req.method

    return wsgihelpers.respond_json(ctx, model.tax_benefit_system.legislation_json, headers = headers)


@wsgihelpers.wsgify
def api1_entities(req):
    def build_entity_data(entity_class):
        entity_data = {
            'isPersonsEntity': entity_class.is_persons_entity,
            'label': entity_class.label,
            'nameKey': entity_class.name_key,
            }
        if hasattr(entity_class, 'roles_key'):
            entity_data.update({
                'maxCardinalityByRoleKey': entity_class.max_cardinality_by_role_key,
                'roles': entity_class.roles_key,
                'labelByRoleKey': entity_class.label_by_role_key,
                })
        return entity_data

    ctx = contexts.Ctx(req)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx)

    assert req.method == 'GET', req.method

    entities_class = model.tax_benefit_system.entity_class_by_key_plural.itervalues()
    data = collections.OrderedDict(sorted({
        entity_class.key_plural: build_entity_data(entity_class)
        for entity_class in entities_class
        }.iteritems()))
    return wsgihelpers.respond_json(ctx, data, headers = headers)


@wsgihelpers.wsgify
def api1_field(req):
    ctx = contexts.Ctx(req)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx)

    assert req.method == 'GET', req.method

    params = req.GET
    inputs = dict(
        context = params.get('context'),
        input_variables = params.get('input_variables'),
        variable = params.get('variable'),
        )
    data, errors = conv.pipe(
        conv.struct(
            dict(
                context = conv.noop,  # For asynchronous calls
                input_variables = conv.pipe(
                    conv.test_isinstance((bool, int, basestring)),
                    conv.anything_to_bool,
                    conv.default(False),
                    ),
                variable = conv.pipe(
                    conv.cleanup_line,
                    conv.default(u'revdisp'),
                    conv.test_in(model.tax_benefit_system.column_by_name),
                    ),
                ),
            default = 'drop',
            ),
        )(inputs, state = ctx)
    if errors is not None:
        return wsgihelpers.respond_json(ctx,
            collections.OrderedDict(sorted(dict(
                apiVersion = '1.0',
                context = inputs.get('context'),
                error = collections.OrderedDict(sorted(dict(
                    code = 400,  # Bad Request
                    errors = [conv.jsonify_value(errors)],
                    message = ctx._(u'Bad parameters in request'),
                    ).iteritems())),
                method = req.script_name,
                params = inputs,
                url = req.url.decode('utf-8'),
                ).iteritems())),
            headers = headers,
            )

    simulation = simulations.Simulation(
        period = periods.period(datetime.date.today().year),
        tax_benefit_system = model.tax_benefit_system,
        )
    holder = simulation.get_or_new_holder(data['variable'])

    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(dict(
            apiVersion = '1.0',
            context = data['context'],
            method = req.script_name,
            params = inputs,
            url = req.url.decode('utf-8'),
            value = holder.to_field_json(
                input_variables_extractor = model.input_variables_extractor if data['input_variables'] else None,
                ),
            ).iteritems())),
        headers = headers,
        )


@wsgihelpers.wsgify
def api1_fields(req):
    ctx = contexts.Ctx(req)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx)

    assert req.method == 'GET', req.method
    params = req.GET
    inputs = dict(
        context = params.get('context'),
        )
    data, errors = conv.pipe(
        conv.struct(
            dict(
                context = conv.noop,  # For asynchronous calls
                ),
            default = 'drop',
            ),
        )(inputs, state = ctx)
    if errors is not None:
        return wsgihelpers.respond_json(ctx,
            collections.OrderedDict(sorted(dict(
                apiVersion = '1.0',
                context = inputs.get('context'),
                error = collections.OrderedDict(sorted(dict(
                    code = 400,  # Bad Request
                    errors = [conv.jsonify_value(errors)],
                    message = ctx._(u'Bad parameters in request'),
                    ).iteritems())),
                method = req.script_name,
                params = inputs,
                url = req.url.decode('utf-8'),
                ).iteritems())),
            headers = headers,
            )

    columns = collections.OrderedDict(
        (name, column.to_json())
        for name, column in model.tax_benefit_system.column_by_name.iteritems()
        if name not in ('idfam', 'idfoy', 'idmen', 'noi', 'quifam', 'quifoy', 'quimen')
        if column.formula_class is None
        )

    columns_tree = collections.OrderedDict(
        (
            dict(
                fam = 'familles',
                foy = 'foyers_fiscaux',
                ind = 'individus',
                men = 'menages',
                )[entity],
            copy.deepcopy(tree),
            )
        for entity, tree in model.tax_benefit_system.columns_name_tree_by_entity.iteritems()
        )

    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(dict(
            apiVersion = '1.0',
            columns = columns,
            columns_tree = columns_tree,
            context = data['context'],
            method = req.script_name,
            params = inputs,
            prestations = collections.OrderedDict(
                (name, column.to_json())
                for name, column in model.tax_benefit_system.column_by_name.iteritems()
                if column.formula_class is not None
                ),
            url = req.url.decode('utf-8'),
            ).iteritems())),
        headers = headers,
        )


@wsgihelpers.wsgify
def api1_formula(req):
    ctx = contexts.Ctx(req)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx)

    tax_benefit_system = model.tax_benefit_system

    requested_column, error = conv.pipe(
        conv.cleanup_line,
        conv.test_in(tax_benefit_system.column_by_name),
        conv.function(lambda column_name: tax_benefit_system.column_by_name[column_name]),
        conv.test(lambda column: column.formula_class is not None, error = N_(u"Variable is not a formula")),
        conv.not_none,
        )(req.urlvars.get('name'), state = ctx)
    if error is not None:
        return wsgihelpers.respond_json(ctx,
            collections.OrderedDict(sorted(dict(
                apiVersion = '1.0',
                error = collections.OrderedDict(sorted(dict(
                    code = 400,  # Bad Request
                    errors = [conv.jsonify_value(error)],
                    message = ctx._(u'Invalid formula name in request URL'),
                    ).iteritems())),
                method = req.script_name,
                params = req.body,
                url = req.url.decode('utf-8'),
                ).iteritems())),
            headers = headers,
            )

    params = req.GET
    inputs = dict(params)
    data, errors = conv.pipe(
        conv.struct(
            dict(
                (column.name, column.input_to_dated_python)
                for column in tax_benefit_system.column_by_name.itervalues()
                ),
            drop_none_values = True,
            ),
        )(params, state = ctx)
    if errors is not None:
        return wsgihelpers.respond_json(ctx,
            collections.OrderedDict(sorted(dict(
                apiVersion = '1.0',
                context = inputs.get('context'),
                error = collections.OrderedDict(sorted(dict(
                    code = 400,  # Bad Request
                    errors = [conv.jsonify_value(errors)],
                    message = ctx._(u'Bad parameters in request'),
                    ).iteritems())),
                method = req.script_name,
                params = inputs,
                url = req.url.decode('utf-8'),
                ).iteritems())),
            headers = headers,
            )

    period = periods.period('month', datetime.date.today())
    simulation = simulations.Simulation(
        debug = False,
        period = period,
        tax_benefit_system = tax_benefit_system,
        )
    # Initialize entities, assuming there is only one person and one of each other entities ("familles",
    # "foyers fiscaux", etc).
    persons = None
    for entity in simulation.entity_by_key_plural.itervalues():
        entity.count = 1
        entity.roles_count = 1
        entity.step_size = 1
        if entity.is_persons_entity:
            persons = entity
    # Link person to its entities using ID & role.
    for entity in simulation.entity_by_key_plural.itervalues():
        if not entity.is_persons_entity:
            holder = persons.get_or_new_holder(entity.index_for_person_variable_name)
            holder.set_array(period, np.array([0]))
            holder = persons.get_or_new_holder(entity.role_for_person_variable_name)
            holder.set_array(period, np.array([0]))
    # Inject all variables from query string into arrays.
    for column_name, value in data.iteritems():
        column = tax_benefit_system.column_by_name[column_name]
        entity = simulation.entity_by_key_plural[column.entity_key_plural]
        holder = entity.get_or_new_holder(column_name)
        holder.set_array(period, np.array([value]))

    requested_dated_holder = simulation.compute(requested_column.name)

    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(dict(
            apiVersion = '1.0',
            # context = data['context'],
            method = req.script_name,
            params = inputs,
            url = req.url.decode('utf-8'),
            value = requested_dated_holder.to_value_json()[0],  # We have only one person => Unwrap the array.
            ).iteritems())),
        headers = headers,
        )


@wsgihelpers.wsgify
def api1_graph(req):
    ctx = contexts.Ctx(req)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx)

    assert req.method == 'GET', req.method
    params = req.GET
    inputs = dict(
        context = params.get('context'),
        variable = params.get('variable'),
        )
    tax_benefit_system = model.tax_benefit_system
    data, errors = conv.pipe(
        conv.struct(
            dict(
                context = conv.noop,  # For asynchronous calls
                variable = conv.pipe(
                    conv.cleanup_line,
                    conv.default(u'revdisp'),
                    conv.test_in(tax_benefit_system.column_by_name),
                    ),
                ),
            default = 'drop',
            ),
        )(inputs, state = ctx)
    if errors is not None:
        return wsgihelpers.respond_json(ctx,
            collections.OrderedDict(sorted(dict(
                apiVersion = '1.0',
                context = inputs.get('context'),
                error = collections.OrderedDict(sorted(dict(
                    code = 400,  # Bad Request
                    errors = [conv.jsonify_value(errors)],
                    message = ctx._(u'Bad parameters in request'),
                    ).iteritems())),
                method = req.script_name,
                params = inputs,
                url = req.url.decode('utf-8'),
                ).iteritems())),
            headers = headers,
            )

    simulation = simulations.Simulation(
        period = periods.period(datetime.date.today().year),
        tax_benefit_system = tax_benefit_system,
        )
    edges = []
    nodes = []
    visited = set()
    simulation.graph(data['variable'], edges, nodes, visited)

    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(dict(
            apiVersion = '1.0',
            context = data['context'],
            edges = edges,
            method = req.script_name,
            nodes = nodes,
            params = inputs,
            url = req.url.decode('utf-8'),
            ).iteritems())),
        headers = headers,
        )


@wsgihelpers.wsgify
def api1_reforms(req):
    ctx = contexts.Ctx(req)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx)
    params = req.GET
    inputs = dict(params)
    data, errors = conv.pipe(
        conv.struct(
            dict(
                context = conv.noop,  # For asynchronous calls
                ),
            default = 'drop',
            ),
        )(inputs, state = ctx)
    reform_names = conf['reforms'].keys()
    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(dict(
            apiVersion = '1.0',
            context = data['context'],
            method = req.script_name,
            params = inputs,
            reforms = reform_names,
            url = req.url.decode('utf-8'),
            ).iteritems())),
        headers = headers,
        )


@wsgihelpers.wsgify
def api1_simulate(req):
    ctx = contexts.Ctx(req)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx)

    assert req.method == 'POST', req.method

    if conf['load_alert']:
        try:
            load_average = os.getloadavg()
        except (AttributeError, OSError):
            # When load average is not available, always accept request.
            pass
        else:
            if load_average[0] / cpu_count > 1:
                return wsgihelpers.respond_json(ctx,
                    collections.OrderedDict(sorted(dict(
                        apiVersion = '1.0',
                        error = collections.OrderedDict(sorted(dict(
                            code = 503,  # Service Unavailable
                            message = ctx._(u'Server is overloaded: {} {} {}').format(*load_average),
                            ).iteritems())),
                        method = req.script_name,
                        url = req.url.decode('utf-8'),
                        ).iteritems())),
                    headers = headers,
                    )

    content_type = req.content_type
    if content_type is not None:
        content_type = content_type.split(';', 1)[0].strip()
    if content_type != 'application/json':
        return wsgihelpers.respond_json(ctx,
            collections.OrderedDict(sorted(dict(
                apiVersion = '1.0',
                error = collections.OrderedDict(sorted(dict(
                    code = 400,  # Bad Request
                    message = ctx._(u'Bad content-type: {}').format(content_type),
                    ).iteritems())),
                method = req.script_name,
                url = req.url.decode('utf-8'),
                ).iteritems())),
            headers = headers,
            )

    inputs, error = conv.pipe(
        conv.make_input_to_json(object_pairs_hook = collections.OrderedDict),
        conv.test_isinstance(dict),
        conv.not_none,
        )(req.body, state = ctx)
    if error is not None:
        return wsgihelpers.respond_json(ctx,
            collections.OrderedDict(sorted(dict(
                apiVersion = '1.0',
                error = collections.OrderedDict(sorted(dict(
                    code = 400,  # Bad Request
                    errors = [conv.jsonify_value(error)],
                    message = ctx._(u'Invalid JSON in request POST body'),
                    ).iteritems())),
                method = req.script_name,
                params = req.body,
                url = req.url.decode('utf-8'),
                ).iteritems())),
            headers = headers,
            )

    data, errors = conv.struct(
        dict(
            # api_key = conv.pipe(  # Shared secret between client and server
            #     conv.test_isinstance(basestring),
            #     conv.input_to_uuid_str,
            #     conv.not_none,
            #     ),
            context = conv.test_isinstance(basestring),  # For asynchronous calls
            decomposition = conv.noop,  # Real conversion is done once tax-benefit system is known.
            reform_names = conv.noop,  # Real conversion is done once tax-benefit system is known.
            scenarios = conv.pipe(
                conv.test_isinstance(list),
                conv.uniform_sequence(
                    conv.not_none,  # Real conversion is done once tax-benefit system is known.
                    ),
                conv.test(lambda scenarios: len(scenarios) >= 1, error = N_(u'At least one scenario is required')),
                conv.test(lambda scenarios: len(scenarios) <= 100,
                    error = N_(u"There can't be more than 100 scenarios")),
                conv.not_none,
                ),
            tax_benefit_system = model.TaxBenefitSystem.json_to_cached_or_new_instance,
            trace = conv.pipe(
                conv.test_isinstance((bool, int)),
                conv.anything_to_bool,
                conv.default(False),
                ),
            validate = conv.pipe(
                conv.test_isinstance((bool, int)),
                conv.anything_to_bool,
                conv.default(False),
                ),
            ),
        )(inputs, state = ctx)

    if errors is None:
        tax_benefit_system = data['tax_benefit_system']
        data, errors = conv.struct(
            dict(
                reform_names = conv.pipe(
                    conv.test_isinstance(list),
                    conv.uniform_sequence(
                        conv.pipe(
                            conv.test_isinstance(basestring),
                            conv.cleanup_line,
                            conv.test_in(conf['reforms'].keys()),
                            ),
                        drop_none_items = True,
                        ),
                    conv.empty_to_none,
                    conv.test(lambda values: len(values) == 1, error = u'Only one reform name is accepted for now'),
                    ),
                ),
            default = conv.noop,
            )(data, state = ctx)

        if errors is None:
            if data['reform_names'] is None:
                with_reform = False
            else:
                with_reform = True
                reform_name = data['reform_names'][0]
                build_reform = conf['reforms'][reform_name]
                Reform = build_reform(tax_benefit_system)
                tax_benefit_system = Reform()
            reference_tax_benefit_system = tax_benefit_system.real_reference
            data, errors = conv.struct(
                dict(
                    decomposition = conv.pipe(
                        conv.condition(
                            conv.test_isinstance(basestring),
                            conv.test(lambda filename: filename in os.listdir(reference_tax_benefit_system.DECOMP_DIR)),
                            decompositions.make_validate_node_json(reference_tax_benefit_system),
                            ),
                        conv.default(reference_tax_benefit_system.DEFAULT_DECOMP_FILE),
                        ),
                    scenarios = conv.uniform_sequence(
                        tax_benefit_system.Scenario.make_json_to_cached_or_new_instance(
                            cache_dir = conf['cache_dir'],
                            repair = data['validate'],
                            tax_benefit_system = tax_benefit_system,
                            )
                        ),
                    ),
                default = conv.noop,
                )(data, state = ctx)

    if errors is not None:
        return wsgihelpers.respond_json(ctx,
            collections.OrderedDict(sorted(dict(
                apiVersion = '1.0',
                context = inputs.get('context'),
                error = collections.OrderedDict(sorted(dict(
                    code = 400,  # Bad Request
                    errors = [conv.jsonify_value(errors)],
                    message = ctx._(u'Bad parameters in request'),
                    ).iteritems())),
                method = req.script_name,
                params = inputs,
                url = req.url.decode('utf-8'),
                ).iteritems())),
            headers = headers,
            )

#    api_key = data['api_key']
#    account = model.Account.find_one(
#        dict(
#            api_key = api_key,
#            ),
#        as_class = collections.OrderedDict,
#        )
#    if account is None:
#        return wsgihelpers.respond_json(ctx,
#            collections.OrderedDict(sorted(dict(
#                apiVersion = '1.0',
#                context = data['context'],
#                error = collections.OrderedDict(sorted(dict(
#                    code = 401,  # Unauthorized
#                    message = ctx._('Unknown API Key: {}').format(api_key),
#                    ).iteritems())),
#                method = req.script_name,
#                params = inputs,
#                url = req.url.decode('utf-8'),
#                ).iteritems())),
#            headers = headers,
#            )

    suggestions = {}
    for scenario_index, scenario in enumerate(data['scenarios']):
        if data['validate']:
            original_test_case = scenario.test_case
            scenario.test_case = copy.deepcopy(original_test_case)
        suggestion = scenario.suggest()
        if data['validate']:
            scenario.test_case = original_test_case
        if suggestion is not None:
            suggestions.setdefault('scenarios', {})[scenario_index] = suggestion
    if not suggestions:
        suggestions = None

    if data['validate']:
        # Only a validation is requested. Don't launch simulation
        return wsgihelpers.respond_json(ctx,
            collections.OrderedDict(sorted(dict(
                apiVersion = '1.0',
                context = inputs.get('context'),
                method = req.script_name,
                params = inputs,
                repaired_scenarios = [
                    scenario.to_json()
                    for scenario in data['scenarios']
                    ],
                suggestions = suggestions,
                url = req.url.decode('utf-8'),
                ).iteritems())),
            headers = headers,
            )

    if isinstance(data['decomposition'], basestring):
        decomposition_json = reference_tax_benefit_system.get_decomposition_json(data['decomposition'])
    else:
        decomposition_json = data['decomposition']

    simulations = []
    for scenario in data['scenarios']:
        if with_reform:
            # First compute the reference simulation (ie without reform).
            simulation = scenario.new_simulation(trace = data['trace'], reference = True)
            for node in decompositions.iter_decomposition_nodes(decomposition_json):
                if not node.get('children'):
                    simulation.calculate(node['code'])
            simulations.append(simulation)
        simulation = scenario.new_simulation(trace = data['trace'])
        for node in decompositions.iter_decomposition_nodes(decomposition_json):
            if not node.get('children'):
                simulation.calculate(node['code'])
        simulations.append(simulation)

    response_json = copy.deepcopy(decomposition_json)  # Use decomposition as a skeleton for response.
    for node in decompositions.iter_decomposition_nodes(response_json, children_first = True):
        children = node.get('children')
        if children:
            node['values'] = map(lambda *l: sum(l), *(
                child['values']
                for child in children
                ))
        else:
            node['values'] = values = []
            for simulation in simulations:
                holder = simulation.get_holder(node['code'])
                column = holder.column
                values.extend(
                    column.transform_value_to_json(value)
                    for value in holder.new_test_case_array(simulation.period).tolist()
                    )
        column = tax_benefit_system.column_by_name.get(node['code'])
        if column is not None and column.url is not None:
            node['url'] = column.url

    if data['trace']:
        simulations_variables_json = []
        tracebacks_json = []
        for simulation in simulations:
            simulation_variables_json = {}
            traceback_json = []
            for (variable_name, period), step in simulation.traceback.iteritems():
                holder = step['holder']
                if variable_name not in simulation_variables_json:
                    variable_value_json = holder.to_value_json()
                    if variable_value_json is not None:
                        simulation_variables_json[variable_name] = variable_value_json
                input_variables_infos = step.get('input_variables_infos')
                column = holder.column
                used_periods = step.get('used_periods')
                traceback_json.append(dict(
                    cell_type = column.val_type,
                    default_input_variables = step.get('default_input_variables', False),
                    entity = column.entity,
                    input_variables = [
                        (variable_name, str(variable_period))
                        for variable_name, variable_period in input_variables_infos
                        ] if input_variables_infos else None,
                    is_computed = step.get('is_computed', False),
                    label = column.label,
                    name = variable_name,
                    period = str(period) if period is not None else None,
                    used_periods = [
                        str(used_period)
                        for used_period in used_periods
                        ] if used_periods is not None else None,
                    ))
            simulations_variables_json.append(simulation_variables_json)
            tracebacks_json.append(traceback_json)
    else:
        simulations_variables_json = None
        tracebacks_json = None

    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(dict(
            apiVersion = '1.0',
            context = data['context'],
            method = req.script_name,
            params = inputs,
            suggestions = suggestions,
            tracebacks = tracebacks_json,
            url = req.url.decode('utf-8'),
            value = response_json,
            variables = simulations_variables_json,
            ).iteritems())),
        headers = headers,
        )


@wsgihelpers.wsgify
def api1_submit_legislation(req):
    """Submit, validate and optionally convert a JSON legislation."""
    ctx = contexts.Ctx(req)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx)

    assert req.method == 'POST', req.method

    content_type = req.content_type
    if content_type is not None:
        content_type = content_type.split(';', 1)[0].strip()
    if content_type != 'application/json':
        return wsgihelpers.respond_json(ctx,
            collections.OrderedDict(sorted(dict(
                apiVersion = '1.0',
                error = collections.OrderedDict(sorted(dict(
                    code = 400,  # Bad Request
                    message = ctx._(u'Bad content-type: {}').format(content_type),
                    ).iteritems())),
                method = req.script_name,
                url = req.url.decode('utf-8'),
                ).iteritems())),
            headers = headers,
            )

    inputs, error = conv.pipe(
        conv.make_input_to_json(object_pairs_hook = collections.OrderedDict),
        conv.test_isinstance(dict),
        conv.not_none,
        )(req.body, state = ctx)
    if error is not None:
        return wsgihelpers.respond_json(ctx,
            collections.OrderedDict(sorted(dict(
                apiVersion = '1.0',
                error = collections.OrderedDict(sorted(dict(
                    code = 400,  # Bad Request
                    errors = [conv.jsonify_value(error)],
                    message = ctx._(u'Invalid JSON in request POST body'),
                    ).iteritems())),
                method = req.script_name,
                params = req.body,
                url = req.url.decode('utf-8'),
                ).iteritems())),
            headers = headers,
            )

    data, errors = conv.struct(
        dict(
            # api_key = conv.pipe(  # Shared secret between client and server
            #     conv.test_isinstance(basestring),
            #     conv.input_to_uuid_str,
            #     conv.not_none,
            #     ),
            context = conv.test_isinstance(basestring),  # For asynchronous calls
            date = conv.pipe(
                conv.test_isinstance(basestring),
                conv.iso8601_input_to_date,
                ),
            legislation = conv.pipe(
                legislations.validate_any_legislation_json,
                conv.not_none,
                ),
            ),
        )(inputs, state = ctx)
    if errors is not None:
        return wsgihelpers.respond_json(ctx,
            collections.OrderedDict(sorted(dict(
                apiVersion = '1.0',
                context = inputs.get('context'),
                error = collections.OrderedDict(sorted(dict(
                    code = 400,  # Bad Request
                    errors = [conv.jsonify_value(errors)],
                    message = ctx._(u'Bad parameters in request'),
                    ).iteritems())),
                method = req.script_name,
                params = inputs,
                url = req.url.decode('utf-8'),
                ).iteritems())),
            headers = headers,
            )

#    api_key = data['api_key']
#    account = model.Account.find_one(
#        dict(
#            api_key = api_key,
#            ),
#        as_class = collections.OrderedDict,
#        )
#    if account is None:
#        return wsgihelpers.respond_json(ctx,
#            collections.OrderedDict(sorted(dict(
#                apiVersion = '1.0',
#                context = data['context'],
#                error = collections.OrderedDict(sorted(dict(
#                    code = 401,  # Unauthorized
#                    message = ctx._('Unknown API Key: {}').format(api_key),
#                    ).iteritems())),
#                method = req.script_name,
#                params = inputs,
#                url = req.url.decode('utf-8'),
#                ).iteritems())),
#            headers = headers,
#            )

    legislation_json = data['legislation']
    if legislation_json.get('datesim') is None:
        datesim = data['date']
        if datesim is None:
            dated_legislation_json = None
        else:
            dated_legislation_json = legislations.generate_dated_legislation_json(legislation_json, datesim)
    else:
        dated_legislation_json = legislation_json
        legislation_json = None

    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(dict(
            apiVersion = '1.0',
            context = data['context'],
            dated_legislation = dated_legislation_json,
            method = req.script_name,
            params = inputs,
            url = req.url.decode('utf-8'),
            legislation = legislation_json,
            ).iteritems())),
        headers = headers,
        )


def make_router():
    """Return a WSGI application that searches requests to controllers """
    global router
    router = urls.make_router(
        ('POST', '^/api/1/calculate/?$', api1_calculate),
        ('GET', '^/api/1/default-legislation/?$', api1_default_legislation),
        ('GET', '^/api/1/entities/?$', api1_entities),
        ('GET', '^/api/1/field/?$', api1_field),
        ('GET', '^/api/1/fields/?$', api1_fields),
        ('GET', '^/api/1/formula/(?P<name>[^/]+)/?$', api1_formula),
        ('GET', '^/api/1/graph/?$', api1_graph),
        ('POST', '^/api/1/legislations/?$', api1_submit_legislation),
        ('GET', '^/api/1/reforms/?$', api1_reforms),
        ('POST', '^/api/1/simulate/?$', api1_simulate),
        )
    return router
