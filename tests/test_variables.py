# -*- coding: utf-8 -*-

from httplib import OK, NOT_FOUND
import json
from nose.tools import assert_equal, assert_regexp_matches
from . import subject

# /variables

variables_response = subject.get('/variables')


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
        u"description": u"Date de naissance",
        u"valueType": u"Date",
        u"defaultValue": u"1970-01-01",
        u"definitionPeriod": u"eternity",
        u"entity": u"individu",
        # url
        }

    for key, expected_value in expected_values.iteritems():
        yield check_input_variable_value, key, expected_value


def test_input_variable_github_url():
    assert_regexp_matches(input_variable['source'], '^https://github\.com/openfisca/openfisca-dummy-country/blob/\d+\.\d+\.\d+/openfisca_dummy_country/model/model\.py#L\d+-L\d+$')
