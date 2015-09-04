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


"""Middleware initialization"""


import json
import logging
import sys

try:
    import ipdb
except ImportError:
    ipdb = None
from weberror.errormiddleware import ErrorMiddleware
import webob

from . import conf, controllers, environment, urls

log = logging.getLogger(__name__)


def launch_debugger_on_exception(app):
    """WSGI middleware that catches all exceptions and launches a debugger."""
    def _launch_debugger_on_exception(environ, start_response):
        try:
            return app(environ, start_response)
        except Exception as exc:
            log.exception(exc)
            e, m, tb = sys.exc_info()
            ipdb.post_mortem(tb)
            raise
    return _launch_debugger_on_exception


def environment_setter(app):
    """WSGI middleware that sets request-dependant environment."""
    def set_environment(environ, start_response):
        req = webob.Request(environ)
        urls.application_url = req.application_url
        try:
            return app(req.environ, start_response)
        except webob.exc.WSGIHTTPException as wsgi_exception:
            return wsgi_exception(environ, start_response)

    return set_environment


def exception_to_json(app):
    """WSGI middleware that catches all exceptions and responds a JSON with the message."""
    def respond_json_exception(environ, start_response):
        try:
            return app(environ, start_response)
        except Exception as exc:
            log.exception(exc)
            start_response('500 Internal Server Error', [('content-type', 'application/json; charset=utf-8')])
            return [json.dumps({'error': u'Internal Server Error'})]

    return respond_json_exception


def x_api_version_header_setter(app):
    """WSGI middleware that sets response X-API-Version header."""
    def set_x_api_version_header(environ, start_response):
        req = webob.Request(environ)
        res = req.get_response(app)
        res.headers.update({'X-API-Version': environment.git_head_sha})
        return res(environ, start_response)

    return set_x_api_version_header


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

    # Set X-API-Version response header
    app = x_api_version_header_setter(app)

    # CUSTOM MIDDLEWARE HERE (filtered by error handling middlewares)

    # Handle Python exceptions
    if conf['debug'] and ipdb is not None:
        app = launch_debugger_on_exception(app)
    app = exception_to_json(app)
    if not conf['debug']:
        app = ErrorMiddleware(app, global_conf, **conf['errorware'])

    return app
