# -*- coding: utf-8 -*-


"""Middleware initialization"""


import json
import logging
import sys

try:
    import ipdb
except ImportError:
    ipdb = None
import weberror.errormiddleware
from webob.dec import wsgify

from . import conf, controllers, environment, urls

log = logging.getLogger(__name__)


@wsgify.middleware
def launch_debugger_on_exception(req, app):
    try:
        return req.get_response(app)
    except Exception as exc:
        log.exception(exc)
        e, m, tb = sys.exc_info()
        ipdb.post_mortem(tb)
        raise


@wsgify.middleware
def set_application_url(req, app):
    urls.application_url = req.application_url
    return req.get_response(app)


@wsgify.middleware
def ensure_json_content_type(req, app):
    """
    ErrorMiddleware returns hard-coded content-type text/html.
    Here we force it to be application/json.
    """
    res = req.get_response(app, catch_exc_info=True)
    res.content_type = 'application/json; charset=utf-8'
    return res


@wsgify.middleware
def add_x_api_version_header(req, app):
    res = req.get_response(app)
    res.headers.update({'X-API-Version': environment.api_package_version})
    return res


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
    app = set_application_url(app)

    # CUSTOM MIDDLEWARE HERE (filtered by error handling middlewares)

    # Handle Python exceptions
    if not conf['debug']:
        def json_error_template(head_html, exception, extra):
            error_json = {
                'code': 500,
                'hint': u'See the HTTP server log to see the exception traceback.',
                'message': exception,
                }
            if head_html:
                error_json['head_html'] = head_html
            if extra:
                error_json['extra'] = extra
            return json.dumps({'error': error_json})
        weberror.errormiddleware.error_template = json_error_template
        app = weberror.errormiddleware.ErrorMiddleware(app, global_conf, **conf['errorware'])

    app = ensure_json_content_type(app)
    app = add_x_api_version_header(app)

    if conf['debug'] and ipdb is not None:
        app = launch_debugger_on_exception(app)

    return app
