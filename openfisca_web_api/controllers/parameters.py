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


"""Parameters controller"""


import collections

from openfisca_core import legislations, periods

from .. import contexts, conv, environment, model, wsgihelpers


@wsgihelpers.wsgify
def api1_parameters(req):
    ctx = contexts.Ctx(req)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx)

    assert req.method == 'GET', req.method
    params = req.GET
    inputs = dict(
        instant = params.get('instant'),
        names = params.getall('name'),
        )

    parameters_name = [
        parameter_json['name']
        for parameter_json in model.parameters_json_cache
        ]

    data, errors = conv.pipe(
        conv.struct(
            dict(
                instant = conv.pipe(
                    conv.empty_to_none,
                    conv.test_isinstance(basestring),
                    conv.function(lambda str: periods.instant(str)),
                    ),
                names = conv.pipe(
                    conv.uniform_sequence(
                        conv.pipe(
                            conv.empty_to_none,
                            conv.test_in(parameters_name, error = u'Parameter does not exist'),
                            ),
                        drop_none_items = True,
                        ),
                    conv.empty_to_none,
                    ),
                ),
            default = 'drop',
            ),
        )(inputs, state = ctx)

    if errors is not None:
        return wsgihelpers.respond_json(ctx,
            collections.OrderedDict(sorted(dict(
                apiVersion = 1,
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

    tax_benefit_system = model.tax_benefit_system

    if data['instant'] is None:
        if data['names'] is None:
            parameters_json = model.parameters_json_cache
        else:
            parameters_json = [
                parameter_json
                for parameter_json in model.parameters_json_cache
                if parameter_json['name'] in data['names']
                ]
    else:
        instant = data['instant']
        parameters_json = []
        dated_legislation_json = legislations.generate_dated_legislation_json(
            tax_benefit_system.legislation_json,
            instant,
            )
        for name in data['names']:
            name_fragments = name.split('.')
            parameter_json = dated_legislation_json
            for name_fragment in name_fragments:
                parameter_json = parameter_json['children'][name_fragment]
            parameter_json['name'] = name
            parameter_json_in_cache = [
                parameter_json1
                for parameter_json1 in model.parameters_json_cache
                if parameter_json1['name'] == name
                ][0]
            parameter_json['description'] = parameter_json_in_cache['description']
            parameters_json.append(parameter_json)

    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(dict(
            apiVersion = 1,
            country_package_git_head_sha = environment.country_package_git_head_sha,
            currency = tax_benefit_system.CURRENCY,
            method = req.script_name,
            parameters = parameters_json,
            parameters_file_path = model.parameters_file_path,
            url = req.url.decode('utf-8'),
            ).iteritems())),
        headers = headers,
        )
