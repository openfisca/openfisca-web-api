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
QUERY_STRING = '?salaire_de_base=1300'


def send(formula = 'salaire_net_a_payer', method = 'GET', with_query_string = False):
    target = TARGET_URL + formula

    if with_query_string:
        target += QUERY_STRING

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


def test_invalid_formula_status_code():
    assert_equal(send(formula = 'inexistent')['status_code'], 400)


def test_invalid_formula_error():
    assert_equal(
        send(formula = 'inexistent')['payload']['error']['message'],
        'Invalid formula name in request URL'
        )


def test_invalid_formula_value():
    assert_not_in('value', send(formula = 'inexistent')['payload'])


def test_invalid_formula_params():
    assert_equal(
        {'salaire_de_base': 1300},
        send(formula = 'inexistent')['payload']['params']
        )


def test_formula_value_without_params():
    value = send()['payload']['value']
    assert_is_instance(value, float)
    assert_equal(value, 0)


def test_formula_value_with_params():
    value = send(with_query_string = True)['payload']['value']
    assert_is_instance(value, float)
    assert_not_equal(value, 0)


def test_formula_echo_params_without_params():
    params = send()['payload']['params']
    assert_equal({}, params)


def test_formula_echo_params_with_params():
    params = send()['payload']['params']
    assert_equal({'salaire_de_base': 1300}, params)
