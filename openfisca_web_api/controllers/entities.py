# -*- coding: utf-8 -*-


"""Entities controller"""


import collections

from .. import contexts, conv, model, wsgihelpers


@wsgihelpers.wsgify
def api2_entities(req):
    ctx = contexts.Ctx(req)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx)

    assert req.method == 'GET', req.method

    params = req.GET
    inputs = dict(
        context = params.get('context'),
        reforms = params.getall('reform'),
        )

    str_list_to_reforms = conv.make_str_list_to_reforms()

    data, errors = conv.pipe(
        conv.struct(
            dict(
                context = conv.noop,  # For asynchronous calls
                reforms = str_list_to_reforms,
                ),
            default = 'drop',
            ),
        )(inputs, state = ctx)

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

    country_tax_benefit_system = model.tax_benefit_system
    tax_benefit_system = model.get_cached_composed_reform(
        reform_keys = data['reforms'],
        tax_benefit_system = country_tax_benefit_system,
        ) if data['reforms'] is not None else country_tax_benefit_system

    entities = {
        entity.key: entity.to_json()
        for entity in tax_benefit_system.entities
        }

    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(dict(
            apiVersion = 1,
            context = data['context'],
            entities = collections.OrderedDict(sorted(entities.iteritems())),
            method = req.script_name,
            params = inputs,
            ).iteritems())),
        headers = headers,
        )
