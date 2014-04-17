# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014 OpenFisca Team
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


"""Root controllers"""


import collections
import copy
import datetime
import os
import xml.etree

#from openfisca_core import datatables, legislations, legislationsxml
from openfisca_core import decompositions, decompositionsxml, legislations, simulations

from . import conf, contexts, conv, urls, wsgihelpers


N_ = lambda message: message
router = None


@wsgihelpers.wsgify
def api1_default_legislation(req):
    """Return default legislation in JSON format."""
    ctx = contexts.Ctx(req)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx)

    assert req.method == 'GET', req.method

    tax_benefit_system = ctx.TaxBenefitSystem()
    return wsgihelpers.respond_json(ctx, tax_benefit_system.legislation_json, headers = headers)


@wsgihelpers.wsgify
def api1_field(req):
    ctx = contexts.Ctx(req)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx)

    assert req.method == 'GET', req.method

    params = req.GET
    inputs = dict(
        context = params.get('context'),
        variable = params.get('variable'),
        )
    tax_benefit_system = ctx.TaxBenefitSystem()
    data, errors = conv.pipe(
        conv.struct(
            dict(
                context = conv.noop,  # For asynchronous calls
                variable = conv.pipe(
                    conv.cleanup_line,
                    conv.default(u'revdisp'),
                    conv.test_in(tax_benefit_system.column_by_name),
                    ),
                ),
            default = 'drop',
            ),
        )(inputs, state = ctx)
    if errors is not None:
        return wsgihelpers.respond_json(ctx,
            collections.OrderedDict(sorted(dict(
                apiVersion = '1.0',
                context = inputs.get('context'),
                error = collections.OrderedDict(sorted(dict(
                    code = 400,  # Bad Request
                    errors = [errors],
                    message = ctx._(u'Bad parameters in request'),
                    ).iteritems())),
                method = req.script_name,
                params = inputs,
                url = req.url.decode('utf-8'),
                ).iteritems())),
            headers = headers,
            )

    simulation = simulations.Simulation(
        date = datetime.date(datetime.date.today().year, 1, 1),
        tax_benefit_system = tax_benefit_system,
        )
    holder = simulation.get_or_new_holder(data['variable'])

    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(dict(
            apiVersion = '1.0',
            context = data['context'],
            method = req.script_name,
            params = inputs,
            url = req.url.decode('utf-8'),
            value = holder.to_json(with_array = False),
            ).iteritems())),
        headers = headers,
        )


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
                apiVersion = '1.0',
                context = inputs.get('context'),
                error = collections.OrderedDict(sorted(dict(
                    code = 400,  # Bad Request
                    errors = [errors],
                    message = ctx._(u'Bad parameters in request'),
                    ).iteritems())),
                method = req.script_name,
                params = inputs,
                url = req.url.decode('utf-8'),
                ).iteritems())),
            headers = headers,
            )

    columns = collections.OrderedDict(
        (name, column.to_json())
        for name, column in ctx.TaxBenefitSystem.column_by_name.iteritems()
        if name not in ('idfam', 'idfoy', 'idmen', 'noi', 'quifam', 'quifoy', 'quimen')
        if column.formula_constructor is None
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
        for entity, tree in ctx.TaxBenefitSystem.columns_name_tree_by_entity.iteritems()
        )

    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(dict(
            apiVersion = '1.0',
            columns = columns,
            columns_tree = columns_tree,
            context = data['context'],
            method = req.script_name,
            params = inputs,
            prestations = collections.OrderedDict(
                (name, column.to_json())
                for name, column in ctx.TaxBenefitSystem.prestation_by_name.iteritems()
                if column.formula_constructor is not None
                ),
            url = req.url.decode('utf-8'),
            ).iteritems())),
        headers = headers,
        )


@wsgihelpers.wsgify
def api1_graph(req):
    ctx = contexts.Ctx(req)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx)

    assert req.method == 'GET', req.method
    params = req.GET
    inputs = dict(
        context = params.get('context'),
        variable = params.get('variable'),
        )
    tax_benefit_system = ctx.TaxBenefitSystem()
    data, errors = conv.pipe(
        conv.struct(
            dict(
                context = conv.noop,  # For asynchronous calls
                variable = conv.pipe(
                    conv.cleanup_line,
                    conv.default(u'revdisp'),
                    conv.test_in(tax_benefit_system.column_by_name),
                    ),
                ),
            default = 'drop',
            ),
        )(inputs, state = ctx)
    if errors is not None:
        return wsgihelpers.respond_json(ctx,
            collections.OrderedDict(sorted(dict(
                apiVersion = '1.0',
                context = inputs.get('context'),
                error = collections.OrderedDict(sorted(dict(
                    code = 400,  # Bad Request
                    errors = [errors],
                    message = ctx._(u'Bad parameters in request'),
                    ).iteritems())),
                method = req.script_name,
                params = inputs,
                url = req.url.decode('utf-8'),
                ).iteritems())),
            headers = headers,
            )

    simulation = simulations.Simulation(
        date = datetime.date(datetime.date.today().year, 1, 1),
        tax_benefit_system = tax_benefit_system,
        )
    edges = []
    nodes = []
    visited = set()
    simulation.graph(data['variable'], edges, nodes, visited)

    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(dict(
            apiVersion = '1.0',
            context = data['context'],
            edges = edges,
            method = req.script_name,
            nodes = nodes,
            params = inputs,
            url = req.url.decode('utf-8'),
            ).iteritems())),
        headers = headers,
        )


@wsgihelpers.wsgify
def api1_simulate(req):
    ctx = contexts.Ctx(req)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx)

    assert req.method == 'POST', req.method

    try:
        load_average = os.getloadavg()
    except (AttributeError, OSError):
        # When load average is not available, always accept request.
        pass
    else:
        if load_average[0] > 0.75:
            return wsgihelpers.respond_json(ctx,
                collections.OrderedDict(sorted(dict(
                    apiVersion = '1.0',
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
                apiVersion = '1.0',
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
        conv.make_input_to_json(),
        conv.test_isinstance(dict),
        conv.not_none,
        )(req.body, state = ctx)
    if error is not None:
        return wsgihelpers.respond_json(ctx,
            collections.OrderedDict(sorted(dict(
                apiVersion = '1.0',
                error = collections.OrderedDict(sorted(dict(
                    code = 400,  # Bad Request
                    errors = [error],
                    message = ctx._(u'Invalid JSON in request POST body'),
                    ).iteritems())),
                method = req.script_name,
                params = req.body,
                url = req.url.decode('utf-8'),
                ).iteritems())),
            headers = headers,
            )

    data, errors = conv.struct(
        dict(
#            api_key = conv.pipe(  # Shared secret between client and server
#                conv.test_isinstance(basestring),
#                conv.input_to_uuid,
#                conv.not_none,
#                ),
            context = conv.test_isinstance(basestring),  # For asynchronous calls
            decomposition = conv.noop,  # Real conversion is done once tax-benefit system is known.
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
            tax_benefit_system = ctx.TaxBenefitSystem.json_to_instance,
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
        tax_benefit_system = data['tax_benefit_system']
        data, errors = conv.struct(
            dict(
                decomposition = conv.pipe(
                    conv.condition(
                        conv.test_isinstance(basestring),
                        conv.test(lambda filename: filename in os.listdir(tax_benefit_system.DECOMP_DIR)),
                        decompositions.make_validate_node_json(tax_benefit_system),
                        ),
                    conv.default(os.path.join(tax_benefit_system.DECOMP_DIR, tax_benefit_system.DEFAULT_DECOMP_FILE)),
                    ),
                scenarios = conv.uniform_sequence(
                    tax_benefit_system.Scenario.make_json_to_instance(cache_dir = conf['cache_dir'],
                        tax_benefit_system = tax_benefit_system),
                    ),
                ),
            default = conv.noop,
            )(data, state = ctx)
    if errors is not None:
        return wsgihelpers.respond_json(ctx,
            collections.OrderedDict(sorted(dict(
                apiVersion = '1.0',
                context = inputs.get('context'),
                error = collections.OrderedDict(sorted(dict(
                    code = 400,  # Bad Request
                    errors = [errors],
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
#                apiVersion = '1.0',
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

    suggestions = {}
    for scenario_index, scenario in enumerate(data['scenarios']):
        suggestion = scenario.suggest()
        if suggestion is not None:
            suggestions.setdefault('scenarios', {})[scenario_index] = suggestion
    if not suggestions:
        suggestions = None

    if data['validate']:
        # Only a validation is requested. Don't launch simulation
        return wsgihelpers.respond_json(ctx,
            collections.OrderedDict(sorted(dict(
                apiVersion = '1.0',
                context = inputs.get('context'),
                method = req.script_name,
                params = inputs,
                suggestions = suggestions,
                url = req.url.decode('utf-8'),
                ).iteritems())),
            headers = headers,
            )

    if isinstance(data['decomposition'], basestring):
        # TODO: Cache decomposition_json.
        decomposition_tree = xml.etree.ElementTree.parse(os.path.join(tax_benefit_system.DECOMP_DIR,
            data['decomposition']))
        decomposition_xml_json = conv.check(decompositionsxml.xml_decomposition_to_json)(decomposition_tree.getroot(),
            state = ctx)
        decomposition_xml_json = conv.check(decompositionsxml.make_validate_node_xml_json(tax_benefit_system))(
            decomposition_xml_json, state = ctx)
        decomposition_json = decompositionsxml.transform_node_xml_json_to_json(decomposition_xml_json)
    else:
        decomposition_json = data['decomposition']

    simulations = []
    for scenario in data['scenarios']:
        simulation = scenario.new_simulation(trace = data['trace'])
        for node in decompositions.iter_decomposition_nodes(decomposition_json):
            if not node.get('children'):
                simulation.calculate(node['code'])
        simulations.append(simulation)

    response_json = copy.deepcopy(decomposition_json)
    for node in decompositions.iter_decomposition_nodes(response_json, children_first = True):
        children = node.get('children')
        if children:
            node['values'] = map(lambda *l: sum(l), *(
                child['values']
                for child in children
                ))
        else:
            node['values'] = values = []
            for simulation in simulations:
                holder = simulation.get_holder(node['code'])
                values.extend(holder.new_test_case_array().tolist())
        column = tax_benefit_system.column_by_name.get(node['code'])
        if column is not None and column.url is not None:
            node['url'] = column.url

    if data['trace']:
        tracebacks = []
        for simulation in simulations:
            traceback_json = collections.OrderedDict()
            for step in simulation.traceback:
                holder = step['holder']
                column = holder.column
                traceback_json[column.name] = dict(
                    array = holder.array.tolist() if holder.array is not None else None,
                    default_arguments = step['default_arguments'],
                    entity = column.entity,
                    label = column.label,
                    )
            tracebacks.append(traceback_json)
    else:
        tracebacks = None

    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(dict(
            apiVersion = '1.0',
            context = data['context'],
            method = req.script_name,
            params = inputs,
            suggestions = suggestions,
            tracebacks = tracebacks,
            url = req.url.decode('utf-8'),
            value = response_json,
            ).iteritems())),
        headers = headers,
        )


@wsgihelpers.wsgify
def api1_submit_legislation(req):
    """Submit, validate and optionally convert a JSON legislation."""
    ctx = contexts.Ctx(req)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx)

    assert req.method == 'POST', req.method

    content_type = req.content_type
    if content_type is not None:
        content_type = content_type.split(';', 1)[0].strip()
    if content_type != 'application/json':
        return wsgihelpers.respond_json(ctx,
            collections.OrderedDict(sorted(dict(
                apiVersion = '1.0',
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
        conv.make_input_to_json(),
        conv.test_isinstance(dict),
        conv.not_none,
        )(req.body, state = ctx)
    if error is not None:
        return wsgihelpers.respond_json(ctx,
            collections.OrderedDict(sorted(dict(
                apiVersion = '1.0',
                error = collections.OrderedDict(sorted(dict(
                    code = 400,  # Bad Request
                    errors = [error],
                    message = ctx._(u'Invalid JSON in request POST body'),
                    ).iteritems())),
                method = req.script_name,
                params = req.body,
                url = req.url.decode('utf-8'),
                ).iteritems())),
            headers = headers,
            )

    data, errors = conv.struct(
        dict(
#            api_key = conv.pipe(  # Shared secret between client and server
#                conv.test_isinstance(basestring),
#                conv.input_to_uuid,
#                conv.not_none,
#                ),
            context = conv.test_isinstance(basestring),  # For asynchronous calls
            date = conv.pipe(
                conv.test_isinstance(basestring),
                conv.iso8601_input_to_date,
                ),
            legislation = conv.pipe(
                legislations.validate_any_legislation_json,
                conv.not_none,
                ),
            ),
        )(inputs, state = ctx)
    if errors is not None:
        return wsgihelpers.respond_json(ctx,
            collections.OrderedDict(sorted(dict(
                apiVersion = '1.0',
                context = inputs.get('context'),
                error = collections.OrderedDict(sorted(dict(
                    code = 400,  # Bad Request
                    errors = [errors],
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
#                apiVersion = '1.0',
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

    legislation_json = data['legislation']
    if legislation_json.get('datesim') is None:
        datesim = data['date']
        if datesim is None:
            dated_legislation_json = None
        else:
            dated_legislation_json = legislations.generate_dated_legislation_json(legislation_json, datesim)
    else:
        dated_legislation_json = legislation_json
        legislation_json = None

    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(dict(
            apiVersion = '1.0',
            context = data['context'],
            dated_legislation = dated_legislation_json,
            method = req.script_name,
            params = inputs,
            url = req.url.decode('utf-8'),
            legislation = legislation_json,
            ).iteritems())),
        headers = headers,
        )


def make_router():
    """Return a WSGI application that searches requests to controllers """
    global router
    router = urls.make_router(
        ('GET', '^/api/1/default-legislation/?$', api1_default_legislation),
        ('GET', '^/api/1/field/?$', api1_field),
        ('GET', '^/api/1/fields/?$', api1_fields),
        ('GET', '^/api/1/graph/?$', api1_graph),
        ('POST', '^/api/1/legislations/?$', api1_submit_legislation),
        ('POST', '^/api/1/simulate/?$', api1_simulate),
        )
    return router
