# -*- coding: utf-8 -*-


"""Variables controller"""


import collections
import datetime

from openfisca_core import periods, simulations, columns

from .. import conf, contexts, conv, environment, model, wsgihelpers


@wsgihelpers.wsgify
def api1_variables(req):
    wsgihelpers.track(req.url.decode('utf-8'))
    ctx = contexts.Ctx(req)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx)

    assert req.method == 'GET', req.method
    params = req.GET
    inputs = dict(
        names = params.getall('name'),
        )

    tax_benefit_system = model.tax_benefit_system
    tax_benefit_system_variables_name = tax_benefit_system.variables.keys()

    data, errors = conv.pipe(
        conv.struct(
            dict(
                names = conv.pipe(
                    conv.uniform_sequence(
                        conv.pipe(
                            conv.empty_to_none,
                            conv.test_in(tax_benefit_system_variables_name, error = u'Variable does not exist'),
                            ),
                        drop_none_items = True,
                        ),
                    conv.empty_to_none,
                    ),
                ),
            default = 'drop',
            ),
        )(inputs, state = ctx)

    if errors is not None:
        return wsgihelpers.respond_json(ctx,
            collections.OrderedDict(sorted(dict(
                apiVersion = 1,
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

    simulation = None
    variables_json = []
    for variable_name in data['names'] or tax_benefit_system_variables_name:
        variable = tax_benefit_system.variables[variable_name]
        column = columns.make_column_from_variable(variable)
        variable_json = column.to_json()
        # This part checks that no enum tries to go through the API
        if 'cerfa_field' in variable_json.keys():
            cerfa = variable_json['cerfa_field']
            for key in cerfa:
                from enum import Enum
                if isinstance(key, Enum):
                    cerfa[key.name] = cerfa[key]
                    del cerfa[key]
        if variable_json.get('source_file_path'):
            variable_json['source_file_path'] = environment.get_relative_file_path(variable_json['source_file_path'])
        label = variable_json.get('label')
        if label is not None and label == variable_name:
            del variable_json['label']
        if not column.is_input_variable():
            if simulation is None:
                simulation = simulations.Simulation(
                    period = periods.period(datetime.date.today().year),
                    tax_benefit_system = model.tax_benefit_system,
                    )
        variables_json.append(variable_json)

    response_dict = dict(
        apiVersion = 1,
        country_package_name = conf['country_package'],
        country_package_version= environment.country_package_version,
        method = req.script_name,
        url = req.url.decode('utf-8'),
        variables = variables_json,
        )
    if hasattr(tax_benefit_system, 'CURRENCY'):
        response_dict['currency'] = tax_benefit_system.CURRENCY

    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(response_dict.iteritems())),
        headers = headers,
        )
