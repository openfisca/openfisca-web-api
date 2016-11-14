# -*- coding: utf-8 -*-


"""Fields controller"""


import collections
import copy

from .. import contexts, conv, model, wsgihelpers


def get_column_json(column):
    column_json = column.to_json()
    column_json['entity'] = column.entity.key  # Overwrite with symbol instead of key plural for compatibility.
    return column_json


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

    columns = collections.OrderedDict(
        (name, get_column_json(column))
        for name, column in model.tax_benefit_system.column_by_name.iteritems()
        if name not in ('idfam', 'idfoy', 'idmen', 'noi', 'quifam', 'quifoy', 'quimen')
        if column.is_input_variable()
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
    prestations = collections.OrderedDict(
        (name, get_column_json(column))
        for name, column in model.tax_benefit_system.column_by_name.iteritems()
        if not column.is_input_variable()
        )

    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(dict(
            apiStatus = u'deprecated',
            apiVersion = 1,
            columns = columns,
            columns_tree = columns_tree,
            context = data['context'],
            method = req.script_name,
            params = inputs,
            prestations = prestations,
            url = req.url.decode('utf-8'),
            ).iteritems())),
        headers = headers,
        )
