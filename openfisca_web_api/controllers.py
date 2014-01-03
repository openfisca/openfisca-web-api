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
import itertools
import os

from openfisca_core import datatables, model, parameters, taxbenefitsystems

from . import contexts, conv, urls, wsgihelpers


N_ = lambda message: message
router = None


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
                conv.not_none,
                ),
            nmen = conv.pipe(
                conv.test_isinstance(int),
                conv.test_greater_or_equal(1),
                conv.not_none,
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
            x_axis = conv.pipe(
                conv.test_isinstance(basestring),
                conv.test_in(model.x_axes.keys()),
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
#    if not account.admin:
#        return wsgihelpers.respond_json(ctx,
#            collections.OrderedDict(sorted(dict(
#                apiVersion = '1.0',
#                context = data['context'],
#                error = collections.OrderedDict(sorted(dict(
#                    code = 403,  # Forbidden
#                    message = ctx._('Non-admin API Key: {}').format(api_key),
#                    ).iteritems())),
#                method = req.script_name,
#                params = inputs,
#                url = req.url.decode('utf-8'),
#                ).iteritems())),
#            headers = headers,
#            )

    decomp_file = os.path.join(model.DECOMP_DIR, model.DEFAULT_DECOMP_FILE)
    difference = data['difference']
    # The aefa prestation can be disabled by uncommenting the following line:
    disabled_prestations = None  # ['aefa']
    maxrev = data['maxrev']
    nmen = data['nmen']
    num_table = 1
    reform = data['reform']
    subset = None
    verbose = False

    legislations = []
    scenarios = []
    for scenario_data in data['scenarios']:
        datesim = datetime.date(scenario_data.pop('year'), 1, 1)

        scenario = model.Scenario()
        scenario.maxrev = maxrev
        scenario.nmen = nmen
        scenario.same_rev_couple = False
        scenario.x_axis = data['x_axis']
        scenario.year = datesim.year
        scenario.__dict__.update(scenario_data)
        scenarios.append(scenario)

        reader = parameters.XmlReader(model.PARAM_FILE, datesim)
        legislation_tree = reader.tree
        legislation = parameters.Tree2Object(legislation_tree, defaut = True)
        legislation.datesim = datesim
        legislations.append(legislation)
    if reform:
        scenario = model.Scenario()
        scenario.maxrev = maxrev
        scenario.nmen = nmen
        scenario.same_rev_couple = False
        scenario.x_axis = data['x_axis']
        scenario.year = datesim.year
        scenario.__dict__.update(scenario_data)
        scenarios.append(scenario)

        reader = parameters.XmlReader(model.PARAM_FILE, datesim)
        legislation_tree = reader.tree
        legislation = parameters.Tree2Object(legislation_tree, defaut = False)
        legislation.datesim = datesim
        legislations.append(legislation)

    output_trees = []
    for index, (legislation, scenario) in enumerate(itertools.izip(legislations, scenarios)):
        datesim = legislation.datesim
        input_table = datatables.DataTable(model.InputDescription, datesim = datesim, num_table = num_table,
            subset = subset, print_missing = verbose)
        input_table.test_case = scenario
        scenario.populate_datatable(input_table)

        previous_legislation = legislations[index - 1] if index > 0 else legislation
        output_table = taxbenefitsystems.TaxBenefitSystem(model.OutputDescription, legislation, previous_legislation,
            datesim = datesim, num_table = num_table)
        output_table.set_inputs(input_table)
        output_table.disable(disabled_prestations)
        output_table.decomp_file = decomp_file
        output_tree = output_table.test_case_calculate()

        if (difference or reform) and index > 0:
            output_tree.difference(output_trees[0])

        output_trees.append(output_tree)

#    gc.collect()

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


def make_router():
    """Return a WSGI application that searches requests to controllers """
    global router
    router = urls.make_router(
        ('POST', '^/api/1/simulate/?$', api1_simulate),
        )
    return router
