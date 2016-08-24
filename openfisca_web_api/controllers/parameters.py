# -*- coding: utf-8 -*-


"""Parameters controller"""


import collections

from openfisca_core import legislations, periods

from .. import conf, contexts, conv, environment, model, wsgihelpers


@wsgihelpers.wsgify
def api1_parameters(req):
    ctx = contexts.Ctx(req)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx)

    assert req.method == 'GET', req.method
    params = req.GET
    inputs = dict(
        instant = params.get('instant'),
        names = params.getall('name'),
        )

    parameters_name = [
        parameter_json['name']
        for parameter_json in model.parameters_json_cache
        ]

    data, errors = conv.pipe(
        conv.struct(
            dict(
                instant = conv.pipe(
                    conv.empty_to_none,
                    conv.test_isinstance(basestring),
                    conv.function(lambda str: periods.instant(str)),
                    ),
                names = conv.pipe(
                    conv.uniform_sequence(
                        conv.pipe(
                            conv.empty_to_none,
                            conv.test_in(parameters_name, error = u'Parameter does not exist'),
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

    tax_benefit_system = model.tax_benefit_system

    if data['instant'] is None:
        if data['names'] is None:
            parameters_json = model.parameters_json_cache
        else:
            parameters_json = [
                parameter_json
                for parameter_json in model.parameters_json_cache
                if parameter_json['name'] in data['names']
                ]
    else:
        instant = data['instant']
        parameters_json = []
        dated_legislation_json = legislations.generate_dated_legislation_json(
            tax_benefit_system.get_legislation(),
            instant,
            )
        for name in data['names']:
            name_fragments = name.split('.')
            parameter_json = dated_legislation_json
            for name_fragment in name_fragments:
                parameter_json = parameter_json['children'][name_fragment]
            parameter_json['name'] = name
            parameter_json_in_cache = [
                parameter_json1
                for parameter_json1 in model.parameters_json_cache
                if parameter_json1['name'] == name
                ][0]
            parameter_json['description'] = parameter_json_in_cache['description']
            parameters_json.append(parameter_json)

    response_dict = dict(
        apiVersion = 1,
        country_package_name = conf['country_package'],
        country_package_version = environment.country_package_version,
        method = req.script_name,
        parameters = parameters_json,
        url = req.url.decode('utf-8'),
        )
    if hasattr(tax_benefit_system, 'CURRENCY'):
        response_dict['currency'] = tax_benefit_system.CURRENCY
    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(response_dict.iteritems())),
        headers = headers,
        )
