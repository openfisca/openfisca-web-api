# -*- coding: utf-8 -*-

from httplib import OK, NOT_FOUND
import json
from nose.tools import assert_equal
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


def test_error_code_non_existing_variable():
    response = subject.get('/variable/non_existing_variable')
    assert_equal(response.status_code, NOT_FOUND)


def test_return_code_existing_parameter():
    response = subject.get('/variable/birth')
    assert_equal(response.status_code, OK)


def test_input_variable_value():
    response = subject.get('/variable/birth')
    variable = json.loads(response.data)
    assert_equal(
        variable,
        {
            u"description": u"Date de naissance",
            u"valueType": u"Date",
            u"defaultValue": "1970-01-01",
            u"definitionPeriod": u"eternity",
            u"entity": u"individu",
            # u"source": u"https://github.com/openfisca/openfisca-dummy-country/blob/master/openfisca_dummy_country/model/model.py#L31-L35"
            }
        )
