# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014, 2015 OpenFisca Team
# https://github.com/openfisca
#
# This file is part of OpenFisca.
#
# OpenFisca is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import json

from webob import Request
from nose.tools import *
from unittest.case import SkipTest

from . import common


TARGET_URL = '/api/1/formula/'
INPUT_VARIABLE = 'salaire_de_base'
VALID_FORMULA = 'salaire_net_a_payer'
INVALID_FORMULA = 'inexistent'
PARAM_VALUE = 1300
VALID_QUERY_STRING = '?{0}={1}'.format(INPUT_VARIABLE, PARAM_VALUE)
INVALID_QUERY_STRING = '?{0}={1}'.format(INVALID_FORMULA, PARAM_VALUE)


def send(formula = VALID_FORMULA, method = 'GET', query_string = ''):
    target = TARGET_URL + formula + query_string

    req = Request.blank(target, method = method)
    res = req.get_response(common.app)

    return {
        'status_code': res.status_code,
        'payload': json.loads(res.body)
        }


def setup_module(module):
    common.get_or_load_app()


def test_formula_get_status_code():
    assert_equal(send()['status_code'], 200)


def test_formula_post_status_code():
    assert_equal(send(method = 'POST')['status_code'], 405)


def test_formula_put_status_code():
    assert_equal(send(method = 'PUT')['status_code'], 405)


def test_formula_delete_status_code():
    assert_equal(send(method = 'DELETE')['status_code'], 405)


def test_formula_api_version():
    assert_equal(send()['payload']['apiVersion'], 1)


def test_not_a_formula_status_code():
    assert_equal(send(formula = INPUT_VARIABLE)['status_code'], 422)


def test_not_a_formula_error_message():
    message = send(formula = INPUT_VARIABLE)['payload']['error']['message']
    assert_in(INPUT_VARIABLE, message)
    assert_in('input variable', message)
    assert_in('cannot be computed', message)


def test_not_a_formula_value():
    assert_not_in('value', send(formula = INPUT_VARIABLE)['payload'])


def test_invalid_formula_status_code():
    assert_equal(send(formula = INVALID_FORMULA)['status_code'], 404)


def test_invalid_formula_error_message():
    message = send(formula = INVALID_FORMULA)['payload']['error']['message']
    assert_in(INVALID_FORMULA, message)
    assert_in('does not exist', message)


def test_invalid_formula_value():
    assert_not_in('value', send(formula = INVALID_FORMULA)['payload'])


def test_invalid_formula_params():
    params = send(formula = INVALID_FORMULA, query_string = VALID_QUERY_STRING)['payload']['params']

    assert_equal({INPUT_VARIABLE: PARAM_VALUE}, params)


def test_formula_value_without_params():
    value = send()['payload']['value']
    assert_is_instance(value, float)
    assert_equal(value, 0)


def test_formula_value_with_params():
    value = send(query_string = VALID_QUERY_STRING)['payload']['value']
    assert_is_instance(value, float)
    assert_not_equal(value, 0)


def test_formula_echo_params_without_params():
    params = send()['payload']['params']
    assert_equal({}, params)


def test_formula_echo_params_with_params():
    params = send(query_string = VALID_QUERY_STRING)['payload']['params']
    assert_equal({INPUT_VARIABLE: PARAM_VALUE}, params)


def test_bad_params_status_code():
    assert_equal(send(query_string = INVALID_QUERY_STRING)['status_code'], 400)


def test_bad_params_error_message():
    message = send(query_string = INVALID_QUERY_STRING)['payload']['error']['message']

    assert_in(INVALID_FORMULA, message)
    assert_in('does not exist', message)


def test_bad_params_value():
    assert_not_in('value', send(query_string = INVALID_QUERY_STRING)['payload'])


def test_bad_period_status_code():
    assert_equal(send(query_string = '?period=herp')['status_code'], 400)


def test_bad_period_error_message():
    message = send(query_string = '?period=herp')['payload']['error']['message']

    assert_in('herp', message)
    assert_in('could not be parsed', message)


def test_bad_period_value():
    assert_not_in('value', send(query_string = '?period=herp')['payload'])
