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


"""Middleware initialization"""


import webob
from weberror.errormiddleware import ErrorMiddleware

from . import conf, contexts, controllers, environment, urls


def environment_setter(app):
    """WSGI middleware that sets request-dependant environment."""
    def set_environment(environ, start_response):
        req = webob.Request(environ)
        ctx = contexts.Ctx(req)
        urls.application_url = req.application_url
#        if conf['host_urls'] is not None:
#            host_url = req.host_url + '/'
#            if host_url not in conf['host_urls']:
#                return wsgihelpers.bad_request(ctx, explanation = ctx._('Web site not found.'))(environ,
#                    start_response)

#        from . import model
#        model.configure(ctx)

        return app(req.environ, start_response)

    return set_environment


def make_app(global_conf, **app_conf):
    """Create a WSGI application and return it

    ``global_conf``
        The inherited configuration for this application. Normally from
        the [DEFAULT] section of the Paste ini file.

    ``app_conf``
        The application's local configuration. Normally specified in
        the [app:<name>] section of the Paste ini file (where <name>
        defaults to main).
    """
    # Configure the environment and fill conf dictionary.
    environment.load_environment(global_conf, app_conf)

    # Dispatch request to controllers.
    app = controllers.make_router()

    # Init request-dependant environment
    app = environment_setter(app)

    # CUSTOM MIDDLEWARE HERE (filtered by error handling middlewares)

    # Handle Python exceptions
    if not conf['debug']:
        app = ErrorMiddleware(app, global_conf, **conf['errorware'])

    return app
