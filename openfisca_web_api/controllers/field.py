# -*- coding: utf-8 -*-


"""Field controller"""


import collections

from openfisca_core import columns

from .. import contexts, conv, model, wsgihelpers


@wsgihelpers.wsgify
def api1_field(req):
    wsgihelpers.track(req.url.decode('utf-8'))
    ctx = contexts.Ctx(req)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx)

    assert req.method == 'GET', req.method
    params = req.GET
    inputs = dict(
        context = params.get('context'),
        input_variables = params.get('input_variables'),
        reforms = params.getall('reform'),
        variable = params.get('variable'),
        )

    str_list_to_reforms = conv.make_str_list_to_reforms()

    data, errors = conv.pipe(
        conv.struct(
            dict(
                context = conv.noop,  # For asynchronous calls
                input_variables = conv.pipe(
                    conv.test_isinstance((bool, int, basestring)),
                    conv.anything_to_bool,
                    conv.default(True),
                    ),
                reforms = str_list_to_reforms,
                variable = conv.noop,  # Real conversion is done once tax-benefit system is known.
                ),
            default = 'drop',
            ),
        )(inputs, state = ctx)

    if errors is None:
        country_tax_benefit_system = model.tax_benefit_system
        tax_benefit_system = model.get_cached_composed_reform(
            reform_keys = data['reforms'],
            tax_benefit_system = country_tax_benefit_system,
            ) if data['reforms'] is not None else country_tax_benefit_system
        data, errors = conv.struct(
            dict(
                variable = conv.pipe(
                    conv.empty_to_none,
                    conv.default(u'revenu_disponible'),
                    conv.test_in(tax_benefit_system.variables),
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

    variable_name = data['variable']
    variable = tax_benefit_system.get_variable(variable_name)
    value_json = columns.make_column_from_variable(variable).to_json()
    value_json['entity'] = variable.entity.key  # Overwrite with symbol instead of key plural for compatibility.

    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(dict(
            apiStatus = u'deprecated',
            apiVersion = 1,
            context = data['context'],
            method = req.script_name,
            params = inputs,
            url = req.url.decode('utf-8'),
            value = value_json,
            ).iteritems())),
        headers = headers,
        )
