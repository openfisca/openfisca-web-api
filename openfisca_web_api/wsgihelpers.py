# -*- coding: utf-8 -*-


"""Decorators to wrap functions to make them WSGI applications.

The main decorator :class:`wsgify` turns a function into a WSGI application.
"""


import collections
import datetime
import json
from functools import update_wrapper

import webob.dec
import webob.exc


def N_(message):
    return message


errors_title = {
    400: N_("Unable to Access"),
    401: N_("Access Denied"),
    403: N_("Access Denied"),
    404: N_("Unable to Access"),
    500: N_("Internal Server Error"),
    }


def wsgify(func, *args, **kwargs):
    result = webob.dec.wsgify(func, *args, **kwargs)
    update_wrapper(result, func)
    return result


def handle_cross_origin_resource_sharing(ctx):
    # Cf http://www.w3.org/TR/cors/#resource-processing-model
    environ = ctx.req.environ
    headers = []
    origin = environ.get('HTTP_ORIGIN')
    if origin is None:
        return headers
    if ctx.req.method == 'OPTIONS':
        method = environ.get('HTTP_ACCESS_CONTROL_REQUEST_METHOD')
        if method is None:
            return headers
        headers_name = environ.get('HTTP_ACCESS_CONTROL_REQUEST_HEADERS') or ''
        headers.append(('Access-Control-Allow-Credentials', 'true'))
        headers.append(('Access-Control-Allow-Origin', origin))
        headers.append(('Access-Control-Max-Age', '3628800'))
        headers.append(('Access-Control-Allow-Methods', method))
        headers.append(('Access-Control-Allow-Headers', headers_name))
        raise webob.exc.status_map[204](headers = headers)  # No Content
    headers.append(('Access-Control-Allow-Credentials', 'true'))
    headers.append(('Access-Control-Allow-Origin', origin))
    headers.append(('Access-Control-Expose-Headers', 'WWW-Authenticate'))
    return headers


def respond_json(ctx, data, code = None, headers = [], json_dumps_default = None, jsonp = None):
    """Return a JSON response.

    This function is optimized for JSON following
    `Google JSON Style Guide <http://google-styleguide.googlecode.com/svn/trunk/jsoncstyleguide.xml>`_, but will handle
    any JSON except for HTTP errors.
    """
    if isinstance(data, collections.Mapping):
        # Remove null properties as recommended by Google JSON Style Guide.
        data = type(data)(
            (name, value)
            for name, value in data.iteritems()
            if value is not None
            )
        error = data.get('error')
        if isinstance(error, collections.Mapping):
            error = data['error'] = type(error)(
                (name, value)
                for name, value in error.iteritems()
                if value is not None
                )
    else:
        error = None
    if jsonp:
        content_type = 'application/javascript; charset=utf-8'
    else:
        content_type = 'application/json; charset=utf-8'
    if error:
        code = code or error['code']
        assert isinstance(code, int)
        response = webob.exc.status_map[code](headers = headers)
        response.content_type = content_type
        if code == 204:  # No content
            return response
        if error.get('code') is None:
            error['code'] = code
        if error.get('message') is None:
            title = errors_title.get(code)
            title = ctx._(title) if title is not None else response.status
            error['message'] = title
    else:
        response = ctx.req.response
        response.content_type = content_type
        if code is not None:
            response.status = code
        response.headers.update(headers)
    # try:
    #     text = json.dumps(data, encoding = 'utf-8', ensure_ascii = False, indent = 2)
    # except UnicodeDecodeError:
    #     text = json.dumps(data, ensure_ascii = True, indent = 2)
    if json_dumps_default is None:
        text = json.dumps(data)
    else:
        text = json.dumps(data, default = json_dumps_default)
    text = unicode(text)
    if jsonp:
        text = u'{0}({1})'.format(jsonp, text)
    response.text = text
    return response


def convert_date_to_json(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    else:
        return json.JSONEncoder().default(obj)


def handle_error(error, ctx, headers):
    raise respond_json(ctx,
        dict(
            error = dict(
                code = 400,
                message = u"{}: {}".format(error.__class__.__name__, error.message),
                ),
            ),
        headers = headers,
        )
