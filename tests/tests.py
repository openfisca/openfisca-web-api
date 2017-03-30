# -*- coding: utf-8 -*-

from httplib import OK, NOT_FOUND
import json
import pkg_resources
from nose.tools import assert_equal

from openfisca_web_api.app import create_app

TEST_COUNTRY_PACKAGE_NAME = 'openfisca_dummy_country'
distribution = pkg_resources.get_distribution(TEST_COUNTRY_PACKAGE_NAME)
subject = create_app(TEST_COUNTRY_PACKAGE_NAME).test_client()


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
        {u'description': u'Taux d\'impôt sur les salaires'}
        )

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
            u'description': u'Taux d\'impôt sur les salaires',
            u'values': {u'2016-01-01': 0.35, u'2015-01-01': 0.32, u'1998-01-01': 0.3}
            }
        )


def test_stopped_parameter_values():
    response = subject.get('/parameter/impot.bouclier')
    parameter = json.loads(response.data)
    assert_equal(
        parameter,
        {
            u'id': u'impot.bouclier',
            u'description': u'Montant maximum de l\'impôt',
            u'values': {u'2012-01-01': None, u'2009-01-01': 0.6, u'2008-01-01': 0.5}
            }
        )


def check_code(route, code):
    response = subject.get(route)
    assert_equal(response.status_code, code)


def test_routes_robustness():
    expected_codes = {
        '/parameters/': OK,
        '/parameter': NOT_FOUND,
        '/parameter/': NOT_FOUND,
        '/parameter/with-ÜNı©ød€': NOT_FOUND,
        '/parameter/with%20url%20encoding': NOT_FOUND,
        '/parameter/impot.taux/': OK,
        '/parameter/impot.taux/too-much-nesting': NOT_FOUND,
        '/parameter//impot.taux/': NOT_FOUND,
        }

    for route, code in expected_codes.iteritems():
        yield check_code, route, code
