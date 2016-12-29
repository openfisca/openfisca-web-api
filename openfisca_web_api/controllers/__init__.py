# -*- coding: utf-8 -*-


"""Controllers"""


import collections

from . import calculate, entities, field, fields, formula, graph, parameters, reforms, simulate, swagger, variables
from .. import contexts, urls, wsgihelpers


router = None


@wsgihelpers.wsgify
def index(req):
    ctx = contexts.Ctx(req)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx)

    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(dict(
            apiVersion = 1,
            message = u'Welcome, this is OpenFisca Web API.',
            method = req.script_name,
            ).iteritems())),
        headers = headers,
        )


def make_router():
    """Return a WSGI application that searches requests to controllers """
    global router
    routings = [
        ('GET', '^/$', index),
        ('GET', '^/api/?$', index),
        ('POST', '^/api/1/calculate/?$', calculate.api1_calculate),
        ('GET', '^/api/2/entities/?$', entities.api2_entities),
        ('GET', '^/api/1/field/?$', field.api1_field),
        ('GET', '^/api/1/fields/?$', fields.api1_fields),
        ('GET', '^/api/1/formula/(?P<name>[^/]+)/?$', formula.api1_formula),
        ('GET', '^/api/2/formula/(?:(?P<period>[A-Za-z0-9:-]*)/)?(?P<names>[A-Za-z0-9_+-]+)/?$', formula.api2_formula),
        ('GET', '^/api/1/graph/?$', graph.api1_graph),
        ('GET', '^/api/1/parameters/?$', parameters.api1_parameters),
        ('GET', '^/api/1/reforms/?$', reforms.api1_reforms),
        ('POST', '^/api/1/simulate/?$', simulate.api1_simulate),
        ('GET', '^/api/1/swagger$', swagger.api1_swagger),
        ('GET', '^/api/1/variables/?$', variables.api1_variables),
        ]
    router = urls.make_router(*routings)
    return router
