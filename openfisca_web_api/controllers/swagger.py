# -*- coding: utf-8 -*-
"""Swagger controller"""


import datetime
import pkg_resources

from . import formula
from .formula import default_period
from .. import contexts, model, wsgihelpers


PACKAGE_VERSION = pkg_resources.get_distribution('OpenFisca-Web-API').version
SWAGGER_BASE_PATH = '/api/2/formula'


@wsgihelpers.wsgify
def api1_swagger(req):
    ctx = contexts.Ctx(req)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx)

    return wsgihelpers.respond_json(ctx, build_json(), headers = headers)


def build_json():
    result = build_metadata()
    result['paths'] = build_paths()
    return result


def build_metadata():
    return {
        'swagger': '2.0',
        'basePath': SWAGGER_BASE_PATH,
        'info': {
            'version': PACKAGE_VERSION,
            'title': 'OpenFisca',
            'description': formula.api2_formula.__doc__,
            'termsOfService': 'http://github.com/openfisca/openfisca-web-api',
            'contact': {
                'name': 'OpenFisca team',
                'email': 'contact@openfisca.fr',
                'url': 'http://github.com/openfisca/openfisca-web-api/issues'
                },
            'license': {
                'name': 'AGPL',
                'url': 'https://www.gnu.org/licenses/agpl-3.0.html'
                }
            },
        'parameters': {
            'periodParam': {
                'name': 'period',
                'in': 'path',
                'required': True,   # Swagger spec: in path => required; pattern thus allows empty values
                'default': default_period(),
                'description': 'The period for which the given taxes are to be computed',
                'type': 'string',
                'format': 'period',
                'pattern': '^([12]\d{3}(\-\d{2}){0,2})?$'
                }
            }
        }


def build_paths():
    return {
        '/{period}/' + name: {
            'get': map_path_to_swagger(column)
            }
        for name, column in model.tax_benefit_system.column_by_name.iteritems()
        if not column.is_input_variable()
        }


def map_path_to_swagger(column):
    column_json = column.to_json()

    result = map_path_base_to_swagger(column_json)
    result['responses'] = make_responses_for(column_json)

    try:
        result['parameters'] = get_parameters(column)
    except Exception, e:
        print('Error mapping parameters of formula "{}":'.format(column.to_json().get('name')))  # noqa
        print(e)  # noqa

    return result


def map_path_base_to_swagger(column_json):
    result = {
        'summary': column_json.get('label'),
        'tags': [column_json.get('entity')],
        }

    if column_json.get('url'):
        result['externalDocs'] = {'url': column_json.get('url')}

    return result


def make_responses_for(column_json):
    return {
        200: {
            'description': column_json.get('label'),
            'schema': make_response_schema_for(column_json)
            },
        400: {
            'description': 'At least one of the sent parameters could not be parsed.',
            'schema': {
                'type': 'object',
                'required': [
                    'params',
                    'error',
                    'apiVersion'
                    ],
                'properties': {
                    'params': {
                        'type': 'object'
                        },
                    'error': {
                        'type': 'object',
                        'required': [
                            'message'
                            ],
                        'properties': {
                            'message': {
                                'type': 'string'
                                }
                            }
                        },
                    'apiVersion': {
                        'type': 'string',
                        'format': 'semver'
                        }
                    }
                }
            }
        }


def make_response_schema_for(column_json):
    return {
        "type": "object",
        "required": [
            "apiVersion",
            "values",
            "params",
            "period"
            ],
        "properties": {
            "apiVersion": {
                "type": "string",
                "format": "semver"
                },
            "values": {
                "type": "object",
                "required": [
                    column_json.get('name')
                    ],
                "properties": {
                    column_json.get('name'): map_type_to_swagger(column_json.get('@type', 'string'))
                    }
                },
            "params": {
                "type": "object"
                },
            "period": {
                "type": "array"
                }
            }
        }


def get_parameters(column):
    result = map_parameters_to_swagger(column)
    result.append({
        '$ref': '#/parameters/periodParam'
        })
    return result


def map_parameters_to_swagger(column):
    input_variables, parameters = model.get_cached_input_variables_and_parameters(column)

    return [
        map_parameter_to_swagger(model.tax_benefit_system.column_by_name[variable_name])
        for variable_name in input_variables
        ]


def map_parameter_to_swagger(column):
    column_json = column.to_json()

    result = map_type_to_swagger(column_json.get('@type'))

    if column_json.get('labels'):
        result['enum'] = column_json.get('labels').values()

    result.update({
        'name': column_json.get('name'),
        'description': column_json.get('label'),
        'default': get_default_value(column, column_json),
        'in': 'query'
        })

    return result


def get_default_value(column, column_json = None):
    result = column.default

    if isinstance(result, datetime.date):
        result = '%s-%s-%s' % (result.year, result.month, result.day)
    elif column_json.get('labels'):  # the default value is actually the key to the array of allowed values
        if column_json is None:
            column_json = column.to_json()
        result = column_json.get('labels').get(result)

    return result


# Transforms a Python type to a Swagger type
def map_type_to_swagger(type):
    result = {'type': type.lower()}

    if type == 'Integer':
        result['format'] = 'int32'
    elif type == 'Float':
        result['type'] = 'number'
        result['format'] = 'float'
    elif type == 'Date':
        result['type'] = 'string'
        result['format'] = 'date'
    elif type == 'Enumeration':
        result['type'] = 'string'

    return result
