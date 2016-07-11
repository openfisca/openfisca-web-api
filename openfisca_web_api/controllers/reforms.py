# -*- coding: utf-8 -*-


"""Reforms controller"""


import collections

from .. import contexts, conv, model, wsgihelpers


@wsgihelpers.wsgify
def api1_reforms(req):
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

    declared_reforms_key = model.reforms.keys()

    reforms = collections.OrderedDict(sorted({
        reform_key: reform.name
        for reform_key, reform in model.reformed_tbs.iteritems()
        }.iteritems())) if declared_reforms_key is not None else None

    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(dict(
            apiVersion = 1,
            context = data['context'],
            method = req.script_name,
            params = inputs,
            reforms = reforms,
            url = req.url.decode('utf-8'),
            ).iteritems())),
        headers = headers,
        )
