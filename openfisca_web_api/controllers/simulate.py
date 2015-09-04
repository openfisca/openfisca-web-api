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


"""Simulate controller"""


from __future__ import division

import collections
import copy
import multiprocessing
import os

from openfisca_core import decompositions

from .. import conf, contexts, conv, model, wsgihelpers


cpu_count = multiprocessing.cpu_count()


def N_(message):
    return message


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

    data, errors = conv.struct(
        dict(
            # api_key = conv.pipe(  # Shared secret between client and server
            #     conv.test_isinstance(basestring),
            #     conv.input_to_uuid_str,
            #     conv.not_none,
            #     ),
            base_reforms = str_to_reforms,
            context = conv.test_isinstance(basestring),  # For asynchronous calls
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
            ),
        )(inputs, state = ctx)

    if errors is None:
        country_tax_benefit_system = model.tax_benefit_system
        base_tax_benefit_system = model.get_cached_composed_reform(
            reform_keys = data['base_reforms'],
            tax_benefit_system = country_tax_benefit_system,
            ) if data['base_reforms'] is not None else country_tax_benefit_system
        if data['reforms'] is not None:
            reform_tax_benefit_system = model.get_cached_composed_reform(
                reform_keys = data['reforms'],
                tax_benefit_system = base_tax_benefit_system,
                )

        base_scenarios, base_scenarios_errors = conv.uniform_sequence(
            base_tax_benefit_system.Scenario.make_json_to_cached_or_new_instance(
                ctx = ctx,
                repair = data['validate'],
                tax_benefit_system = base_tax_benefit_system,
                )
            )(data['scenarios'], state = ctx)
        errors = {'scenarios': base_scenarios_errors} if base_scenarios_errors is not None else None

        if errors is None and data['reforms'] is not None:
            reform_scenarios, reform_scenarios_errors = conv.uniform_sequence(
                reform_tax_benefit_system.Scenario.make_json_to_cached_or_new_instance(
                    ctx = ctx,
                    repair = data['validate'],
                    tax_benefit_system = reform_tax_benefit_system,
                    )
                )(data['scenarios'], state = ctx)
            errors = {'scenarios': reform_scenarios_errors} if reform_scenarios_errors is not None else None

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

    scenarios = base_scenarios if data['reforms'] is None else reform_scenarios

    suggestions = {}
    for scenario_index, scenario in enumerate(scenarios):
        if data['validate']:
            original_test_case = scenario.test_case
            scenario.test_case = copy.deepcopy(original_test_case)
        suggestion = scenario.suggest()  # This modifies scenario.test_case!
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

    decomposition_json = model.get_cached_or_new_decomposition_json(tax_benefit_system = base_tax_benefit_system)
    base_simulations = [scenario.new_simulation(trace = data['trace']) for scenario in base_scenarios]
    base_response_json = decompositions.calculate(base_simulations, decomposition_json)

    if data['reforms'] is not None:
        reform_decomposition_json = model.get_cached_or_new_decomposition_json(
            tax_benefit_system = reform_tax_benefit_system,
            )
        reform_simulations = [scenario.new_simulation(trace = data['trace']) for scenario in reform_scenarios]
        reform_response_json = decompositions.calculate(reform_simulations, reform_decomposition_json)

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
                input_variables_infos = step.get('input_variables_infos')
                column = holder.column
                traceback_json.append(dict(
                    cell_type = column.val_type,  # Unification with OpenFisca Julia name.
                    default_input_variables = step.get('default_input_variables', False),
                    entity = column.entity,
                    input_variables = [
                        (variable_name, str(variable_period))
                        for variable_name, variable_period in input_variables_infos
                        ] if input_variables_infos else None,
                    is_computed = step.get('is_computed', False),
                    label = column.label if column.label != variable_name else None,
                    name = variable_name,
                    period = str(period) if period is not None else None,
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
        value = reform_response_json if data['reforms'] is not None else base_response_json,
        variables = simulations_variables_json,
        )
    if data['reforms'] is not None:
        response_data['base_value'] = base_response_json
    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(response_data.iteritems())),
        headers = headers,
        )
