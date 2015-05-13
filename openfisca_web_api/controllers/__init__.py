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


"""Controllers"""


from . import calculate, entities, field, fields, formula, graph, reforms, simulate, swagger
from .. import urls


router = None


def make_router():
    """Return a WSGI application that searches requests to controllers """
    global router
    routings = [
        ('POST', '^/api/1/calculate/?$', calculate.api1_calculate),
        ('GET', '^/api/1/entities/?$', entities.api1_entities),
        ('GET', '^/api/1/field/?$', field.api1_field),
        ('GET', '^/api/1/fields/?$', fields.api1_fields),
        ('GET', '^/api/1/formula/(?P<name>[^/]+)/?$', formula.api1_formula),
        ('GET', '^/api/2/formula/(?:(?P<period>[A-Za-z0-9:-]*)/)?(?P<names>[A-Za-z0-9_+-]+)/?$', formula.api2_formula),
        ('GET', '^/api/1/graph/?$', graph.api1_graph),
        ('GET', '^/api/1/reforms/?$', reforms.api1_reforms),
        ('POST', '^/api/1/simulate/?$', simulate.api1_simulate),
        ('GET', '^/api/1/swagger$', swagger.api1_swagger),
        ]
    router = urls.make_router(*routings)
    return router
