# -*- coding: utf-8 -*-

from httplib import OK  # NOT_FOUND
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
