# -*- coding: utf-8 -*-


"""Calculate controller"""


from __future__ import division

import collections
import copy
import itertools
import os
import time

from openfisca_core.legislations import ParameterNotFound
from openfisca_core.taxbenefitsystems import VariableNotFound

from .. import conf, contexts, conv, environment, model, wsgihelpers


def N_(message):
    return message


def build_output_variables(simulations, use_label, variables):
    return [
        {
            variable: simulation.get_holder(variable).to_value_json(use_label = use_label)
            for variable in variables
            }
        for simulation in simulations
        ]


def fill_test_cases_with_values(intermediate_variables, scenarios, simulations, use_label, variables):
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
            variable_value_json = holder.to_value_json(use_label = use_label)
            if variable_value_json is None:
                continue
            variable_name = holder.column.name
            entity_members = test_case[holder.entity.plural]
            if isinstance(variable_value_json, dict):
                for entity_member_index, entity_member in enumerate(entity_members):
                    entity_member[variable_name] = {}
                    for period, array_or_dict_json in variable_value_json.iteritems():
                            if type(array_or_dict_json) == dict:
                                if len(array_or_dict_json) == 1:
                                    entity_member[variable_name][period] = \
                                        array_or_dict_json[array_or_dict_json.keys()[0]][entity_member_index]
                                else:
                                    entity_member[variable_name][period] = {}
                                    for key, array in array_or_dict_json.iteritems():
                                        entity_member[variable_name][period][key] = array[entity_member_index]
                            else:
                                entity_member[variable_name][period] = array_or_dict_json[entity_member_index]
            else:
                for entity_member, cell_json in itertools.izip(entity_members, variable_value_json):
                    entity_member[variable_name] = cell_json
        output_test_cases.append(test_case)
    return output_test_cases


@wsgihelpers.wsgify
def api1_calculate(req):
    def calculate_simulations(scenarios, variables, trace):
        simulations = []
        for scenario_index, scenario in enumerate(scenarios):
            simulation = scenario.new_simulation(trace = trace)
            for variable_name in variables:
                try:
                    simulation.calculate_output(variable_name, simulation.period)
                except ParameterNotFound as exc:
                    raise wsgihelpers.respond_json(ctx,
                        collections.OrderedDict(sorted(dict(
                            apiVersion = 1,
                            context = inputs.get('context'),
                            error = collections.OrderedDict(sorted(dict(
                                code = 500,
                                errors = [{"scenarios": {scenario_index: exc.to_json()}}],
                                ).iteritems())),
                            method = req.script_name,
                            params = inputs,
                            url = req.url.decode('utf-8'),
                            ).iteritems())),
                        headers = headers,
                        )
                except VariableNotFound as exc:
                    wsgihelpers.handle_error(exc, ctx, headers)
            simulations.append(simulation)
        return simulations

    total_start_time = time.time()

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
            if load_average[0] / environment.cpu_count > 1:
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

    str_list_to_reforms = conv.make_str_list_to_reforms()

    data, errors = conv.struct(
        dict(
            base_reforms = str_list_to_reforms,
            context = conv.test_isinstance(basestring),  # For asynchronous calls
            intermediate_variables = conv.pipe(
                conv.test_isinstance((bool, int)),
                conv.anything_to_bool,
                conv.default(False),
                ),
            labels = conv.pipe(  # Return labels (of enumerations) instead of numeric values.
                conv.test_isinstance((bool, int)),
                conv.anything_to_bool,
                conv.default(False),
                ),
            output_format = conv.pipe(
                conv.test_isinstance(basestring),
                conv.test_in(['test_case', 'variables']),
                conv.default('test_case'),
                ),
            reforms = str_list_to_reforms,
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
            time = conv.pipe(
                conv.test_isinstance((bool, int)),
                conv.anything_to_bool,
                conv.default(False),
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
                        conv.empty_to_none,
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
        compose_reforms_start_time = time.time()

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

        compose_reforms_end_time = time.time()
        compose_reforms_time = compose_reforms_end_time - compose_reforms_start_time

        build_scenarios_start_time = time.time()

        try:
            base_scenarios, base_scenarios_errors = conv.uniform_sequence(
                base_tax_benefit_system.Scenario.make_json_to_cached_or_new_instance(
                    ctx = ctx,
                    repair = data['validate'],
                    tax_benefit_system = base_tax_benefit_system,
                    )
                )(data['scenarios'], state = ctx)
        except (ValueError, VariableNotFound) as exc:
            wsgihelpers.handle_error(exc, ctx, headers)
        errors = {'scenarios': base_scenarios_errors} if base_scenarios_errors is not None else None

        if errors is None and data['reforms'] is not None:
            try:
                reform_scenarios, reform_scenarios_errors = conv.uniform_sequence(
                    reform_tax_benefit_system.Scenario.make_json_to_cached_or_new_instance(
                        ctx = ctx,
                        repair = data['validate'],
                        tax_benefit_system = reform_tax_benefit_system,
                        )
                    )(data['scenarios'], state = ctx)
            except (ValueError, VariableNotFound) as exc:
                wsgihelpers.handle_error(exc, ctx, headers)
            errors = {'scenarios': reform_scenarios_errors} if reform_scenarios_errors is not None else None

        build_scenarios_end_time = time.time()
        build_scenarios_time = build_scenarios_end_time - build_scenarios_start_time

        if errors is None:
            data, errors = conv.struct(
                dict(
                    variables = conv.uniform_sequence(
                        conv.make_validate_variable(
                            base_tax_benefit_system = base_tax_benefit_system,
                            reform_tax_benefit_system = reform_tax_benefit_system if data['reforms'] else None,
                            reforms = data['reforms'],
                            ),
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
        total_end_time = time.time()
        total_time = total_end_time - total_start_time
        response_data = dict(
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
            )
        if data['time']:
            response_data['time'] = collections.OrderedDict(sorted(dict(
                build_scenarios = build_scenarios_time,
                compose_reforms = compose_reforms_time,
                total = total_time,
                ).iteritems())),
        return wsgihelpers.respond_json(ctx,
            collections.OrderedDict(sorted(response_data.iteritems())),
            headers = headers,
            )

    calculate_simulation_start_time = time.time()

    trace_simulations = data['trace'] or data['intermediate_variables']

    try:
        base_simulations = calculate_simulations(scenarios, data['variables'], trace = trace_simulations)
        if data['reforms'] is not None:
            reform_simulations = calculate_simulations(reform_scenarios, data['variables'], trace = trace_simulations)
    except ValueError as exc:
        wsgihelpers.handle_error(exc, ctx, headers)

    calculate_simulation_end_time = time.time()
    calculate_simulation_time = calculate_simulation_end_time - calculate_simulation_start_time

    if data['output_format'] == 'test_case':
        base_value = fill_test_cases_with_values(
            intermediate_variables = data['intermediate_variables'],
            scenarios = base_scenarios,
            simulations = base_simulations,
            use_label = data['labels'],
            variables = data['variables'],
            )
        if data['reforms'] is not None:
            reform_value = fill_test_cases_with_values(
                intermediate_variables = data['intermediate_variables'],
                scenarios = reform_scenarios,
                simulations = reform_simulations,
                use_label = data['labels'],
                variables = data['variables'],
                )
    else:
        assert data['output_format'] == 'variables'
        base_value = build_output_variables(
            simulations = base_simulations,
            use_label = data['labels'],
            variables = data['variables'],
            )
        if data['reforms'] is not None:
            reform_value = build_output_variables(
                simulations = reform_simulations,
                use_label = data['labels'],
                variables = data['variables'],
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
                parameters_infos = step.get('parameters_infos')
                traceback_json.append(collections.OrderedDict(sorted(dict(
                    cell_type = column.val_type,  # Unification with OpenFisca Julia name.
                    default_input_variables = step.get('default_input_variables', False),
                    entity = column.entity.key,
                    input_variables = [
                        (input_variable_name, str(input_variable_period))
                        for input_variable_name, input_variable_period in input_variables_infos
                        ] if input_variables_infos else None,
                    is_computed = step.get('is_computed', False),
                    label = column.label if column.label != variable_name else None,
                    name = variable_name,
                    parameters = parameters_infos or None,
                    period = str(period) if period is not None else None,
                    ).iteritems())))
            simulations_variables_json.append(simulation_variables_json)
            tracebacks_json.append(traceback_json)
    else:
        simulations_variables_json = None
        tracebacks_json = None

    response_data = collections.OrderedDict(sorted(dict(
        apiVersion = 1,
        context = data['context'],
        method = req.script_name,
        params = inputs,
        suggestions = suggestions,
        tracebacks = tracebacks_json,
        url = req.url.decode('utf-8'),
        value = reform_value if data['reforms'] is not None else base_value,
        variables = simulations_variables_json,
        ).iteritems()))
    if data['reforms'] is not None:
        response_data['base_value'] = base_value

    total_end_time = time.time()
    total_time = total_end_time - total_start_time

    if data['time']:
        response_data['time'] = collections.OrderedDict(sorted(dict(
            build_scenarios = build_scenarios_time,
            compose_reforms = compose_reforms_time,
            calculate_simulation = calculate_simulation_time,
            total = total_time,
            ).iteritems()))

    return wsgihelpers.respond_json(ctx, response_data, headers = headers)
