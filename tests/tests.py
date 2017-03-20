# -*- coding: utf-8 -*-

from httplib import OK, NOT_FOUND
import json
import pkg_resources
from nose.tools import assert_equal

from openfisca_web_api.app import create_app

TEST_COUNTRY_PACKAGE = 'openfisca_dummy_country'
distribution = pkg_resources.get_distribution(TEST_COUNTRY_PACKAGE)
subject = create_app(TEST_COUNTRY_PACKAGE).test_client()


# /parameters

parameters_response = subject.get('/parameters')


def test_return_code():
    assert_equal(parameters_response.status_code, OK)


def test_package_name_header():
    assert_equal(parameters_response.headers.get('Country-Package'), distribution.key)


def test_package_version_header():
    assert_equal(parameters_response.headers.get('Country-Package-Version'), distribution.version)


def test_response_data():
    parameters = json.loads(parameters_response.data)
    assert_equal(
        parameters[u'impot.taux'],
        {u'description': u'taux d\'impôt sur les salaires'}
        )


def test_with_extra_slash():
    response = subject.get('/parameters/')
    assert_equal(response.status_code, NOT_FOUND)


# /parameter/<id>

def test_error_code_non_existing_parameter():
    response = subject.get('/parameter/non.existing.parameter')
    assert_equal(response.status_code, NOT_FOUND)


def test_return_code_existing_parameter():
    response = subject.get('/parameter/impot.taux')
    assert_equal(response.status_code, OK)


def test_fuzzied_parameter_values():
    response = subject.get('/parameter/impot.taux')
    parameter = json.loads(response.data)
    assert_equal(
        parameter,
        {
            u'id': u'impot.taux',
            u'description': u'taux d\'impôt sur les salaires',
            u'values': {u'2016-01-01': 0.35, u'2015-01-01': 0.32, u'1998-01-01': 0.3}
            }
        )


def test_stopped_parameter_values():
    response = subject.get('/parameter/csg.activite.deductible.taux')
    parameter = json.loads(response.data)
    assert_equal(
        parameter,
        {
            u'id': u'csg.activite.deductible.taux',
            u'description': u'taux de la CSG déductible',
            u'values': {u'2016-01-01': None, u'2015-01-01': 0.06, u'1998-01-01': 0.051}
            }
        )


def check_route_not_found(route):
    response = subject.get(route)
    assert_equal(response.status_code, NOT_FOUND)


def test_wrong_routes():
    wrong_routes = [
        '/parameter',
        '/parameter/',
        '/parameter/with-ÜNı©ød€',
        '/parameter/with%20url%20encoding',
        '/parameter/impot.taux/',
        '/parameter/impot.taux/too-much-nesting',
        '/parameter//impot.taux/',
        ]
    for route in wrong_routes:
        yield check_route_not_found, route
