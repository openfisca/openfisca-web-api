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


"""Fields controller"""


import collections

from .. import contexts, model, wsgihelpers


def walk_legislation_json(node_json, descriptions, parameters_json, path_fragments):
    children_json = node_json.get('children') or None
    if children_json is None:
        parameter_json = node_json.copy()  # No need to deepcopy since it is a leaf.
        description = u' ; '.join(
            fragment
            for fragment in descriptions + [node_json.get('description')]
            if fragment
            )
        parameter_json['description'] = description
        parameter_json['name'] = u'.'.join(path_fragments)
        parameters_json.append(parameter_json)
    else:
        for child_name, child_json in children_json.iteritems():
            walk_legislation_json(
                child_json,
                descriptions = descriptions + [node_json.get('description')],
                parameters_json = parameters_json,
                path_fragments = path_fragments + [child_name],
                )


@wsgihelpers.wsgify
def api1_parameters(req):
    ctx = contexts.Ctx(req)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx)

    assert req.method == 'GET', req.method

    legislation_json = model.tax_benefit_system.legislation_json
    parameters_json = []
    walk_legislation_json(
        legislation_json,
        descriptions = [],
        parameters_json = parameters_json,
        path_fragments = [],
        )

    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(dict(
            apiVersion = 1,
            method = req.script_name,
            parameters = parameters_json,
            url = req.url.decode('utf-8'),
            ).iteritems())),
        headers = headers,
        )
