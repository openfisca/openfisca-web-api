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
import itertools
import os
import xml.etree

#from openfisca_core import datatables, legislations, legislationsxml
from openfisca_core import decompositions, decompositionsxml, legislations, legislationsxml, simulations

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

    columns = collections.OrderedDict([
        (u'prenom', {
            u"@type": u"String",
            u"entity": u"ind",
            u"label": u"Prénom",
            u"name": u"prenom",
            }),
        (u'birth', {
            u"@type": u"Integer",
            u"entity": u"ind",
            u"label": u"Année de naissance",
            u"min": 1870,
            u"max": 2099,  # To be able to simulate future.
            u"name": u"birth",
            }),
        ])
    columns.update(
        (name, column.to_json())
        for name, column in ctx.TaxBenefitSystem.column_by_name.iteritems()
        if name not in ('age', 'agem', 'idfam', 'idfoy', 'idmen', 'noi', 'quifam', 'quifoy', 'quimen')
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
    columns_tree['individus']['children'][0]['children'][0:0] = [
        'prenom',
        'birth',
        ]

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
    simulation.graph(data['variable'], edges, 0, nodes, visited)

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

    if data['validate']:
        # Only a validation is requested. Don't launch simulation
        return wsgihelpers.respond_json(ctx,
            collections.OrderedDict(sorted(dict(
                apiVersion = '1.0',
                context = inputs.get('context'),
                method = req.script_name,
                params = inputs,
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
        simulation = scenario.new_simulation()
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

    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(dict(
            apiVersion = '1.0',
            context = data['context'],
            method = req.script_name,
            params = inputs,
            url = req.url.decode('utf-8'),
            value = response_json,
            ).iteritems())),
        headers = headers,
        )


@wsgihelpers.wsgify
def api1_simulate_survey(req):
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
            difference = conv.pipe(
                conv.test_isinstance((bool, int)),
                conv.anything_to_bool,
                conv.default(False),
                ),
            num_table = conv.pipe(
                conv.test_isinstance(int),
                conv.test_in((1, 3)),
                conv.not_none,
                ),
            reform = conv.pipe(
                conv.test_isinstance((bool, int)),
                conv.anything_to_bool,
                conv.default(False),
                ),
            year = conv.pipe(
                conv.test_isinstance(int),
                conv.test_greater_or_equal(1900),  # TODO: Check that year is valid in params.
                conv.not_none,
                ),
            ),
        )(inputs, state = ctx)
    if errors is None:
        tax_benefit_system = data['tax_benefit_system']
        if data['reform'] and len(data['scenarios']) > 1:
            errors = dict(reform = ctx._(u'In reform mode, a single scenario must be provided'))
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

    datesim = datetime.date(data['year'], 1, 1)
    difference = data['difference']
    # The aefa prestation can be disabled by uncommenting the following line:
    disabled_prestations = None  # ['aefa']
    num_table = data['num_table']
    reform = data['reform']
    survey_filename = {
        1: 'survey.h5',
        3: 'survey3.h5',
        }[num_table]
    survey_file_path = os.path.join(TaxBenefitSystem.DATA_DIR, survey_filename)
    verbose = False

    compact_legislations = []
    compact_legislation = tax_benefit_system.get_compact_legislation(datesim)
    compact_legislations.append(compact_legislation)
    if reform:
        # TODO: Use variant legislation instead of the default one.
        dated_legislation_json = legislations.generate_dated_legislation_json(legislation_json, datesim)
        compact_legislation = legislations.compact_dated_node_json(dated_legislation_json)
        if tax_benefit_system.preprocess_legislation_parameters is not None:
            tax_benefit_system.preprocess_legislation_parameters(compact_legislation)
        compact_legislations.append(compact_legislation)

    for index, compact_legislation in enumerate(compact_legislations):
        datesim = compact_legislation.datesim
        input_table = datatables.DataTable(TaxBenefitSystem.column_by_name, datesim = datesim, num_table = num_table,
            print_missing = verbose)
        input_table.load_data_from_survey(survey_file_path, num_table = num_table, print_missing = verbose)

        previous_compact_legislation = compact_legislations[index - 1] if index > 0 else compact_legislation
        output_table = taxbenefitsystems.TaxBenefitSystem(TaxBenefitSystem.prestation_by_name, compact_legislation,
            previous_compact_legislation, datesim = datesim, num_table = num_table)
        output_table.set_inputs(input_table)
        output_table.disable(disabled_prestations)
        output_table.calculate_survey()

    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(dict(
            apiVersion = '1.0',
            context = data['context'],
            method = req.script_name,
            params = inputs,
            url = req.url.decode('utf-8'),
#            value = [
#                output_tree.to_json()
#                for output_tree in output_trees
#                ],
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
        ('GET', '^/api/1/fields/?$', api1_fields),
        ('GET', '^/api/1/graph/?$', api1_graph),
        ('POST', '^/api/1/legislations/?$', api1_submit_legislation),
        ('POST', '^/api/1/simulate/?$', api1_simulate),
        ('POST', '^/api/1/simulate-survey/?$', api1_simulate_survey),
        )
    return router
