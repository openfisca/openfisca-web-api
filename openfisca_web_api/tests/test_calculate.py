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


import copy
import json

from nose.tools import assert_equal, assert_in, assert_is_instance
from webob import Request

from . import common


test_case = {
    'scenarios': [
        {
            'test_case': {
                'familles': [
                    {
                        'parents': ['ind0', 'ind1'],
                        },
                    ],
                'foyers_fiscaux': [
                    {
                        'declarants': ['ind0', 'ind1'],
                        },
                    ],
                'individus': [
                    {'id': 'ind0', 'sali': 15000},
                    {'id': 'ind1'},
                    ],
                'menages': [
                    {
                        'conjoint': 'ind1',
                        'personne_de_reference': 'ind0',
                        },
                    ],
                },
            'period': '2013',
            },
        ],
    'variables': ['revdisp'],
    }


def setup_module(module):
    common.get_or_load_app()


def test_calculate_without_body():
    req = Request.blank('/api/1/calculate', headers = (('Content-Type', 'application/json'),), method = 'POST')
    res = req.get_response(common.app)
    assert_equal(res.status_code, 400)


def test_calculate_with_invalid_body():
    req = Request.blank(
        '/api/1/calculate',
        body = 'XXX',
        headers = (('Content-Type', 'application/json'),),
        method = 'POST',
        )
    res = req.get_response(common.app)
    assert_equal(res.status_code, 400)


def test_calculate_with_test_case():
    req = Request.blank(
        '/api/1/calculate',
        body = json.dumps(test_case),
        headers = (('Content-Type', 'application/json'),),
        method = 'POST',
        )
    res = req.get_response(common.app)
    assert_equal(res.status_code, 200)
    res_json = json.loads(res.body)
    assert_is_instance(res_json, dict)
    assert_in('value', res_json)


def test_calculate_with_trace():
    test_case_with_trace = copy.deepcopy(test_case)
    test_case_with_trace['trace'] = True
    req = Request.blank(
        '/api/1/calculate',
        body = json.dumps(test_case_with_trace),
        headers = (('Content-Type', 'application/json'),),
        method = 'POST',
        )
    res = req.get_response(common.app)
    assert_equal(res.status_code, 200)
    res_json = json.loads(res.body)
    assert_is_instance(res_json, dict)
    assert_in('value', res_json)
    assert_in('tracebacks', res_json)
