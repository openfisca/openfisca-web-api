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
from nose.tools import assert_equal, assert_in, assert_not_in, assert_is_instance, assert_not_equal

from . import common


TARGET_URL = '/api/2/formula/'
INPUT_VARIABLE = 'salaire_de_base'
VALID_PERIOD = '2015-01'
VALID_DAY = VALID_PERIOD + '-01'
INVALID_PERIOD = 'herp'
VALID_FORMULA = 'salaire_net_a_payer'
DATED_FORMULA = 'allegement_fillon'
DATE_PARAM = 'apprentissage_contrat_debut'
DATE_PARAM_VALUE = VALID_PERIOD + '-03'
VALID_OTHER_FORMULA = 'salaire_imposable'
INVALID_FORMULA = 'inexistent'
PARAM_VALUE = 1300
VALID_QUERY_STRING = '{0}={1}'.format(INPUT_VARIABLE, PARAM_VALUE)
INVALID_QUERY_STRING = '{0}={1}'.format(INVALID_FORMULA, PARAM_VALUE)


def send(formula = VALID_FORMULA, method = 'GET', period = '', query_string = ''):
    if period:
        period += '/'

    target = TARGET_URL + period + formula + '?' + query_string

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
    assert_equal(send()['payload']['apiVersion'], '2.1.0')


def test_dated_formula_status_code():
    assert_equal(send(formula = DATED_FORMULA)['status_code'], 200)


def test_not_a_formula_status_code():
    assert_equal(send(formula = INPUT_VARIABLE)['status_code'], 422)


def test_not_a_formula_error_message():
    message = send(formula = INPUT_VARIABLE)['payload']['error']['message']

    assert_in(INPUT_VARIABLE, message)
    assert_in('input variable', message)
    assert_in('cannot be computed', message)
    assert_not_in('{', message)  # serialisation failed


def test_invalid_formula_status_code():
    assert_equal(send(formula = INVALID_FORMULA)['status_code'], 404)


def test_invalid_formula_error_message():
    message = send(formula = INVALID_FORMULA)['payload']['error']['message']

    assert_in(INVALID_FORMULA, message)
    assert_in('does not exist', message)
    assert_not_in('{', message)  # serialisation failed


def test_invalid_formula_params():
    params = send(formula = INVALID_FORMULA, query_string = VALID_QUERY_STRING)['payload']['params']

    assert_equal({INPUT_VARIABLE: PARAM_VALUE}, params)


def test_invalid_formula_with_valid_formula_status_code():
    assert_equal(send(formula = VALID_FORMULA + '+' + INVALID_FORMULA)['status_code'], 404)


def test_invalid_formula_with_valid_formula_error_message():
    message = send(formula = VALID_FORMULA + '+' + INVALID_FORMULA)['payload']['error']['message']

    assert_in(INVALID_FORMULA, message)
    assert_in('does not exist', message)
    assert_not_in('{', message)  # serialisation failed


def test_formula_value_without_params():
    value = send()['payload']['values'][VALID_FORMULA]
    assert_is_instance(value, float)
    assert_equal(value, 0)


def test_formula_value_with_params():
    value = send(query_string = VALID_QUERY_STRING)['payload']['values'][VALID_FORMULA]
    assert_is_instance(value, float)
    assert_not_equal(value, 0)


def test_formula_echo_params_without_params():
    params = send()['payload']['params']
    assert_equal({}, params)


def test_formula_echo_params_with_params():
    params = send(query_string = VALID_QUERY_STRING)['payload']['params']
    assert_equal({INPUT_VARIABLE: PARAM_VALUE}, params)


def test_echo_params_date():
    params = send(query_string = DATE_PARAM + '=' + DATE_PARAM_VALUE)['payload']['params']
    assert_equal({DATE_PARAM: DATE_PARAM_VALUE}, params)


def test_bad_params_status_code():
    assert_equal(send(query_string = INVALID_QUERY_STRING)['status_code'], 400)


def test_bad_params_error_message():
    message = send(query_string = INVALID_QUERY_STRING)['payload']['error']['message']

    assert_in(INVALID_FORMULA, message)
    assert_in('does not exist', message)
    assert_not_in('{', message)  # serialisation failed


def test_unnormalizable_params_status_code():
    assert_equal(send(query_string = 'birth=herp')['status_code'], 400)


def test_unnormalizable_params_error_message():
    message = send(query_string = 'birth=herp')['payload']['error']['message']

    assert_in('birth', message)
    assert_in('normalized', message)
    assert_not_in('{', message)  # serialisation failed


def test_multiple_formulas_value_without_params():
    values = send(formula = VALID_FORMULA + '+' + VALID_OTHER_FORMULA)['payload']['values']

    for formula_name in (VALID_FORMULA, VALID_OTHER_FORMULA):
        assert_in(formula_name, values)
        assert_is_instance(values[formula_name], float)
        assert_equal(values[formula_name], 0)


def test_period_year():
    assert_equal(send(period = '2012')['payload']['period'], ['year', [2012, 1, 1], 1])


def test_period_month():
    assert_equal(send(period = '2013-02')['payload']['period'], ['month', [2013, 2, 1], 1])


def test_invalid_period_status_code():
    assert_equal(send(period = INVALID_PERIOD)['status_code'], 400)


def test_invalid_period_error_message():
    message = send(period = INVALID_PERIOD)['payload']['error']['message']

    assert_in(INVALID_PERIOD, message)
    assert_in('could not be parsed', message)
    assert_not_in('{', message)  # serialisation failed


def test_invalid_period_day_status_code():
    assert_equal(send(period = VALID_DAY)['status_code'], 400)


def test_invalid_period_day_error_message():
    message = send(period = VALID_DAY)['payload']['error']['message']

    assert_in(VALID_DAY, message)
    assert_in('year', message)
    assert_in('month', message)
    assert_not_in('{', message)  # serialisation failed
