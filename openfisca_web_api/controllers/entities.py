# -*- coding: utf-8 -*-


"""Entities controller"""


import collections

from .. import contexts, conv, model, wsgihelpers


def build_entity_data(entity_class):
    entity_data = {'label': entity_class.label}
    if entity_class.is_persons_entity:
        entity_data['isPersonsEntity'] = entity_class.is_persons_entity
    else:
        entity_data.update({
            'maxCardinalityByRoleKey': entity_class.max_cardinality_by_role_key,
            'roles': entity_class.roles_key,
            'labelByRoleKey': entity_class.label_by_role_key,
            })
    return entity_data


@wsgihelpers.wsgify
def api1_entities(req):
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

    entities_class = tax_benefit_system.entity_class_by_key_plural.itervalues()
    entities = {
        entity_class.key_plural: build_entity_data(entity_class)
        for entity_class in entities_class
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
