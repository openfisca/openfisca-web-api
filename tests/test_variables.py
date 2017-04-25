# -*- coding: utf-8 -*-

from httplib import OK, NOT_FOUND
import json
from nose.tools import assert_equal, assert_regexp_matches, assert_not_in
from . import subject

# /variables

variables_response = subject.get('/variables')
GITHUB_URL_REGEX = '^https://github\.com/openfisca/openfisca-dummy-country/blob/\d+\.\d+\.\d+/openfisca_dummy_country/model/model\.py#L\d+-L\d+$'


def test_return_code():
    assert_equal(variables_response.status_code, OK)


def test_response_data():
    variables = json.loads(variables_response.data)
    assert_equal(
        variables[u'birth'],
        {u'description': u'Date de naissance'}
        )


# /variable/<id>


def test_error_code_non_existing_variable():
    response = subject.get('/variable/non_existing_variable')
    assert_equal(response.status_code, NOT_FOUND)


input_variable_response = subject.get('/variable/birth')
input_variable = json.loads(input_variable_response.data)


def test_return_code_existing_input_variable():
    assert_equal(input_variable_response.status_code, OK)


def check_input_variable_value(key, expected_value):
    assert_equal(input_variable[key], expected_value)


def test_input_variable_value():
    expected_values = {
        u'description': u'Date de naissance',
        u'valueType': u'Date',
        u'defaultValue': u'1970-01-01',
        u'definitionPeriod': u'eternity',
        u'entity': u'individu',
        u'references': [u'https://fr.wikipedia.org/wiki/Date_de_naissance'],
        }

    for key, expected_value in expected_values.iteritems():
        yield check_input_variable_value, key, expected_value


def test_input_variable_github_url():
    assert_regexp_matches(input_variable['source'], GITHUB_URL_REGEX)


variable_response = subject.get('/variable/salaire_net')
variable = json.loads(variable_response.data)


def test_return_code_existing_variable():
    assert_equal(variable_response.status_code, OK)


def check_variable_value(key, expected_value):
    assert_equal(variable[key], expected_value)


def test_variable_value():
    expected_values = {
        u'description': u'Salaire net',
        u'valueType': u'Float',
        u'defaultValue': 0,
        u'definitionPeriod': u'month',
        u'entity': u'individu',
        }

    for key, expected_value in expected_values.iteritems():
        yield check_variable_value, key, expected_value


def test_null_values_are_dropped():
    assert_not_in('references', variable.keys())


def test_variable_formula_github_link():
    assert_regexp_matches(variable['formulas']['0001-01-01']['source'], GITHUB_URL_REGEX)


def test_variable_formula_content():
    formula_code = "def function(individu, period):\n    salaire_brut = individu('salaire_brut', period)\n\n    return salaire_brut * 0.8\n"
    assert_equal(variable['formulas']['0001-01-01']['content'], formula_code)
