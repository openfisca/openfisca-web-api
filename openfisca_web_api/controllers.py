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
import datetime
import os
from xml.etree import ElementTree

from openfisca_core import datatables, legislations, legislationsxml, model, taxbenefitsystems

from . import contexts, conv, urls, wsgihelpers


N_ = lambda message: message
router = None


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

    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(dict(
            apiVersion = '1.0',
            columns_tree = model.columns_name_tree_by_entity,
            columns = collections.OrderedDict(
                (name, column.to_json())
                for name, column in model.column_by_name.iteritems()
                if name not in ('age', 'agem', 'idfam', 'idfoy', 'idmen', 'noi', 'quifam', 'quifoy', 'quimen')
                ),
            context = data['context'],
            method = req.script_name,
            params = inputs,
            prestations = collections.OrderedDict(
                (name, column.to_json())
                for name, column in model.prestation_by_name.iteritems()
                ),
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
            difference = conv.pipe(
                conv.test_isinstance((bool, int)),
                conv.anything_to_bool,
                conv.default(False),
                ),
            maxrev = conv.pipe(
                conv.test_isinstance((float, int)),
                conv.anything_to_float,
                ),
            nmen = conv.pipe(
                conv.test_isinstance(int),
                conv.test_greater_or_equal(1),
                conv.default(1),
                ),
            reform = conv.pipe(
                conv.test_isinstance((bool, int)),
                conv.anything_to_bool,
                conv.default(False),
                ),
            scenarios = conv.pipe(
                conv.test_isinstance(list),
                conv.uniform_sequence(
                    conv.pipe(
                        model.Scenario.json_to_attributes,
                        conv.not_none,
                        ),
                    ),
                conv.test(lambda scenarios: len(scenarios) >= 1, error = N_(u'At least one scenario is required')),
                conv.test(lambda scenarios: len(scenarios) <= 2, error = N_(u'There can be no more than 2 scenarios')),
                conv.not_none,
                ),
            validate = conv.pipe(
                conv.test_isinstance((bool, int)),
                conv.anything_to_bool,
                conv.default(False),
                ),
            x_axis = conv.pipe(
                conv.test_isinstance(basestring),
                conv.test_in(model.x_axes.keys()),
                ),
            ),
        )(inputs, state = ctx)
    if errors is None:
        data, errors = conv.struct(
            dict(
                maxrev = conv.not_none if data['nmen'] > 1 else conv.test_none(
                    error = u'No value allowed when "nmen" is 1'),
                reform = conv.test_equals(False, error = u'In reform mode, only a single scenario must be provided')
                    if len(data['scenarios']) > 1 else conv.noop,
                x_axis = conv.not_none if data['nmen'] > 1 else conv.test_none(
                    error = u'No value allowed when "nmen" is 1'),
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

    decomp_file = os.path.join(model.DECOMP_DIR, model.DEFAULT_DECOMP_FILE)
    difference = data['difference']
    # The aefa prestation can be disabled by uncommenting the following line:
    disabled_prestations = None  # ['aefa']
    maxrev = data['maxrev']
    nmen = data['nmen']
    num_table = 1
    reform = data['reform']
    verbose = False

    scenarios = []
    for scenario_data in data['scenarios']:
        datesim = datetime.date(scenario_data.pop('year'), 1, 1)

        scenario = model.Scenario()
        scenario.nmen = nmen
        if nmen > 1:
            scenario.maxrev = maxrev
            scenario.x_axis = data['x_axis']
        scenario.same_rev_couple = False
        scenario.year = datesim.year
        scenario.__dict__.update(scenario_data)
        scenarios.append(scenario)
    if reform:
        # Keep datesim from the latest scenario (assume there is only one).

        scenario = model.Scenario()
        scenario.nmen = nmen
        if nmen > 1:
            scenario.maxrev = maxrev
            scenario.x_axis = data['x_axis']
        scenario.same_rev_couple = False
        scenario.year = datesim.year
        scenario.__dict__.update(scenario_data)
        scenarios.append(scenario)

    output_trees = []
    for index, scenario in enumerate(scenarios):
        datesim = scenario.compact_legislation.datesim
        input_table = datatables.DataTable(model.column_by_name, datesim = datesim, num_table = num_table,
            print_missing = verbose)
        input_table.test_case = scenario
        scenario.populate_datatable(input_table)

        previous_compact_legislation = scenarios[index - 1].compact_legislation if index > 0 \
            else scenario.compact_legislation
        output_table = taxbenefitsystems.TaxBenefitSystem(model.prestation_by_name, scenario.compact_legislation,
            previous_compact_legislation, datesim = datesim, num_table = num_table)
        output_table.set_inputs(input_table)
        output_table.disable(disabled_prestations)
        output_table.decomp_file = decomp_file
        output_tree = output_table.calculate_test_case()

        if (difference or reform) and index > 0:
            output_tree.difference(output_trees[0])

        output_trees.append(output_tree)

    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(dict(
            apiVersion = '1.0',
            context = data['context'],
            method = req.script_name,
            params = inputs,
            url = req.url.decode('utf-8'),
            value = [
                output_tree.to_json()
                for output_tree in output_trees
                ],
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
    survey_file_path = os.path.join(model.DATA_DIR, survey_filename)
    verbose = False

    legislation_tree = ElementTree.parse(model.PARAM_FILE)
    legislation_xml_json = conv.check(legislationsxml.xml_legislation_to_json)(legislation_tree.getroot(), state = ctx)
    legislation_xml_json, error = legislationsxml.validate_node_xml_json(legislation_xml_json, state = ctx)
    # TODO: Fail on error.
    _, legislation_json = legislationsxml.transform_node_xml_json_to_json(legislation_xml_json)

    compact_legislations = []
    dated_legislation_json = legislations.generate_dated_legislation_json(legislation_json, datesim)
    compact_legislation = legislations.compact_dated_node_json(dated_legislation_json)
    compact_legislations.append(compact_legislation)
    if reform:
        # TODO: Use variant legislation instead of the default one.
        dated_legislation_json = legislations.generate_dated_legislation_json(legislation_json, datesim)
        compact_legislation = legislations.compact_dated_node_json(dated_legislation_json)
        compact_legislations.append(compact_legislation)

    for index, compact_legislation in enumerate(compact_legislations):
        datesim = compact_legislation.datesim
        input_table = datatables.DataTable(model.column_by_name, datesim = datesim, num_table = num_table,
            print_missing = verbose)
        input_table.load_data_from_survey(survey_file_path, num_table = num_table, print_missing = verbose)

        previous_compact_legislation = compact_legislations[index - 1] if index > 0 else compact_legislation
        output_table = taxbenefitsystems.TaxBenefitSystem(model.prestation_by_name, compact_legislation,
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
            value = conv.pipe(
                legislations.validate_node_json,
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

    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(dict(
            apiVersion = '1.0',
            context = data['context'],
            method = req.script_name,
            params = inputs,
            url = req.url.decode('utf-8'),
            value = data,
            ).iteritems())),
        headers = headers,
        )


def make_router():
    """Return a WSGI application that searches requests to controllers """
    global router
    router = urls.make_router(
        ('GET', '^/api/1/fields/?$', api1_fields),
        ('POST', '^/api/1/legislations/?$', api1_submit_legislation),
        ('POST', '^/api/1/simulate/?$', api1_simulate),
        ('POST', '^/api/1/simulate-survey/?$', api1_simulate_survey),
        )
    return router
