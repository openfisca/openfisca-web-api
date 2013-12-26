# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013 OpenFisca Team
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


from openfisca_core import model

from . import contexts, templates, urls, wsgihelpers


router = None


@wsgihelpers.wsgify
def index(req):
    ctx = contexts.Ctx(req)
    print model.InputDescription
    return templates.render(ctx, '/index.mako')


def make_router():
    """Return a WSGI application that searches requests to controllers """
    global router
    router = urls.make_router(
        ('GET', '^/?$', index),

#        (None, '^/admin/accounts(?=/|$)', accounts.route_admin_class),
#        (None, '^/admin/formulas(?=/|$)', formulas.route_admin_class),
#        (None, '^/admin/sessions(?=/|$)', sessions.route_admin_class),
#        (None, '^/admin/parameters(?=/|$)', parameters.route_admin_class),
#        (None, '^/api/1/accounts(?=/|$)', accounts.route_api1_class),
#        (None, '^/api/1/formulas(?=/|$)', formulas.route_api1_class),
#        (None, '^/api/1/parameters(?=/|$)', parameters.route_api1_class),
#        ('POST', '^/login/?$', accounts.login),
#        ('POST', '^/logout/?$', accounts.logout),
        )
    return router
