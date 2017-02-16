# -*- coding: utf-8 -*-


"""Graph controller"""


import collections
import datetime

from openfisca_core import periods, simulations

from .. import contexts, conv, model, wsgihelpers


@wsgihelpers.wsgify
def api1_graph(req):
    ctx = contexts.Ctx(req)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx)

    assert req.method == 'GET', req.method

    params = req.GET
    inputs = dict(
        context = params.get('context'),
        reforms = params.getall('reform'),
        variable = params.get('variable'),
        )

    if model.input_variables_extractor is None:
        return wsgihelpers.respond_json(ctx,
            collections.OrderedDict(sorted(dict(
                apiVersion = 1,
                context = inputs.get('context'),
                error = collections.OrderedDict(sorted(dict(
                    code = 501,
                    errors = [ctx._(u'openfisca_parsers is not installed on this instance of the API')],
                    message = ctx._(u'Not implemented'),
                    ).iteritems())),
                method = req.script_name,
                params = inputs,
                url = req.url.decode('utf-8'),
                ).iteritems())),
            headers = headers,
            )

    str_list_to_reforms = conv.make_str_list_to_reforms()

    data, errors = conv.pipe(
        conv.struct(
            dict(
                context = conv.noop,  # For asynchronous calls
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
                    conv.test_in(tax_benefit_system.column_by_name),
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

    simulation = simulations.Simulation(
        period = periods.period(datetime.date.today().year),
        tax_benefit_system = tax_benefit_system,
        )
    edges = []
    nodes = []
    visited = set()
    simulation.graph(
        column_name = data['variable'],
        edges = edges,
        get_input_variables_and_parameters = model.get_cached_input_variables_and_parameters,
        nodes = nodes,
        visited = visited,
        )

    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(dict(
            apiVersion = 1,
            context = data['context'],
            edges = edges,
            method = req.script_name,
            nodes = nodes,
            params = inputs,
            url = req.url.decode('utf-8'),
            ).iteritems())),
        headers = headers,
        )
