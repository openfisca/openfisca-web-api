# -*- coding: utf-8 -*-


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
    """
    WSGI middleware that catches all uncaught exceptions and responds a generic JSON object.
    Since Webob wsgify decorator catches HTTPException subclasses, here remains only the others.
    """
    def respond_json_exception(environ, start_response):
        try:
            return app(environ, start_response)
        except Exception as exc:
            log.exception(exc)
            start_response('500 Internal Server Error', [('content-type', 'application/json; charset=utf-8')])
            error_json = {
                'error': {
                    'code': 500,
                    'hint': u'See the HTTP server log to see the exception traceback.',
                    'message': u'Internal Server Error',
                    },
                }
            return [json.dumps(error_json)]

    return respond_json_exception


def x_api_version_header_setter(app):
    """WSGI middleware that sets response X-API-Version header."""
    def set_x_api_version_header(environ, start_response):
        req = webob.Request(environ)
        res = req.get_response(app)
        res.headers.update({'X-API-Version': environment.api_package_version})
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
