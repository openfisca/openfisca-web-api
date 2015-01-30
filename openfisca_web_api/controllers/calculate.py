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

from openfisca_core import reforms

from .. import conf, contexts, conv, model, wsgihelpers


cpu_count = multiprocessing.cpu_count()
N_ = lambda message: message


def build_and_calculate_simulations(variables, scenarios, trace = False):
    simulations = []
    for scenario in scenarios:
        simulation = scenario.new_simulation(trace = trace)
        for variable in variables:
            simulation.calculate(variable)
        simulations.append(simulation)
    return simulations


def fill_test_cases_with_values(intermediate_variables, scenarios, simulations, tax_benefit_system, variables):
    output_test_cases = []
    for scenario, simulation in itertools.izip(scenarios, simulations):
        if intermediate_variables:
            holders = []
            for step in simulation.traceback.itervalues():
                holder = step['holder']
                if holder not in holders:
                    holders.append(holder)
        else:
            holders = [
                simulation.get_holder(variable)
                for variable in variables
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
    return output_test_cases


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

    str_to_reforms = conv.make_str_to_reforms()
    str_to_variables = conv.pipe(
        conv.test_isinstance(list),
        conv.uniform_sequence(
            conv.pipe(
                conv.test_isinstance(basestring),
                conv.empty_to_none,
                # Remaining of conversion is done once tax-benefit system is known.
                conv.not_none,
                ),
            constructor = set,
            ),
        conv.test(lambda variables: len(variables) >= 1, error = N_(u'At least one variable is required')),
        conv.not_none,
        )

    data, errors = conv.struct(
        dict(
            # api_key = conv.pipe(  # Shared secret between client and server
            #     conv.test_isinstance(basestring),
            #     conv.input_to_uuid_str,
            #     conv.not_none,
            #     ),
            base_reforms = str_to_reforms,
            base_variables = str_to_variables,
            context = conv.test_isinstance(basestring),  # For asynchronous calls
            intermediate_variables = conv.pipe(
                conv.test_isinstance((bool, int)),
                conv.anything_to_bool,
                conv.default(False),
                ),
            reforms = str_to_reforms,
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
            reform_variables = str_to_variables,
            ),
        )(inputs, state = ctx)

    if errors is None:
        country_tax_benefit_system = model.tax_benefit_system
        base_tax_benefit_system = reforms.compose_reforms(
            base_tax_benefit_system = country_tax_benefit_system,
            build_reform_list = [model.build_reform_function_by_key[reform_key] for reform_key in data['base_reforms']],
            ) if data['base_reforms'] is not None else country_tax_benefit_system
        if data['reforms'] is not None:
            reform_tax_benefit_system = reforms.compose_reforms(
                base_tax_benefit_system = base_tax_benefit_system,
                build_reform_list = [model.build_reform_function_by_key[reform_key] for reform_key in data['reforms']],
                )
        data, errors = conv.struct(
            dict(
                base_scenarios = conv.uniform_sequence(
                    base_tax_benefit_system.Scenario.make_json_to_cached_or_new_instance(
                        repair = data['validate'],
                        tax_benefit_system = base_tax_benefit_system,
                        )
                    ),
                base_variables = conv.uniform_sequence(
                    conv.test_in(base_tax_benefit_system.column_by_name),
                    ),
                reform_scenarios = conv.uniform_sequence(
                    reform_tax_benefit_system.Scenario.make_json_to_cached_or_new_instance(
                        repair = data['validate'],
                        tax_benefit_system = reform_tax_benefit_system,
                        )
                    ),
                reform_variables = conv.uniform_sequence(
                    conv.test_in(reform_tax_benefit_system.column_by_name),
                    ) if data['reforms'] is not None else conv.noop,
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

    scenarios = data['reform_scenarios'] if data['reforms'] is not None else data['base_scenarios']

    suggestions = {}
    for scenario_index, scenario in enumerate(scenarios):
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
                    for scenario in scenarios
                    ],
                suggestions = suggestions,
                url = req.url.decode('utf-8'),
                ).iteritems())),
            headers = headers,
            )

    base_simulations = build_and_calculate_simulations(
        scenarios = data['base_scenarios'],
        trace = data['intermediate_variables'] or data['trace'],
        variables = data['base_variables'],
        )
    if data['reforms'] is not None:
        reform_simulations = build_and_calculate_simulations(
            scenarios = data['reform_scenarios'],
            trace = data['intermediate_variables'] or data['trace'],
            variables = data['reform_variables'],
            )

    base_output_test_cases = fill_test_cases_with_values(
        intermediate_variables = data['intermediate_variables'],
        scenarios = data['base_scenarios'],
        simulations = base_simulations,
        tax_benefit_system = base_tax_benefit_system,
        variables = data['base_variables'],
        )
    if data['reforms'] is not None:
        reform_output_test_cases = fill_test_cases_with_values(
            intermediate_variables = data['intermediate_variables'],
            scenarios = data['reform_scenarios'],
            simulations = reform_simulations,
            tax_benefit_system = reform_tax_benefit_system,
            variables = data['reform_variables'],
            )

    if data['trace']:
        simulations_variables_json = []
        tracebacks_json = []
        simulations = reform_simulations if data['reforms'] is not None else base_simulations
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

    response_data = dict(
        apiVersion = 1,
        context = data['context'],
        method = req.script_name,
        params = inputs,
        suggestions = suggestions,
        tracebacks = tracebacks_json,
        url = req.url.decode('utf-8'),
        value = reform_output_test_cases if data['reforms'] is not None else base_output_test_cases,
        variables = simulations_variables_json,
        )
    if data['reforms'] is not None:
        response_data['baseValue'] = base_output_test_cases
    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(response_data.iteritems())),
        headers = headers,
        )
