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


"""Field controller"""


import collections
import datetime

from openfisca_core import periods, simulations

from .. import contexts, conv, model, wsgihelpers


@wsgihelpers.wsgify
def api1_field(req):
    ctx = contexts.Ctx(req)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx)

    assert req.method == 'GET', req.method
    params = req.GET
    inputs = dict(
        context = params.get('context'),
        input_variables = params.get('input_variables'),
        reforms = params.getall('reform'),
        variable = params.get('variable'),
        )

    str_to_reforms = conv.make_str_to_reforms()

    data, errors = conv.pipe(
        conv.struct(
            dict(
                context = conv.noop,  # For asynchronous calls
                input_variables = conv.pipe(
                    conv.test_isinstance((bool, int, basestring)),
                    conv.anything_to_bool,
                    conv.default(True),
                    ),
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

    variable_name = data['variable']
    column = tax_benefit_system.column_by_name[variable_name]
    value_json = column.to_json()
    if data['input_variables'] and not column.is_input_variable():
        simulation = simulations.Simulation(
            period = periods.period(datetime.date.today().year),
            tax_benefit_system = tax_benefit_system,
            )
        holder = simulation.get_or_new_holder(variable_name)
        value_json['formula'] = holder.formula.to_json(
            get_input_variables_and_parameters = model.get_cached_input_variables_and_parameters,
            with_input_variables_details = True,
            )
    value_json['entity'] = column.entity  # Overwrite with symbol instead of key plural for compatibility.

    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(dict(
            apiStatus = u'deprecated',
            apiVersion = 1,
            context = data['context'],
            method = req.script_name,
            params = inputs,
            url = req.url.decode('utf-8'),
            value = value_json,
            ).iteritems())),
        headers = headers,
        )
