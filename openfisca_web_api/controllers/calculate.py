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


"""Calculate controller"""


from __future__ import division

import collections
import copy
import itertools
import multiprocessing
import os

from .. import conf, contexts, conv, model, wsgihelpers


cpu_count = multiprocessing.cpu_count()
N_ = lambda message: message


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
                        apiVersion = 1,
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
                apiVersion = 1,
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
                apiVersion = 1,
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
        tax_benefit_system = model.tax_benefit_system
        data, errors = conv.struct(
            dict(
                reform_names = conv.pipe(
                    conv.test_isinstance(list),
                    conv.uniform_sequence(
                        conv.pipe(
                            conv.test_isinstance(basestring),
                            conv.cleanup_line,
                            conv.test_in((conf['reforms'] or {}).keys()),
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
            # reference_tax_benefit_system = tax_benefit_system.real_reference
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
                apiVersion = 1,
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
#                apiVersion = 1,
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
                apiVersion = 1,
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
            apiVersion = 1,
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
