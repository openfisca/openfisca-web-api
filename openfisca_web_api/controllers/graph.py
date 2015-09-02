# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014, 2015 OpenFisca Team
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

    str_to_reforms = conv.make_str_to_reforms()

    data, errors = conv.pipe(
        conv.struct(
            dict(
                context = conv.noop,  # For asynchronous calls
                reforms = str_to_reforms,
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
                    conv.default(u'revdisp'),
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
